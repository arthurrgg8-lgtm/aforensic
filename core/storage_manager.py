import os
import subprocess
import platform
import shutil

class StorageManager:
    """
    Cross-platform storage detection and mounting engine for external USB drives,
    NVMe forensics SSDs, and local destination directories.
    """

    @staticmethod
    def get_os_type():
        return platform.system().lower()

    @staticmethod
    def list_external_storage():
        os_type = StorageManager.get_os_type()
        if os_type == "linux":
            return StorageManager._list_storage_linux()
        elif os_type == "darwin":
            return StorageManager._list_storage_macos()
        elif os_type == "windows":
            return StorageManager._list_storage_windows()
        return []

    @staticmethod
    def _list_storage_linux():
        devices = []
        if not shutil.which("lsblk"):
            return devices

        try:
            res = subprocess.run(
                ["lsblk", "-J", "-o", "NAME,SIZE,TYPE,MOUNTPOINT,LABEL,MODEL,TRAN,RM,RO"],
                capture_output=True, text=True, timeout=3
            )
            import json
            data = json.loads(res.stdout)
            blockdevices = data.get("blockdevices", [])

            for bd in blockdevices:
                StorageManager._process_linux_block_device(bd, devices)
        except Exception:
            pass
        return devices

    @staticmethod
    def _process_linux_block_device(bd, devices):
        name = bd.get("name", "")
        size = bd.get("size", "")
        tran = str(bd.get("tran", "")).lower()
        rm = bd.get("rm", False)
        mp = bd.get("mountpoint")
        label = bd.get("label") or bd.get("model") or "External Disk"
        ro = bd.get("ro", False)

        is_ext = (tran == "usb" or rm is True or "/media/" in str(mp) or "/mnt/" in str(mp))
        if is_ext:
            devices.append({
                "device_name": f"/dev/{name}",
                "size": size,
                "mountpoint": mp,
                "label": label.strip() if label else "External USB Drive",
                "is_mounted": bool(mp),
                "is_readonly": bool(ro),
                "type": "USB / External Storage"
            })

        for child in bd.get("children", []):
            StorageManager._process_linux_block_device(child, devices)

    @staticmethod
    def _list_storage_macos():
        devices = []
        try:
            res = subprocess.run(["df", "-h"], capture_output=True, text=True, timeout=3)
            for line in res.stdout.splitlines():
                if "/Volumes/" in line:
                    parts = line.split()
                    if len(parts) >= 9:
                        devices.append({
                            "device_name": parts[0],
                            "size": parts[1],
                            "mountpoint": " ".join(parts[8:]),
                            "label": os.path.basename(" ".join(parts[8:])),
                            "is_mounted": True,
                            "is_readonly": False,
                            "type": "External Volume"
                        })
        except Exception:
            pass
        return devices

    @staticmethod
    def _list_storage_windows():
        devices = []
        try:
            for letter in range(ord('D'), ord('Z') + 1):
                drive = f"{chr(letter)}:\\"
                if os.path.exists(drive):
                    devices.append({
                        "device_name": drive,
                        "size": "Available",
                        "mountpoint": drive,
                        "label": f"Drive ({drive})",
                        "is_mounted": True,
                        "is_readonly": False,
                        "type": "Windows Volume"
                    })
        except Exception:
            pass
        return devices

    @staticmethod
    def mount_device_if_needed(device_path, target_mount_dir=None):
        if not target_mount_dir:
            dev_basename = os.path.basename(device_path)
            target_mount_dir = f"/media/forensic_{dev_basename}"

        os.makedirs(target_mount_dir, exist_ok=True)
        try:
            subprocess.run(["mount", device_path, target_mount_dir], capture_output=True, timeout=5)
            return True, target_mount_dir
        except Exception as e:
            return False, str(e)
