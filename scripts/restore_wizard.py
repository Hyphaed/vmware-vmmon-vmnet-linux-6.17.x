#!/usr/bin/env python3
"""
VMware Module Restore Wizard
Interactive UI for restoring VMware modules from backups
"""

import os
import sys
import json
import shutil
import hashlib
from pathlib import Path
from datetime import datetime
from typing import List, Dict, Tuple, Optional

# Import our PyTermGUI-based shared UI
try:
    from vmware_ui import VMwareUI
except ImportError:
    # If running from different directory, try to import from scripts/
    sys.path.insert(0, str(Path(__file__).parent))
    from vmware_ui import VMwareUI


class BackupInfo:
    """Information about a backup"""
    def __init__(self, path: Path):
        self.path = path
        self.name = path.name
        self.timestamp = path.stat().st_mtime
        self.size = self._calculate_size()
        self.files = self._list_files()
        self.hashes = self._calculate_hashes()
        self.is_original = False  # Will be determined by comparing hashes
    
    def _calculate_size(self) -> int:
        """Calculate total size of backup"""
        total = 0
        if self.path.is_file():
            return self.path.stat().st_size
        elif self.path.is_dir():
            for item in self.path.rglob('*'):
                if item.is_file():
                    total += item.stat().st_size
        return total
    
    def _list_files(self) -> List[str]:
        """List files in backup"""
        files = []
        if self.path.is_file():
            files.append(self.path.name)
        elif self.path.is_dir():
            for item in self.path.iterdir():
                if item.is_file():
                    files.append(item.name)
        return files
    
    def _calculate_hashes(self) -> Dict[str, str]:
        """Calculate MD5 hashes of tar files in backup"""
        hashes = {}
        try:
            if self.path.is_dir():
                for item in self.path.iterdir():
                    if item.suffix == '.tar' and item.is_file():
                        hashes[item.name] = self._md5_file(item)
            elif self.path.is_file() and self.path.suffix == '.tar':
                hashes[self.path.name] = self._md5_file(self.path)
        except Exception:
            pass  # If hash calculation fails, just skip
        return hashes
    
    def _md5_file(self, filepath: Path) -> str:
        """Calculate MD5 hash of a file"""
        md5 = hashlib.md5()
        with open(filepath, 'rb') as f:
            for chunk in iter(lambda: f.read(8192), b''):
                md5.update(chunk)
        return md5.hexdigest()


