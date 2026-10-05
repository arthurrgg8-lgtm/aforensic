import sqlite3
import os
import re
from core.db_utils import connect_readonly_sqlite

class ContactsParser:
    """
    Parses Android Contacts from Content Provider (content://contacts/data)
    or offline SQLite database (contacts2.db).
    """

    def __init__(self, raw_data_or_db_path=None, truecaller_path=None):
        self.source = raw_data_or_db_path
        self.truecaller_path = truecaller_path
        self.contacts = []
        self.number_to_name = {}

    def parse(self):
        if isinstance(self.source, list):
            self._parse_content_provider_rows(self.source)
        elif isinstance(self.source, str) and os.path.exists(self.source):
            self._parse_sqlite_db(self.source)

        if self.truecaller_path and os.path.exists(self.truecaller_path):
            self._parse_truecaller_db(self.truecaller_path)

        return self.contacts

    def resolve_number(self, phone_number):
        if not phone_number:
            return "Unknown Contact"
        clean = re.sub(r'[^0-9+]', '', phone_number)
        if clean in self.number_to_name:
            return self.number_to_name[clean]
        if len(clean) >= 10 and clean[-10:] in self.number_to_name:
            return self.number_to_name[clean[-10:]]
        return "Unknown Contact"

    def _parse_content_provider_rows(self, rows):
        grouped = {}
        for row in rows:
            name = row.get("display_name") or row.get("name") or "Unnamed Contact"
            phone = row.get("data1") or row.get("number") or ""
            email = row.get("data2") if "@" in str(row.get("data2", "")) else ""

            if name not in grouped:
                grouped[name] = {"phones": set(), "emails": set()}
            if phone:
                grouped[name]["phones"].add(phone)
            if email:
                grouped[name]["emails"].add(email)

        for name, data in grouped.items():
            phones = list(data["phones"])
            record = {
                "source": "Android Contacts Provider",
                "first_name": name,
                "last_name": "",
                "name": name,
                "phone_numbers": phones,
                "email_addresses": list(data["emails"]),
                "organization": "",
                "job_title": "",
                "notes": ""
            }
            self.contacts.append(record)
            for p in phones:
                clean_p = re.sub(r'[^0-9+]', '', p)
                if clean_p:
                    self.number_to_name[clean_p] = name
                    if len(clean_p) >= 10:
                        self.number_to_name[clean_p[-10:]] = name

    def _parse_sqlite_db(self, db_path):
        try:
            conn = connect_readonly_sqlite(db_path)
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()

            query = """
            SELECT 
                r._id,
                r.display_name,
                d1.data1 as phone_number,
                d2.data1 as email_address
            FROM raw_contacts r
            LEFT JOIN data d1 ON r._id = d1.raw_contact_id AND d1.mimetype_id = (SELECT _id FROM mimetypes WHERE mimetype = 'vnd.android.cursor.item/phone_v2')
            LEFT JOIN data d2 ON r._id = d2.raw_contact_id AND d2.mimetype_id = (SELECT _id FROM mimetypes WHERE mimetype = 'vnd.android.cursor.item/email_v2')
            WHERE r.display_name IS NOT NULL
            """
            cur.execute(query)
            grouped = {}
            for row in cur.fetchall():
                name = row["display_name"] or "Unnamed Contact"
                phone = row["phone_number"] or ""
                email = row["email_address"] or ""

                if name not in grouped:
                    grouped[name] = {"phones": set(), "emails": set()}
                if phone:
                    grouped[name]["phones"].add(phone)
                if email:
                    grouped[name]["emails"].add(email)

            for name, data in grouped.items():
                phones = list(data["phones"])
                self.contacts.append({
                    "source": "contacts2.db",
                    "first_name": name,
                    "last_name": "",
                    "name": name,
                    "phone_numbers": phones,
                    "email_addresses": list(data["emails"]),
                    "organization": "",
                    "job_title": "",
                    "notes": ""
                })
                for p in phones:
                    clean_p = re.sub(r'[^0-9+]', '', p)
                    if clean_p:
                        self.number_to_name[clean_p] = name
                        if len(clean_p) >= 10:
                            self.number_to_name[clean_p[-10:]] = name
            conn.close()
        except Exception:
            pass

    def _parse_truecaller_db(self, tc_path):
        try:
            conn = connect_readonly_sqlite(tc_path)
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()
            cur.execute("SELECT name, phone FROM tc_contacts WHERE phone IS NOT NULL")
            for row in cur.fetchall():
                name = row["name"] or ""
                phone = row["phone"] or ""
                clean_p = re.sub(r'[^0-9+]', '', phone)
                if name and clean_p:
                    self.contacts.append({
                        "source": "Truecaller Cache",
                        "first_name": name,
                        "last_name": "",
                        "name": f"[Truecaller] {name}",
                        "phone_numbers": [phone],
                        "email_addresses": [],
                        "organization": "",
                        "job_title": "",
                        "notes": ""
                    })
                    if clean_p not in self.number_to_name:
                        self.number_to_name[clean_p] = f"[Truecaller] {name}"
            conn.close()
        except Exception:
            pass
