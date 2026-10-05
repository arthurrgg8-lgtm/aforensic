import sqlite3
import os
import re
from core.time_utils import unix_to_datetime, format_datetime_utc, format_datetime_local
from core.db_utils import connect_readonly_sqlite

class WhatsAppParser:
    """
    Parses Android WhatsApp databases (msgstore.db, wa.db) and shared media.
    """

    def __init__(self, db_path=None, media_dir=None):
        self.db_path = db_path
        self.media_dir = media_dir
        self.messages = []

    def parse(self):
        if self.db_path and os.path.exists(self.db_path):
            self._parse_msgstore_db(self.db_path)
        return self.messages

    def _parse_msgstore_db(self, db_path):
        try:
            conn = connect_readonly_sqlite(db_path)
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()

            cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = set(r[0] for r in cur.fetchall())

            # Modern WhatsApp (messages / message / jid tables)
            if "message" in tables and "chat" in tables:
                query = """
                SELECT 
                    m._id,
                    m.key_id,
                    m.from_me,
                    m.timestamp,
                    m.text_data,
                    m.message_type,
                    c.subject as chat_name,
                    j.raw_string as chat_jid
                FROM message m
                LEFT JOIN chat c ON m.chat_row_id = c._id
                LEFT JOIN jid j ON c.jid_row_id = j._id
                ORDER BY m.timestamp DESC
                """
                cur.execute(query)
                for row in cur.fetchall():
                    dt = unix_to_datetime(row["timestamp"])
                    is_me = bool(row["from_me"])
                    chat_name = row["chat_name"] or row["chat_jid"] or "WhatsApp Chat"
                    jid = row["chat_jid"] or "N/A"

                    self.messages.append({
                        "source": "WhatsApp (msgstore.db)",
                        "message_id": str(row["key_id"] or row["_id"]),
                        "sender": "Self" if is_me else jid,
                        "recipient": jid if is_me else "Self",
                        "chat_name": chat_name,
                        "chat_jid": jid,
                        "direction": "Outgoing" if is_me else "Incoming",
                        "text": row["text_data"] or "",
                        "media_type": "Text" if row["message_type"] == 0 else f"Media (Type {row['message_type']})",
                        "timestamp_utc": format_datetime_utc(dt),
                        "timestamp_local": format_datetime_local(dt),
                        "raw_datetime": dt
                    })

            # Legacy WhatsApp (messages table)
            elif "messages" in tables:
                query = """
                SELECT 
                    _id, key_id, key_remote_jid, key_from_me, data, timestamp, media_wa_type
                FROM messages
                ORDER BY timestamp DESC
                """
                cur.execute(query)
                for row in cur.fetchall():
                    dt = unix_to_datetime(row["timestamp"])
                    is_me = bool(row["key_from_me"])
                    jid = row["key_remote_jid"] or "Unknown"

                    self.messages.append({
                        "source": "WhatsApp Legacy",
                        "message_id": str(row["key_id"] or row["_id"]),
                        "sender": "Self" if is_me else jid,
                        "recipient": jid if is_me else "Self",
                        "chat_name": jid,
                        "chat_jid": jid,
                        "direction": "Outgoing" if is_me else "Incoming",
                        "text": row["data"] or "",
                        "media_type": "Text" if row["media_wa_type"] == "0" else f"Media ({row['media_wa_type']})",
                        "timestamp_utc": format_datetime_utc(dt),
                        "timestamp_local": format_datetime_local(dt),
                        "raw_datetime": dt
                    })
            conn.close()
        except Exception:
            pass
