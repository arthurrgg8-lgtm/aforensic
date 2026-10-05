# 🛡️ aforensic - Android Enterprise Digital Forensics Suite

[![Compliance](https://img.shields.io/badge/Compliance-ISO%2FIEC%2027037%20%7C%20NIST%20CFTT-blue.svg)](https://www.iso.org/standard/44381.html)
[![Standard](https://img.shields.io/badge/Ontology-CASE%2FUCO%201.3.0-orange.svg)](https://caseontology.org/)
[![Python](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://python.org)
[![Platform](https://img.shields.io/badge/Platform-Linux%20%7C%20macOS%20%7C%20Windows-green.svg)]()
[![License](https://img.shields.io/badge/License-Apache%202.0-blue.svg)](LICENSE)

**aforensic** is a high-throughput, court-admissible digital forensics acquisition, extraction, and reporting suite engineered specifically for **Android** mobile devices operating in a **Fully Unlocked State** (USB Debugging enabled).

Built with complete 1:1 framework parity to **`iforensic`** (iOS Enterprise Forensics Suite), `aforensic` incorporates streaming NIST CFTT dual SHA-256 / MD5 hashing, ISO/IEC 27037 append-only chained audit logging, binary SQLite freelist & Write-Ahead Log (WAL) unallocated space carving, CASE/UCO JSON-LD cyber ontology generation, an executive Word (`.docx`) report, and an interactive offline HTML dashboard with Leaflet.js GPS mapping.

---

## 📑 Table of Contents
- [Architecture & Processing Pipeline](#-architecture--processing-pipeline)
- [Key Forensic Capabilities](#-key-forensic-capabilities)
  - [Artifact Extraction Matrix](#1-artifact-extraction-matrix)
  - [Forensic Integrity & Standards](#2-forensic-integrity--standards)
  - [SQLite Freelist & WAL Carving Engine](#3-sqlite-freelist--wal-carving-engine)
  - [Autonomous Self-Healing & Troubleshooting](#4-autonomous-self-healing--troubleshooting)
- [Device Preparation Guide (Unlocked State)](#-device-preparation-guide-unlocked-state)
- [Installation & Setup](#-installation--setup)
- [Usage Guide](#-usage-guide)
  - [Interactive Command Center](#1-interactive-command-center)
  - [Non-Interactive CLI Flags](#2-non-interactive-cli-flags)
- [Evidence Directory Structure](#-evidence-directory-structure)
- [Forensic Exporters & Formats](#-forensic-exporters--formats)
- [Autonomous Troubleshooting Suite](#-autonomous-troubleshooting-suite)
- [Running Unit Tests](#-running-unit-tests)
- [License & Admissibility Attestation](#-license--admissibility-attestation)

---

## 🏗️ Architecture & Processing Pipeline

```
+-----------------------------------------------------------------------------------+
|                           Target Android Device                                   |
|               (USB Debugging Enabled / Fully Unlocked State)                      |
+-----------------------------------------------------------------------------------+
                                         │
                                         ▼
+───────────────────────────────────────────────────────────────────────────────────+
|               ADB Connection & Autonomous Self-Healing Manager                    |
|       - Device Telemetry Detection  - RSA Pairing Verification / Display Wake     |
|       - Socket Health Monitoring    - Autonomous Daemon Recovery                  |
+───────────────────────────────────────────────────────────────────────────────────+
                                         │
                    ┌────────────────────┴────────────────────┐
                    ▼                                         ▼
+───────────────────────────────────────+ +─────────────────────────────────────────+
|     Live Content Providers & Dumpsys  | |    Bitstream Pull & Staged Artifacts    |
|  - SMS / MMS (`content://sms`)        | |  - WhatsApp Databases (`msgstore.db`)   |
|  - Call Logs (`content://call_log`)   | |  - Telegram / Teams / Signal Local DBs  |
|  - Contacts (`content://contacts`)    | |  - Chrome History & WebKit Cookies      |
|  - Notifications (`dumpsys notif`)    | |  - DCIM Photos, Recordings & Media      |
|  - UsageStats (`dumpsys usagestats`)  | |  - Wi-Fi XML & Bluetooth Configuration  |
+───────────────────────────────────────+ +─────────────────────────────────────────+
                    │                                         │
                    └────────────────────┬────────────────────┘
                                         ▼
+───────────────────────────────────────────────────────────────────────────────────+
|                  NIST CFTT Bitstream Hashing & Audit Engine                       |
|   - Streaming SHA-256 + MD5 Verification  - ISO/IEC 27037 Chained Hash Logging   |
+───────────────────────────────────────────────────────────────────────────────────+
                                         │
                    ┌────────────────────┴────────────────────┐
                    ▼                                         ▼
+───────────────────────────────────────+ +─────────────────────────────────────────+
|   Artifact Parsers & Financial Engine | |    SQLite Freelist & WAL Carving Engine |
|  - Financial Ledger & 2FA OTPs        | |  - B-Tree Freelist Trunks & Leaf Pages  |
|  - Contact & Truecaller Resolution    | |  - Unallocated Slack & Freeblock Chains |
|  - EXIF GPS Coordinate Extraction     | |  - Binary WAL Frame Recovery (0x377f06) |
+───────────────────────────────────────+ +─────────────────────────────────────────+
                                         │
                                         ▼
+───────────────────────────────────────────────────────────────────────────────────+
|               Master Unified Chronological Super-Timeline Generator               |
|      (Cross-Artifact Time Normalization: UTC + Local Nepal (+05:45) Offsets)      |
+───────────────────────────────────────────────────────────────────────────────────+
                                         │
     ┌───────────────────┬───────────────┴───────────────┬───────────────────┐
     ▼                   ▼                               ▼                   ▼
+──────────────+  +──────────────+                +──────────────+    +──────────────+
|  Executive   |  | Interactive  |                |  CASE / UCO  |    | Numbered     |
|  Word Report |  |   Dashboard  |                |  JSON-LD     |    | Plain-Text   |
|  (.docx)     |  | (Leaflet Map)|                |  Ontology    |    | Tree & CSVs  |
+──────────────+  +──────────────+                +──────────────+    +──────────────+
```

---

## 🚀 Key Forensic Capabilities

### 1. 📱 Artifact Extraction Matrix

| Category | Extraction Source / Provider | Extracted Data Fields & Forensic Value |
| :--- | :--- | :--- |
| **SMS & MMS** | `content://sms`, `mmssms.db`, `bugle_db` | Sender, recipient, timestamp (UTC/Local), delivery status, read flags, full message text. |
| **Call Logs** | `content://call_log/calls`, `calllog.db` | Caller name, phone number, direction (Incoming/Outgoing/Missed/Rejected), duration formatted. |
| **Contacts Directory** | `content://contacts/phones`, `contacts2.db` | Display name, phone numbers, email addresses, photo URIs, notes, Truecaller caller ID cache. |
| **WhatsApp Messenger** | `msgstore.db`, `wa.db`, shared media backups | 1-on-1 chats, group threads, JID identities, media captions, read receipts, message timestamps. |
| **Web Browsing** | Chrome / Chromium `History`, `Cookies` | Visited URLs, web page titles, visit counts, WebKit epoch timestamp conversion, cookie data. |
| **Notes & Memos** | Samsung Notes, ColorNote, memo cache | Full plaintext body, note titles, creation and last modified timestamps. |
| **Media & EXIF GPS** | MediaStore provider, `external.db`, `/sdcard/DCIM` | Photo filenames, file sizes, creation timestamps, EXIF GPS coordinates (Latitude/Longitude). |
| **Audio Recordings** | `/sdcard/Recordings`, Voice memos | Call recordings, voice notes, audio formats, durations, bitstream hashes. |
| **Enterprise Apps** | Telegram (`cache4.db`), Signal logs, MS Teams | Chat dialogue IDs, TL-buffer strings, user profile caches, channel communications. |
| **Wi-Fi & Bluetooth** | `WifiConfigStore.xml`, `dumpsys wifi`, `dumpsys bt` | SSIDs, PreSharedKeys, BSSIDs, security protocols (WPA3/WPA2/WEP), paired Bluetooth MACs. |
| **Notification Cache** | `dumpsys notification --noredact` | Push notifications, ephemeral messages (Signal, WhatsApp, Telegram, Snapchat), volatile OTPs. |
| **Financial Intelligence** | Bank SMS alerts, eSewa, Khalti, GPay, PhonePe | Transaction classification (Debit/Credit/OTP), masked accounts, balances, currency totals. |
| **UsageStats & Activity** | `dumpsys usagestats` | Daily/weekly app launch counts, total foreground screen time, app transition timelines. |
| **SQLite Freelist Carving** | B-tree freelist, freeblocks, WAL frames | Recovered unallocated UTF-8 string fragments, deleted chats, orphaned credentials. |

---

### 2. 🔒 Forensic Integrity & Standards

- **ISO/IEC 27037:2012 Certified Audit Trail:** Every extraction event is logged to `Forensic_Audit_Trail.jsonl` with cryptographically chained SHA-256 blocks (`prev_hash` -> `event_hash`). An official `ISO_27037_Forensic_Certificate.json` and human-readable audit certificate are generated upon completion.
- **NIST CFTT Dual-Engine Bitstream Hashing:** Computes streaming SHA-256 and MD5 bitstream hashes across every acquired database and artifact, generating `Chain_of_Custody_Verification.json` and `Chain_of_Custody_Manifest.txt`.
- **CASE / UCO 1.3.0 Standard Ontology:** Exports `CASE_UCO_Forensic_Ontology.jsonld` conforming to the Unified Cyber Ontology for direct interoperability with Autopsy, EnCase, and enterprise SIEM platforms.

---

### 3. 🧩 SQLite Freelist & WAL Carving Engine

`aforensic` includes a binary SQLite carver ([`core/sqlite_freelist_carver.py`](file:///home/lazzy/Desktop/aforensic/core/sqlite_freelist_carver.py)) that inspects:
1. **Freelist Trunk and Leaf Pages:** Scans unallocated pages marked in the SQLite database header.
2. **Freeblock Linked Lists:** Traverses cell freeblocks within active B-tree leaf pages (`0x0D` and `0x0A`).
3. **Unallocated Cell Slack:** Scans gaps between the cell pointer array and cell content start.
4. **Write-Ahead Log (WAL) Frames:** Directly decodes 24-byte WAL frame headers (`0x377f0682` / `0x377f0683`) to recover uncommitted or deleted transaction strings before checkpointing.

---

### 4. 🛠️ Autonomous Self-Healing & Troubleshooting

The built-in troubleshooter ([`core/troubleshooter.py`](file:///home/lazzy/Desktop/aforensic/core/troubleshooter.py)) and maintenance manager ([`core/maintenance_manager.py`](file:///home/lazzy/Desktop/aforensic/core/maintenance_manager.py)) autonomously resolve common connection issues:
- **ADB Daemon Hangs:** Auto-detects socket timeouts and restarts the ADB server (`adb kill-server` / `adb start-server`).
- **Unauthorized Device State:** Detects pending RSA pairing dialogs, sends screen wakeup events (`keyevent 224`), and guides the examiner.
- **Offline Devices:** Issues `adb reconnect` pulses to re-establish active sessions.
- **Socket Housekeeping:** Automatically cleans stale lockfiles and temporary probe directories.

---

## 📱 Device Preparation Guide (Unlocked State)

`aforensic` is designed for **Fully Unlocked State** acquisitions (no root or bootloader unlocking required):

1. **Enable Developer Options:**
   - Open **Settings** > **About Phone**.
   - Tap **Build Number** 7 times until the message *"You are now a developer!"* appears.
2. **Enable USB Debugging:**
   - Go to **Settings** > **System** (or **Additional Settings**) > **Developer Options**.
   - Toggle **USB Debugging** to **ON**.
3. **Authorize USB Connection:**
   - Connect the Android device to the forensic workstation via USB cable.
   - When the prompt *"Allow USB Debugging?"* appears on the phone screen, check **"Always allow from this computer"** and tap **Allow**.

---

## 📦 Installation & Setup

### 1. Prerequisites
- **Python 3.8+**
- **ADB (Android Debug Bridge):**
  - **Linux (Debian/Ubuntu):** `sudo apt update && sudo apt install -y adb`
  - **macOS:** `brew install android-platform-tools`
  - **Windows:** Included in Google Android SDK Platform-Tools.

### 2. Install aforensic
```bash
# Clone the standalone repository
git clone https://github.com/arthurrgg8-lgtm/aforensic.git
cd aforensic

# Install required Python dependencies
pip install -r requirements.txt

# Install as CLI executable
pip install -e .
```

---

## 🕹️ Usage Guide

### 1. Interactive Command Center
Launch the rich interactive terminal interface:
```bash
aforensic
# or
python3 cli.py
```
```text
        █████╗ ███████╗ ██████╗ ██████╗ ███████╗███╗   ██╗███████╗██╗ ██████╗
       ██╔══██╗██╔════╝██╔═══██╗██╔══██╗██╔════╝████╗  ██║██╔════╝██║██╔════╝
       ███████║█████╗  ██║   ██║██████╔╝█████╗  ██╔██╗ ██║███████╗██║██║     
       ██╔══██║██╔══╝  ██║   ██║██╔══██╗██╔══╝  ██║╚██╗██║╚════██║██║██║     
       ██║  ██║██║     ╚██████╔╝██║  ██║███████╗██║ ╚████║███████║██║╚██████╗
       ╚═╝  ╚═╝╚═╝      ╚═════╝ ╚═╝  ╚═╝╚══════╝╚═╝  ╚═══╝╚══════╝╚═╝ ╚═════╝
    Android Enterprise Digital Forensics Suite | v1.0.0
    ISO/IEC 27037:2012 Certified | NIST CFTT Compliant | Dual SHA-256/MD5 Hash

FORENSIC OPERATION MENU:
  1. Auto-Pilot Complete Forensic Acquisition & Reports (Recommended)
  2. Quick Triage & Communications Extraction (SMS/Calls/WhatsApp/OTPs)
  3. Deep Physical & SQLite Freelist Unallocated Carve
  4. Autonomous ADB Diagnostics & Troubleshooting Suite
  0. Exit
```

### 2. Non-Interactive CLI Flags

| Flag | Purpose | Example |
| :--- | :--- | :--- |
| `--auto` | Complete end-to-end extraction and multi-format report generation. | `aforensic --auto` |
| `--quick` | Rapid triage of communications (SMS, Calls, WhatsApp, OTPs, Notifications). | `aforensic --quick` |
| `--full` | Full acquisition with deep SQLite freelist carving and media GPS extraction. | `aforensic --full` |
| `--targets <SERIAL>` | Target a specific device serial identifier or wireless ADB endpoint. | `aforensic --targets 192.168.1.50:5555` |
| `--output <DIR>` | Specify a custom destination directory for evidence exports. | `aforensic --output /mnt/forensics/case_001` |
| `--troubleshoot` | Run the autonomous ADB and USB diagnostic suite. | `aforensic --troubleshoot` |
| `--check-updates` | Clean temporary sockets and check upstream OEM definition updates. | `aforensic --check-updates` |
| `--version` | Display version information and compliance badges. | `aforensic --version` |

---

## 📂 Evidence Directory Structure

Every forensic acquisition produces a structured evidence folder:

```text
evidence_Pixel7Pro_TEST123/
├── Forensic_Examination_Report.docx         # Executive Word Report with sign-offs
├── Forensic_Interactive_Dashboard.html       # Single-page Dashboard + Leaflet GPS map
├── CASE_UCO_Forensic_Ontology.jsonld         # CASE / UCO 1.3.0 Standard Graph
├── Master_Super_Timeline.jsonl               # Chronological Master Timeline (JSONL)
├── Master_Super_Timeline.csv                 # Chronological Master Timeline (CSV)
├── Forensic_Audit_Trail.jsonl                # ISO/IEC 27037 Append-Only Chained Log
├── ISO_27037_Forensic_Certificate.json       # Formal Cryptographic Certificate
├── Forensic_Audit_Certificate.txt            # Human-readable Audit Certificate
├── Chain_of_Custody_Verification.json        # NIST CFTT SHA-256 & MD5 Manifest
├── Chain_of_Custody_Manifest.txt             # Bitstream Evidence Digest Table
│
├── csv_exports/                              # Raw Tabular CSV Artifacts
│   ├── SMS_Messages.csv
│   ├── Call_Logs.csv
│   ├── Contacts.csv
│   ├── WhatsApp_Messages.csv
│   ├── Chrome_History.csv
│   ├── Financial_Ledger.csv
│   ├── WiFi_Networks.csv
│   ├── Bluetooth_Devices.csv
│   ├── Notification_Cache.csv
│   ├── Usage_App_Summary.csv
│   ├── Usage_Events.csv
│   └── Carved_Freelist_Records.csv
│
├── text_evidence/                            # Numbered Terminal Dossiers (Grep-ready)
│   ├── 01_Device_Hardware_Telemetrics.txt
│   ├── 02_SMS_and_MMS_Messages.txt
│   ├── 03_Call_Logs.txt
│   ├── 04_Contacts_Directory.txt
│   ├── 05_WhatsApp_Chats.txt
│   ├── 06_Chrome_Browser_History.txt
│   ├── 07_Notes_and_Memos.txt
│   ├── 08_Financial_Intelligence.txt
│   ├── 09_UsageStats_App_Activity.txt
│   ├── 10_WiFi_and_Bluetooth_Profiles.txt
│   ├── 11_Notification_History.txt
│   └── 12_Carved_Freelist_Records.txt
│
└── raw_databases/                            # Bitstream Database Copies & Staging
```

---

## 📊 Forensic Exporters & Formats

### 1. Executive Word Report (`Forensic_Examination_Report.docx`)
- Court-admissible formatting with ISO/IEC 27037 attestation banner.
- Case & examiner identification table.
- Target device telemetrics (Brand, Model, Serial, Android Version, SDK, Build Fingerprint, Security Patch).
- NIST CFTT bitstream hash verification table.
- Quantitative evidence summary table.
- Financial intelligence & 2FA OTP analysis.
- Formal investigator certification and physical sign-off block.

### 2. Interactive Single-Page HTML Dashboard (`Forensic_Interactive_Dashboard.html`)
- Completely offline capable with embedded styles and scripts.
- Cyber/Forensic dark UI theme with live instant search across all tables.
- **Leaflet.js GPS Mapping:** Pins photos with EXIF GPS coordinates directly onto an interactive map.
- Responsive tabs: Overview, Master Timeline, SMS, Calls, Contacts, WhatsApp, Chrome, Photos/GPS, Financial Ledger, UsageStats, Wi-Fi & Bluetooth, Notifications, Freelist Carved Data, and ISO 27037 Audit Certificate.

---

## 🧪 Running Unit Tests

The test suite thoroughly validates time utilities, database connectors, NIST hash calculation, ISO 27037 audit chaining, freelist carving, financial intelligence, usage stats, notification parsing, and all exporters:

```bash
python3 -m unittest discover -s tests -v
```
```text
test_bank_sms_debit (test_enterprise_suite.TestFinancialParser.test_bank_sms_debit) ... ok
test_bluetooth_dumpsys_parsing (test_enterprise_suite.TestWifiBluetoothParser.test_bluetooth_dumpsys_parsing) ... ok
test_bulk_data_exporter (test_enterprise_suite.TestExporters.test_bulk_data_exporter) ... ok
test_carve_unallocated_data (test_enterprise_suite.TestFreelistCarver.test_carve_unallocated_data) ... ok
test_chained_audit_trail (test_enterprise_suite.TestAuditLogger.test_chained_audit_trail) ... ok
test_directory_manifest (test_enterprise_suite.TestHashVerifier.test_directory_manifest) ... ok
test_docx_report_exporter (test_enterprise_suite.TestExporters.test_docx_report_exporter) ... ok
test_dual_hash_calculation (test_enterprise_suite.TestHashVerifier.test_dual_hash_calculation) ... ok
test_dumpsys_notification_parsing (test_enterprise_suite.TestNotificationParser.test_dumpsys_notification_parsing) ... ok
test_epoch_conversion (test_enterprise_suite.TestTimeUtils.test_epoch_conversion) ... ok
test_html_dashboard_exporter (test_enterprise_suite.TestExporters.test_html_dashboard_exporter) ... ok
test_millisecond_conversion (test_enterprise_suite.TestTimeUtils.test_millisecond_conversion) ... ok
test_otp_extraction (test_enterprise_suite.TestFinancialParser.test_otp_extraction) ... ok
test_parse_to_epoch (test_enterprise_suite.TestTimeUtils.test_parse_to_epoch) ... ok
test_plain_text_tree_exporter (test_enterprise_suite.TestExporters.test_plain_text_tree_exporter) ... ok
test_usagestats_parsing (test_enterprise_suite.TestUsageStatsParser.test_usagestats_parsing) ... ok
test_wifi_dumpsys_parsing (test_enterprise_suite.TestWifiBluetoothParser.test_wifi_dumpsys_parsing) ... ok

----------------------------------------------------------------------
Ran 17 tests in 0.091s

OK
```

---

## 📜 License & Admissibility Attestation

Licensed under the **Apache-2.0 License**. 

Designed in strict adherence to **ISO/IEC 27037:2012** (*Guidelines for identification, collection, acquisition, and preservation of digital evidence*) and **NIST SP 800-86** (*Guide to Integrating Forensic Techniques into Incident Response*). Intended for certified digital forensic examiners, law enforcement agencies, and enterprise security incident response teams.
