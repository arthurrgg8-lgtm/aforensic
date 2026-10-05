"""
Comprehensive Enterprise Test Suite for aforensic.
Tests all core modules, artifact parsers, freelist carvers, and exporters.
"""

import os
import sys
import tempfile
import unittest
import sqlite3
import json
from datetime import datetime, timezone

# Ensure project root is on sys.path
sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from core.time_utils import format_epoch_timestamp, parse_timestamp_to_epoch
from core.db_utils import get_readonly_connection
from core.hash_verifier import HashVerifier
from core.audit_logger import AuditLogger
from core.sqlite_freelist_carver import SQLiteFreelistCarver
from core.timeline import TimelineBuilder
from core.troubleshooter import Troubleshooter
from core.maintenance_manager import MaintenanceManager

from parsers.sms_parser import SMSParser
from parsers.calls_parser import CallsParser
from parsers.contacts_parser import ContactsParser
from parsers.whatsapp_parser import WhatsAppParser
from parsers.chrome_parser import ChromeParser
from parsers.notes_parser import NotesParser
from parsers.financial_parser import FinancialParser
from parsers.notification_parser import NotificationParser
from parsers.wifi_bluetooth_parser import WifiBluetoothParser
from parsers.usagestats_parser import UsageStatsParser

from exporters.bulk_data_exporter import BulkDataExporter
from exporters.plain_text_tree_exporter import PlainTextTreeExporter
from exporters.docx_report import DocxReportExporter
from exporters.html_dashboard import HTMLDashboardExporter


class TestTimeUtils(unittest.TestCase):
    def test_epoch_conversion(self):
        # 1672531199 = 2022-12-31 23:59:59 UTC
        formatted = format_epoch_timestamp(1672531199)
        self.assertIn("2022-12-31", formatted)
        self.assertIn("UTC", formatted)

    def test_millisecond_conversion(self):
        formatted = format_epoch_timestamp(1672531199000)
        self.assertIn("2022-12-31", formatted)

    def test_parse_to_epoch(self):
        epoch = parse_timestamp_to_epoch("2022-12-31 23:59:59")
        self.assertEqual(epoch, 1672531199)


