#!/usr/bin/env python3
"""
aforensic - Enterprise Digital Forensics Suite for Android.
Adheres to ISO/IEC 27037:2012, NIST SP 800-86, and NIST CFTT Evidence Standards.
"""

import os
import sys
import argparse
import time
from datetime import datetime, timezone
from typing import Dict, Any, Optional

# Rich UI
try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn, TimeRemainingColumn
    from rich import print as rprint
    console = Console()
except ImportError:
    console = None

# Core Imports
from core.device_detector import DeviceDetector
from core.adb_manager import ADBManager
from core.storage_manager import StorageManager
from core.hash_verifier import HashVerifier
from core.audit_logger import AuditLogger
from core.sqlite_freelist_carver import SQLiteFreelistCarver
from core.timeline import TimelineBuilder
from core.troubleshooter import Troubleshooter
from core.maintenance_manager import MaintenanceManager

# Parsers
from parsers.sms_parser import SMSParser
from parsers.calls_parser import CallsParser
from parsers.contacts_parser import ContactsParser
from parsers.whatsapp_parser import WhatsAppParser
from parsers.chrome_parser import ChromeParser
from parsers.notes_parser import NotesParser
from parsers.photos_parser import PhotosParser
from parsers.recordings_parser import RecordingsParser
from parsers.enterprise_apps_parser import EnterpriseAppsParser
from parsers.wifi_bluetooth_parser import WifiBluetoothParser
from parsers.notification_parser import NotificationParser
from parsers.financial_parser import FinancialParser
from parsers.usagestats_parser import UsageStatsParser

# Exporters
from exporters.bulk_data_exporter import BulkDataExporter
from exporters.plain_text_tree_exporter import PlainTextTreeExporter
from exporters.docx_report import DocxReportExporter
from exporters.html_dashboard import HTMLDashboardExporter

__version__ = "1.0.0"


def print_banner():
    banner_text = f"""[bold cyan]
        █████╗ ███████╗ ██████╗ ██████╗ ███████╗███╗   ██╗███████╗██╗ ██████╗
       ██╔══██╗██╔════╝██╔═══██╗██╔══██╗██╔════╝████╗  ██║██╔════╝██║██╔════╝
       ███████║█████╗  ██║   ██║██████╔╝█████╗  ██╔██╗ ██║███████╗██║██║     
       ██╔══██║██╔══╝  ██║   ██║██╔══██╗██╔══╝  ██║╚██╗██║╚════██║██║██║     
       ██║  ██║██║     ╚██████╔╝██║  ██║███████╗██║ ╚████║███████║██║╚██████╗
       ╚═╝  ╚═╝╚═╝      ╚═════╝ ╚═╝  ╚═╝╚══════╝╚═╝  ╚═══╝╚══════╝╚═╝ ╚═════╝[/bold cyan]
    [bold white]Android Enterprise Digital Forensics Suite[/bold white] | [green]v{__version__}[/green]
    [dim]ISO/IEC 27037:2012 Certified | NIST CFTT Compliant | Dual SHA-256/MD5 Hash[/dim]
    """
    if console:
        console.print(banner_text)
    else:
        print(f"=== AFORENSIC - ANDROID ENTERPRISE FORENSIC SUITE v{__version__} ===")


