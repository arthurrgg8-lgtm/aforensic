"""
Android UsageStats and App Activity Parser for aforensic.
Extracts application execution frequency, total foreground duration, last active timestamps,
and event transitions from 'dumpsys usagestats'.
"""

import re
from typing import List, Dict, Any, Optional
from core.time_utils import format_epoch_timestamp


class UsageStatsParser:
    def __init__(self, adb_manager=None):
        self.adb = adb_manager

    def parse_dumpsys_usagestats(self, dumpsys_text: str) -> Dict[str, Any]:
        """
        Parses 'dumpsys usagestats' into package usage metrics and activity events.
        """
        app_stats = []
        events = []

        if not dumpsys_text:
            return {"apps": app_stats, "events": events}

        # 1. Parse App Summary Stats
        # Format example:
        # package=com.whatsapp totalTime="01:45:22" lastTime="2026-10-05 14:20:00" appLaunchCount=42
        # or: package=com.whatsapp total="1h45m" lastUsed="1672531199000" ...
        pkg_lines = re.findall(r'package=([a-zA-Z0-9_.]+)(.*?)(?=\n\s*package=|\n\s*Choose|$)', dumpsys_text, re.DOTALL)
        
        for pkg_name, block in pkg_lines:
            if not pkg_name or pkg_name == "null":
                continue

            # Extract total time
            total_time_m = re.search(r'total(?:TimeInForeground|Time)="?([^"\r\n]+)"?', block)
            total_time = total_time_m.group(1).strip() if total_time_m else "N/A"

            # Extract last time used
            last_used_m = re.search(r'last(?:Time)?(?:Used)?="?([^"\r\n]+)"?', block)
            last_used = last_used_m.group(1).strip() if last_used_m else "N/A"

            # Extract launch count
            launch_count_m = re.search(r'(?:appLaunchCount|launchCount)=(\d+)', block)
            launch_count = int(launch_count_m.group(1)) if launch_count_m else 0

            app_stats.append({
                "package": pkg_name,
                "total_foreground_time": total_time,
                "last_time_used": last_used,
                "launch_count": launch_count,
                "source": "dumpsys usagestats"
            })

        # 2. Parse Event Log
        # Format example:
        # time="2026-10-05 14:02:11" type=MOVE_TO_FOREGROUND package=com.android.chrome
        event_lines = re.findall(r'time="?([^"\r\n]+)"?\s+type=([A-Z_]+)\s+package=([a-zA-Z0-9_.]+)', dumpsys_text)
        for ts, ev_type, pkg in event_lines[:2000]:  # Cap at 2000 events
            events.append({
                "timestamp": ts,
                "event_type": ev_type,
                "package": pkg,
                "source": "dumpsys usagestats events"
            })

        # Sort app stats by launch count descending
        app_stats.sort(key=lambda x: x["launch_count"], reverse=True)

        return {
            "apps": app_stats,
            "events": events
        }

    def extract_live(self) -> Dict[str, Any]:
        """
        Executes live dumpsys usagestats via ADB.
        """
        if not self.adb:
            return {"apps": [], "events": []}

        raw = self.adb.run_dumpsys("usagestats")
        return self.parse_dumpsys_usagestats(raw)
