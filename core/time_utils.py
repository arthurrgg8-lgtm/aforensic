"""
Forensic Time and Timestamp Conversion Utilities for aforensic.
Supports Unix seconds, milliseconds, microseconds, UTC formatting,
and Nepal (+05:45) local offsets.
"""

import datetime
from datetime import timezone, timedelta
from typing import Optional, Tuple


def unix_to_datetime(unix_time) -> Optional[datetime.datetime]:
    """
    Converts Unix timestamp (seconds, milliseconds, or microseconds) to UTC datetime object.
    """
    if unix_time is None or unix_time == 0 or unix_time == "null" or unix_time == "":
        return None
    try:
        val = float(unix_time)
        if val > 1e14:  # Microseconds (e.g. Android contacts/calls in micros)
            val = val / 1000000.0
        elif val > 1e11:  # Milliseconds (e.g. Android SMS/CallLog date in ms)
            val = val / 1000.0
        return datetime.datetime.fromtimestamp(val, tz=timezone.utc)
    except Exception:
        return None


def format_datetime_utc(dt: Optional[datetime.datetime]) -> str:
    if not dt:
        return "N/A"
    return dt.strftime("%Y-%m-%d %H:%M:%S UTC")


def format_datetime_local(dt: Optional[datetime.datetime], offset_hours: float = 5.75) -> str:
    """
    Default offset is +05:45 (Nepal Standard Time).
    """
    if not dt:
        return "N/A"
    local_tz = timezone(timedelta(hours=offset_hours))
    return dt.astimezone(local_tz).strftime("%Y-%m-%d %H:%M:%S %Z")


def format_epoch_timestamp(epoch_val, offset_hours: float = 0.0) -> str:
    """
    Converts epoch timestamp (sec/ms/micros) directly to standard formatted string.
    """
    if not epoch_val:
        return "N/A"
    dt = unix_to_datetime(epoch_val)
    if not dt:
        return str(epoch_val)
    if offset_hours == 0.0:
        return format_datetime_utc(dt)
    return format_datetime_local(dt, offset_hours)


def parse_timestamp_to_epoch(ts_str: str) -> Optional[int]:
    """
    Parses a timestamp string (e.g., '2022-12-31 23:59:59') into Unix epoch seconds.
    """
    if not ts_str or ts_str == "N/A":
        return None
    formats = [
        "%Y-%m-%d %H:%M:%S",
        "%Y-%m-%d %H:%M:%S %Z",
        "%Y-%m-%dT%H:%M:%S",
        "%Y-%m-%d %H:%M:%S.%f",
        "%Y-%m-%d"
    ]
    # Clean trailing UTC
    clean_str = ts_str.replace(" UTC", "").strip()
    for fmt in formats:
        try:
            dt = datetime.datetime.strptime(clean_str, fmt).replace(tzinfo=timezone.utc)
            return int(dt.timestamp())
        except ValueError:
            continue
    return None


def parse_any_time(val, offset_hours: float = 5.75) -> Tuple[str, str]:
    if not val:
        return "N/A", "N/A"
    try:
        dt = unix_to_datetime(val)
        if dt:
            return format_datetime_utc(dt), format_datetime_local(dt, offset_hours)
    except Exception:
        pass
    return "N/A", "N/A"
