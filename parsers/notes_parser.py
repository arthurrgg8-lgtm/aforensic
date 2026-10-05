"""
Notes and Memos Parser for aforensic.
Extracts and normalizes notes from:
- Samsung Notes (snotes.db, memo.db)
- Xiaomi / Redmi / POCO Notes (note.db, notes.db)
- Oppo / Realme / OnePlus Notes (note.db)
- Vivo / iQOO Notes
- Google Keep memo caches
- ColorNote (colornote.db) and standalone .txt / .memo files
"""

import sqlite3
import os
import json
import re
from typing import List, Dict, Any, Optional
from core.time_utils import unix_to_datetime, format_datetime_utc, format_datetime_local, format_epoch_timestamp
from core.db_utils import connect_readonly_sqlite


class NotesParser:
    def __init__(self, notes_db_path: Optional[str] = None, notes_dir: Optional[str] = None):
        self.db_path = notes_db_path
        self.notes_dir = notes_dir
        self.notes: List[Dict[str, Any]] = []

    def parse(self) -> List[Dict[str, Any]]:
        if self.db_path and os.path.exists(self.db_path):
            self._parse_notes_db(self.db_path)

        if self.notes_dir and os.path.exists(self.notes_dir):
            self._scan_notes_directory(self.notes_dir)

        return self.notes

    def parse_all(self, base_dir: str) -> List[Dict[str, Any]]:
        """
        Walks base_dir and parses all discovered OEM notes databases and memo files.
        """
        if not os.path.exists(base_dir):
            return self.notes

        for root, _, files in os.walk(base_dir):
            for f in files:
                full_p = os.path.join(root, f)
                f_lower = f.lower()
                if f_lower in ("snotes.db", "notes.db", "note.db", "memo.db", "colornote.db") or (f_lower.endswith(".db") and "note" in f_lower):
                    self._parse_notes_db(full_p)
                elif f_lower.endswith((".memo", ".note")):
                    self._parse_single_memo(full_p)

        self._scan_notes_directory(base_dir)
        return self.notes

    def _parse_notes_db(self, db_path: str):
        try:
            conn = connect_readonly_sqlite(db_path)
            if not conn:
                return
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()

            cur.execute("SELECT name FROM sqlite_master WHERE type='table'")
            tables = set(r[0].lower() for r in cur.fetchall())

            # 1. Samsung Notes (notes / snotes)
            if "notes" in tables or "snotes" in tables or "note" in tables:
                tbl = next(t for t in ["snotes", "notes", "note"] if t in tables)
                cur.execute(f"SELECT * FROM {tbl} LIMIT 500")
                for row in cur.fetchall():
                    keys = [k.lower() for k in row.keys()]
                    title = row["title"] if "title" in keys else "Untitled Note"
                    content = row["content"] if "content" in keys else (row["body"] if "body" in keys else (row["snippet"] if "snippet" in keys else ""))
                    mod_time = row["modified_time"] if "modified_time" in keys else (row["created_time"] if "created_time" in keys else (row["date"] if "date" in keys else 0))
                    
                    self.notes.append({
                        "source": f"OEM Notes ({os.path.basename(db_path)})",
                        "app": "Notes",
                        "title": title or "Untitled Note",
                        "content": str(content) if content else "",
                        "snippet": str(content)[:200] if content else "",
                        "folder": "Notes",
                        "account": "Device Account",
                        "created_time": format_epoch_timestamp(mod_time),
                        "modified_time": format_epoch_timestamp(mod_time),
                        "modified_utc": format_epoch_timestamp(mod_time),
                        "modified_local": format_epoch_timestamp(mod_time, offset_hours=5.75)
                    })

            # 2. ColorNote (colornote.db / notelist)
            elif "notelist" in tables:
                cur.execute("SELECT * FROM notelist LIMIT 500")
                for row in cur.fetchall():
                    keys = [k.lower() for k in row.keys()]
                    title = row["title"] if "title" in keys else "ColorNote"
                    content = row["note"] if "note" in keys else ""
                    mod_time = row["modified_date"] if "modified_date" in keys else 0

                    self.notes.append({
                        "source": "ColorNote",
                        "app": "ColorNote",
                        "title": title or "Untitled Note",
                        "content": str(content) if content else "",
                        "snippet": str(content)[:200] if content else "",
                        "folder": "ColorNote",
                        "account": "Local Device",
                        "created_time": format_epoch_timestamp(mod_time),
                        "modified_time": format_epoch_timestamp(mod_time),
                        "modified_utc": format_epoch_timestamp(mod_time),
                        "modified_local": format_epoch_timestamp(mod_time, offset_hours=5.75)
                    })
            conn.close()
        except Exception:
            pass

    def _parse_single_memo(self, fp: str):
        try:
            with open(fp, "r", encoding="utf-8", errors="ignore") as fh:
                text = fh.read()
            stat = os.stat(fp)
            self.notes.append({
                "source": "OEM Memo",
                "app": "Memo",
                "title": os.path.splitext(os.path.basename(fp))[0],
                "content": text,
                "snippet": text[:200],
                "folder": os.path.basename(os.path.dirname(fp)),
                "account": "Local Storage",
                "created_time": format_epoch_timestamp(stat.st_mtime),
                "modified_time": format_epoch_timestamp(stat.st_mtime),
                "modified_utc": format_epoch_timestamp(stat.st_mtime),
                "modified_local": format_epoch_timestamp(stat.st_mtime, offset_hours=5.75)
            })
        except Exception:
            pass

    def _scan_notes_directory(self, notes_dir: str):
        for root, _, files in os.walk(notes_dir):
            for f in files:
                if f.endswith((".txt", ".memo")):
                    fp = os.path.join(root, f)
                    self._parse_single_memo(fp)
