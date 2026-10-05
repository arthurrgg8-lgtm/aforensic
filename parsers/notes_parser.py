import sqlite3
import os
import json
import re
from core.time_utils import unix_to_datetime, format_datetime_utc, format_datetime_local
from core.db_utils import connect_readonly_sqlite

class NotesParser:
    """
    Parses Android Notes (Samsung Notes, Google Keep, Xiaomi Notes, ColorNotes)
    from extracted SQLite databases or dumped memo files.
    """

    def __init__(self, notes_db_path=None, notes_dir=None):
        self.db_path = notes_db_path
        self.notes_dir = notes_dir
        self.notes = []

    def parse(self):
        if self.db_path and os.path.exists(self.db_path):
            self._parse_notes_db(self.db_path)

        if self.notes_dir and os.path.exists(self.notes_dir):
            self._scan_notes_directory(self.notes_dir)

        return self.notes

    def _parse_notes_db(self, db_path):
        try:
            conn = connect_readonly_sqlite(db_path)
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()

            cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = set(r[0].lower() for r in cur.fetchall())

            # 1. Samsung Notes (notes / snotes)
            if "notes" in tables or "snotes" in tables:
                tbl = "notes" if "notes" in tables else "snotes"
                cur.execute(f"SELECT * FROM {tbl} LIMIT 500")
                for row in cur.fetchall():
                    keys = row.keys()
                    title = row["title"] if "title" in keys else "Untitled Note"
                    content = row["content"] if "content" in keys else (row["body"] if "body" in keys else "")
                    mod_time = row["modified_time"] if "modified_time" in keys else (row["created_time"] if "created_time" in keys else 0)
                    dt = unix_to_datetime(mod_time)

                    self.notes.append({
                        "source": "Samsung Notes",
                        "title": title or "Untitled Note",
                        "snippet": str(content)[:200] if content else "",
                        "full_content": str(content) if content else "",
                        "folder": "Samsung Notes",
                        "account": "Samsung Account",
                        "tags": [],
                        "modified_utc": format_datetime_utc(dt),
                        "modified_local": format_datetime_local(dt),
                        "raw_datetime": dt
                    })

            # 2. ColorNote (colornote.db / notes table)
            elif "colornote" in tables or "notelist" in tables:
                cur.execute("SELECT * FROM notelist LIMIT 500")
                for row in cur.fetchall():
                    keys = row.keys()
                    title = row["title"] if "title" in keys else "ColorNote"
                    content = row["note"] if "note" in keys else ""
                    mod_time = row["modified_date"] if "modified_date" in keys else 0
                    dt = unix_to_datetime(mod_time)

                    self.notes.append({
                        "source": "ColorNote",
                        "title": title or "Untitled Note",
                        "snippet": str(content)[:200] if content else "",
                        "full_content": str(content) if content else "",
                        "folder": "ColorNote",
                        "account": "Local Device",
                        "tags": [],
                        "modified_utc": format_datetime_utc(dt),
                        "modified_local": format_datetime_local(dt),
                        "raw_datetime": dt
                    })
            conn.close()
        except Exception:
            pass

    def _scan_notes_directory(self, notes_dir):
        for root, _, files in os.walk(notes_dir):
            for f in files:
                if f.endswith((".txt", ".json", ".memo")):
                    fp = os.path.join(root, f)
                    try:
                        with open(fp, "r", encoding="utf-8", errors="ignore") as fh:
                            text = fh.read()
                        stat = os.stat(fp)
                        dt = unix_to_datetime(stat.st_mtime)

                        self.notes.append({
                            "source": "Memo File",
                            "title": os.path.splitext(f)[0],
                            "snippet": text[:200],
                            "full_content": text,
                            "folder": os.path.basename(root),
                            "account": "Local Storage",
                            "tags": [],
                            "modified_utc": format_datetime_utc(dt),
                            "modified_local": format_datetime_local(dt),
                            "raw_datetime": dt
                        })
                    except Exception:
                        pass
