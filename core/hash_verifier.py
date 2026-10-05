"""
NIST CFTT & ISO/IEC 27037 Compliant Cryptographic Evidence Verification Engine for aforensic.
Computes streaming SHA-256 and MD5 hashes across evidence files.
"""

import os
import hashlib
import json
import datetime
from typing import Dict, Any, Optional


class HashVerifier:
    def __init__(self, evidence_dir: Optional[str] = None):
        self.evidence_dir = evidence_dir
        self.last_manifest: Optional[Dict[str, Any]] = None

    @staticmethod
    def calculate_file_hashes(file_path: str, block_size: int = 65536) -> Dict[str, Any]:
        sha256 = hashlib.sha256()
        md5 = hashlib.md5()
        if not os.path.exists(file_path) or not os.path.isfile(file_path):
            return {"sha256": "0" * 64, "md5": "0" * 32, "file_size": 0}

        with open(file_path, "rb") as f:
            for block in iter(lambda: f.read(block_size), b""):
                sha256.update(block)
                md5.update(block)
        return {
            "sha256": sha256.hexdigest(),
            "md5": md5.hexdigest(),
            "file_size": os.path.getsize(file_path)
        }

    def verify_directory(self, target_dir: Optional[str] = None) -> Dict[str, Any]:
        """
        Computes dual SHA-256 / MD5 hashes for all files within target directory.
        """
        dir_to_scan = target_dir or self.evidence_dir or "."
        manifest = {
            "verification_time_utc": datetime.datetime.now(datetime.timezone.utc).isoformat(),
            "standard": "NIST CFTT / ISO/IEC 27037:2012",
            "hashes": {},
            "total_files_hashed": 0,
            "total_size_bytes": 0
        }

        master_hasher = hashlib.sha256()

        for root, _, files in os.walk(dir_to_scan):
            for f in sorted(files):
                full_p = os.path.join(root, f)
                rel_p = os.path.relpath(full_p, dir_to_scan)
                try:
                    h = self.calculate_file_hashes(full_p)
                    manifest["hashes"][rel_p] = h
                    manifest["total_files_hashed"] += 1
                    manifest["total_size_bytes"] += h["file_size"]
                    master_hasher.update(f"{rel_p}:{h['sha256']}".encode("utf-8"))
                except Exception:
                    pass

        manifest["master_hash"] = master_hasher.hexdigest()
        self.last_manifest = manifest
        return manifest

    def save_hash_manifest(self, output_dir: Optional[str] = None) -> Optional[str]:
        """
        Saves the hash verification manifest to JSON and text formats.
        """
        target = output_dir or self.evidence_dir
        if not target:
            return None
        os.makedirs(target, exist_ok=True)

        if not self.last_manifest:
            self.verify_directory(target)

        manifest = self.last_manifest
        json_path = os.path.join(target, "Chain_of_Custody_Verification.json")
        with open(json_path, "w", encoding="utf-8") as jf:
            json.dump(manifest, jf, indent=2)

        txt_path = os.path.join(target, "Chain_of_Custody_Manifest.txt")
        with open(txt_path, "w", encoding="utf-8") as tf:
            tf.write("=" * 80 + "\n")
            tf.write("      aFORENSIC ANDROID EVIDENCE CHAIN OF CUSTODY & INTEGRITY MANIFEST\n")
            tf.write("      Standard: NIST CFTT & ISO/IEC 27037:2012 Digital Evidence Preservation\n")
            tf.write("=" * 80 + "\n")
            tf.write(f"Verification Timestamp : {manifest.get('verification_time_utc')}\n")
            tf.write(f"Master Evidence SHA-256: {manifest.get('master_hash')}\n")
            tf.write(f"Total Evidence Files   : {manifest.get('total_files_hashed')}\n")
            tf.write(f"Total Ingested Data    : {manifest.get('total_size_bytes', 0) / (1024*1024):.2f} MB\n")
            tf.write("-" * 80 + "\n\n")
            tf.write(f"{'Relative File Path':<50} {'SHA-256 Digest':<64}\n")
            tf.write("-" * 115 + "\n")
            for r_path, data in manifest.get("hashes", {}).items():
                tf.write(f"{r_path[:48]:<50} {data['sha256']}\n")

        return json_path

    @staticmethod
    def generate_chain_of_custody(evidence_dir: str, output_dir: str, case_id: str = "CASE_ANDROID"):
        verifier = HashVerifier(evidence_dir)
        verifier.verify_directory()
        verifier.save_hash_manifest(output_dir)
        return verifier.last_manifest
