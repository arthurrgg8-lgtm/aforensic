"""
Bulk Data and Standardized Format Exporter for aforensic.
Generates CSV files for all artifact categories, Master Unified Super-Timeline (CSV/JSONL),
and standard Cyber Analytics / Unified Cyber Ontology (CASE / UCO JSON-LD).
"""

import os
import csv
import json
import uuid
from datetime import datetime, timezone
from typing import List, Dict, Any


class BulkDataExporter:
    def __init__(self, output_dir: str):
        self.output_dir = output_dir
        self.csv_dir = os.path.join(output_dir, "csv_exports")
        os.makedirs(self.csv_dir, exist_ok=True)

    def _write_csv(self, filename: str, rows: List[Dict[str, Any]]):
        """
        Helper to write a list of dictionaries to a CSV file.
        """
        if not rows:
            return
        
        file_path = os.path.join(self.csv_dir, filename)
        # Collect all unique fieldnames
        fieldnames = []
        for r in rows:
            for k in r.keys():
                if k not in fieldnames:
                    fieldnames.append(k)

        with open(file_path, "w", newline="", encoding="utf-8", errors="replace") as f:
            writer = csv.DictWriter(f, fieldnames=fieldnames)
            writer.writeheader()
            for r in rows:
                # Format nested data
                clean_row = {}
                for k, v in r.items():
                    if isinstance(v, (list, dict)):
                        clean_row[k] = json.dumps(v, ensure_ascii=False)
                    else:
                        clean_row[k] = v
                writer.writerow(clean_row)

    def export_all(self, artifacts: Dict[str, Any], timeline_events: List[Dict[str, Any]], device_info: Dict[str, Any]):
        """
        Exports all extracted forensic artifacts into CSV, Timeline, and CASE/UCO JSON-LD formats.
        """
        # 1. Export CSVs
        if "sms" in artifacts:
            self._write_csv("SMS_Messages.csv", artifacts["sms"])
        if "calls" in artifacts:
            self._write_csv("Call_Logs.csv", artifacts["calls"])
        if "contacts" in artifacts:
            self._write_csv("Contacts.csv", artifacts["contacts"])
        if "whatsapp" in artifacts:
            self._write_csv("WhatsApp_Messages.csv", artifacts["whatsapp"])
        if "chrome" in artifacts:
            self._write_csv("Chrome_History.csv", artifacts["chrome"])
        if "notes" in artifacts:
            self._write_csv("Notes_Memos.csv", artifacts["notes"])
        if "photos" in artifacts:
            self._write_csv("Media_Exif_GPS.csv", artifacts["photos"])
        if "recordings" in artifacts:
            self._write_csv("Audio_Recordings.csv", artifacts["recordings"])
        if "enterprise_apps" in artifacts:
            self._write_csv("Enterprise_Apps.csv", artifacts["enterprise_apps"])
        if "wifi" in artifacts:
            self._write_csv("WiFi_Networks.csv", artifacts["wifi"])
        if "bluetooth" in artifacts:
            self._write_csv("Bluetooth_Devices.csv", artifacts["bluetooth"])
        if "notifications" in artifacts:
            self._write_csv("Notification_Cache.csv", artifacts["notifications"])
        if "financial" in artifacts and isinstance(artifacts["financial"], dict):
            self._write_csv("Financial_Ledger.csv", artifacts["financial"].get("ledger", []))
        if "usagestats" in artifacts and isinstance(artifacts["usagestats"], dict):
            self._write_csv("Usage_App_Summary.csv", artifacts["usagestats"].get("apps", []))
            self._write_csv("Usage_Events.csv", artifacts["usagestats"].get("events", []))
        if "carved_records" in artifacts:
            self._write_csv("Carved_Freelist_Records.csv", artifacts["carved_records"])

        # 2. Master Unified Super-Timeline (CSV and JSONL)
        if timeline_events:
            self._write_csv("Master_Super_Timeline.csv", timeline_events)
            jsonl_path = os.path.join(self.output_dir, "Master_Super_Timeline.jsonl")
            with open(jsonl_path, "w", encoding="utf-8") as f:
                for ev in timeline_events:
                    f.write(json.dumps(ev, ensure_ascii=False) + "\n")

        # 3. Standard CASE / UCO (Unified Cyber Ontology) JSON-LD export
        self.export_case_uco(artifacts, timeline_events, device_info)

    def export_case_uco(self, artifacts: Dict[str, Any], timeline_events: List[Dict[str, Any]], device_info: Dict[str, Any]):
        """
        Generates standard CASE/UCO 1.3.0 compliant JSON-LD document for interoperability
        with law enforcement and DFIR enterprise toolsets (Autopsy, EnCase, X-Ways).
        """
        case_id = f"case-android-{uuid.uuid4()}"
        device_id = f"device-{device_info.get('serial', 'unknown')}"
        investigation_id = f"investigation-{uuid.uuid4()}"

        uco_objects = [
            {
                "@id": f"kb:{investigation_id}",
                "@type": "uco-investigation:Investigation",
                "uco-core:name": "Android Digital Forensic Extraction",
                "uco-core:description": f"Automated forensic extraction of {device_info.get('manufacturer', '')} {device_info.get('model', '')}",
                "uco-investigation:investigationStatus": "Completed",
                "uco-investigation:focus": "Mobile Device Forensic Bitstream and Logical Evidence Acquisition"
            },
            {
                "@id": f"kb:{device_id}",
                "@type": "uco-identity:Device",
                "uco-core:name": f"{device_info.get('manufacturer', 'Android')} {device_info.get('model', 'Device')}",
                "uco-observable:serialNumber": device_info.get("serial", "N/A"),
                "uco-observable:model": device_info.get("model", "N/A"),
                "uco-observable:manufacturer": device_info.get("manufacturer", "N/A"),
                "uco-observable:osVersion": f"Android {device_info.get('android_version', 'N/A')} (SDK {device_info.get('sdk_version', 'N/A')})"
            }
        ]

        # Add sample of timeline events as observable actions/messages
        for ev in timeline_events[:500]:  # Represent initial 500 events in graph
            ev_id = f"action-{uuid.uuid4()}"
            uco_objects.append({
                "@id": f"kb:{ev_id}",
                "@type": "uco-observable:ObservableAction",
                "uco-core:name": ev.get("source", "Forensic Event"),
                "uco-observable:startTime": ev.get("timestamp_utc", ""),
                "uco-core:description": ev.get("summary", ""),
                "uco-observable:actionStatus": "Success",
                "uco-observable:object": f"kb:{device_id}"
            })

        uco_doc = {
            "@context": {
                "kb": "http://example.org/kb/",
                "uco-core": "https://ontology.unifiedcyberontology.org/uco/core/",
                "uco-investigation": "https://ontology.unifiedcyberontology.org/uco/investigation/",
                "uco-observable": "https://ontology.unifiedcyberontology.org/uco/observable/",
                "uco-identity": "https://ontology.unifiedcyberontology.org/uco/identity/",
                "case-investigation": "https://ontology.caseontology.org/case/investigation/"
            },
            "@graph": uco_objects,
            "generated_at": datetime.now(timezone.utc).isoformat(),
            "standard_version": "CASE/UCO v1.3.0"
        }

        jsonld_path = os.path.join(self.output_dir, "CASE_UCO_Forensic_Ontology.jsonld")
        with open(jsonld_path, "w", encoding="utf-8") as f:
            json.dump(uco_doc, f, indent=2, ensure_ascii=False)
