# 🛡️ aforensic - Android Enterprise Digital Forensics Suite

[![Compliance](https://img.shields.io/badge/Compliance-ISO%2FIEC%2027037%20%7C%20NIST%20CFTT-blue.svg)](https://www.iso.org/standard/44381.html)
[![Standard](https://img.shields.io/badge/Ontology-CASE%2FUCO%201.3.0-orange.svg)](https://caseontology.org/)
[![Python](https://img.shields.io/badge/Python-3.8%2B-blue.svg)](https://python.org)
[![Platform](https://img.shields.io/badge/Platform-Linux%20%7C%20macOS%20%7C%20Windows-green.svg)]()

**aforensic** is a high-throughput, court-admissible digital forensics acquisition, extraction, and reporting framework engineered specifically for **Android** devices operating in a **Fully Unlocked State** (USB Debugging enabled).

Built with 1:1 framework parity to `iforensic` (iOS Forensics Suite), **aforensic** incorporates streaming NIST CFTT dual SHA-256 / MD5 hashing, ISO/IEC 27037 append-only chained audit logging, binary SQLite freelist & WAL unallocated space carving, CASE/UCO JSON-LD cyber ontology generation, an executive Word (`.docx`) report, and an interactive offline HTML forensic dashboard with Leaflet.js GPS mapping.

---

## 🚀 Key Forensic Capabilities

### 1. 📱 Comprehensive Artifact Coverage
| Artifact Category | Acquisition Vectors & Parsed Databases | Key Forensic Fields Extracted |
| :--- | :--- | :--- |
| **SMS & MMS** | `content://sms`, `mmssms.db`, `bugle_db` | Sender, recipient, timestamp (UTC & Local), delivery status, message body, thread ID. |
| **Call History** | `content://call_log/calls`, `calllog.db` | Caller name, phone number, direction (Incoming/Outgoing/Missed/Rejected), formatted duration. |
| **Contacts Directory** | `content://contacts/phones`, `contacts2.db` | Display name, mobile/work numbers, email addresses, photo URIs, Truecaller cache tags. |
| **WhatsApp Messenger** | `msgstore.db`, `wa.db`, shared media backups | 1-on-1 chats, group conversations, sender JID, timestamps, media captions, read receipts. |
| **Web Browsing** | Chrome / Chromium `History`, `Cookies` | Visited URLs, page titles, visit counts, WebKit epoch timestamp decoding, cookies. |
| **Notes & Memos** | Samsung Notes, ColorNote, Google Keep memo cache | Note titles, full plaintext bodies, creation and last modification timestamps. |
| **Media & EXIF GPS** | MediaStore provider, `external.db`, DCIM | Camera photos, video metadata, EXIF GPS coordinates (Latitude/Longitude), timestamps. |
| **Audio Recordings** | Voice memos, call recordings (`/sdcard/Recordings`) | Audio file headers, duration, recording timestamps, bitstream hashes. |
| **Enterprise Apps** | Telegram (`cache4.db`), Signal logs, MS Teams DBs | Dialogue IDs, uncommitted TL-buffers, user profile caches, channel communications. |
| **Wi-Fi & Bluetooth** | `WifiConfigStore.xml`, `dumpsys wifi`, `dumpsys bluetooth` | SSIDs, PreSharedKeys, BSSIDs, security types (WPA3/WPA2/WEP), paired Bluetooth MAC addresses. |
| **Notification Cache** | `dumpsys notification --noredact` | Active and historical push notifications, ephemeral messages (Signal, WhatsApp, Telegram, Snapchat). |
| **Financial Ledger** | Bank alerts, eSewa, Khalti, Google Pay, PhonePe | Automated transaction categorization (Debit/Credit/OTP), masked accounts, currency volumes. |
| **UsageStats & Activity** | `dumpsys usagestats` | Daily/weekly app launch counts, total foreground screen time, app transition events. |
| **SQLite Freelist Carving** | B-tree freelist pages, freeblock chains, WAL frames | Recovered unallocated UTF-8 strings, deleted chat fragments, orphaned credentials. |

---

## 🔒 Forensic Integrity & Standards

- **ISO/IEC 27037:2012 Certified Audit Trail:** Maintains `Forensic_Audit_Trail.jsonl` where every examiner action is signed with sequential SHA-256 hash chains (`prev_hash` -> `event_hash`).
- **NIST CFTT Bitstream Verification:** Calculates streaming SHA-256 and MD5 bitstream hashes across every database and acquired evidence artifact.
- **CASE / UCO 1.3.0 Standard Ontology:** Exports `CASE_UCO_Forensic_Ontology.jsonld` for immediate ingestion into enterprise DFIR platforms (Autopsy, EnCase, X-Ways).
- **Executive Word (`.docx`) Report:** Court-ready dossier featuring case metadata, device telemetrics, artifact tables, and formal examiner sign-off block.
- **Interactive Offline HTML Dashboard:** Single-page dashboard with dark UI theme, client-side live search, Leaflet.js GPS mapping for EXIF photo coordinates, and freelist viewer.

---

## 🛠️ Autonomous Self-Healing & Troubleshooting

`aforensic` includes an automated diagnostics engine (`core/troubleshooter.py`) and maintenance manager (`core/maintenance_manager.py`) that executes non-destructive auto-repairs:
- Automatically detects and restarts frozen ADB daemon servers (`adb kill-server` / `adb start-server`).
- Detects `unauthorized` device states, wakes the phone display, and guides the examiner to accept RSA keys.
- Cleans orphaned socket locks and temporary staging files.
- Checks upstream GitHub repositories for updated OEM profile definitions.

---

## 📦 Installation & Prerequisites

### 1. Requirements
- **Python 3.8+**
- **ADB (Android Debug Bridge)** installed and accessible on PATH:
  - **Linux (Debian/Ubuntu):** `sudo apt update && sudo apt install -y adb`
  - **macOS:** `brew install android-platform-tools`
  - **Windows:** Included in Android SDK Platform Tools.

### 2. Install aforensic
```bash
git clone https://github.com/arthurrgg8-lgtm/aforensic.git
cd aforensic
pip install -r requirements.txt
pip install -e .
```

---

## 🕹️ Usage & Command Line Interface

### 1. Interactive Command Center
Launch the interactive terminal UI:
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

### 2. Non-Interactive CLI Automation
```bash
# Auto-Pilot complete extraction with reports
aforensic --auto

# Quick communications triage
aforensic --quick

# Full acquisition targeting specific device serial and custom destination
aforensic --full --targets 192.168.1.50:5555 --output /mnt/forensics/case_001

# Run autonomous troubleshooter diagnostics
aforensic --troubleshoot

# Check definitions and clean stale sockets
aforensic --check-updates
```

---

## 📂 Evidence Output Structure

```text
evidence_Pixel7Pro_TEST123/
├── Forensic_Examination_Report.docx         # Executive Word Report
├── Forensic_Interactive_Dashboard.html       # Offline Dashboard + Leaflet Map
├── CASE_UCO_Forensic_Ontology.jsonld         # CASE / UCO 1.3.0 Graph
├── Master_Super_Timeline.jsonl               # Chronological JSONL Timeline
├── Forensic_Audit_Trail.jsonl                # ISO/IEC 27037 Chained Hash Log
├── ISO_27037_Forensic_Certificate.json       # Formal Verification Certificate
├── Chain_of_Custody_Verification.json        # NIST CFTT SHA-256/MD5 Hashes
├── Chain_of_Custody_Manifest.txt             # Human-readable Bitstream Digest
├── csv_exports/                              # Raw Tabular CSV Exports
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
├── text_evidence/                            # Numbered Terminal Dossiers
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
└── raw_databases/                            # Staged Bitstream Copies
```

---

## 🧪 Running Unit Tests

To run the complete enterprise test suite:
```bash
python3 -m unittest discover -s tests -v
```

---

## 📜 License & Forensic Attestation
Licensed under the Apache-2.0 License. Designed for authorized law enforcement, corporate incident response teams, and certified digital forensic examiners.