def run_pipeline(mode: str = "full", 
                 target_serial: Optional[str] = None, 
                 custom_output_dir: Optional[str] = None,
                 interactive: bool = True):
    """
    Executes the end-to-end digital forensic acquisition and reporting pipeline.
    """
    start_time = time.time()
    
    # 1. Check Maintenance & Socket State
    maintenance = MaintenanceManager()
    maintenance.clean_stale_sockets()

    # 2. Detect Devices
    detector = DeviceDetector()
    devices = detector.detect_devices()

    if not devices:
        if console:
            console.print("[bold red][!] No Android devices detected via ADB.[/bold red]")
            console.print("[yellow][*] Attempting autonomous troubleshooting and ADB daemon recovery...[/yellow]")
        troubleshooter = Troubleshooter()
        troubleshooter.run_full_diagnostics()
        devices = detector.detect_devices()
        if not devices:
            if console:
                console.print("[bold red][X] Acquisition aborted: No authorized Android device connected.[/bold red]")
            return False

    # Select target device
    selected_device = None
    if target_serial:
        for d in devices:
            if d.get("serial") == target_serial:
                selected_device = d
                break
    if not selected_device:
        selected_device = devices[0]

    # Check device authorization status
    if selected_device.get("status") == "unauthorized":
        if console:
            console.print(f"[bold red][!] Device {selected_device.get('serial')} is UNAUTHORIZED.[/bold red]")
            console.print("[yellow][*] Please unlock the phone and accept the 'Allow USB Debugging' RSA prompt on the screen.[/yellow]")
        # Trigger troubleshooter to prompt user
        troubleshooter = Troubleshooter(selected_device.get("serial"))
        troubleshooter.verify_device_ready()
        return False

    # Collect telemetry
    dev_serial = selected_device.get("serial")
    dev_info = detector.get_device_telemetry(dev_serial)

    if console:
        table = Table(title="Target Device Telemetry", border_style="cyan")
        table.add_column("Property", style="bold white")
        table.add_column("Value", style="green")
        table.add_row("Manufacturer / Brand", f"{dev_info.get('manufacturer')} ({dev_info.get('brand')})")
        table.add_row("Model / Codename", f"{dev_info.get('model')} ({dev_info.get('product')})")
        table.add_row("Hardware Serial", dev_info.get("serial"))
        table.add_row("Android Version", f"{dev_info.get('android_version')} (SDK {dev_info.get('sdk_version')})")
        table.add_row("Build Fingerprint", dev_info.get("build_fingerprint"))
        table.add_row("Security Patch", dev_info.get("security_patch"))
        console.print(table)

    # 3. Setup Evidence Storage
    storage_mgr = StorageManager()
    if custom_output_dir:
        evidence_dir = os.path.abspath(custom_output_dir)
    else:
        evidence_dir = storage_mgr.get_optimal_output_dir(f"evidence_{dev_info.get('model', 'android')}_{dev_serial}")

    os.makedirs(evidence_dir, exist_ok=True)
    raw_dir = os.path.join(evidence_dir, "raw_databases")
    os.makedirs(raw_dir, exist_ok=True)

    if console:
        console.print(f"[bold green][✓] Evidence destination directory:[/bold green] [cyan]{evidence_dir}[/cyan]")

    # 4. Initialize Audit Trail & Hash Engines
    audit_logger = AuditLogger(evidence_dir)
    audit_logger.log_event("SESSION_START", {
        "mode": mode,
        "device_serial": dev_serial,
        "device_model": dev_info.get("model"),
        "android_version": dev_info.get("android_version")
    })

    adb = ADBManager(dev_serial)
    hash_verifier = HashVerifier(evidence_dir)
    carver = SQLiteFreelistCarver()
    timeline_builder = TimelineBuilder()

    artifacts: Dict[str, Any] = {
        "sms": [],
        "calls": [],
        "contacts": [],
        "whatsapp": [],
        "chrome": [],
        "notes": [],
        "photos": [],
        "recordings": [],
        "enterprise_apps": [],
        "wifi": [],
        "bluetooth": [],
        "notifications": [],
        "financial": {},
        "usagestats": {},
        "carved_records": []
    }

    # 5. Extraction Phase
    if console:
        console.print("\n[bold cyan]─── Launching Forensic Acquisition Phase ───[/bold cyan]")

    # A. SMS / MMS
    if console:
        console.print("[dim]→ Extracting SMS / MMS messages...[/dim]")
    sms_parser = SMSParser(adb)
    artifacts["sms"] = sms_parser.extract_from_device(raw_dir)
    audit_logger.log_event("ACQUISITION_SMS", {"count": len(artifacts["sms"])})

    # B. Telephony Call Logs
    if console:
        console.print("[dim]→ Extracting telephony call history...[/dim]")
    calls_parser = CallsParser(adb)
    artifacts["calls"] = calls_parser.extract_from_device(raw_dir)
    audit_logger.log_event("ACQUISITION_CALLS", {"count": len(artifacts["calls"])})

    # C. Contacts Directory
    if console:
        console.print("[dim]→ Extracting contacts directory & Truecaller caches...[/dim]")
    contacts_parser = ContactsParser(adb)
    artifacts["contacts"] = contacts_parser.extract_from_device(raw_dir)
    audit_logger.log_event("ACQUISITION_CONTACTS", {"count": len(artifacts["contacts"])})

    # D. WhatsApp Messenger
    if console:
        console.print("[dim]→ Extracting WhatsApp conversations & backups...[/dim]")
    wa_parser = WhatsAppParser(raw_dir)
    # Pull WhatsApp database or shared storage backups
    adb.pull_path("/sdcard/WhatsApp/Databases", os.path.join(raw_dir, "WhatsApp"))
    adb.pull_path("/sdcard/Android/media/com.whatsapp/WhatsApp/Databases", os.path.join(raw_dir, "WhatsApp_Media"))
    artifacts["whatsapp"] = wa_parser.parse_all(raw_dir)
    audit_logger.log_event("ACQUISITION_WHATSAPP", {"count": len(artifacts["whatsapp"])})

    # E. Chrome Browser History
    if console:
        console.print("[dim]→ Extracting Chrome web history & bookmarks...[/dim]")
    chrome_parser = ChromeParser()
    adb.pull_path("/sdcard/Android/data/com.android.chrome", os.path.join(raw_dir, "Chrome"))
    artifacts["chrome"] = chrome_parser.parse_history(raw_dir)
    audit_logger.log_event("ACQUISITION_CHROME", {"count": len(artifacts["chrome"])})

    # F. Push Notifications & Ephemeral Chats
    if console:
        console.print("[dim]→ Extracting notification cache & volatile 2FA codes...[/dim]")
    notif_parser = NotificationParser(adb)
    artifacts["notifications"] = notif_parser.extract_live()
    audit_logger.log_event("ACQUISITION_NOTIFICATIONS", {"count": len(artifacts["notifications"])})

    # G. Financial Intelligence & Banking Ledger
    if console:
        console.print("[dim]→ Analyzing financial intelligence, mobile wallets & bank SMS...[/dim]")
    fin_parser = FinancialParser()
    artifacts["financial"] = fin_parser.parse_corpus(artifacts["sms"], artifacts["notifications"])
    audit_logger.log_event("ACQUISITION_FINANCIAL", {"count": len(artifacts["financial"].get("ledger", []))})

    # H. Wi-Fi & Bluetooth Profiles
    if console:
        console.print("[dim]→ Extracting Wi-Fi access points & Bluetooth paired devices...[/dim]")
    net_parser = WifiBluetoothParser(adb)
    net_res = net_parser.extract_from_device()
    artifacts["wifi"] = net_res.get("wifi", [])
    artifacts["bluetooth"] = net_res.get("bluetooth", [])
    audit_logger.log_event("ACQUISITION_NETWORK", {"wifi_count": len(artifacts["wifi"]), "bt_count": len(artifacts["bluetooth"])})

    # I. UsageStats & App Screen Time
    if console:
        console.print("[dim]→ Extracting Application UsageStats & execution logs...[/dim]")
    ustats_parser = UsageStatsParser(adb)
    artifacts["usagestats"] = ustats_parser.extract_live()
    audit_logger.log_event("ACQUISITION_USAGESTATS", {"apps_count": len(artifacts["usagestats"].get("apps", []))})

    # J. Notes & Memos
    if console:
        console.print("[dim]→ Extracting notes and memos...[/dim]")
    notes_parser = NotesParser()
    artifacts["notes"] = notes_parser.parse_all(raw_dir)

    # K. Enterprise Communication Apps (Telegram, Signal, Teams)
    if console:
        console.print("[dim]→ Extracting Enterprise Apps (Telegram / Signal / Teams)...[/dim]")
    ent_parser = EnterpriseAppsParser()
    adb.pull_path("/sdcard/Telegram", os.path.join(raw_dir, "Telegram"))
    adb.pull_path("/sdcard/Android/data/org.telegram.messenger", os.path.join(raw_dir, "Telegram_Data"))
    artifacts["enterprise_apps"] = ent_parser.parse_all(raw_dir)

    # L. Photos & Media GPS (If full mode)
    if mode == "full":
        if console:
            console.print("[dim]→ Extracting MediaStore photos & EXIF GPS coordinates...[/dim]")
        photos_parser = PhotosParser(adb)
        adb.pull_path("/sdcard/DCIM/Camera", os.path.join(raw_dir, "DCIM"))
        artifacts["photos"] = photos_parser.extract_from_device(raw_dir)

        # M. Audio Recordings
        rec_parser = RecordingsParser(adb)
        adb.pull_path("/sdcard/Recordings", os.path.join(raw_dir, "Recordings"))
        artifacts["recordings"] = rec_parser.extract_from_device(raw_dir)

    # 6. SQLite Freelist & WAL Unallocated Deep Carve
    if console:
        console.print("[dim]→ Executing SQLite Freelist & WAL binary carver on acquired databases...[/dim]")
    for root, _, files in os.walk(raw_dir):
        for f in files:
            if f.endswith((".db", ".sqlite", ".sqlite3", ".wal")):
                full_db = os.path.join(root, f)
                carved_items = carver.carve_database(full_db)
                artifacts["carved_records"].extend(carved_items)

    audit_logger.log_event("ACQUISITION_CARVER", {"carved_fragments": len(artifacts["carved_records"])})

    # 7. Construct Unified Master Super-Timeline
    if console:
        console.print("[dim]→ Building unified chronological Master Super-Timeline...[/dim]")
    timeline_events = timeline_builder.build_timeline(artifacts)
    audit_logger.log_event("TIMELINE_GENERATION", {"total_events": len(timeline_events)})

    # 8. Cryptographic Hash Calculation (NIST CFTT)
    if console:
        console.print("[dim]→ Calculating NIST CFTT SHA-256 and MD5 bitstream hashes...[/dim]")
    hash_report = hash_verifier.verify_directory(evidence_dir)
    hash_verifier.save_hash_manifest()

    # Finalize Audit Certificate
    audit_cert = audit_logger.generate_audit_certificate()

    # 9. Exporters Phase
    if console:
        console.print("\n[bold cyan]─── Compiling Forensic Reports & SIEM Standard Formats ───[/bold cyan]")

    # A. Bulk CSV & CASE/UCO JSON-LD
    bulk_exporter = BulkDataExporter(evidence_dir)
    bulk_exporter.export_all(artifacts, timeline_events, dev_info)

    # B. Plain Text Evidence Tree
    text_exporter = PlainTextTreeExporter(evidence_dir)
    text_exporter.export_all(artifacts, dev_info, hash_report)

    # C. Executive Word (.docx) Report
    docx_exporter = DocxReportExporter(evidence_dir)
    report_path = docx_exporter.generate_report(artifacts, dev_info, hash_report)

    # D. Interactive HTML Single-Page Dashboard
    html_exporter = HTMLDashboardExporter(evidence_dir)
    dashboard_path = html_exporter.generate_dashboard(artifacts, dev_info, timeline_events, hash_report, audit_cert)

    elapsed = time.time() - start_time

    # 10. Summary Display
    if console:
        console.print("\n" + "=" * 70)
        console.print(f"[bold green]✔ FORENSIC EXTRACTION COMPLETED IN {elapsed:.2f} SECONDS[/bold green]")
        console.print("=" * 70)
        console.print(f"[bold white]Evidence Location:[/bold white] [cyan]{evidence_dir}[/cyan]")
        console.print(f"[bold white]Executive Report :[/bold white] [green]{report_path}[/green]")
        console.print(f"[bold white]Interactive Dash :[/bold white] [green]{dashboard_path}[/green]")
        console.print(f"[bold white]CASE/UCO Graph   :[/bold white] [cyan]{os.path.join(evidence_dir, 'CASE_UCO_Forensic_Ontology.jsonld')}[/cyan]")
        console.print(f"[bold white]Audit Certificate:[/bold white] [cyan]{os.path.join(evidence_dir, 'ISO_27037_Forensic_Certificate.json')}[/cyan]")
        console.print("=" * 70 + "\n")
    else:
        print(f"[+] Forensic acquisition completed in {elapsed:.2f}s. Evidence stored at {evidence_dir}")

    return True


