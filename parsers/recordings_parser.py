"""
Audio Recordings and Voice Memos Parser for aforensic.
Extracts native call recordings and voice memos across all Android OEMs:
- Samsung (Voice Recorder, Recordings)
- Xiaomi / Redmi / POCO (MIUI sound_recorder, call_rec)
- Oppo / Realme / OnePlus (Recordings)
- Vivo / iQOO (Record/Call, Record/Voice)
- Transsion / Tecno / Infinix (SoundRecorder)
- Google Pixel / Motorola (Recorder, Sounds)
"""

import os
from typing import List, Dict, Any, Optional
from core.time_utils import unix_to_datetime, format_datetime_utc, format_datetime_local


class RecordingsParser:
    AUDIO_EXTS = {'.m4a', '.opus', '.aac', '.wav', '.amr', '.mp3', '.ogg', '.3gp'}

    def __init__(self, adb_manager=None, recordings_dir: Optional[str] = None):
        self.adb = adb_manager
        self.recordings_dir = recordings_dir
        self.results = {
            "voice_memos": [],
            "call_recordings": [],
            "carved_audio_files": [],
            "total_audio_artifacts": 0
        }

    def parse(self, directory: Optional[str] = None) -> Dict[str, Any]:
        target_dir = directory or self.recordings_dir
        if not target_dir or not os.path.exists(target_dir):
            return self.results

        for root, _, files in os.walk(target_dir):
            for f in files:
                ext = os.path.splitext(f)[1].lower()
                if ext in self.AUDIO_EXTS:
                    full_p = os.path.join(root, f)
                    try:
                        stat = os.stat(full_p)
                        dt = unix_to_datetime(stat.st_mtime)
                        size_kb = round(stat.st_size / 1024, 2)

                        item = {
                            "filename": f,
                            "path": full_p,
                            "size_kb": size_kb,
                            "timestamp_utc": format_datetime_utc(dt),
                            "timestamp_local": format_datetime_local(dt),
                            "directory": os.path.basename(root)
                        }

                        if "call" in f.lower() or "call" in root.lower():
                            self.results["call_recordings"].append(item)
                        else:
                            self.results["voice_memos"].append(item)

                        self.results["carved_audio_files"].append(item)
                    except Exception:
                        pass

        self.results["total_audio_artifacts"] = len(self.results["carved_audio_files"])
        return self.results

    def extract_from_device(self, raw_dir: str) -> List[Dict[str, Any]]:
        """
        Parses all audio recordings pulled into the raw staging directory.
        """
        parsed = self.parse(raw_dir)
        return parsed.get("carved_audio_files", [])
