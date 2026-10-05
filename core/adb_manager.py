import subprocess
import os
import re
import shutil
import time

class ADBManager:
    """
    High-Performance Android Debug Bridge (ADB) Extraction Engine.
    Executes Content Provider streams, pulls shared storage artifacts, and captures dumpsys logs.
    """

    def __init__(self, serial=None):
        self.serial = serial
        self.cmd_prefix = ["adb"]
        if serial:
            self.cmd_prefix.extend(["-s", serial])

    def run_shell(self, shell_cmd, timeout=15):
        """
        Executes an ADB shell command and returns output.
        """
        try:
            res = subprocess.run(
                self.cmd_prefix + ["shell", shell_cmd],
                capture_output=True, text=True, timeout=timeout
            )
            return res.stdout
        except Exception:
            return ""

    def query_content_provider(self, uri, projection=None, sort_order=None, timeout=20):
        """
        Queries an Android Content Provider directly via adb shell content query.
        Parses returned key=value row blocks into a list of structured dictionaries.
        """
        cmd = f"content query --uri {uri}"
        if projection:
            cmd += f" --projection {projection}"
        if sort_order:
            cmd += f" --sort '{sort_order}'"

        raw_output = self.run_shell(cmd, timeout=timeout)
        if not raw_output or "Row:" not in raw_output:
            return []

        rows = []
        for block in raw_output.split("Row:"):
            block = block.strip()
            if not block:
                continue

            row_data = {}
            # Match keys and values in format: key=val, key2=val2 or val with spaces/quotes
            # Tokens are comma-separated
            tokens = re.split(r',\s*(?=[a-zA-Z0-9_]+[=])', block)
            for token in tokens:
                if "=" in token:
                    k, v = token.split("=", 1)
                    k = k.strip()
                    v = v.strip()
                    if v.startswith("NULL") or v == "null":
                        v = None
                    elif v.startswith("'") and v.endswith("'") and len(v) >= 2:
                        v = v[1:-1]
                    row_data[k] = v

            if row_data:
                rows.append(row_data)

        return rows

    def pull_file(self, remote_path, local_destination, timeout=30):
        """
        Pulls a remote file from Android filesystem to local evidence path.
        """
        os.makedirs(os.path.dirname(os.path.abspath(local_destination)), exist_ok=True)
        try:
            res = subprocess.run(
                self.cmd_prefix + ["pull", remote_path, local_destination],
                capture_output=True, text=True, timeout=timeout
            )
            return res.returncode == 0 and os.path.exists(local_destination)
        except Exception:
            return False

    def pull_directory(self, remote_dir, local_destination, timeout=60):
        """
        Pulls a remote directory from Android filesystem to local destination.
        """
        os.makedirs(local_destination, exist_ok=True)
        try:
            res = subprocess.run(
                self.cmd_prefix + ["pull", remote_dir, local_destination],
                capture_output=True, text=True, timeout=timeout
            )
            return res.returncode == 0
        except Exception:
            return False

    def run_dumpsys(self, service, timeout=15):
        """
        Dumps runtime service diagnostics (e.g. usagestats, notification, wifi, battery).
        """
        return self.run_shell(f"dumpsys {service}", timeout=timeout)

    def list_installed_packages(self):
        """
        Queries all installed third-party and system packages.
        """
        raw = self.run_shell("pm list packages -f -u", timeout=10)
        packages = []
        for line in raw.splitlines():
            line = line.strip()
            if line.startswith("package:"):
                # Format: package:/data/app/...=com.example.app
                val = line[8:]
                if "=" in val:
                    apk_p, pkg_name = val.rsplit("=", 1)
                    packages.append({
                        "package_name": pkg_name,
                        "apk_path": apk_p,
                        "is_third_party": "/data/app/" in apk_p
                    })
        return packages

    def find_shared_storage_files(self, search_subpath="", extensions=None):
        """
        Finds files in /sdcard/ /storage/emulated/0/ matching specific extensions.
        """
        base_path = f"/sdcard/{search_subpath}".rstrip("/")
        cmd = f"ls -laR '{base_path}'"
        raw = self.run_shell(cmd, timeout=15)
        
        found_files = []
        cur_dir = base_path
        for line in raw.splitlines():
            line = line.strip()
            if line.endswith(":"):
                cur_dir = line[:-1]
            elif line and not line.startswith("total"):
                parts = line.split()
                if len(parts) >= 8 and not parts[0].startswith("d"):
                    fname = parts[-1]
                    if not extensions or any(fname.lower().endswith(ext) for ext in extensions):
                        found_files.append(f"{cur_dir}/{fname}")
        return found_files