class RestoreWizard:
    """Interactive wizard for restoring VMware modules"""
    
    def __init__(self):
        self.ui = VMwareUI()
        self.distro = self._detect_distro()
        self.vmware_mod_dir = self._get_vmware_dir()
        self.backup_base_dir = self._get_backup_dir()
        self.backups: List[BackupInfo] = []
    
    def _detect_distro(self) -> str:
        """Detect Linux distribution"""
        if Path("/etc/gentoo-release").exists():
            return "gentoo"
        elif Path("/etc/fedora-release").exists():
            return "fedora"
        elif Path("/etc/arch-release").exists():
            return "arch"
        elif Path("/etc/debian_version").exists():
            return "debian"
        else:
            return "unknown"
    
    def _get_vmware_dir(self) -> Path:
        """Get VMware modules directory"""
        if self.distro == "gentoo":
            return Path("/opt/vmware/lib/vmware/modules/source")
        else:
            return Path("/usr/lib/vmware/modules/source")
    
    def _get_backup_dir(self) -> Path:
        """Get backup base directory"""
        if self.distro == "gentoo":
            return Path("/tmp")
        else:
            return self.vmware_mod_dir
    
    def detect_backups(self) -> List[BackupInfo]:
        """Detect all available backups"""
        backups = []
        
        with self.ui.show_progress("Scanning for backups...") as progress:
            task = progress.add_task("[cyan]Detecting backups...", total=None)
            
            # Look for backup directories
            if self.backup_base_dir.exists():
                for item in self.backup_base_dir.iterdir():
                    if item.name.startswith("backup-") or item.name.startswith("vmware-backup-"):
                        backups.append(BackupInfo(item))
            
            # Also check VMware mod dir for tarball backups
            if self.vmware_mod_dir.exists() and self.vmware_mod_dir != self.backup_base_dir:
                for item in self.vmware_mod_dir.iterdir():
                    if item.name.startswith("backup-") or "backup" in item.name.lower():
                        backups.append(BackupInfo(item))
            
            progress.update(task, completed=True)
        
        # Sort by timestamp (oldest first to find original)
        backups.sort(key=lambda b: b.timestamp)
        
        # Identify the original backup (oldest one with valid hashes)
        if backups:
            oldest_backup = backups[0]
            if oldest_backup.hashes:
                oldest_backup.is_original = True
                self._mark_original_backup(oldest_backup, backups[1:])
        
        # Sort by timestamp (newest first for display)
        backups.sort(key=lambda b: b.timestamp, reverse=True)
        return backups
    
    def _mark_original_backup(self, original: BackupInfo, other_backups: List[BackupInfo]):
        """Mark backups that match the original based on hash comparison"""
        if not original.hashes:
            return
        
        for backup in other_backups:
            if backup.hashes == original.hashes:
                backup.is_original = True
    
    def display_backups_table(self):
        """Display backups in a table"""
        self.ui.show_section("Available Backups")
        
        if not self.backups:
            self.ui.show_error("No backups found!")
            self.ui.show_info(f"Checked directory: {self.backup_base_dir}")
            return False
        
        # Check if we have original backups
        has_original = any(b.is_original for b in self.backups)
        if has_original:
            self.ui.show_info("✨ [bold green]Original VMware modules backup detected![/bold green]")
            self.ui.console.print("[dim]Original backups contain unmodified VMware modules (verified by hash)[/dim]")
            self.ui.console.print()
        
        table = self.ui.create_table(
            headers=["#", "Backup Name", "Date/Time", "Size", "Type"]
        )
        
        for idx, backup in enumerate(self.backups, 1):
            timestamp_str = self.ui.format_timestamp(backup.timestamp)
            size_str = self.ui.format_size(backup.size)
            
            # Determine backup type
            if backup.is_original:
                type_str = "[bold green]✓ Original[/bold green]"
            else:
                type_str = "[yellow]Modified[/yellow]"
            
            # Format backup name
            backup_name = backup.name
            if backup.is_original:
                backup_name = f"[bold]{backup_name}[/bold]"
            
            # Highlight recent backups (< 7 days) only for non-original
            if not backup.is_original:
                age_days = (datetime.now().timestamp() - backup.timestamp) / 86400
                if age_days < 1:
                    timestamp_str = f"[green]{timestamp_str}[/green]"
                elif age_days < 7:
                    timestamp_str = f"[yellow]{timestamp_str}[/yellow]"
            
            table.add_row(
                str(idx),
                backup_name,
                timestamp_str,
                size_str,
                type_str
            )
        
        self.ui.console.print(table)
        self.ui.console.print()
        
        if has_original:
            self.ui.console.print("[dim]💡 Tip: Original backups can be used to restore factory VMware modules[/dim]")
            self.ui.console.print()
        
        return True
    
    def select_backup(self) -> BackupInfo:
        """Let user select a backup"""
        self.ui.console.print("[dim]Enter the number of the backup to restore (0 to cancel)[/dim]")
        self.ui.console.print()
        
        while True:
            choice = self.ui.prompt(
                "Select backup",
                default="0"
            )
            
            try:
                idx = int(choice)
                if idx == 0:
                    self.ui.show_warning("Restore cancelled by user")
                    sys.exit(0)
                elif 1 <= idx <= len(self.backups):
                    return self.backups[idx - 1]
                else:
                    self.ui.show_error(f"Invalid selection: {idx}")
            except ValueError:
                self.ui.show_error("Please enter a valid number")
    
    def show_backup_details(self, backup: BackupInfo):
        """Display detailed backup information"""
        self.ui.show_section("Backup Details")
        
        details_table = Table(show_header=False, box=box.SIMPLE, border_style=HYPHAED_GREEN)
        details_table.add_column("Property", style="cyan", width=20)
        details_table.add_column("Value", style="white")
        
        details_table.add_row("Backup Name", backup.name)
        
        # Show backup type prominently
        if backup.is_original:
            details_table.add_row("Type", "[bold green]✓ Original VMware Modules[/bold green]")
            details_table.add_row("", "[dim](Unmodified factory modules)[/dim]")
        else:
            details_table.add_row("Type", "[yellow]Modified/Patched Modules[/yellow]")
        
        details_table.add_row("Created", self.ui.format_timestamp(backup.timestamp))
        details_table.add_row("Total Size", self.ui.format_size(backup.size))
        details_table.add_row("Location", str(backup.path))
        details_table.add_row("Files Count", str(len(backup.files)))
        
        self.ui.console.print(details_table)
        self.ui.console.print()
        
        # Show file list
        if backup.files:
            self.ui.console.print("[cyan]Files in backup:[/cyan]")
            for file in backup.files[:10]:  # Show first 10 files
                self.ui.console.print(f"  • {file}")
            if len(backup.files) > 10:
                self.ui.console.print(f"  [dim]... and {len(backup.files) - 10} more files[/dim]")
            self.ui.console.print()
    
    def show_current_status(self):
        """Show current module status"""
        self.ui.show_section("Current Module Status")
        
        status_table = Table(show_header=False, box=box.SIMPLE, border_style=HYPHAED_GREEN)
        status_table.add_column("Module", style="cyan", width=20)
        status_table.add_column("Status", style="white")
        
        # Check if modules are loaded
        import subprocess
        
        try:
            lsmod_output = subprocess.check_output(["lsmod"], text=True)
            vmmon_loaded = "vmmon" in lsmod_output
            vmnet_loaded = "vmnet" in lsmod_output
            
            status_table.add_row(
                "vmmon",
                "[green]✓ Loaded[/green]" if vmmon_loaded else "[red]✗ Not loaded[/red]"
            )
            status_table.add_row(
                "vmnet",
                "[green]✓ Loaded[/green]" if vmnet_loaded else "[red]✗ Not loaded[/red]"
            )
            
            # Get module versions
            if vmmon_loaded:
                try:
                    modinfo = subprocess.check_output(["modinfo", "vmmon"], text=True)
                    for line in modinfo.split('\n'):
                        if line.startswith("vermagic:"):
                            version = line.split()[1]
                            status_table.add_row("Kernel version", version)
                            break
                except:
                    pass
        except:
            status_table.add_row("Status", "[yellow]Could not determine[/yellow]")
        
        self.ui.console.print(status_table)
        self.ui.console.print()
    
    def perform_restore(self, backup: BackupInfo) -> bool:
        """Perform the actual restore operation"""
        self.ui.show_section("Performing Restore")
        
        # This will be handled by the bash script
        # We just export the configuration
        config = {
            'backup_path': str(backup.path),
            'backup_name': backup.name,
            'vmware_mod_dir': str(self.vmware_mod_dir),
            'distro': self.distro,
            'timestamp': datetime.now().isoformat()
        }
        
        config_file = Path("/tmp/vmware_restore_config.json")
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)
        
        self.ui.show_success(f"Configuration saved to: {config_file}")
        return True
    
    def run(self):
        """Main wizard flow"""
        try:
            # Welcome
            self.ui.show_banner(
                "VMWARE MODULE RESTORE WIZARD",
                "Python-Powered Backup Management"
            )
            
            # Show current status
            self.show_current_status()
            
            # Detect backups
            self.backups = self.detect_backups()
            
            # Display backups
            if not self.display_backups_table():
                return 1
            
            # Select backup
            selected_backup = self.select_backup()
            
            # Show details
            self.show_backup_details(selected_backup)
            
            # Confirm
            if not self.ui.confirm("Proceed with restore?"):
                self.ui.show_warning("Restore cancelled by user")
                return 0
            
            # Perform restore
            if self.perform_restore(selected_backup):
                self.ui.console.print()
                self.ui.show_panel(
                    "[bold green]✓ Configuration Complete![/bold green]\n\n" +
                    "The restore script will now restore the selected backup.",
                    title="Ready to Proceed",
                    border_color=HYPHAED_GREEN
                )
                self.ui.console.print()
                return 0
            else:
                self.ui.show_error("Restore configuration failed")
                return 1
        
        except KeyboardInterrupt:
            self.ui.console.print("\n\n[yellow]Restore cancelled by user.[/yellow]")
            return 1
        except Exception as e:
            self.ui.show_error(f"Error: {e}")
            return 1


def main():
    """Entry point"""
    # Check if running as root
    if os.geteuid() != 0:
        print("ERROR: This script must be run as root (use sudo)")
        return 1
    
    wizard = RestoreWizard()
    return wizard.run()


if __name__ == "__main__":
    sys.exit(main())

