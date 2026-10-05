import sqlite3
import os
from core.time_utils import unix_to_datetime, format_datetime_utc, format_datetime_local
from core.db_utils import connect_readonly_sqlite

class CallsParser:
    """
    Parses Android Call Logs from Content Provider (content://call_log/calls)
    or offline SQLite database (calllog.db).
    """

    CALL_TYPE_MAP = {
        "1": "Incoming (Answered)",
        "2": "Outgoing",
        "3": "Missed",
        "4": "Voicemail",
        "5": "Rejected",
        "6": "Blocked",
        1: "Incoming (Answered)",
        2: "Outgoing",
        3: "Missed",
        4: "Voicemail",
        5: "Rejected",
        6: "Blocked"
    }

    def __init__(self, raw_data_or_db_path):
        self.source = raw_data_or_db_path
        self.calls = []

    def parse(self):
        if isinstance(self.source, list):
            return self._parse_content_provider_rows(self.source)
        elif isinstance(self.source, str) and os.path.exists(self.source):
            return self._parse_sqlite_db(self.source)
        return []

    def _format_duration(self, seconds):
        try:
            s = int(seconds)
            if s == 0:
                return "0s"
            m, s_rem = divmod(s, 60)
            h, m_rem = divmod(m, 60)
            if h > 0:
                return f"{h}h {m_rem}m {s_rem}s"
            elif m > 0:
                return f"{m}m {s_rem}s"
            return f"{s}s"
        except Exception:
            return "0s"

    def _parse_content_provider_rows(self, rows):
        for row in rows:
            dt = unix_to_datetime(row.get("date"))
            call_type = row.get("type", 1)
            status = self.CALL_TYPE_MAP.get(call_type, "Incoming (Answered)")

            dur = int(row.get("duration", 0) or 0)
            contact_name = row.get("name") or "Unknown Contact"
            number = row.get("number", "Unknown")

            self.calls.append({
                "source": "Android CallLog Provider",
                "call_id": row.get("_id", "N/A"),
                "contact_name": contact_name,
                "number": number,
                "status": status,
                "duration": dur,
                "duration_formatted": self._format_duration(dur),
                "timestamp_utc": format_datetime_utc(dt),
                "timestamp_local": format_datetime_local(dt),
                "raw_datetime": dt,
                "service_provider": "Cellular Network"
            })
        return self.calls

    def _parse_sqlite_db(self, db_path):
        try:
            conn = connect_readonly_sqlite(db_path)
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()

            query = "SELECT _id, number, date, duration, type, name FROM calls ORDER BY date DESC"
            cur.execute(query)
            for row in cur.fetchall():
                dt = unix_to_datetime(row["date"])
                dur = int(row["duration"] or 0)
                status = self.CALL_TYPE_MAP.get(row["type"], "Incoming (Answered)")

                self.calls.append({
                    "source": "calllog.db",
                    "call_id": str(row["_id"]),
                    "contact_name": row["name"] or "Unknown Contact",
                    "number": row["number"] or "Unknown",
                    "status": status,
                    "duration": dur,
                    "duration_formatted": self._format_duration(dur),
                    "timestamp_utc": format_datetime_utc(dt),
                    "timestamp_local": format_datetime_local(dt),
                    "raw_datetime": dt,
                    "service_provider": "Cellular Network"
                })
            conn.close()
        except Exception:
            pass
        return self.calls