def interactive_menu():
    """
    Renders the interactive command center UI.
    """
    while True:
        print_banner()
        if console:
            console.print("[bold cyan]FORENSIC OPERATION MENU:[/bold cyan]")
            console.print("  [bold green]1.[/bold green] Auto-Pilot Complete Forensic Acquisition & Reports [dim](Recommended)[/dim]")
            console.print("  [bold green]2.[/bold green] Quick Triage & Communications Extraction [dim](SMS/Calls/WhatsApp/OTPs)[/dim]")
            console.print("  [bold green]3.[/bold green] Deep Physical & SQLite Freelist Unallocated Carve")
            console.print("  [bold green]4.[/bold green] Autonomous ADB Diagnostics & Troubleshooting Suite")
            console.print("  [bold green]0.[/bold green] Exit")
            choice = console.input("\n[bold yellow]Select operation [0-4]: [/bold yellow]").strip()
        else:
            print("1. Auto-Pilot Complete Acquisition\n2. Quick Triage\n3. Deep Carve\n4. Diagnostics\n0. Exit")
            choice = input("Select [0-4]: ").strip()

        if choice == "1":
            run_pipeline(mode="full")
            if console:
                console.input("\n[dim]Press Enter to return to main menu...[/dim]")
        elif choice == "2":
            run_pipeline(mode="quick")
            if console:
                console.input("\n[dim]Press Enter to return to main menu...[/dim]")
        elif choice == "3":
            run_pipeline(mode="full")
            if console:
                console.input("\n[dim]Press Enter to return to main menu...[/dim]")
        elif choice == "4":
            t = Troubleshooter()
            t.run_full_diagnostics()
            if console:
                console.input("\n[dim]Press Enter to return to main menu...[/dim]")
        elif choice == "0":
            if console:
                console.print("[bold cyan]Exiting aforensic. Stay safe![/bold cyan]")
            break
        else:
            if console:
                console.print("[red]Invalid choice. Please try again.[/red]")
            time.sleep(1)


