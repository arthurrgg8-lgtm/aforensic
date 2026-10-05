import sqlite3
import os
import re
from core.time_utils import unix_to_datetime, format_datetime_utc, format_datetime_local
from core.db_utils import connect_readonly_sqlite

class SMSParser:
    """
    Parses Android SMS/MMS messages from live Content Providers (content://sms)
    or offline SQLite databases (mmssms.db / bugle_db).
    """

    def __init__(self, raw_data_or_db_path):
        self.source = raw_data_or_db_path
        self.messages = []

    def parse(self):
        if isinstance(self.source, list):
            return self._parse_content_provider_rows(self.source)
        elif isinstance(self.source, str) and os.path.exists(self.source):
            return self._parse_sqlite_db(self.source)
        return []

    def _parse_content_provider_rows(self, rows):
        for row in rows:
            date_val = row.get("date") or row.get("date_sent")
            dt = unix_to_datetime(date_val)

            type_val = str(row.get("type", "1"))
            # Type 1: Received/Incoming, Type 2: Sent/Outgoing
            direction = "Outgoing" if type_val == "2" else "Incoming"

            sender = row.get("address", "Unknown")
            body = row.get("body", "")

            self.messages.append({
                "source": "Android Telephony Provider",
                "message_id": row.get("_id", "N/A"),
                "sender": sender,
                "recipient": "Self (Device Owner)" if direction == "Incoming" else sender,
                "direction": direction,
                "text": body,
                "timestamp_utc": format_datetime_utc(dt),
                "timestamp_local": format_datetime_local(dt),
                "raw_datetime": dt,
                "service": "SMS/MMS",
                "is_read": bool(int(row.get("read", 1) or 1))
            })
        return self.messages

    def _parse_sqlite_db(self, db_path):
        try:
            conn = connect_readonly_sqlite(db_path)
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()

            cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = set(r[0] for r in cur.fetchall())

            if "sms" in tables:
                query = "SELECT _id, address, date, date_sent, read, type, body, service_center FROM sms ORDER BY date DESC"
                cur.execute(query)
                for row in cur.fetchall():
                    dt = unix_to_datetime(row["date"])
                    direction = "Outgoing" if row["type"] == 2 else "Incoming"
                    self.messages.append({
                        "source": "mmssms.db",
                        "message_id": str(row["_id"]),
                        "sender": row["address"] or "Unknown",
                        "recipient": "Self (Device Owner)" if direction == "Incoming" else (row["address"] or "Unknown"),
                        "direction": direction,
                        "text": row["body"] or "",
                        "timestamp_utc": format_datetime_utc(dt),
                        "timestamp_local": format_datetime_local(dt),
                        "raw_datetime": dt,
                        "service": "SMS/MMS",
                        "is_read": bool(row["read"])
                    })
            conn.close()
        except Exception:
            pass
        return self.messages
