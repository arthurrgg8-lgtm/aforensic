"""
Wi-Fi and Bluetooth Artifacts Parser for aforensic.
Extracts Wi-Fi network configurations, saved credentials, connection history,
and paired Bluetooth devices from dumpsys output and system config files.
"""

import os
import re
import xml.etree.ElementTree as ET
from typing import List, Dict, Any, Optional
from core.time_utils import format_epoch_timestamp


class WifiBluetoothParser:
    def __init__(self, adb_manager=None):
        self.adb = adb_manager

    def parse_dumpsys_wifi(self, dumpsys_text: str) -> List[Dict[str, Any]]:
        """
        Parses 'dumpsys wifi' output for configured networks and current connection status.
        """
        networks = []
        if not dumpsys_text:
            return networks

        # Regex patterns for network configurations in dumpsys wifi
        # Typical format: ID: 0 SSID: "Home_WiFi" BSSID: any ...
        config_blocks = re.split(r'(?m)^(?=ID:\s*\d+|Configured Networks:|NetworkSelectionHistory)', dumpsys_text)
        
        seen_ssids = set()
        for block in config_blocks:
            ssid_match = re.search(r'SSID:\s*"?([^"\r\n]+)"?', block)
            if not ssid_match:
                continue

            ssid = ssid_match.group(1).strip()
            if not ssid or ssid in seen_ssids or ssid == "null":
                continue
            seen_ssids.add(ssid)

            # Extract security type
            sec_type = "Open"
            if "WPA_PSK" in block or "WPA2" in block or "PSK" in block:
                sec_type = "WPA/WPA2-PSK"
            elif "SAE" in block or "WPA3" in block:
                sec_type = "WPA3-SAE"
            elif "EAP" in block:
                sec_type = "Enterprise-EAP"
            elif "WEP" in block:
                sec_type = "WEP"

            # Extract BSSID
            bssid_match = re.search(r'BSSID:\s*([0-9a-fA-F:]{17}|any)', block)
            bssid = bssid_match.group(1) if bssid_match else "Any"

            # Extract last connected timestamp if present
            last_conn_match = re.search(r'lastConnected:\s*(\d+)', block)
            last_conn = "N/A"
            if last_conn_match:
                try:
                    last_conn = format_epoch_timestamp(int(last_conn_match.group(1)))
                except Exception:
                    pass

            # Extract priority/network ID
            net_id_match = re.search(r'ID:\s*(\d+)', block)
            net_id = net_id_match.group(1) if net_id_match else "N/A"

            networks.append({
                "type": "Wi-Fi Network",
                "ssid": ssid,
                "security": sec_type,
                "bssid": bssid,
                "network_id": net_id,
                "last_connected": last_conn,
                "source": "dumpsys wifi"
            })

        return networks

    def parse_wifi_xml(self, xml_content_or_path: str) -> List[Dict[str, Any]]:
        """
        Parses WifiConfigStore.xml from /data/misc/wifi/ or extracted evidence.
        """
        networks = []
        try:
            if os.path.exists(xml_content_or_path):
                tree = ET.parse(xml_content_or_path)
                root = tree.getroot()
            else:
                root = ET.fromstring(xml_content_or_path)

            for net_elem in root.iter("Network"):
                ssid = ""
                preshared_key = ""
                sec_type = "Unknown"
                bssid = "Any"
                last_connected = "N/A"

                for elem in net_elem.iter("string"):
                    name = elem.get("name", "")
                    text = elem.text or ""
                    if name == "SSID":
                        ssid = text.strip('"')
                    elif name == "PreSharedKey":
                        preshared_key = text.strip('"')
                    elif name == "KeyMgmt":
                        sec_type = text
                    elif name == "BSSID":
                        bssid = text

                for elem in net_elem.iter("long"):
                    if elem.get("name") == "LastConnected":
                        try:
                            val = int(elem.get("value", 0))
                            if val > 0:
                                last_connected = format_epoch_timestamp(val)
                        except Exception:
                            pass

                if ssid:
                    networks.append({
                        "type": "Wi-Fi Network (Config)",
                        "ssid": ssid,
                        "security": sec_type,
                        "pre_shared_key": preshared_key if preshared_key else "[Protected/None]",
                        "bssid": bssid,
                        "last_connected": last_connected,
                        "source": "WifiConfigStore.xml"
                    })
        except Exception:
            pass

        return networks

    def parse_dumpsys_bluetooth(self, dumpsys_text: str) -> List[Dict[str, Any]]:
        """
        Parses 'dumpsys bluetooth_manager' or 'dumpsys bluetooth' for bonded devices.
        """
        devices = []
        if not dumpsys_text:
            return devices

        # Match paired/bonded devices: Name, MAC Address, Bond state
        # e.g.: Device: 00:11:22:33:44:55 (AirPods Pro) BondState: 12
        matches = re.findall(r'([0-9A-Fa-f]{2}[:-][0-9A-Fa-f]{2}[:-][0-9A-Fa-f]{2}[:-][0-9A-Fa-f]{2}[:-][0-9A-Fa-f]{2}[:-][0-9A-Fa-f]{2})\s*\(?([^)\r\n]*)\)?', dumpsys_text)
        
        seen_macs = set()
        for mac, raw_name in matches:
            mac_clean = mac.upper()
            if mac_clean in seen_macs or mac_clean == "00:00:00:00:00:00":
                continue
            seen_macs.add(mac_clean)

            name = raw_name.strip()
            if not name or name == "null" or "Address" in name:
                name = "Unknown Bluetooth Device"

            devices.append({
                "type": "Bluetooth Paired Device",
                "mac_address": mac_clean,
                "device_name": name,
                "status": "Paired/Bonded",
                "source": "dumpsys bluetooth"
            })

        return devices

    def extract_from_device(self) -> Dict[str, List[Dict[str, Any]]]:
        """
        Executes live dumpsys via ADB to fetch Wi-Fi & Bluetooth profiles.
        """
        results = {"wifi": [], "bluetooth": []}
        if not self.adb:
            return results

        # 1. Wifi dumpsys
        wifi_raw = self.adb.run_dumpsys("wifi")
        results["wifi"] = self.parse_dumpsys_wifi(wifi_raw)

        # 2. Bluetooth dumpsys
        bt_raw = self.adb.run_dumpsys("bluetooth_manager")
        if not bt_raw or len(bt_raw) < 50:
            bt_raw = self.adb.run_dumpsys("bluetooth")
        results["bluetooth"] = self.parse_dumpsys_bluetooth(bt_raw)

        return results
