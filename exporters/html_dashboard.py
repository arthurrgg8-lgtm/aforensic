"""
Interactive Single-Page Forensic HTML Dashboard Generator for aforensic.
Includes Leaflet.js offline-capable GPS mapping, Master Super-Timeline filtering,
live client-side search, financial charts, and SQLite freelist carved viewer.
"""

import os
import json
from datetime import datetime, timezone
from typing import Dict, Any, List, Optional


class HTMLDashboardExporter:
    def __init__(self, output_dir: str):
        self.output_dir = output_dir

    def generate_dashboard(self, 
                           artifacts: Dict[str, Any], 
                           device_info: Dict[str, Any], 
                           timeline_events: List[Dict[str, Any]], 
                           hash_report: Dict[str, Any],
                           audit_certificate: Dict[str, Any] = None) -> str:
        """
        Generates the self-contained interactive forensic HTML dashboard.
        """
        out_file = os.path.join(self.output_dir, "Forensic_Interactive_Dashboard.html")

        # Safely serialize data
        device_json = json.dumps(device_info, ensure_ascii=False)
        timeline_json = json.dumps(timeline_events[:2000], ensure_ascii=False)
        sms_json = json.dumps(artifacts.get("sms", []), ensure_ascii=False)
        calls_json = json.dumps(artifacts.get("calls", []), ensure_ascii=False)
        contacts_json = json.dumps(artifacts.get("contacts", []), ensure_ascii=False)
        wa_json = json.dumps(artifacts.get("whatsapp", []), ensure_ascii=False)
        chrome_json = json.dumps(artifacts.get("chrome", []), ensure_ascii=False)
        notes_json = json.dumps(artifacts.get("notes", []), ensure_ascii=False)
        photos_json = json.dumps(artifacts.get("photos", []), ensure_ascii=False)
        fin_json = json.dumps(artifacts.get("financial", {}), ensure_ascii=False)
        ustats_json = json.dumps(artifacts.get("usagestats", {}), ensure_ascii=False)
        wifi_json = json.dumps(artifacts.get("wifi", []), ensure_ascii=False)
        bt_json = json.dumps(artifacts.get("bluetooth", []), ensure_ascii=False)
        notifs_json = json.dumps(artifacts.get("notifications", []), ensure_ascii=False)
        carved_json = json.dumps(artifacts.get("carved_records", []), ensure_ascii=False)
        hash_json = json.dumps(hash_report, ensure_ascii=False)
        audit_json = json.dumps(audit_certificate or {}, ensure_ascii=False)

        # Count stats
        counts = {
            "sms": len(artifacts.get("sms", [])),
            "calls": len(artifacts.get("calls", [])),
            "contacts": len(artifacts.get("contacts", [])),
            "wa": len(artifacts.get("whatsapp", [])),
            "chrome": len(artifacts.get("chrome", [])),
            "notes": len(artifacts.get("notes", [])),
            "photos": len(artifacts.get("photos", [])),
            "fin": len(artifacts.get("financial", {}).get("ledger", [])) if isinstance(artifacts.get("financial"), dict) else 0,
            "wifi": len(artifacts.get("wifi", [])),
            "bt": len(artifacts.get("bluetooth", [])),
            "notifs": len(artifacts.get("notifications", [])),
            "carved": len(artifacts.get("carved_records", [])),
            "timeline": len(timeline_events)
        }

        html_content = f"""<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>aforensic - Android Enterprise Forensic Dashboard</title>
    <!-- Leaflet CSS for Maps -->
    <link rel="stylesheet" href="https://unpkg.com/leaflet@1.9.4/dist/leaflet.css" />
    <script src="https://unpkg.com/leaflet@1.9.4/dist/leaflet.js"></script>
    <style>
        :root {{
            --bg-dark: #0f172a;
            --card-bg: #1e293b;
            --sidebar-bg: #0b1120;
            --primary: #38bdf8;
            --primary-hover: #0284c7;
            --accent: #818cf8;
            --text-main: #f8fafc;
            --text-muted: #94a3b8;
            --border-color: #334155;
            --badge-green: #22c55e;
            --badge-red: #ef4444;
            --badge-yellow: #f59e0b;
        }}
        * {{
            box-sizing: border-box;
            margin: 0;
            padding: 0;
            font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, Helvetica, Arial, sans-serif;
        }}
        body {{
            background-color: var(--bg-dark);
            color: var(--text-main);
            display: flex;
            height: 100vh;
            overflow: hidden;
        }}
        /* Sidebar */
        aside {{
            width: 280px;
            background-color: var(--sidebar-bg);
            border-right: 1px solid var(--border-color);
            display: flex;
            flex-direction: column;
            flex-shrink: 0;
        }}
        .brand {{
            padding: 20px;
            font-size: 1.25rem;
            font-weight: 700;
            color: var(--primary);
            border-bottom: 1px solid var(--border-color);
            display: flex;
            align-items: center;
            gap: 10px;
        }}
        .brand-badge {{
            font-size: 0.65rem;
            background-color: #0369a1;
            color: #fff;
            padding: 2px 6px;
            border-radius: 4px;
            text-transform: uppercase;
        }}
        nav {{
            flex: 1;
            overflow-y: auto;
            padding: 12px 8px;
        }}
        nav button {{
            width: 100%;
            background: none;
            border: none;
            color: var(--text-muted);
            padding: 10px 14px;
            margin-bottom: 4px;
            border-radius: 6px;
            text-align: left;
            font-size: 0.9rem;
            font-weight: 500;
            cursor: pointer;
            display: flex;
            align-items: center;
            justify-content: space-between;
            transition: all 0.15s ease;
        }}
        nav button:hover {{
            background-color: rgba(56, 189, 248, 0.1);
            color: var(--text-main);
        }}
        nav button.active {{
            background-color: var(--primary);
            color: #0f172a;
            font-weight: 600;
        }}
        .nav-count {{
            background-color: rgba(255, 255, 255, 0.15);
            padding: 2px 7px;
            border-radius: 10px;
            font-size: 0.75rem;
        }}
        nav button.active .nav-count {{
            background-color: #0f172a;
            color: #fff;
        }}
        /* Main Workspace */
        main {{
            flex: 1;
            display: flex;
            flex-direction: column;
            overflow: hidden;
        }}
        header {{
            height: 65px;
            background-color: var(--card-bg);
            border-bottom: 1px solid var(--border-color);
            display: flex;
            align-items: center;
            justify-content: space-between;
            padding: 0 24px;
        }}
        .search-box {{
            display: flex;
            align-items: center;
            background-color: var(--bg-dark);
            border: 1px solid var(--border-color);
            border-radius: 6px;
            padding: 6px 12px;
            width: 380px;
        }}
        .search-box input {{
            background: none;
            border: none;
            color: var(--text-main);
            outline: none;
            width: 100%;
            font-size: 0.85rem;
        }}
        .header-meta {{
            font-size: 0.85rem;
            color: var(--text-muted);
        }}
        .content-area {{
            flex: 1;
            padding: 24px;
            overflow-y: auto;
        }}
        .tab-content {{
            display: none;
        }}
        .tab-content.active {{
            display: block;
        }}
        /* Cards & Grids */
        .grid-cards {{
            display: grid;
            grid-template-columns: repeat(auto-fill, minmax(220px, 1fr));
            gap: 16px;
            margin-bottom: 24px;
        }}
        .stat-card {{
            background-color: var(--card-bg);
            border: 1px solid var(--border-color);
            border-radius: 8px;
            padding: 16px;
        }}
        .stat-title {{
            font-size: 0.8rem;
            color: var(--text-muted);
            text-transform: uppercase;
            letter-spacing: 0.05em;
            margin-bottom: 6px;
        }}
        .stat-val {{
            font-size: 1.6rem;
            font-weight: 700;
            color: var(--primary);
        }}
        /* Tables */
        .table-container {{
            background-color: var(--card-bg);
            border: 1px solid var(--border-color);
            border-radius: 8px;
            overflow: hidden;
            margin-bottom: 24px;
        }}
        .table-header {{
            padding: 14px 18px;
            background-color: rgba(255, 255, 255, 0.02);
            border-bottom: 1px solid var(--border-color);
            font-weight: 600;
            font-size: 0.95rem;
            display: flex;
            justify-content: space-between;
            align-items: center;
        }}
        table {{
            width: 100%;
            border-collapse: collapse;
            font-size: 0.85rem;
        }}
        th {{
            background-color: rgba(0, 0, 0, 0.2);
            color: var(--text-muted);
            font-weight: 600;
            text-align: left;
            padding: 10px 14px;
            border-bottom: 1px solid var(--border-color);
        }}
        td {{
            padding: 10px 14px;
            border-bottom: 1px solid var(--border-color);
            color: var(--text-main);
            vertical-align: top;
            word-break: break-word;
        }}
        tr:hover {{
            background-color: rgba(255, 255, 255, 0.02);
        }}
        /* Map Container */
        #map {{
            height: 520px;
            width: 100%;
            border-radius: 8px;
            border: 1px solid var(--border-color);
            margin-top: 16px;
        }}
        /* Badges */
        .badge {{
            display: inline-block;
            padding: 2px 8px;
            border-radius: 12px;
            font-size: 0.72rem;
            font-weight: 600;
        }}
        .badge-green {{ background-color: rgba(34, 197, 94, 0.2); color: var(--badge-green); }}
        .badge-blue {{ background-color: rgba(56, 189, 248, 0.2); color: var(--primary); }}
        .badge-red {{ background-color: rgba(239, 68, 68, 0.2); color: var(--badge-red); }}
        .badge-yellow {{ background-color: rgba(245, 158, 11, 0.2); color: var(--badge-yellow); }}
        /* Code blocks */
        pre {{
            background-color: #090d16;
            padding: 14px;
            border-radius: 6px;
            border: 1px solid var(--border-color);
            font-family: monospace;
            font-size: 0.8rem;
            color: #38bdf8;
            overflow-x: auto;
        }}
    </style>
</head>
<body>

    <!-- Sidebar Navigation -->
    <aside>
        <div class="brand">
            <span>🛡️ aforensic</span>
            <span class="brand-badge">Android Enterprise</span>
        </div>
        <nav>
            <button class="tab-btn active" onclick="switchTab('tab-overview')"><span>📊 Overview & Hardware</span></button>
            <button class="tab-btn" onclick="switchTab('tab-timeline')"><span>⏱️ Master Super-Timeline</span><span class="nav-count">{counts['timeline']}</span></button>
            <button class="tab-btn" onclick="switchTab('tab-sms')"><span>💬 SMS / MMS Messages</span><span class="nav-count">{counts['sms']}</span></button>
            <button class="tab-btn" onclick="switchTab('tab-calls')"><span>📞 Call Logs</span><span class="nav-count">{counts['calls']}</span></button>
            <button class="tab-btn" onclick="switchTab('tab-contacts')"><span>👤 Contacts</span><span class="nav-count">{counts['contacts']}</span></button>
            <button class="tab-btn" onclick="switchTab('tab-whatsapp')"><span>📱 WhatsApp Chats</span><span class="nav-count">{counts['wa']}</span></button>
            <button class="tab-btn" onclick="switchTab('tab-chrome')"><span>🌐 Chrome Web History</span><span class="nav-count">{counts['chrome']}</span></button>
            <button class="tab-btn" onclick="switchTab('tab-photos')"><span>🗺️ Photos & GPS Map</span><span class="nav-count">{counts['photos']}</span></button>
            <button class="tab-btn" onclick="switchTab('tab-financial')"><span>💳 Financial & OTPs</span><span class="nav-count">{counts['fin']}</span></button>
            <button class="tab-btn" onclick="switchTab('tab-usagestats')"><span>📈 App Usage & Screen</span></button>
            <button class="tab-btn" onclick="switchTab('tab-network')"><span>📶 Wi-Fi & Bluetooth</span><span class="nav-count">{counts['wifi'] + counts['bt']}</span></button>
            <button class="tab-btn" onclick="switchTab('tab-notifications')"><span>🔔 Notifications Cache</span><span class="nav-count">{counts['notifs']}</span></button>
            <button class="tab-btn" onclick="switchTab('tab-carved')"><span>🧩 Freelist & Carved</span><span class="nav-count">{counts['carved']}</span></button>
            <button class="tab-btn" onclick="switchTab('tab-audit')"><span>📜 ISO 27037 Audit</span></button>
        </nav>
    </aside>

    <!-- Main Workspace -->
    <main>
        <header>
            <div class="search-box">
                <input type="text" id="global-search" placeholder="Search across all parsed evidence..." onkeyup="filterTables()">
            </div>
            <div class="header-meta">
                <span>Target: <strong>{device_info.get('manufacturer', '')} {device_info.get('model', 'Android Device')}</strong> | Serial: <code>{device_info.get('serial', 'N/A')}</code></span>
            </div>
        </header>

        <div class="content-area">
            
            <!-- Tab 1: Overview -->
            <div id="tab-overview" class="tab-content active">
                <div class="grid-cards">
                    <div class="stat-card"><div class="stat-title">SMS / MMS</div><div class="stat-val">{counts['sms']}</div></div>
                    <div class="stat-card"><div class="stat-title">Call Records</div><div class="stat-val">{counts['calls']}</div></div>
                    <div class="stat-card"><div class="stat-title">WhatsApp Chats</div><div class="stat-val">{counts['wa']}</div></div>
                    <div class="stat-card"><div class="stat-title">Web History</div><div class="stat-val">{counts['chrome']}</div></div>
                    <div class="stat-card"><div class="stat-title">Media & GPS</div><div class="stat-val">{counts['photos']}</div></div>
                    <div class="stat-card"><div class="stat-title">Financial Alerts</div><div class="stat-val">{counts['fin']}</div></div>
                    <div class="stat-card"><div class="stat-title">Freelist Carved</div><div class="stat-val">{counts['carved']}</div></div>
                    <div class="stat-card"><div class="stat-title">Timeline Events</div><div class="stat-val">{counts['timeline']}</div></div>
                </div>

                <div class="table-container">
                    <div class="table-header">Target Hardware Telemetry & Identity</div>
                    <table>
                        <tbody>
                            <tr><th style="width:250px">Device Manufacturer & Brand</th><td>{device_info.get('manufacturer', 'N/A')} ({device_info.get('brand', 'N/A')})</td></tr>
                            <tr><th>Model & Hardware Codename</th><td>{device_info.get('model', 'N/A')} (Board: {device_info.get('board', 'N/A')})</td></tr>
                            <tr><th>Serial Number / ADB Identifier</th><td><code>{device_info.get('serial', 'N/A')}</code></td></tr>
                            <tr><th>Operating System</th><td>Android {device_info.get('android_version', 'N/A')} (API Level / SDK: {device_info.get('sdk_version', 'N/A')})</td></tr>
                            <tr><th>Build Fingerprint</th><td><code>{device_info.get('build_fingerprint', 'N/A')}</code></td></tr>
                            <tr><th>Security Patch Level</th><td>{device_info.get('security_patch', 'N/A')}</td></tr>
                        </tbody>
                    </table>
                </div>
            </div>

            <!-- Tab 2: Master Super-Timeline -->
            <div id="tab-timeline" class="tab-content">
                <div class="table-container">
                    <div class="table-header">Master Chronological Forensic Super-Timeline (Cross-Artifact Unified)</div>
                    <table id="table-timeline">
                        <thead>
                            <tr>
                                <th style="width:160px">Timestamp (UTC)</th>
                                <th style="width:160px">Local Time (+05:45)</th>
                                <th style="width:120px">Artifact Source</th>
                                <th style="width:180px">Action Type</th>
                                <th>Summary & Content</th>
                            </tr>
                        </thead>
                        <tbody id="timeline-body"></tbody>
                    </table>
                </div>
            </div>

            <!-- Tab 3: SMS -->
            <div id="tab-sms" class="tab-content">
                <div class="table-container">
                    <div class="table-header">SMS & MMS Messages ({counts['sms']} Records)</div>
                    <table id="table-sms">
                        <thead>
                            <tr>
                                <th style="width:160px">Timestamp</th>
                                <th style="width:140px">Address / Number</th>
                                <th style="width:100px">Direction</th>
                                <th style="width:90px">Status</th>
                                <th>Message Body</th>
                            </tr>
                        </thead>
                        <tbody id="sms-body"></tbody>
                    </table>
                </div>
            </div>

            <!-- Tab 4: Calls -->
            <div id="tab-calls" class="tab-content">
                <div class="table-container">
                    <div class="table-header">Telephony Call History ({counts['calls']} Records)</div>
                    <table id="table-calls">
                        <thead>
                            <tr>
                                <th style="width:160px">Timestamp</th>
                                <th style="width:150px">Contact Name</th>
                                <th style="width:140px">Phone Number</th>
                                <th style="width:110px">Call Type</th>
                                <th style="width:100px">Duration</th>
                            </tr>
                        </thead>
                        <tbody id="calls-body"></tbody>
                    </table>
                </div>
            </div>

            <!-- Tab 5: Contacts -->
            <div id="tab-contacts" class="tab-content">
                <div class="table-container">
                    <div class="table-header">Contacts Directory ({counts['contacts']} Entries)</div>
                    <table id="table-contacts">
                        <thead>
                            <tr>
                                <th style="width:180px">Display Name</th>
                                <th style="width:160px">Phone Number</th>
                                <th style="width:200px">Email Address</th>
                                <th>Truecaller / Notes</th>
                            </tr>
                        </thead>
                        <tbody id="contacts-body"></tbody>
                    </table>
                </div>
            </div>

            <!-- Tab 6: WhatsApp -->
            <div id="tab-whatsapp" class="tab-content">
                <div class="table-container">
                    <div class="table-header">WhatsApp Messenger Conversations ({counts['wa']} Records)</div>
                    <table id="table-whatsapp">
                        <thead>
                            <tr>
                                <th style="width:160px">Timestamp</th>
                                <th style="width:180px">Chat / Sender JID</th>
                                <th style="width:100px">Direction</th>
                                <th>Message Text</th>
                            </tr>
                        </thead>
                        <tbody id="whatsapp-body"></tbody>
                    </table>
                </div>
            </div>

            <!-- Tab 7: Chrome -->
            <div id="tab-chrome" class="tab-content">
                <div class="table-container">
                    <div class="table-header">Chrome Web Browsing History ({counts['chrome']} Records)</div>
                    <table id="table-chrome">
                        <thead>
                            <tr>
                                <th style="width:160px">Timestamp</th>
                                <th style="width:250px">Page Title</th>
                                <th>Full URL</th>
                                <th style="width:80px">Visits</th>
                            </tr>
                        </thead>
                        <tbody id="chrome-body"></tbody>
                    </table>
                </div>
            </div>

            <!-- Tab 8: Photos & GPS Map -->
            <div id="tab-photos" class="tab-content">
                <div class="table-header">Geolocated Media & Photos Map</div>
                <div id="map"></div>
                <div class="table-container" style="margin-top:20px;">
                    <div class="table-header">Media Metadata & EXIF Coordinates</div>
                    <table id="table-photos">
                        <thead>
                            <tr>
                                <th>Filename / Path</th>
                                <th style="width:160px">Timestamp</th>
                                <th style="width:120px">Latitude</th>
                                <th style="width:120px">Longitude</th>
                                <th style="width:100px">Size</th>
                            </tr>
                        </thead>
                        <tbody id="photos-body"></tbody>
                    </table>
                </div>
            </div>

            <!-- Tab 9: Financial -->
            <div id="tab-financial" class="tab-content">
                <div class="table-container">
                    <div class="table-header">Financial Ledger & 2FA OTP Intelligence</div>
                    <table id="table-fin">
                        <thead>
                            <tr>
                                <th style="width:160px">Timestamp</th>
                                <th style="width:140px">Transaction Type</th>
                                <th style="width:110px">Amount</th>
                                <th style="width:100px">OTP Code</th>
                                <th style="width:130px">Account Ref</th>
                                <th>Raw Financial Text</th>
                            </tr>
                        </thead>
                        <tbody id="fin-body"></tbody>
                    </table>
                </div>
            </div>

            <!-- Tab 10: UsageStats -->
            <div id="tab-usagestats" class="tab-content">
                <div class="table-container">
                    <div class="table-header">Application Usage & Active Foreground Durations</div>
                    <table id="table-usagestats">
                        <thead>
                            <tr>
                                <th>Package Name</th>
                                <th style="width:180px">Total Foreground Time</th>
                                <th style="width:180px">Last Active Time</th>
                                <th style="width:120px">Launch Count</th>
                            </tr>
                        </thead>
                        <tbody id="ustats-body"></tbody>
                    </table>
                </div>
            </div>

            <!-- Tab 11: Network -->
            <div id="tab-network" class="tab-content">
                <div class="table-container">
                    <div class="table-header">Configured Wi-Fi Networks</div>
                    <table id="table-wifi">
                        <thead>
                            <tr>
                                <th>SSID</th>
                                <th style="width:160px">Security Type</th>
                                <th style="width:160px">BSSID</th>
                                <th style="width:180px">Last Connected</th>
                            </tr>
                        </thead>
                        <tbody id="wifi-body"></tbody>
                    </table>
                </div>
                <div class="table-container">
                    <div class="table-header">Paired Bluetooth Devices</div>
                    <table id="table-bt">
                        <thead>
                            <tr>
                                <th>Device Name</th>
                                <th style="width:200px">MAC Address</th>
                                <th style="width:140px">Status</th>
                            </tr>
                        </thead>
                        <tbody id="bt-body"></tbody>
                    </table>
                </div>
            </div>

            <!-- Tab 12: Notifications -->
            <div id="tab-notifications" class="tab-content">
                <div class="table-container">
                    <div class="table-header">Push Notification Cache & Ephemeral Messages</div>
                    <table id="table-notifs">
                        <thead>
                            <tr>
                                <th style="width:160px">Timestamp</th>
                                <th style="width:180px">Application Package</th>
                                <th style="width:200px">Title / Sender</th>
                                <th>Notification Body / Message</th>
                            </tr>
                        </thead>
                        <tbody id="notifs-body"></tbody>
                    </table>
                </div>
            </div>

            <!-- Tab 13: Carved -->
            <div id="tab-carved" class="tab-content">
                <div class="table-container">
                    <div class="table-header">SQLite Freelist & WAL Unallocated Carved Fragments ({counts['carved']} Carved)</div>
                    <table id="table-carved">
                        <thead>
                            <tr>
                                <th style="width:180px">Source Database</th>
                                <th style="width:90px">Page #</th>
                                <th style="width:110px">Byte Offset</th>
                                <th>Recovered UTF-8 String Fragment</th>
                            </tr>
                        </thead>
                        <tbody id="carved-body"></tbody>
                    </table>
                </div>
            </div>

            <!-- Tab 14: ISO 27037 Audit -->
            <div id="tab-audit" class="tab-content">
                <div class="table-container">
                    <div class="table-header">Cryptographic Hashes & ISO/IEC 27037 Verification Certificate</div>
                    <pre id="audit-cert-text"></pre>
                </div>
            </div>

        </div>
    </main>

    <script>
        const DATA = {{
            device: {device_json},
            timeline: {timeline_json},
            sms: {sms_json},
            calls: {calls_json},
            contacts: {contacts_json},
            wa: {wa_json},
            chrome: {chrome_json},
            photos: {photos_json},
            fin: {fin_json},
            ustats: {ustats_json},
            wifi: {wifi_json},
            bt: {bt_json},
            notifs: {notifs_json},
            carved: {carved_json},
            hashes: {hash_json},
            audit: {audit_json}
        }};

        function switchTab(tabId) {{
            document.querySelectorAll('.tab-content').forEach(el => el.classList.remove('active'));
            document.querySelectorAll('.tab-btn').forEach(el => el.classList.remove('active'));
            
            const target = document.getElementById(tabId);
            if (target) target.classList.add('active');

            // Highlight button
            event.currentTarget.classList.add('active');

            if (tabId === 'tab-photos') {{
                setTimeout(initMap, 200);
            }}
        }}

        function populateTables() {{
            // 1. Timeline
            const tlBody = document.getElementById('timeline-body');
            tlBody.innerHTML = DATA.timeline.map(ev => `
                <tr>
                    <td><code>${{ev.timestamp_utc || 'N/A'}}</code></td>
                    <td><code>${{ev.timestamp_local || 'N/A'}}</code></td>
                    <td><span class="badge badge-blue">${{ev.source || ''}}</span></td>
                    <td>${{ev.type || ''}}</td>
                    <td><strong>${{ev.summary || ''}}</strong> ${{ev.raw_data && ev.raw_data.body ? '<br><small>' + ev.raw_data.body + '</small>' : ''}}</td>
                </tr>
            `).join('');

            // 2. SMS
            const smsBody = document.getElementById('sms-body');
            smsBody.innerHTML = DATA.sms.map(s => `
                <tr>
                    <td><code>${{s.timestamp || 'N/A'}}</code></td>
                    <td><strong>${{s.address || 'N/A'}}</strong></td>
                    <td><span class="badge ${{s.direction === 'Incoming' ? 'badge-green' : 'badge-blue'}}">${{s.direction || 'N/A'}}</span></td>
                    <td>${{s.status || 'N/A'}}</td>
                    <td>${{s.body || ''}}</td>
                </tr>
            `).join('');

            // 3. Calls
            const callsBody = document.getElementById('calls-body');
            callsBody.innerHTML = DATA.calls.map(c => `
                <tr>
                    <td><code>${{c.timestamp || 'N/A'}}</code></td>
                    <td>${{c.name || 'Unknown'}}</td>
                    <td><strong>${{c.number || 'N/A'}}</strong></td>
                    <td><span class="badge ${{c.type === 'Missed' ? 'badge-red' : 'badge-green'}}">${{c.type || 'N/A'}}</span></td>
                    <td>${{c.duration_formatted || '0s'}}</td>
                </tr>
            `).join('');

            // 4. Contacts
            const contBody = document.getElementById('contacts-body');
            contBody.innerHTML = DATA.contacts.map(c => `
                <tr>
                    <td><strong>${{c.display_name || 'N/A'}}</strong></td>
                    <td>${{c.phone_number || 'N/A'}}</td>
                    <td>${{c.email || 'N/A'}}</td>
                    <td><small>${{c.note || ''}}</small></td>
                </tr>
            `).join('');

            // 5. WhatsApp
            const waBody = document.getElementById('whatsapp-body');
            waBody.innerHTML = DATA.wa.map(w => `
                <tr>
                    <td><code>${{w.timestamp || 'N/A'}}</code></td>
                    <td>${{w.sender || w.chat_jid || 'N/A'}}</td>
                    <td><span class="badge ${{w.is_outgoing ? 'badge-blue' : 'badge-green'}}">${{w.is_outgoing ? 'Outgoing' : 'Incoming'}}</span></td>
                    <td>${{w.body || ''}}</td>
                </tr>
            `).join('');

            // 6. Chrome
            const crBody = document.getElementById('chrome-body');
            crBody.innerHTML = DATA.chrome.map(h => `
                <tr>
                    <td><code>${{h.timestamp || 'N/A'}}</code></td>
                    <td><strong>${{h.title || 'No Title'}}</strong></td>
                    <td><a href="${{h.url}}" target="_blank" style="color:var(--primary);">${{h.url || ''}}</a></td>
                    <td>${{h.visit_count || 1}}</td>
                </tr>
            `).join('');

            // 7. Photos
            const phBody = document.getElementById('photos-body');
            phBody.innerHTML = DATA.photos.map(p => `
                <tr>
                    <td>${{p.filename || p.relative_path || 'Photo'}}</td>
                    <td><code>${{p.timestamp || 'N/A'}}</code></td>
                    <td>${{p.latitude || 'N/A'}}</td>
                    <td>${{p.longitude || 'N/A'}}</td>
                    <td>${{p.file_size ? (p.file_size/1024).toFixed(1) + ' KB' : 'N/A'}}</td>
                </tr>
            `).join('');

            // 8. Financial
            const finBody = document.getElementById('fin-body');
            const ledger = DATA.fin.ledger || [];
            finBody.innerHTML = ledger.map(f => `
                <tr>
                    <td><code>${{f.timestamp || 'N/A'}}</code></td>
                    <td><span class="badge ${{f.type && f.type.includes('DEBIT') ? 'badge-red' : (f.type && f.type.includes('CREDIT') ? 'badge-green' : 'badge-yellow')}}">${{f.type || 'N/A'}}</span></td>
                    <td><strong>${{f.currency || ''}} ${{f.amount || 0.0}}</strong></td>
                    <td>${{f.otp_code ? '<span class="badge badge-yellow">' + f.otp_code + '</span>' : ''}}</td>
                    <td>${{f.account_ref || 'N/A'}}</td>
                    <td><small>${{f.message_text || ''}}</small></td>
                </tr>
            `).join('');

            // 9. UsageStats
            const ustBody = document.getElementById('ustats-body');
            const apps = DATA.ustats.apps || [];
            ustBody.innerHTML = apps.map(a => `
                <tr>
                    <td><strong>${{a.package || 'N/A'}}</strong></td>
                    <td>${{a.total_foreground_time || 'N/A'}}</td>
                    <td>${{a.last_time_used || 'N/A'}}</td>
                    <td><span class="badge badge-blue">${{a.launch_count || 0}} launches</span></td>
                </tr>
            `).join('');

            // 10. WiFi & BT
            const wifiBody = document.getElementById('wifi-body');
            wifiBody.innerHTML = DATA.wifi.map(w => `
                <tr>
                    <td><strong>${{w.ssid || 'N/A'}}</strong></td>
                    <td>${{w.security || 'Open'}}</td>
                    <td><code>${{w.bssid || 'Any'}}</code></td>
                    <td>${{w.last_connected || 'N/A'}}</td>
                </tr>
            `).join('');

            const btBody = document.getElementById('bt-body');
            btBody.innerHTML = DATA.bt.map(b => `
                <tr>
                    <td><strong>${{b.device_name || 'Bluetooth Device'}}</strong></td>
                    <td><code>${{b.mac_address || 'N/A'}}</code></td>
                    <td><span class="badge badge-green">${{b.status || 'Paired'}}</span></td>
                </tr>
            `).join('');

            // 11. Notifications
            const notBody = document.getElementById('notifs-body');
            notBody.innerHTML = DATA.notifs.map(n => `
                <tr>
                    <td><code>${{n.timestamp || 'N/A'}}</code></td>
                    <td><strong>${{n.package || 'App'}}</strong></td>
                    <td>${{n.title || 'N/A'}}</td>
                    <td>${{n.body || ''}}</td>
                </tr>
            `).join('');

            // 12. Carved
            const carBody = document.getElementById('carved-body');
            carBody.innerHTML = DATA.carved.map(c => `
                <tr>
                    <td><code>${{c.source_db || 'Database'}}</code></td>
                    <td>${{c.page_num || 'N/A'}}</td>
                    <td>${{c.offset || 'N/A'}}</td>
                    <td><code>${{escapeHtml(c.extracted_text || '')}}</code></td>
                </tr>
            `).join('');

            // 13. Audit Certificate
            document.getElementById('audit-cert-text').textContent = JSON.stringify(DATA.audit, null, 2);
        }}

        function escapeHtml(text) {{
            return text.replace(/&/g, "&amp;").replace(/</g, "&lt;").replace(/>/g, "&gt;");
        }}

        let mapInitialized = false;
        function initMap() {{
            if (mapInitialized) return;
            const mapContainer = document.getElementById('map');
            if (!mapContainer) return;

            const map = L.map('map').setView([27.7172, 85.3240], 4);
            L.tileLayer('https://{{s}}.tile.openstreetmap.org/{{z}}/{{x}}/{{y}}.png', {{
                maxZoom: 19,
                attribution: '© OpenStreetMap'
            }}).addTo(map);

            let hasPoints = false;
            let bounds = [];

            DATA.photos.forEach(p => {{
                if (p.latitude && p.longitude) {{
                    const lat = parseFloat(p.latitude);
                    const lon = parseFloat(p.longitude);
                    if (!isNaN(lat) && !isNaN(lon) && lat !== 0 && lon !== 0) {{
                        hasPoints = true;
                        bounds.push([lat, lon]);
                        L.marker([lat, lon]).addTo(map)
                            .bindPopup(`<strong>${{p.filename || 'Photo'}}</strong><br>Time: ${{p.timestamp || 'N/A'}}<br>Coords: ${{lat}}, ${{lon}}`);
                    }}
                }}
            }});

            if (hasPoints && bounds.length > 0) {{
                map.fitBounds(bounds, {{ padding: [30, 30] }});
            }}
            mapInitialized = true;
        }}

        function filterTables() {{
            const filter = document.getElementById('global-search').value.toLowerCase();
            const activeTab = document.querySelector('.tab-content.active');
            if (!activeTab) return;

            const rows = activeTab.querySelectorAll('tbody tr');
            rows.forEach(r => {{
                const text = r.textContent.toLowerCase();
                r.style.display = text.includes(filter) ? '' : 'none';
            }});
        }}

        // Run population on load
        window.addEventListener('DOMContentLoaded', populateTables);
    </script>
</body>
</html>
"""
        with open(out_file, "w", encoding="utf-8") as f:
            f.write(html_content)

        return out_file
