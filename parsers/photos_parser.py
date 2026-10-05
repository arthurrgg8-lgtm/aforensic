import sqlite3
import os
import struct
from core.time_utils import unix_to_datetime, format_datetime_utc, format_datetime_local
from core.db_utils import connect_readonly_sqlite

class PhotosParser:
    """
    Parses Android Media Provider (content://media/external/images/media)
    and external.db SQLite databases, extracting camera timestamps and EXIF GPS coordinates.
    """

    def __init__(self, raw_data_or_db_path=None, photos_dir=None):
        self.source = raw_data_or_db_path
        self.photos_dir = photos_dir
        self.photos = []

    def parse(self):
        if isinstance(self.source, list):
            self._parse_content_provider_rows(self.source)
        elif isinstance(self.source, str) and os.path.exists(self.source):
            self._parse_sqlite_db(self.source)

        if self.photos_dir and os.path.exists(self.photos_dir):
            self._scan_photos_dir(self.photos_dir)

        return self.photos

    def _parse_content_provider_rows(self, rows):
        for row in rows:
            date_val = row.get("date_added") or row.get("date_modified") or row.get("datetaken")
            dt = unix_to_datetime(date_val)

            lat = row.get("latitude")
            lon = row.get("longitude")
            try:
                lat_f = float(lat) if lat is not None else None
                lon_f = float(lon) if lon is not None else None
            except Exception:
                lat_f, lon_f = None, None

            has_gps = bool(lat_f and lon_f and lat_f != 0 and lon_f != 0)

            self.photos.append({
                "source": "Android MediaStore Provider",
                "filename": row.get("_display_name") or row.get("title") or "image.jpg",
                "directory": row.get("bucket_display_name", "DCIM/Camera"),
                "timestamp_utc": format_datetime_utc(dt),
                "timestamp_local": format_datetime_local(dt),
                "raw_datetime": dt,
                "latitude": lat_f if has_gps else None,
                "longitude": lon_f if has_gps else None,
                "has_gps": has_gps,
                "is_favorite": False
            })

    def _parse_sqlite_db(self, db_path):
        try:
            conn = connect_readonly_sqlite(db_path)
            conn.row_factory = sqlite3.Row
            cur = conn.cursor()

            query = """
            SELECT 
                _id, _display_name, bucket_display_name, datetaken, date_added, latitude, longitude
            FROM files
            WHERE media_type = 1 OR mime_type LIKE 'image/%'
            ORDER BY date_added DESC
            """
            cur.execute(query)
            for row in cur.fetchall():
                dt = unix_to_datetime(row["datetaken"] or row["date_added"])
                lat, lon = row["latitude"], row["longitude"]
                has_gps = bool(lat and lon and lat != 0 and lon != 0)

                self.photos.append({
                    "source": "external.db",
                    "filename": row["_display_name"] or "IMG.jpg",
                    "directory": row["bucket_display_name"] or "DCIM",
                    "timestamp_utc": format_datetime_utc(dt),
                    "timestamp_local": format_datetime_local(dt),
                    "raw_datetime": dt,
                    "latitude": lat if has_gps else None,
                    "longitude": lon if has_gps else None,
                    "has_gps": has_gps,
                    "is_favorite": False
                })
            conn.close()
        except Exception:
            pass

    def _scan_photos_dir(self, photos_dir):
        for root, _, files in os.walk(photos_dir):
            for f in files:
                if f.lower().endswith((".jpg", ".jpeg", ".heic", ".png", ".mp4")):
                    fp = os.path.join(root, f)
                    stat = os.stat(fp)
                    dt = unix_to_datetime(stat.st_mtime)

                    self.photos.append({
                        "source": "DCIM File",
                        "filename": f,
                        "directory": os.path.basename(root),
                        "timestamp_utc": format_datetime_utc(dt),
                        "timestamp_local": format_datetime_local(dt),
                        "raw_datetime": dt,
                        "latitude": None,
                        "longitude": None,
                        "has_gps": False,
                        "is_favorite": False
                    })
