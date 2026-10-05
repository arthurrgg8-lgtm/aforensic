"""
Notification Cache and Dumpsys Notification Parser for aforensic.
Extracts active, historical, and cached push notifications from dumpsys notification.
Crucial for recovering disappearing/ephemeral messages (Signal, Telegram, Snapchat, WhatsApp)
and volatile two-factor OTP codes captured in the notification system.
"""

import re
from typing import List, Dict, Any, Optional
from core.time_utils import format_epoch_timestamp


class NotificationParser:
    def __init__(self, adb_manager=None):
        self.adb = adb_manager

    def parse_dumpsys_notifications(self, dumpsys_text: str) -> List[Dict[str, Any]]:
        """
        Parses dumpsys notification output into structured forensic notification records.
        """
        records = []
        if not dumpsys_text:
            return records

        # Split on NotificationRecord blocks
        # e.g.: NotificationRecord(0x...: pkg=com.whatsapp user=UserHandle{0} id=123 tag=null score=0: Notification(channel=... ...))
        blocks = re.split(r'(?m)^(?=\s*NotificationRecord\(|\s*HistoricalNotification\(|\s*Record\s+\d+)', dumpsys_text)

        for block in blocks:
            if not block.strip():
                continue

            # Extract package name
            pkg_match = re.search(r'pkg=([a-zA-Z0-9_.]+)', block)
            if not pkg_match:
                pkg_match = re.search(r'package=([a-zA-Z0-9_.]+)', block)
            package_name = pkg_match.group(1) if pkg_match else "com.android.system"

            # Extract title: android.title=String (...) or title="..."
            title_match = re.search(r'android\.title=(?:String\s*\((.*?)\)|"([^"]*)")', block)
            title = ""
            if title_match:
                title = title_match.group(1) or title_match.group(2) or ""

            # Extract text / bigText
            text_match = re.search(r'android\.text=(?:CharSequence\s*\((.*?)\)|String\s*\((.*?)\)|"([^"]*)")', block)
            text_body = ""
            if text_match:
                text_body = text_match.group(1) or text_match.group(2) or text_match.group(3) or ""

            big_text_match = re.search(r'android\.bigText=(?:CharSequence\s*\((.*?)\)|String\s*\((.*?)\)|"([^"]*)")', block)
            if big_text_match:
                big_body = big_text_match.group(1) or big_text_match.group(2) or big_text_match.group(3) or ""
                if len(big_body) > len(text_body):
                    text_body = big_body

            # Extract post time: postTime=1672531199000 or when=1672531199000
            time_match = re.search(r'(?:postTime|when)=(\d{10,13})', block)
            raw_time = int(time_match.group(1)) if time_match else 0
            timestamp_str = format_epoch_timestamp(raw_time) if raw_time > 0 else "N/A"

            # Channel / Category
            channel_match = re.search(r'channel=([a-zA-Z0-9_.-]+)', block)
            channel = channel_match.group(1) if channel_match else "Default"

            # Check if ephemeral / messaging app
            is_messaging = any(app in package_name.lower() for app in ["whatsapp", "telegram", "signal", "viber", "messenger", "snapchat", "sms", "mms", "imessage", "banking"])

            if title or text_body:
                records.append({
                    "package": package_name,
                    "title": title.strip(),
                    "body": text_body.strip(),
                    "timestamp": timestamp_str,
                    "raw_time": raw_time,
                    "channel": channel,
                    "is_messaging_app": is_messaging,
                    "source": "dumpsys notification"
                })

        return records

    def extract_live(self) -> List[Dict[str, Any]]:
        """
        Executes ADB dumpsys notification --noredact or dumpsys notification.
        """
        if not self.adb:
            return []

        # Try unredacted first
        raw = self.adb.run_dumpsys("notification --noredact")
        if not raw or "Unknown option" in raw:
            raw = self.adb.run_dumpsys("notification")

        return self.parse_dumpsys_notifications(raw)
