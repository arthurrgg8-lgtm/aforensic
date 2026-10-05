import sqlite3
import os
import datetime
from core.time_utils import unix_to_datetime, format_datetime_utc, format_datetime_local
from core.db_utils import connect_readonly_sqlite

class ChromeParser:
    """
    Parses Android Chrome, Brave, and Samsung Internet Browser SQLite History & Visits.
    """

    def __init__(self, history_db_path=None):
        self.db_path = history_db_path
        self.history = []

    def parse(self):
        if not self.db_path or not os.path.exists(self.db_path):
            return []

        try:
            conn = connect_readonly_sqlite(self.db_path)
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()

            # Chrome History: urls & visits tables
            query = """
            SELECT 
                u.id,
                u.url,
                u.title,
                u.visit_count,
                u.typed_count,
                u.last_visit_time
            FROM urls u
            ORDER BY u.last_visit_time DESC
            """
            cur.execute(query)
            for row in cur.fetchall():
                # WebKit / Chrome time: microseconds since Jan 1, 1601 UTC
                raw_time = row["last_visit_time"]
                dt = None
                if raw_time and raw_time > 0:
                    try:
                        # Convert Chrome timestamp (micros since 1601-01-01) to Unix epoch
                        epoch_delta = 11644473600 # seconds between 1601 and 1970
                        unix_secs = (raw_time / 1000000.0) - epoch_delta
                        dt = unix_to_datetime(unix_secs)
                    except Exception:
                        dt = unix_to_datetime(raw_time)

                self.history.append({
                    "source": "Chrome / WebKit History",
                    "url": row["url"] or "",
                    "title": row["title"] or "Untitled Web Page",
                    "visit_count": row["visit_count"] or 1,
                    "typed_count": row["typed_count"] or 0,
                    "timestamp_utc": format_datetime_utc(dt),
                    "timestamp_local": format_datetime_local(dt),
                    "raw_datetime": dt
                })
            conn.close()
        except Exception:
            pass
        return self.history
