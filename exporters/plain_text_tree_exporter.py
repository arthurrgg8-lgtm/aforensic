"""
Plain-Text Evidence Directory Tree Exporter for aforensic.
Creates human-readable, numbered evidence dossiers formatted for rapid terminal grep,
audit inspections, and court-admissible textual filings.
"""

import os
from typing import List, Dict, Any


class PlainTextTreeExporter:
    def __init__(self, output_dir: str):
        self.output_dir = output_dir
        self.tree_dir = os.path.join(output_dir, "text_evidence")
        os.makedirs(self.tree_dir, exist_ok=True)

    def export_all(self, artifacts: Dict[str, Any], device_info: Dict[str, Any], hash_report: Dict[str, Any] = None):
        """
        Exports all artifacts into clean, numbered .txt files.
        """
        # 1. Device Hardware Info
        self._export_device_info(device_info)

        # 2. SMS / MMS Messages
        if "sms" in artifacts:
            self._export_sms(artifacts["sms"])

        # 3. Call History
        if "calls" in artifacts:
            self._export_calls(artifacts["calls"])

        # 4. Contacts Directory
        if "contacts" in artifacts:
            self._export_contacts(artifacts["contacts"])

        # 5. WhatsApp Chats
        if "whatsapp" in artifacts:
            self._export_whatsapp(artifacts["whatsapp"])

        # 6. Chrome Browser History
        if "chrome" in artifacts:
            self._export_chrome(artifacts["chrome"])

        # 7. Notes and Memos
        if "notes" in artifacts:
            self._export_notes(artifacts["notes"])

        # 8. Financial Intelligence & Ledger
        if "financial" in artifacts:
            self._export_financial(artifacts["financial"])

        # 9. Usage Stats & App Timelines
        if "usagestats" in artifacts:
            self._export_usagestats(artifacts["usagestats"])

        # 10. Wi-Fi & Bluetooth
        self._export_network(artifacts.get("wifi", []), artifacts.get("bluetooth", []))

        # 11. Notifications
        if "notifications" in artifacts:
            self._export_notifications(artifacts["notifications"])

        # 12. Carved Freelist Fragments
        if "carved_records" in artifacts:
            self._export_carved(artifacts["carved_records"])

    def _export_device_info(self, dev: Dict[str, Any]):
        path = os.path.join(self.tree_dir, "01_Device_Hardware_Telemetrics.txt")
        with open(path, "w", encoding="utf-8") as f:
            f.write("=" * 70 + "\n")
            f.write("AFORENSIC - ANDROID FORENSIC ACQUISITION DEVICE PROFILE\n")
            f.write("=" * 70 + "\n\n")
            for k, v in dev.items():
                f.write(f"{k.upper().replace('_', ' '):<25}: {v}\n")

    def _export_sms(self, sms_list: List[Dict[str, Any]]):
        path = os.path.join(self.tree_dir, "02_SMS_and_MMS_Messages.txt")
        with open(path, "w", encoding="utf-8") as f:
            f.write("=" * 70 + "\n")
            f.write(f"SMS / MMS MESSAGES DOSSIER ({len(sms_list)} Records)\n")
            f.write("=" * 70 + "\n\n")
            for idx, msg in enumerate(sms_list, 1):
                f.write(f"[{idx}] Timestamp: {msg.get('timestamp', 'N/A')} | Direction: {msg.get('direction', 'Unknown')} | Status: {msg.get('status', 'N/A')}\n")
                f.write(f"     Address/Sender: {msg.get('address', 'N/A')}\n")
                f.write(f"     Message Body  : {msg.get('body', '')}\n")
                f.write(f"     Source        : {msg.get('source', 'Content Provider')}\n")
                f.write("-" * 60 + "\n")

    def _export_calls(self, call_list: List[Dict[str, Any]]):
        path = os.path.join(self.tree_dir, "03_Call_Logs.txt")
        with open(path, "w", encoding="utf-8") as f:
            f.write("=" * 70 + "\n")
            f.write(f"TELEPHONY CALL LOGS ({len(call_list)} Records)\n")
            f.write("=" * 70 + "\n\n")
            for idx, c in enumerate(call_list, 1):
                f.write(f"[{idx}] Timestamp: {c.get('timestamp', 'N/A')} | Type: {c.get('type', 'N/A')} | Duration: {c.get('duration_formatted', '0s')}\n")
                f.write(f"     Party Name/Number: {c.get('name', 'Unknown')} ({c.get('number', 'N/A')})\n")
                f.write(f"     Source           : {c.get('source', 'Content Provider')}\n")
                f.write("-" * 60 + "\n")

    def _export_contacts(self, contacts: List[Dict[str, Any]]):
        path = os.path.join(self.tree_dir, "04_Contacts_Directory.txt")
        with open(path, "w", encoding="utf-8") as f:
            f.write("=" * 70 + "\n")
            f.write(f"CONTACTS DIRECTORY ({len(contacts)} Records)\n")
            f.write("=" * 70 + "\n\n")
            for idx, ct in enumerate(contacts, 1):
                f.write(f"[{idx}] Name : {ct.get('display_name', 'N/A')}\n")
                f.write(f"     Phone: {ct.get('phone_number', 'N/A')}\n")
                f.write(f"     Email: {ct.get('email', 'N/A')}\n")
                f.write(f"     Truecaller / Note: {ct.get('note', '')}\n")
                f.write("-" * 60 + "\n")

    def _export_whatsapp(self, wa_list: List[Dict[str, Any]]):
        path = os.path.join(self.tree_dir, "05_WhatsApp_Chats.txt")
        with open(path, "w", encoding="utf-8") as f:
            f.write("=" * 70 + "\n")
            f.write(f"WHATSAPP MESSENGER CONVERSATIONS ({len(wa_list)} Records)\n")
            f.write("=" * 70 + "\n\n")
            for idx, msg in enumerate(wa_list, 1):
                f.write(f"[{idx}] Timestamp: {msg.get('timestamp', 'N/A')} | Direction: {'Outgoing' if msg.get('is_outgoing') else 'Incoming'}\n")
                f.write(f"     JID/Sender : {msg.get('sender', 'N/A')} (Chat: {msg.get('chat_jid', 'N/A')})\n")
                f.write(f"     Message    : {msg.get('body', '')}\n")
                f.write(f"     Source     : {msg.get('source_db', 'msgstore.db')}\n")
                f.write("-" * 60 + "\n")

    def _export_chrome(self, history: List[Dict[str, Any]]):
        path = os.path.join(self.tree_dir, "06_Chrome_Browser_History.txt")
        with open(path, "w", encoding="utf-8") as f:
            f.write("=" * 70 + "\n")
            f.write(f"CHROME WEB BROWSING HISTORY ({len(history)} Records)\n")
            f.write("=" * 70 + "\n\n")
            for idx, h in enumerate(history, 1):
                f.write(f"[{idx}] Timestamp: {h.get('timestamp', 'N/A')} | Visits: {h.get('visit_count', 1)}\n")
                f.write(f"     Title: {h.get('title', 'No Title')}\n")
                f.write(f"     URL  : {h.get('url', 'N/A')}\n")
                f.write("-" * 60 + "\n")

    def _export_notes(self, notes: List[Dict[str, Any]]):
        path = os.path.join(self.tree_dir, "07_Notes_and_Memos.txt")
        with open(path, "w", encoding="utf-8") as f:
            f.write("=" * 70 + "\n")
            f.write(f"NOTES AND MEMOS ({len(notes)} Records)\n")
            f.write("=" * 70 + "\n\n")
            for idx, n in enumerate(notes, 1):
                f.write(f"[{idx}] App: {n.get('app', 'Notes')} | Title: {n.get('title', 'Untitled')}\n")
                f.write(f"     Created: {n.get('created_time', 'N/A')} | Modified: {n.get('modified_time', 'N/A')}\n")
                f.write(f"     Content: {n.get('content', '')}\n")
                f.write("-" * 60 + "\n")

    def _export_financial(self, fin: Dict[str, Any]):
        path = os.path.join(self.tree_dir, "08_Financial_Intelligence.txt")
        with open(path, "w", encoding="utf-8") as f:
            summary = fin.get("summary", {})
            f.write("=" * 70 + "\n")
            f.write("FINANCIAL INTELLIGENCE & TRANSACTION AUDIT LEDGER\n")
            f.write("=" * 70 + "\n\n")
            f.write(f"Total Transactions Parsed : {summary.get('total_transactions', 0)}\n")
            f.write(f"Total Debits / Outgoing   : {summary.get('total_debit_amount', 0.0)}\n")
            f.write(f"Total Credits / Incoming  : {summary.get('total_credit_amount', 0.0)}\n")
            f.write(f"2FA OTP Verification Codes: {summary.get('otp_codes_captured', 0)}\n")
            f.write("=" * 70 + "\n\n")

            for idx, t in enumerate(fin.get("ledger", []), 1):
                f.write(f"[{idx}] Timestamp: {t.get('timestamp', 'N/A')} | Type: {t.get('type', 'N/A')}\n")
                f.write(f"     Amount : {t.get('currency', '')} {t.get('amount', 0.0)} | Balance: {t.get('balance', 'N/A')}\n")
                f.write(f"     A/C Ref: {t.get('account_ref', 'N/A')} | OTP: {t.get('otp_code', 'None')}\n")
                f.write(f"     Text   : {t.get('message_text', '')}\n")
                f.write("-" * 60 + "\n")

    def _export_usagestats(self, ustats: Dict[str, Any]):
        path = os.path.join(self.tree_dir, "09_UsageStats_App_Activity.txt")
        with open(path, "w", encoding="utf-8") as f:
            f.write("=" * 70 + "\n")
            f.write("APPLICATION USAGE & FOREGROUND ACTIVITY\n")
            f.write("=" * 70 + "\n\n")
            for idx, app in enumerate(ustats.get("apps", []), 1):
                f.write(f"[{idx}] Package: {app.get('package', 'N/A')}\n")
                f.write(f"     Total Foreground Time: {app.get('total_foreground_time', 'N/A')}\n")
                f.write(f"     Last Active Time     : {app.get('last_time_used', 'N/A')}\n")
                f.write(f"     App Launch Count     : {app.get('launch_count', 0)}\n")
                f.write("-" * 60 + "\n")

    def _export_network(self, wifi: List[Dict[str, Any]], bt: List[Dict[str, Any]]):
        path = os.path.join(self.tree_dir, "10_WiFi_and_Bluetooth_Profiles.txt")
        with open(path, "w", encoding="utf-8") as f:
            f.write("=" * 70 + "\n")
            f.write(f"WI-FI NETWORKS ({len(wifi)} Profiles)\n")
            f.write("=" * 70 + "\n\n")
            for idx, w in enumerate(wifi, 1):
                f.write(f"[{idx}] SSID: {w.get('ssid', 'N/A')} | Security: {w.get('security', 'N/A')} | BSSID: {w.get('bssid', 'N/A')}\n")
                f.write(f"     Last Connected: {w.get('last_connected', 'N/A')}\n")
                f.write("-" * 60 + "\n")

            f.write("\n" + "=" * 70 + "\n")
            f.write(f"BLUETOOTH PAIRED DEVICES ({len(bt)} Devices)\n")
            f.write("=" * 70 + "\n\n")
            for idx, b in enumerate(bt, 1):
                f.write(f"[{idx}] Name: {b.get('device_name', 'N/A')} | MAC: {b.get('mac_address', 'N/A')} | Status: {b.get('status', 'Paired')}\n")
                f.write("-" * 60 + "\n")

    def _export_notifications(self, notifs: List[Dict[str, Any]]):
        path = os.path.join(self.tree_dir, "11_Notification_History.txt")
        with open(path, "w", encoding="utf-8") as f:
            f.write("=" * 70 + "\n")
            f.write(f"NOTIFICATION CACHE & EPHEMERAL MESSAGES ({len(notifs)} Records)\n")
            f.write("=" * 70 + "\n\n")
            for idx, n in enumerate(notifs, 1):
                f.write(f"[{idx}] App: {n.get('package', 'N/A')} | Timestamp: {n.get('timestamp', 'N/A')}\n")
                f.write(f"     Title: {n.get('title', '')}\n")
                f.write(f"     Body : {n.get('body', '')}\n")
                f.write("-" * 60 + "\n")

    def _export_carved(self, carved: List[Dict[str, Any]]):
        path = os.path.join(self.tree_dir, "12_Carved_Freelist_Records.txt")
        with open(path, "w", encoding="utf-8") as f:
            f.write("=" * 70 + "\n")
            f.write(f"CARVED SQLITE FREELIST & WAL DELETED RECORDS ({len(carved)} Fragments)\n")
            f.write("=" * 70 + "\n\n")
            for idx, c in enumerate(carved, 1):
                f.write(f"[{idx}] Source DB: {c.get('source_db', 'Database')} | Page: {c.get('page_num', 'N/A')} | Offset: {c.get('offset', 'N/A')}\n")
                f.write(f"     Extracted UTF-8 Fragment: {c.get('extracted_text', '')}\n")
                f.write("-" * 60 + "\n")
