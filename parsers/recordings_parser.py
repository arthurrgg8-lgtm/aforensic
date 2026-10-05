import os
from core.time_utils import unix_to_datetime, format_datetime_utc, format_datetime_local

class RecordingsParser:
    """
    Parses Android Voice Memos, Sound Recorder audio files, and native Call Recordings.
    """

    AUDIO_EXTS = {'.m4a', '.opus', '.aac', '.wav', '.amr', '.mp3', '.ogg', '.3gp'}

    def __init__(self, recordings_dir=None, contacts_parser=None):
        self.recordings_dir = recordings_dir
        self.contacts_parser = contacts_parser
        self.results = {
            "voice_memos": [],
            "call_recordings": [],
            "carved_audio_files": [],
            "total_audio_artifacts": 0
        }

    def parse(self):
        if not self.recordings_dir or not os.path.exists(self.recordings_dir):
            return self.results

        for root, _, files in os.walk(self.recordings_dir):
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
