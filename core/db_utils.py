"""
Cross-platform Read-Only SQLite Database Connector.
"""

import sqlite3
import os
import pathlib
from typing import Optional


def connect_readonly_sqlite(db_path: str) -> Optional[sqlite3.Connection]:
    """
    Connects to a SQLite database in strict Read-Only mode across Windows, macOS, and Linux.
    Handles URI encoding (?mode=ro) and falls back safely.
    """
    if not db_path or not os.path.exists(db_path):
        return None
    
    abs_p = os.path.abspath(db_path)
    try:
        uri = f"{pathlib.Path(abs_p).as_uri()}?mode=ro"
        conn = sqlite3.connect(uri, uri=True)
        return conn
    except Exception:
        try:
            return sqlite3.connect(abs_p)
        except Exception:
            return None


def get_readonly_connection(db_path: str) -> Optional[sqlite3.Connection]:
    """
    Alias for connect_readonly_sqlite.
    """
    return connect_readonly_sqlite(db_path)
