"""
Master Unified Chronological Super-Timeline Generator for aforensic.
Synthesizes events from SMS, Call logs, WhatsApp, Web history, Notes, Media GPS,
Notifications, and UsageStats into a unified forensic chronology.
"""

import datetime
from datetime import timezone
from typing import List, Dict, Any, Optional
from core.time_utils import unix_to_datetime, format_datetime_utc, format_datetime_local, parse_timestamp_to_epoch


class TimelineBuilder:
    def __init__(self, offset_hours: float = 5.75):
        self.offset_hours = offset_hours
        self.events: List[Dict[str, Any]] = []

    def add_event(self, source: str, event_type: str, timestamp_str: str, summary: str, raw_data: Optional[Dict[str, Any]] = None):
        epoch = parse_timestamp_to_epoch(timestamp_str) or 0
        dt = unix_to_datetime(epoch) if epoch > 0 else None
        
        utc_str = format_datetime_utc(dt) if dt else timestamp_str
        local_str = format_datetime_local(dt, self.offset_hours) if dt else timestamp_str

        self.events.append({
            "source": source,
            "type": event_type,
            "timestamp_utc": utc_str,
            "timestamp_local": local_str,
            "epoch": epoch,
            "summary": summary,
            "raw_data": raw_data or {}
        })

    def build_timeline(self, artifacts: Optional[Dict[str, Any]] = None) -> List[Dict[str, Any]]:
        """
        Builds the unified timeline from artifacts dictionary.
        """
        if artifacts:
            # 1. SMS
            for s in artifacts.get("sms", []):
                self.add_event(
                    source="SMS/MMS",
                    event_type=f"SMS {s.get('direction', 'Message')}",
                    timestamp_str=s.get("timestamp", "N/A"),
                    summary=f"[{s.get('address', 'Unknown')}] {s.get('body', '')[:100]}",
                    raw_data=s
                )

            # 2. Calls
            for c in artifacts.get("calls", []):
                self.add_event(
                    source="Call Log",
                    event_type=f"Call ({c.get('type', 'Unknown')})",
                    timestamp_str=c.get("timestamp", "N/A"),
                    summary=f"Party: {c.get('name', 'Unknown')} ({c.get('number', 'N/A')}) | Dur: {c.get('duration_formatted', '0s')}",
                    raw_data=c
                )

            # 3. WhatsApp
            for w in artifacts.get("whatsapp", []):
                self.add_event(
                    source="WhatsApp",
                    event_type="WhatsApp Message",
                    timestamp_str=w.get("timestamp", "N/A"),
                    summary=f"[{'Outgoing' if w.get('is_outgoing') else 'Incoming'}] {w.get('body', '')[:100]}",
                    raw_data=w
                )

            # 4. Chrome
            for h in artifacts.get("chrome", []):
                self.add_event(
                    source="Chrome Web",
                    event_type="Browser Visit",
                    timestamp_str=h.get("timestamp", "N/A"),
                    summary=f"Visited: {h.get('title', 'Page')} ({h.get('url', '')[:80]})",
                    raw_data=h
                )

            # 5. Photos
            for p in artifacts.get("photos", []):
                loc_txt = f" [GPS: {p.get('latitude')}, {p.get('longitude')}]" if p.get("latitude") else ""
                self.add_event(
                    source="Camera / Media",
                    event_type="Photo Taken",
                    timestamp_str=p.get("timestamp", "N/A"),
                    summary=f"Media: {p.get('filename', 'Photo')}{loc_txt}",
                    raw_data=p
                )

            # 6. Notes
            for n in artifacts.get("notes", []):
                self.add_event(
                    source="Notes / Memos",
                    event_type="Note Created/Modified",
                    timestamp_str=n.get("modified_time") or n.get("created_time") or "N/A",
                    summary=f"Note: {n.get('title', 'Untitled')} - {n.get('content', '')[:80]}",
                    raw_data=n
                )

            # 7. Notifications
            for notif in artifacts.get("notifications", []):
                self.add_event(
                    source="Notification",
                    event_type="Push Alert",
                    timestamp_str=notif.get("timestamp", "N/A"),
                    summary=f"[{notif.get('package', 'App')}] {notif.get('title', '')} - {notif.get('body', '')[:80]}",
                    raw_data=notif
                )

            # 8. Usage events
            ustats = artifacts.get("usagestats", {})
            if isinstance(ustats, dict):
                for ev in ustats.get("events", []):
                    self.add_event(
                        source="UsageStats",
                        event_type=f"App {ev.get('event_type', 'Event')}",
                        timestamp_str=ev.get("timestamp", "N/A"),
                        summary=f"App Activity: {ev.get('package', 'Unknown')}",
                        raw_data=ev
                    )

        # Sort descending by epoch
        self.events.sort(key=lambda x: x.get("epoch", 0), reverse=True)
        return self.events


# Aliases
TimelineEngine = TimelineBuilder
