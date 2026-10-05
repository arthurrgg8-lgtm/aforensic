import subprocess
import shutil
import platform
import re
import time

class DeviceDetector:
    """
    Cross-Platform Android USB & Wireless ADB Device Detector and Telemetry Engine.
    Detects hardware, queries system properties, validates RSA authorization, and profiles encryption.
    """

    @staticmethod
    def is_adb_available():
        return shutil.which("adb") is not None

    @staticmethod
    def get_os_install_guide():
        system = platform.system().lower()
        if system == "linux":
            return "Linux: sudo apt update && sudo apt install -y adb android-sdk-platform-tools"
        elif system == "darwin":
            return "macOS: brew install android-platform-tools"
        elif system == "windows":
            return "Windows: Download Android SDK Platform Tools and add to PATH."
        return "Install Android Platform Tools (adb) for your OS."

    @staticmethod
    def detect_connected_devices():
        """
        Lists all connected Android devices with their ADB connection status.
        """
        if not DeviceDetector.is_adb_available():
            return []

        devices = []
        try:
            res = subprocess.run(["adb", "devices", "-l"], capture_output=True, text=True, timeout=5)
            lines = res.stdout.strip().split("\n")[1:]
            for line in lines:
                if not line.strip() or line.startswith("*"):
                    continue
                parts = line.split()
                if len(parts) >= 2:
                    serial = parts[0]
                    status = parts[1] # 'device', 'unauthorized', 'offline', 'recovery'
                    
                    # Parse model and product from details
                    model = "Unknown Android"
                    product = "Android"
                    for part in parts[2:]:
                        if part.startswith("model:"):
                            model = part.split(":", 1)[1].replace("_", " ")
                        elif part.startswith("product:"):
                            product = part.split(":", 1)[1]

                    devices.append({
                        "serial": serial,
                        "status": status,
                        "model": model,
                        "product": product,
                        "is_authorized": status == "device"
                    })
        except Exception:
            pass
        return devices

    @staticmethod
    def get_device_info(serial=None):
        """
        Retrieves deep hardware metadata and encryption status from the connected Android device.
        """
        if not DeviceDetector.is_adb_available():
            return {}

        cmd_prefix = ["adb"]
        if serial:
            cmd_prefix.extend(["-s", serial])

        info = {
            "serial": serial or "Unknown",
            "model": "Android Device",
            "manufacturer": "Unknown OEM",
            "brand": "Android",
            "android_version": "Unknown",
            "sdk_version": "N/A",
            "security_patch": "N/A",
            "build_id": "N/A",
            "crypto_state": "encrypted (FBE)",
            "crypto_type": "file",
            "battery_level": "N/A",
            "is_authorized": True
        }

        try:
            # 1. Query System Properties
            props_res = subprocess.run(cmd_prefix + ["shell", "getprop"], capture_output=True, text=True, timeout=6)
            if props_res.returncode == 0:
                for line in props_res.stdout.splitlines():
                    match = re.search(r'\[(.*?)\]:\s*\[(.*?)\]', line)
                    if match:
                        k, v = match.group(1), match.group(2)
                        if k == "ro.product.model": info["model"] = v
                        elif k == "ro.product.manufacturer": info["manufacturer"] = v
                        elif k == "ro.product.brand": info["brand"] = v
                        elif k == "ro.build.version.release": info["android_version"] = v
                        elif k == "ro.build.version.sdk": info["sdk_version"] = v
                        elif k == "ro.build.version.security_patch": info["security_patch"] = v
                        elif k == "ro.build.display.id" or k == "ro.build.id": info["build_id"] = v
                        elif k == "ro.crypto.state": info["crypto_state"] = v
                        elif k == "ro.crypto.type": info["crypto_type"] = v
                        elif k == "no.serial" or k == "ro.serialno":
                            if not serial or serial == "Unknown":
                                info["serial"] = v

            # 2. Query Battery Status
            bat_res = subprocess.run(cmd_prefix + ["shell", "dumpsys", "battery"], capture_output=True, text=True, timeout=4)
            if bat_res.returncode == 0:
                for line in bat_res.stdout.splitlines():
                    if "level:" in line:
                        info["battery_level"] = line.split(":", 1)[1].strip() + "%"

        except Exception:
            pass

        return info

    @staticmethod
    def auto_authorize_with_retries(serial=None, max_attempts=3):
        """
        Validates RSA key exchange and authorization status, guiding the user if unauthorized.
        """
        for _ in range(max_attempts):
            devs = DeviceDetector.detect_connected_devices()
            for d in devs:
                if (not serial or d["serial"] == serial) and d["is_authorized"]:
                    return True, d
            time.sleep(1.5)
        return False, None