class TestHashVerifier(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.test_file = os.path.join(self.temp_dir.name, "evidence_file.dat")
        with open(self.test_file, "wb") as f:
            f.write(b"FORENSIC_EVIDENCE_BITSTREAM_TEST_DATA_12345")

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_dual_hash_calculation(self):
        verifier = HashVerifier(self.temp_dir.name)
        hashes = verifier.calculate_file_hashes(self.test_file)
        self.assertIn("sha256", hashes)
        self.assertIn("md5", hashes)
        self.assertEqual(len(hashes["sha256"]), 64)
        self.assertEqual(len(hashes["md5"]), 32)

    def test_directory_manifest(self):
        verifier = HashVerifier(self.temp_dir.name)
        report = verifier.verify_directory()
        self.assertIn("hashes", report)
        self.assertGreaterEqual(report["total_files_hashed"], 1)


class TestAuditLogger(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.logger = AuditLogger(self.temp_dir.name)

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_chained_audit_trail(self):
        self.logger.log_event("TEST_EVENT_1", {"detail": "Initial action"})
        self.logger.log_event("TEST_EVENT_2", {"detail": "Secondary action"})
        cert = self.logger.generate_audit_certificate()
        self.assertEqual(cert["total_logged_events"], 3)
        self.assertIn("certificate_hash", cert)
        self.assertTrue(os.path.exists(os.path.join(self.temp_dir.name, "Forensic_Audit_Trail.jsonl")))


class TestFreelistCarver(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.db_path = os.path.join(self.temp_dir.name, "test_evidence.db")
        conn = sqlite3.connect(self.db_path)
        cur = conn.cursor()
        cur.execute("CREATE TABLE test_tbl (id INTEGER PRIMARY KEY, secret TEXT);")
        cur.execute("INSERT INTO test_tbl VALUES (1, 'CONFIDENTIAL_DELETED_SUSPECT_EVIDENCE_DATA');")
        cur.execute("INSERT INTO test_tbl VALUES (2, 'ANOTHER_CONFIDENTIAL_CONVERSATION_RECORD');")
        conn.commit()
        # Delete row to create freelist entry
        cur.execute("DELETE FROM test_tbl WHERE id = 1;")
        conn.commit()
        conn.close()

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_carve_unallocated_data(self):
        carver = SQLiteFreelistCarver()
        carved = carver.carve_database(self.db_path)
        self.assertIsInstance(carved, list)
        found = any("CONFIDENTIAL" in c["extracted_text"] for c in carved)
        self.assertTrue(found)


class TestFinancialParser(unittest.TestCase):
    def test_bank_sms_debit(self):
        parser = FinancialParser()
        sms_text = "Your A/C XX4921 has been debited by Rs. 5,450.00 on 2026-10-05 for POS purchase. Avail Bal: Rs. 14,200.00."
        res = parser.parse_message_text(sms_text, "2026-10-05 12:00:00")
        self.assertIsNotNone(res)
        self.assertEqual(res["type"], "DEBIT / Outgoing")
        self.assertEqual(res["amount"], 5450.00)
        self.assertEqual(res["currency"], "NPR")
        self.assertEqual(res["account_ref"], "XX4921")
        self.assertEqual(res["balance"], 14200.00)

    def test_otp_extraction(self):
        parser = FinancialParser()
        sms_text = "928371 is your secret OTP for eSewa login. Do not share with anyone."
        res = parser.parse_message_text(sms_text, "2026-10-05 12:05:00")
        self.assertIsNotNone(res)
        self.assertEqual(res["type"], "OTP / 2FA Verification")
        self.assertEqual(res["otp_code"], "928371")


class TestNotificationParser(unittest.TestCase):
    def test_dumpsys_notification_parsing(self):
        parser = NotificationParser()
        sample_dumpsys = """
        NotificationRecord(0x1234: pkg=com.whatsapp user=UserHandle{0} id=101 tag=null score=0: Notification(channel=chat_channel android.title=String (John Doe) android.text=String (Meet me at the secret rendezvous spot at 9 PM) postTime=1672531199000))
        """
        records = parser.parse_dumpsys_notifications(sample_dumpsys)
        self.assertEqual(len(records), 1)
        self.assertEqual(records[0]["package"], "com.whatsapp")
        self.assertEqual(records[0]["title"], "John Doe")
        self.assertEqual(records[0]["body"], "Meet me at the secret rendezvous spot at 9 PM")


class TestUsageStatsParser(unittest.TestCase):
    def test_usagestats_parsing(self):
        parser = UsageStatsParser()
        sample_usagestats = """
        package=com.whatsapp totalTime="02:15:30" lastTime="2026-10-05 14:00:00" appLaunchCount=25
        time="2026-10-05 14:01:00" type=MOVE_TO_FOREGROUND package=com.whatsapp
        """
        res = parser.parse_dumpsys_usagestats(sample_usagestats)
        self.assertEqual(len(res["apps"]), 1)
        self.assertEqual(res["apps"][0]["package"], "com.whatsapp")
        self.assertEqual(res["apps"][0]["launch_count"], 25)
        self.assertEqual(len(res["events"]), 1)


class TestWifiBluetoothParser(unittest.TestCase):
    def test_wifi_dumpsys_parsing(self):
        parser = WifiBluetoothParser()
        dumpsys_sample = """
        ID: 1 SSID: "Forensic_HQ_5G" BSSID: 00:11:22:33:44:55 lastConnected: 1672531199000 WPA_PSK
        """
        res = parser.parse_dumpsys_wifi(dumpsys_sample)
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0]["ssid"], "Forensic_HQ_5G")
        self.assertEqual(res[0]["security"], "WPA/WPA2-PSK")

    def test_bluetooth_dumpsys_parsing(self):
        parser = WifiBluetoothParser()
        sample_bt = """
        Device: 11:22:33:44:55:66 (Investigator AirPods) BondState: 12
        """
        res = parser.parse_dumpsys_bluetooth(sample_bt)
        self.assertEqual(len(res), 1)
        self.assertEqual(res[0]["mac_address"], "11:22:33:44:55:66")
        self.assertEqual(res[0]["device_name"], "Investigator AirPods")


class TestExporters(unittest.TestCase):
    def setUp(self):
        self.temp_dir = tempfile.TemporaryDirectory()
        self.out_dir = self.temp_dir.name
        self.device_info = {
            "manufacturer": "Google",
            "model": "Pixel 7 Pro",
            "brand": "google",
            "serial": "TEST_PIXEL_12345",
            "android_version": "14",
            "sdk_version": "34",
            "build_fingerprint": "google/cheetah/cheetah:14/UD1A.230805.018/10323389:user/release-keys",
            "security_patch": "2026-09-01"
        }
        self.artifacts = {
            "sms": [{"address": "+1234567890", "body": "Classified report attached.", "timestamp": "2026-10-05 12:00:00", "direction": "Incoming", "status": "Read"}],
            "calls": [{"name": "Jane", "number": "+1234567890", "timestamp": "2026-10-05 12:10:00", "type": "Incoming", "duration_formatted": "5m 20s"}],
            "contacts": [{"display_name": "Jane Doe", "phone_number": "+1234567890", "email": "jane@corp.com", "note": "Target"}],
            "whatsapp": [{"sender": "+1234567890", "body": "Meeting set for 20:00", "timestamp": "2026-10-05 12:15:00", "is_outgoing": False}],
            "chrome": [{"title": "Encrypted Web Portal", "url": "https://secure.portal.internal", "timestamp": "2026-10-05 12:20:00", "visit_count": 5}],
            "notes": [{"app": "Notes", "title": "Access Credentials", "content": "Master API Key = SECRET_KEY_999", "created_time": "2026-10-05 12:00:00"}],
            "photos": [{"filename": "IMG_001.jpg", "timestamp": "2026-10-05 12:00:00", "latitude": 27.7172, "longitude": 85.3240, "file_size": 204800}],
            "financial": {
                "summary": {"total_transactions": 1, "total_debit_amount": 500.0, "total_credit_amount": 0.0, "otp_codes_captured": 0},
                "ledger": [{"type": "DEBIT / Outgoing", "amount": 500.0, "currency": "USD", "account_ref": "XX1122", "timestamp": "2026-10-05 12:00:00", "message_text": "Spent $500"}]
            },
            "usagestats": {
                "apps": [{"package": "com.whatsapp", "total_foreground_time": "01:30:00", "last_time_used": "2026-10-05 12:30:00", "launch_count": 10}],
                "events": []
            },
            "wifi": [{"ssid": "Internal_WiFi", "security": "WPA2-PSK", "bssid": "00:11:22:33:44:55", "last_connected": "2026-10-05 12:00:00"}],
            "bluetooth": [{"device_name": "Smart Watch", "mac_address": "AA:BB:CC:DD:EE:FF", "status": "Paired"}],
            "notifications": [{"package": "com.whatsapp", "title": "Jane", "body": "Hey there", "timestamp": "2026-10-05 12:00:00"}],
            "carved_records": [{"source_db": "test.db", "page_num": 1, "offset": 128, "extracted_text": "DELETED_FRAGMENT_EVIDENCE"}]
        }
        self.timeline_builder = TimelineBuilder()
        self.timeline_events = self.timeline_builder.build_timeline(self.artifacts)
        self.hash_verifier = HashVerifier(self.out_dir)
        self.hash_report = self.hash_verifier.verify_directory()

    def tearDown(self):
        self.temp_dir.cleanup()

    def test_bulk_data_exporter(self):
        bulk = BulkDataExporter(self.out_dir)
        bulk.export_all(self.artifacts, self.timeline_events, self.device_info)
        self.assertTrue(os.path.exists(os.path.join(self.out_dir, "csv_exports", "SMS_Messages.csv")))
        self.assertTrue(os.path.exists(os.path.join(self.out_dir, "Master_Super_Timeline.jsonl")))
        self.assertTrue(os.path.exists(os.path.join(self.out_dir, "CASE_UCO_Forensic_Ontology.jsonld")))

    def test_plain_text_tree_exporter(self):
        tree = PlainTextTreeExporter(self.out_dir)
        tree.export_all(self.artifacts, self.device_info, self.hash_report)
        self.assertTrue(os.path.exists(os.path.join(self.out_dir, "text_evidence", "01_Device_Hardware_Telemetrics.txt")))
        self.assertTrue(os.path.exists(os.path.join(self.out_dir, "text_evidence", "02_SMS_and_MMS_Messages.txt")))

    def test_docx_report_exporter(self):
        docx = DocxReportExporter(self.out_dir)
        report_path = docx.generate_report(self.artifacts, self.device_info, self.hash_report)
        self.assertTrue(os.path.exists(report_path))

    def test_html_dashboard_exporter(self):
        html = HTMLDashboardExporter(self.out_dir)
        dash_path = html.generate_dashboard(self.artifacts, self.device_info, self.timeline_events, self.hash_report)
        self.assertTrue(os.path.exists(dash_path))
        with open(dash_path, "r", encoding="utf-8") as f:
            content = f.read()
            self.assertIn("aforensic", content)
            self.assertIn("Leaflet", content)
            self.assertIn("Google", content)


if __name__ == "__main__":
    unittest.main()
