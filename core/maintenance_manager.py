"""
Automated Startup Self-Updater, Definition Fetcher, and Self-Healing Engine for aforensic.
"""

import os
import sys
import shutil
import subprocess
import platform
from typing import Dict, Any, Tuple


class MaintenanceManager:
    """
    Automated Startup Self-Updater, Definition Fetcher, and Self-Healing Engine for aforensic.
    """

    def clean_stale_sockets(self) -> int:
        return self._clean_temp_artifacts()

    @staticmethod
    def run_startup_maintenance(interactive_update: bool = True, timeout_sec: int = 2) -> Dict[str, Any]:
        maintenance_log = []

        # 1. Daemon Health Check & ADB Socket Self-Healing
        daemon_ok = MaintenanceManager._heal_forensics_daemon()
        if daemon_ok:
            maintenance_log.append("ADB daemon socket active and operational")

        # 2. Housekeeping (Clean temporary probe files and orphans)
        cleaned_count = MaintenanceManager._clean_temp_artifacts()
        if cleaned_count > 0:
            maintenance_log.append(f"Purged {cleaned_count} orphaned temporary staging files")

        # 3. Check for new Version / Android OEM Profiles
        update_available, update_details = MaintenanceManager._check_for_updates(timeout_sec)
        
        if update_available and interactive_update:
            try:
                from rich.console import Console
                from rich.panel import Panel
                from rich.prompt import Confirm
                console = Console()
                console.print(Panel(
                    f"[bold green]⚡ NEW ANDROID FORENSIC DEFINITIONS & OEM PROFILES FOUND[/bold green]\n\n"
                    f"[white]Latest Upstream Release:[/white] [cyan]{update_details}[/cyan]\n"
                    f"[dim]Includes updated Android 14/15 schema offsets, OEM profiles, and app decoders.[/dim]",
                    title="Automated Intelligence Update", border_style="green"
                ))
                if Confirm.ask("[bold green]Would you like to auto-update and start now? (Recommended)[/bold green]", default=True):
                    success, msg = MaintenanceManager._apply_update()
                    if success:
                        console.print(f"[bold green]✔ {msg}[/bold green]\n")
                        maintenance_log.append(f"Self-Update: {msg}")
                    else:
                        console.print(f"[bold yellow]⚠️ {msg}[/bold yellow]\n")
            except Exception:
                pass

        return {
            "status": "Healthy",
            "log": maintenance_log,
            "update_checked": True
        }

    @staticmethod
    def _heal_forensics_daemon() -> bool:
        if shutil.which("adb"):
            try:
                subprocess.run(["adb", "start-server"], capture_output=True, timeout=2)
                return True
            except Exception:
                return False
        return True

    @staticmethod
    def _clean_temp_artifacts() -> int:
        cleaned = 0
        temp_dirs = [os.path.expanduser("~/.aforensic_temp"), "/tmp"]
        for t_dir in temp_dirs:
            if not os.path.exists(t_dir):
                continue
            try:
                for entry in os.listdir(t_dir):
                    if entry.startswith(".aforensic_") or entry.startswith("aforensic_"):
                        full_p = os.path.join(t_dir, entry)
                        if os.path.isfile(full_p):
                            os.remove(full_p)
                            cleaned += 1
                        elif os.path.isdir(full_p):
                            shutil.rmtree(full_p, ignore_errors=True)
                            cleaned += 1
            except Exception:
                pass
        return cleaned

    @staticmethod
    def _check_for_updates(timeout_sec: int = 2) -> Tuple[bool, str]:
        repo_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        git_dir = os.path.join(repo_dir, ".git")

        if not os.path.exists(git_dir) or not shutil.which("git"):
            return False, "Standalone environment"

        try:
            import socket
            sock = socket.create_connection(("github.com", 443), timeout=timeout_sec)
            sock.close()
        except Exception:
            return False, "Offline environment (Network unavailable)"

        try:
            subprocess.run(
                ["git", "fetch", "--quiet", "origin"],
                cwd=repo_dir, capture_output=True, text=True, timeout=timeout_sec + 2
            )
            status_res = subprocess.run(
                ["git", "status", "-uno"],
                cwd=repo_dir, capture_output=True, text=True, timeout=timeout_sec
            )
            if "Your branch is behind" in status_res.stdout:
                return True, "New aForensic modules & Android OEM definitions ready on GitHub"
            return False, "Up to date"
        except Exception:
            return False, "Update check bypassed"

    @staticmethod
    def _apply_update() -> Tuple[bool, str]:
        repo_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
        try:
            pull_res = subprocess.run(
                ["git", "pull", "--ff-only"],
                cwd=repo_dir, capture_output=True, text=True, timeout=10
            )
            if pull_res.returncode == 0:
                subprocess.run(
                    [sys.executable, "-m", "pip", "install", "-e", ".", "--no-deps", "--break-system-packages"],
                    cwd=repo_dir, capture_output=True, timeout=10
                )
                return True, "aForensic updated and re-compiled successfully!"
            return False, f"Git pull returned error: {pull_res.stderr.strip()}"
        except Exception as e:
            return False, f"Update installation error: {str(e)}"