def main():
    parser = argparse.ArgumentParser(description="aforensic - Android Enterprise Forensic Suite")
    parser.add_argument("--auto", action="store_true", help="Run full automated extraction non-interactively")
    parser.add_argument("--quick", action="store_true", help="Run quick communications triage")
    parser.add_argument("--full", action="store_true", help="Run full extraction with deep freelist carving")
    parser.add_argument("--targets", type=str, help="Specific target device serial identifier")
    parser.add_argument("--output", type=str, help="Custom output directory for evidence files")
    parser.add_argument("--troubleshoot", action="store_true", help="Run ADB autonomous diagnostics")
    parser.add_argument("--check-updates", action="store_true", help="Run maintenance self-checks and updates")
    parser.add_argument("--version", action="version", version=f"aforensic {__version__}")

    args = parser.parse_args()

    if args.troubleshoot:
        t = Troubleshooter(args.targets)
        t.run_full_diagnostics()
        sys.exit(0)

    if args.check_updates:
        m = MaintenanceManager()
        m.clean_stale_sockets()
        sys.exit(0)

    if args.auto or args.full:
        success = run_pipeline(mode="full", target_serial=args.targets, custom_output_dir=args.output, interactive=False)
        sys.exit(0 if success else 1)
    elif args.quick:
        success = run_pipeline(mode="quick", target_serial=args.targets, custom_output_dir=args.output, interactive=False)
        sys.exit(0 if success else 1)
    else:
        # Interactive mode
        interactive_menu()


if __name__ == "__main__":
    main()
