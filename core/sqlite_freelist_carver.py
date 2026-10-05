"""
Enterprise-grade SQLite Freelist, Write-Ahead Log (WAL), and Unallocated Space Carver for aforensic.
Extracts deleted records, orphaned chat messages, deleted note fragments,
and phone numbers directly from SQLite database pages, WAL buffers, and freelist trunks.
"""

import os
import re
import struct
import string
from typing import List, Dict, Any, Optional


class SQLiteFreelistCarver:
    PHONE_REGEX = re.compile(rb'(\+?[1-9]\d{6,14})')
    EMAIL_REGEX = re.compile(rb'([a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+)')
    URL_REGEX = re.compile(rb'(https?://[a-zA-Z0-9./?=_%&:-]+)')
    PRINTABLE_CHARS = set(bytes(string.printable, 'ascii'))

    def carve_database(self, db_path: str, min_length: int = 4, max_records: int = 250) -> List[Dict[str, Any]]:
        return self.carve_deleted_records(db_path, min_length, max_records)

    @staticmethod
    def carve_deleted_records(db_path: str, min_length: int = 4, max_records: int = 250) -> List[Dict[str, Any]]:
        if not db_path or not os.path.exists(db_path):
            return []

        carved_artifacts = []
        seen_payloads = set()
        db_basename = os.path.basename(db_path)

        try:
            with open(db_path, "rb") as f:
                header = f.read(100)
                if not header.startswith(b"SQLite format 3\x00"):
                    return []

                page_size = struct.unpack(">H", header[16:18])[0]
                if page_size == 1:
                    page_size = 65536
                elif page_size == 0:
                    page_size = 4096

                freelist_trunk = struct.unpack(">I", header[32:36])[0]
                file_size = os.path.getsize(db_path)
                total_pages = max(1, file_size // page_size)

                # 1. Carve Freelist trunk & leaf pages
                current_trunk = freelist_trunk
                visited_trunks = set()
                while current_trunk != 0 and current_trunk not in visited_trunks and current_trunk <= total_pages:
                    visited_trunks.add(current_trunk)
                    offset = (current_trunk - 1) * page_size
                    f.seek(offset)
                    trunk_data = f.read(page_size)
                    if len(trunk_data) < 8:
                        break
                    
                    next_trunk = struct.unpack(">I", trunk_data[0:4])[0]
                    leaf_count = struct.unpack(">I", trunk_data[4:8])[0]

                    for i in range(min(leaf_count, (page_size - 8) // 4)):
                        leaf_page = struct.unpack(">I", trunk_data[8 + (i * 4): 12 + (i * 4)])[0]
                        if 0 < leaf_page <= total_pages:
                            f.seek((leaf_page - 1) * page_size)
                            leaf_data = f.read(page_size)
                            fragments = SQLiteFreelistCarver._extract_strings_from_buffer(leaf_data, min_length)
                            for frag in fragments:
                                if frag not in seen_payloads:
                                    seen_payloads.add(frag)
                                    carved_artifacts.append({
                                        "source_db": db_basename,
                                        "source_type": "Freelist Page",
                                        "page_num": leaf_page,
                                        "page_number": leaf_page,
                                        "offset": (leaf_page - 1) * page_size,
                                        "byte_offset": (leaf_page - 1) * page_size,
                                        "extracted_text": frag,
                                        "carved_text": frag,
                                        "category": SQLiteFreelistCarver._classify_fragment(frag)
                                    })
                                    if len(carved_artifacts) >= max_records:
                                        break
                    current_trunk = next_trunk

                # 2. Carve B-tree leaf pages (Freeblocks, Unallocated gaps, and Deleted cell space)
                for page_idx in range(1, min(total_pages + 1, 500)):
                    offset = (page_idx - 1) * page_size
                    f.seek(offset)
                    page_data = f.read(page_size)
                    if len(page_data) < 8:
                        continue

                    page_header_offset = 100 if page_idx == 1 else 0
                    page_type = page_data[page_header_offset]

                    if page_type in (0x0D, 0x0A):  # Table Leaf or Index Leaf
                        # A. Freeblock chain
                        first_freeblock = struct.unpack(">H", page_data[page_header_offset + 1: page_header_offset + 3])[0]
                        curr_fb = first_freeblock
                        fb_visited = set()
                        while curr_fb != 0 and curr_fb < len(page_data) - 4 and curr_fb not in fb_visited:
                            fb_visited.add(curr_fb)
                            next_fb = struct.unpack(">H", page_data[curr_fb: curr_fb + 2])[0]
                            fb_sz = struct.unpack(">H", page_data[curr_fb + 2: curr_fb + 4])[0]
                            if fb_sz >= 4 and curr_fb + fb_sz <= len(page_data):
                                fb_buf = page_data[curr_fb + 4: curr_fb + fb_sz]
                                for frag in SQLiteFreelistCarver._extract_strings_from_buffer(fb_buf, min_length):
                                    if frag not in seen_payloads:
                                        seen_payloads.add(frag)
                                        carved_artifacts.append({
                                            "source_db": db_basename,
                                            "source_type": "Freeblock Deleted Cell",
                                            "page_num": page_idx,
                                            "page_number": page_idx,
                                            "offset": offset + curr_fb,
                                            "byte_offset": offset + curr_fb,
                                            "extracted_text": frag,
                                            "carved_text": frag,
                                            "category": SQLiteFreelistCarver._classify_fragment(frag)
                                        })
                            curr_fb = next_fb

                        # B. Unallocated space & Full page scan for slack strings
                        cell_count = struct.unpack(">H", page_data[page_header_offset + 3: page_header_offset + 5])[0]
                        cell_content_start = struct.unpack(">H", page_data[page_header_offset + 5: page_header_offset + 7])[0]
                        if cell_content_start == 0:
                            cell_content_start = 65536

                        header_size = 8
                        unallocated_start = page_header_offset + header_size + (cell_count * 2)
                        
                        # Scan all unallocated and cell area data for deleted/orphaned text
                        if unallocated_start < len(page_data):
                            unallocated_buf = page_data[unallocated_start:]
                            fragments = SQLiteFreelistCarver._extract_strings_from_buffer(unallocated_buf, min_length)
                            for frag in fragments:
                                if frag not in seen_payloads and len(frag) >= min_length:
                                    seen_payloads.add(frag)
                                    carved_artifacts.append({
                                        "source_db": db_basename,
                                        "source_type": "Unallocated Cell Slack",
                                        "page_num": page_idx,
                                        "page_number": page_idx,
                                        "offset": offset + unallocated_start,
                                        "byte_offset": offset + unallocated_start,
                                        "extracted_text": frag,
                                        "carved_text": frag,
                                        "category": SQLiteFreelistCarver._classify_fragment(frag)
                                    })
                                    if len(carved_artifacts) >= max_records:
                                        break

            # 3. Carve companion Write-Ahead Log (.wal) if present
            wal_candidates = [f"{db_path}-wal", f"{db_path}.wal", os.path.splitext(db_path)[0] + "-wal"]
            for wal_p in wal_candidates:
                if os.path.exists(wal_p) and os.path.isfile(wal_p):
                    wal_fragments = SQLiteFreelistCarver._carve_wal_file(wal_p, min_length, max_records - len(carved_artifacts))
                    for w_frag in wal_fragments:
                        if w_frag["carved_text"] not in seen_payloads:
                            seen_payloads.add(w_frag["carved_text"])
                            carved_artifacts.append(w_frag)
                    break

        except Exception:
            pass

        return carved_artifacts

    @staticmethod
    def _carve_wal_file(wal_path: str, min_len: int = 4, max_records: int = 50) -> List[Dict[str, Any]]:
        results = []
        try:
            with open(wal_path, "rb") as wf:
                hdr = wf.read(32)
                if len(hdr) < 32:
                    return results
                
                magic = struct.unpack(">I", hdr[:4])[0]
                if magic not in (0x377f0682, 0x377f0683):
                    return results

                page_sz = struct.unpack(">I", hdr[8:12])[0]
                if page_sz < 512 or page_sz > 65536:
                    page_sz = 4096

                frame_idx = 1
                while len(results) < max_records:
                    frame_hdr = wf.read(24)
                    if len(frame_hdr) < 24:
                        break
                    
                    page_num = struct.unpack(">I", frame_hdr[:4])[0]
                    frame_data = wf.read(page_sz)
                    if len(frame_data) < page_sz:
                        break

                    strings = SQLiteFreelistCarver._extract_strings_from_buffer(frame_data, min_len)
                    for s in strings:
                        results.append({
                            "source_db": os.path.basename(wal_path),
                            "source_type": "Write-Ahead Log (WAL) Frame",
                            "page_num": page_num,
                            "page_number": page_num,
                            "offset": 32 + ((frame_idx - 1) * (24 + page_sz)) + 24,
                            "byte_offset": 32 + ((frame_idx - 1) * (24 + page_sz)) + 24,
                            "extracted_text": s,
                            "carved_text": s,
                            "category": SQLiteFreelistCarver._classify_fragment(s)
                        })
                        if len(results) >= max_records:
                            break
                    frame_idx += 1
        except Exception:
            pass
        return results

    @staticmethod
    def _extract_strings_from_buffer(buf: bytes, min_len: int = 4) -> List[str]:
        results = []
        cur_chars = bytearray()

        for b in buf:
            if 32 <= b <= 126 or b in (9, 10, 13):
                cur_chars.append(b)
            else:
                if len(cur_chars) >= min_len:
                    try:
                        decoded = cur_chars.decode('utf-8', errors='ignore').strip()
                        if len(decoded) >= min_len and any(c.isalnum() for c in decoded):
                            results.append(decoded)
                    except Exception:
                        pass
                cur_chars = bytearray()

        if len(cur_chars) >= min_len:
            try:
                decoded = cur_chars.decode('utf-8', errors='ignore').strip()
                if len(decoded) >= min_len and any(c.isalnum() for c in decoded):
                    results.append(decoded)
            except Exception:
                pass

        return results

    @staticmethod
    def _classify_fragment(text: str) -> str:
        t_lower = text.lower()
        if re.search(r'https?://', text):
            return "URL / Link"
        if re.search(r'[a-zA-Z0-9_.+-]+@[a-zA-Z0-9-]+\.[a-zA-Z0-9-.]+', text):
            return "Email Address"
        if re.search(r'(\+?[1-9]\d{7,14})', text) and not any(c.isalpha() for c in text):
            return "Phone Number"
        if any(w in t_lower for w in ["otp", "bank", "card", "usd", "npr", "rs", "inr", "payment", "transferred", "code", "password", "pin"]):
            return "Financial / Credential Fragment"
        return "Deleted Chat / Note Text"
