#!/usr/bin/env python3
"""
VMware System Optimizer
Automatically tunes your Linux system for optimal VMware Workstation performance

Features:
- GRUB boot parameter optimization (IOMMU, hugepages, CPU isolation)
- Kernel parameter tuning (sysctl)
- CPU governor configuration (performance mode)
- Memory optimization (hugepages, swappiness)
- I/O scheduler optimization (NVMe/SSD)
- Network stack tuning
- Install performance libraries
- All changes backed up automatically
"""

import os
import sys
import subprocess
import re
import shutil
from pathlib import Path
from datetime import datetime
from typing import Dict, List, Tuple, Optional

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.progress import Progress, SpinnerColumn, TextColumn
    from rich import box
    HAS_RICH = True
except ImportError:
    HAS_RICH = False
    print("Installing rich library for better UI...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "rich"])
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.progress import Progress, SpinnerColumn, TextColumn
    from rich import box
    HAS_RICH = True

try:
    import questionary
    from questionary import Style
except ImportError:
    print("Questionary not found. Attempting to install in conda environment...", file=sys.stderr)
    
    # Check if we're in a conda/mamba environment
    conda_prefix = os.environ.get('CONDA_PREFIX')
    if conda_prefix:
        # We're in a conda environment, use conda/mamba to install
        try:
            # Try mamba first (faster), then conda
            if shutil.which('mamba'):
                subprocess.check_call(['mamba', 'install', '-y', '-c', 'conda-forge', 'questionary'])
            elif shutil.which('conda'):
                subprocess.check_call(['conda', 'install', '-y', '-c', 'conda-forge', 'questionary'])
            else:
                # Fallback to pip within conda environment (safe)
                subprocess.check_call([sys.executable, "-m", "pip", "install", "questionary"])
        except subprocess.CalledProcessError:
            print("Warning: Could not install questionary in conda environment.", file=sys.stderr)
    else:
        # Not in conda environment - warn user but continue
        print("Warning: Not running in conda/mamba environment. Using basic prompts.", file=sys.stderr)
    
    try:
        import questionary
        from questionary import Style
    except ImportError:
        # Fallback mode
        questionary = None
        Style = None

console = Console()
HYPHAED_GREEN = "#B0D56A"

# Custom Questionary style matching Hyphaed green theme
OPTIMIZER_STYLE = Style([
    ('qmark', 'fg:#B0D56A bold'),           # Question mark - Hyphaed green
    ('question', 'fg:#ffffff bold'),         # Question text - white
    ('answer', 'fg:#B0D56A bold'),          # Answer - Hyphaed green
    ('pointer', 'fg:#B0D56A bold'),         # Pointer - Hyphaed green
    ('highlighted', 'fg:#B0D56A bold'),     # Highlighted option - Hyphaed green
    ('selected', 'fg:#00ffff'),              # Selected - cyan
    ('separator', 'fg:#6C6C6C'),            # Separator - gray
    ('instruction', 'fg:#858585'),           # Instructions - light gray
    ('text', 'fg:#ffffff'),                  # Text - white
    ('disabled', 'fg:#858585 italic')       # Disabled - gray italic
])


class SystemOptimizer:
    """Main system optimization class"""
    
    def __init__(self):
        self.console = Console()
        self.backup_dir = Path(f"/root/vmware-tune-backup-{datetime.now().strftime('%Y%m%d-%H%M%S')}")
        self.changes_made = []
        self.hw_info = self.detect_hardware()
        self.distro_info = self.detect_distribution()
        
    def detect_hardware(self) -> Dict:
        """Detect hardware capabilities"""
        hw = {
            'cpu_count': os.cpu_count() or 1,
            'total_ram_gb': 0,
            'has_iommu': False,
            'has_vtx': False,
            'has_ept': False,
            'has_nvme': False,
            'nvme_devices': [],
            'cpu_vendor': 'unknown',
            'has_avx512': False,
            'has_avx2': False,
        }
        
        # Detect CPU features
        try:
            with open('/proc/cpuinfo', 'r') as f:
                cpuinfo = f.read()
                
            # Check CPU vendor
            if 'Intel' in cpuinfo:
                hw['cpu_vendor'] = 'intel'
            elif 'AMD' in cpuinfo:
                hw['cpu_vendor'] = 'amd'
            
            # Check virtualization
            hw['has_vtx'] = 'vmx' in cpuinfo or 'svm' in cpuinfo
            hw['has_ept'] = 'ept' in cpuinfo or 'npt' in cpuinfo
            hw['has_avx512'] = 'avx512f' in cpuinfo
            hw['has_avx2'] = 'avx2' in cpuinfo
            
        except Exception:
            pass
        
        # Detect IOMMU
        if Path('/sys/class/iommu').exists():
            iommu_devices = list(Path('/sys/class/iommu').iterdir())
            hw['has_iommu'] = len(iommu_devices) > 0
        
        # Detect NVMe devices
        nvme_paths = list(Path('/sys/block').glob('nvme*'))
        hw['has_nvme'] = len(nvme_paths) > 0
        hw['nvme_devices'] = [p.name for p in nvme_paths]
        
        # Get total RAM
        try:
            with open('/proc/meminfo', 'r') as f:
                for line in f:
                    if line.startswith('MemTotal:'):
                        kb = int(line.split()[1])
                        hw['total_ram_gb'] = kb / (1024 * 1024)
                        break
        except Exception:
            pass
        
        return hw
    
    def detect_distribution(self) -> Dict:
        """Detect Linux distribution"""
        distro = {
            'name': 'unknown',
            'id': 'unknown',
            'version': 'unknown',
            'family': 'unknown',
            'bootloader': 'grub',
            'grub_config': '/etc/default/grub',
        }
        
        # Read os-release
        try:
            with open('/etc/os-release', 'r') as f:
                for line in f:
                    if line.startswith('NAME='):
                        distro['name'] = line.split('=')[1].strip().strip('"')
                    elif line.startswith('ID='):
                        distro['id'] = line.split('=')[1].strip().strip('"')
                    elif line.startswith('VERSION_ID='):
                        distro['version'] = line.split('=')[1].strip().strip('"')
        except Exception:
            pass
        
        # Determine family
        if distro['id'] in ['ubuntu', 'debian', 'pop', 'linuxmint', 'elementary']:
            distro['family'] = 'debian'
        elif distro['id'] in ['fedora', 'rhel', 'centos', 'rocky', 'almalinux']:
            distro['family'] = 'rhel'
        elif distro['id'] in ['arch', 'manjaro']:
            distro['family'] = 'arch'
        elif distro['id'] == 'gentoo':
            distro['family'] = 'gentoo'
        elif distro['id'] in ['opensuse', 'opensuse-leap', 'opensuse-tumbleweed', 'sles']:
            distro['family'] = 'suse'
        
        # Check if systemd-boot instead of GRUB
        if Path('/boot/loader/loader.conf').exists():
            distro['bootloader'] = 'systemd-boot'
        
        return distro
    
    def show_banner(self):
        """Display welcome banner"""
        banner = """
╔══════════════════════════════════════════════════════════════╗
║                                                              ║
║       VMware WORKSTATION SYSTEM OPTIMIZER                   ║
║          Tune Your System for Best Performance               ║
║                                                              ║
╚══════════════════════════════════════════════════════════════╝
"""
        self.console.print(f"[{HYPHAED_GREEN}]{banner}[/{HYPHAED_GREEN}]")
        self.console.print()
    
    def display_hardware_summary(self):
        """Show detected hardware"""
        self.console.print(Panel.fit(
            "[bold cyan]Detected Hardware Configuration[/bold cyan]",
            border_style=HYPHAED_GREEN
        ))
        self.console.print()
        
        table = Table(show_header=False, box=box.SIMPLE, border_style=HYPHAED_GREEN)
        table.add_column("Property", style="cyan", width=25)
        table.add_column("Value", style="white")
        
        table.add_row("CPU Cores", str(self.hw_info['cpu_count']))
        table.add_row("Total RAM", f"{self.hw_info['total_ram_gb']:.1f} GB")
        table.add_row("CPU Vendor", self.hw_info['cpu_vendor'].upper())
        
        # Virtualization
        virt_status = "[green]✓ Enabled[/green]" if self.hw_info['has_vtx'] else "[red]✗ Disabled[/red]"
        table.add_row("Virtualization (VT-x/AMD-V)", virt_status)
        
        if self.hw_info['has_ept']:
            table.add_row("EPT/NPT", "[green]✓ Supported[/green]")
        
        # IOMMU
        iommu_status = "[green]✓ Active[/green]" if self.hw_info['has_iommu'] else "[yellow]○ Inactive[/yellow]"
        table.add_row("IOMMU (VT-d/AMD-Vi)", iommu_status)
        
        # SIMD
        if self.hw_info['has_avx512']:
            table.add_row("SIMD", "[green]AVX-512[/green]")
        elif self.hw_info['has_avx2']:
            table.add_row("SIMD", "[green]AVX2[/green]")
        
        # Storage
        if self.hw_info['has_nvme']:
            table.add_row("NVMe Devices", f"{len(self.hw_info['nvme_devices'])} detected")
        
        self.console.print(table)
        self.console.print()
    
    def display_optimizations(self):
        """Show what will be optimized"""
        self.console.print(Panel.fit(
            "[bold yellow]Planned Optimizations[/bold yellow]",
            border_style=HYPHAED_GREEN
        ))
        self.console.print()
        
        opts = []
        
        # GRUB optimizations
        opts.append("[bold]1. GRUB Boot Parameters[/bold]")
        if self.hw_info['cpu_vendor'] == 'intel':
            opts.append("   • intel_iommu=on - Enable Intel VT-d for device passthrough")
        elif self.hw_info['cpu_vendor'] == 'amd':
            opts.append("   • amd_iommu=on - Enable AMD-Vi for device passthrough")
        
        opts.append("   • iommu=pt - IOMMU pass-through mode (best for VMs)")
        opts.append("   • default_hugepagesz=1G hugepagesz=1G - 1GB huge pages")
        opts.append(f"   • hugepages={int(self.hw_info['total_ram_gb'] * 0.25)} - Reserve 25% RAM")
        opts.append("   • transparent_hugepage=never - Disable THP (better for VMs)")
        opts.append("   • mitigations=off - Disable CPU vulnerability mitigations (more performance)")
        
        # Kernel parameters
        opts.append("")
        opts.append("[bold]2. Kernel Parameters (sysctl)[/bold]")
        opts.append("   • vm.swappiness=10 - Minimize swapping")
        opts.append("   • vm.dirty_ratio=15 - Better write performance")
        opts.append("   • vm.vfs_cache_pressure=50 - Keep more cache")
        opts.append("   • kernel.sched_migration_cost_ns=5000000 - Reduce CPU migrations")
        opts.append("   • net.core.netdev_max_backlog=16384 - Better network performance")
        
        # CPU governor
        opts.append("")
        opts.append("[bold]3. CPU Governor[/bold]")
        opts.append("   • Set to 'performance' mode - Maximum CPU frequency")
        
        # I/O scheduler
        if self.hw_info['has_nvme']:
            opts.append("")
            opts.append("[bold]4. I/O Scheduler[/bold]")
            opts.append("   • Set NVMe devices to 'none' scheduler - Best for SSD/NVMe")
        
        # Packages
        opts.append("")
        opts.append("[bold]5. Performance Packages[/bold]")
        if self.distro_info['family'] in ['debian', 'ubuntu']:
            opts.append("   • cpufrequtils - CPU frequency management")
            opts.append("   • linux-tools-generic - Performance profiling tools")
            opts.append("   • tuned - System tuning daemon")
        elif self.distro_info['family'] in ['rhel', 'fedora']:
            opts.append("   • kernel-tools - Performance profiling tools")
            opts.append("   • tuned - System tuning daemon")
        
        for opt in opts:
            self.console.print(opt)
        
        self.console.print()
        
        # Warnings
        self.console.print("[yellow]⚠ Important Notes:[/yellow]")
        self.console.print("  • All changes will be backed up automatically")
        self.console.print("  • A system reboot is required for GRUB changes to take effect")
        self.console.print("  • Disabling mitigations reduces security but improves performance")
        self.console.print("  • You can revert changes using the backup at:", style="dim")
        self.console.print(f"    [cyan]{self.backup_dir}[/cyan]", style="dim")
        self.console.print()
    
    def backup_file(self, file_path: Path):
        """Backup a file before modifying"""
        if not file_path.exists():
            return
        
        self.backup_dir.mkdir(parents=True, exist_ok=True)
        
        # Preserve directory structure
        relative = file_path.relative_to('/') if file_path.is_absolute() else file_path
        backup_path = self.backup_dir / relative
        backup_path.parent.mkdir(parents=True, exist_ok=True)
        
        shutil.copy2(str(file_path), str(backup_path))
        self.console.print(f"[dim]  Backed up: {file_path}[/dim]")
    
    def optimize_grub(self) -> bool:
        """Optimize GRUB configuration"""
        if self.distro_info['bootloader'] != 'grub':
            self.console.print("[yellow]Skipping GRUB optimization (not using GRUB)[/yellow]")
            return False
        
        grub_config = Path(self.distro_info['grub_config'])
        if not grub_config.exists():
            self.console.print(f"[red]GRUB config not found: {grub_config}[/red]")
            return False
        
        self.console.print()
        self.console.print("[cyan]Optimizing GRUB boot parameters...[/cyan]")
        
        # Backup
        self.backup_file(grub_config)
        
        # Read current config
        with open(grub_config, 'r') as f:
            lines = f.readlines()
        
        # Build optimization parameters
        opt_params = []
        
        # IOMMU
        if self.hw_info['cpu_vendor'] == 'intel':
            opt_params.append('intel_iommu=on')
        elif self.hw_info['cpu_vendor'] == 'amd':
            opt_params.append('amd_iommu=on')
        
        opt_params.append('iommu=pt')
        
        # Huge pages
        hugepages_count = int(self.hw_info['total_ram_gb'] * 0.25)
        opt_params.extend([
            'default_hugepagesz=1G',
            'hugepagesz=1G',
            f'hugepages={hugepages_count}',
            'transparent_hugepage=never'
        ])
        
        # Performance
        opt_params.append('mitigations=off')
        
        # Find and modify GRUB_CMDLINE_LINUX_DEFAULT
        modified = False
        new_lines = []
        
        for line in lines:
            if line.strip().startswith('GRUB_CMDLINE_LINUX_DEFAULT='):
                # Extract existing parameters
                match = re.search(r'GRUB_CMDLINE_LINUX_DEFAULT="([^"]*)"', line)
                if match:
                    existing = match.group(1)
                    existing_params = existing.split()
                    
                    # Remove any existing conflicting parameters
                    existing_params = [p for p in existing_params if not any(
                        p.startswith(prefix) for prefix in [
                            'intel_iommu=', 'amd_iommu=', 'iommu=',
                            'hugepages=', 'hugepagesz=', 'default_hugepagesz=',
                            'transparent_hugepage=', 'mitigations='
                        ]
                    )]
                    
                    # Add new parameters
                    all_params = existing_params + opt_params
                    new_line = f'GRUB_CMDLINE_LINUX_DEFAULT="{" ".join(all_params)}"\n'
                    new_lines.append(new_line)
                    modified = True
                else:
                    new_lines.append(line)
            else:
                new_lines.append(line)
        
        if not modified:
            # Add new line if not found
            new_lines.append(f'\n# VMware optimization\nGRUB_CMDLINE_LINUX_DEFAULT="{" ".join(opt_params)}"\n')
        
        # Write new config
        with open(grub_config, 'w') as f:
            f.writelines(new_lines)
        
        self.console.print("  [green]✓[/green] GRUB parameters updated")
        self.changes_made.append("GRUB boot parameters optimized")
        
        # Update GRUB
        self.console.print("  Updating GRUB configuration...")
        try:
            if self.distro_info['family'] in ['debian', 'ubuntu']:
                subprocess.run(['update-grub'], check=True, capture_output=True)
            elif self.distro_info['family'] in ['rhel', 'fedora']:
                subprocess.run(['grub2-mkconfig', '-o', '/boot/grub2/grub.cfg'], check=True, capture_output=True)
            elif self.distro_info['family'] == 'arch':
                subprocess.run(['grub-mkconfig', '-o', '/boot/grub/grub.cfg'], check=True, capture_output=True)
            else:
                self.console.print("  [yellow]Please run 'update-grub' or equivalent manually[/yellow]")
            
            self.console.print("  [green]✓[/green] GRUB configuration updated")
        except subprocess.CalledProcessError as e:
            self.console.print(f"  [red]✗ Failed to update GRUB: {e}[/red]")
            return False
        
        # Update initramfs (required after GRUB changes)
        self.console.print("  Updating initramfs...")
        try:
            if self.distro_info['family'] in ['debian', 'ubuntu']:
                # Update initramfs for all kernels
                subprocess.run(['update-initramfs', '-u', '-k', 'all'], check=True, capture_output=True)
                self.console.print("  [green]✓[/green] Initramfs updated")
            elif self.distro_info['family'] in ['rhel', 'fedora']:
                # Dracut for RHEL/Fedora
                subprocess.run(['dracut', '--force', '--regenerate-all'], check=True, capture_output=True)
                self.console.print("  [green]✓[/green] Initramfs updated (dracut)")
            elif self.distro_info['family'] == 'arch':
                # mkinitcpio for Arch
                subprocess.run(['mkinitcpio', '-P'], check=True, capture_output=True)
                self.console.print("  [green]✓[/green] Initramfs updated (mkinitcpio)")
            else:
                self.console.print("  [yellow]⚠[/yellow] Please update initramfs manually")
        except subprocess.CalledProcessError as e:
            self.console.print(f"  [yellow]⚠ Failed to update initramfs: {e}[/yellow]")
            self.console.print("  [yellow]Please run 'update-initramfs -u' or equivalent manually[/yellow]")
            # Don't fail the whole process if initramfs update fails
        
        return True
    
    def optimize_sysctl(self) -> bool:
        """Optimize kernel parameters"""
        self.console.print()
        self.console.print("[cyan]Optimizing kernel parameters (sysctl)...[/cyan]")
        
        sysctl_conf = Path('/etc/sysctl.d/99-vmware-optimization.conf')
        
        # Backup if exists
        if sysctl_conf.exists():
            self.backup_file(sysctl_conf)
        
        sysctl_params = {
            '# Memory management': None,
            'vm.swappiness': '10',
            'vm.dirty_ratio': '15',
            'vm.dirty_background_ratio': '5',
            'vm.vfs_cache_pressure': '50',
            
            '# Network performance': None,
            'net.core.netdev_max_backlog': '16384',
            'net.core.rmem_max': '134217728',
            'net.core.wmem_max': '134217728',
            'net.ipv4.tcp_rmem': '4096 87380 67108864',
            'net.ipv4.tcp_wmem': '4096 65536 67108864',
            'net.ipv4.tcp_mtu_probing': '1',
            
            '# Scheduler': None,
            'kernel.sched_migration_cost_ns': '5000000',
            'kernel.sched_autogroup_enabled': '0',
        }
        
        with open(sysctl_conf, 'w') as f:
            f.write("# VMware Workstation Performance Optimization\n")
            f.write(f"# Created by tune_system.py on {datetime.now()}\n")
            f.write("# Backup available at: {}\n\n".format(self.backup_dir))
            
            for key, value in sysctl_params.items():
                if value is None:
                    f.write(f"\n{key}\n")
                else:
                    f.write(f"{key} = {value}\n")
        
        # Apply settings
        try:
            result = subprocess.run(['sysctl', '-p', str(sysctl_conf)], capture_output=True, text=True)
            if result.returncode == 0:
                self.console.print("  [green]✓[/green] Kernel parameters optimized")
                self.changes_made.append("Kernel parameters (sysctl) tuned")
                return True
            else:
                # Try to apply individual settings
                self.console.print("  [yellow]⚠[/yellow] Some kernel parameters couldn't be applied")
                success_count = 0
                with open(sysctl_conf, 'r') as f:
                    for line in f:
                        line = line.strip()
                        if line and not line.startswith('#') and '=' in line:
                            key, value = line.split('=', 1)
                            key = key.strip()
                            value = value.strip()
                            try:
                                subprocess.run(['sysctl', '-w', f'{key}={value}'], 
                                             check=True, capture_output=True)
                                success_count += 1
                            except:
                                pass  # Skip parameters that fail
                
                if success_count > 0:
                    self.console.print(f"  [green]✓[/green] Applied {success_count} kernel parameters successfully")
                    self.changes_made.append("Kernel parameters (sysctl) partially tuned")
                    return True
                else:
                    self.console.print("  [red]✗[/red] No kernel parameters could be applied")
                    return False
        except Exception as e:
            self.console.print(f"  [red]✗ Failed to apply sysctl settings: {e}[/red]")
            return False
    
    def optimize_cpu_governor(self) -> bool:
        """Set CPU governor to performance"""
        self.console.print()
        self.console.print("[cyan]Setting CPU governor to performance mode...[/cyan]")
        
        # Check if cpufreq is available
        cpu0_governor = Path('/sys/devices/system/cpu/cpu0/cpufreq/scaling_governor')
        if not cpu0_governor.exists():
            self.console.print("  [yellow]CPU frequency scaling not available[/yellow]")
            return False
        
        # Set all CPUs to performance
        cpu_count = self.hw_info['cpu_count']
        success_count = 0
        
        for cpu_id in range(cpu_count):
            governor_file = Path(f'/sys/devices/system/cpu/cpu{cpu_id}/cpufreq/scaling_governor')
            if governor_file.exists():
                try:
                    with open(governor_file, 'w') as f:
                        f.write('performance')
                    success_count += 1
                except Exception:
                    pass
        
        if success_count > 0:
            self.console.print(f"  [green]✓[/green] Set {success_count}/{cpu_count} CPUs to performance mode")
            
            # Make it permanent using cpupower or systemd
            systemd_service = """[Unit]
Description=Set CPU governor to performance
After=multi-user.target

[Service]
Type=oneshot
ExecStart=/bin/sh -c 'echo performance | tee /sys/devices/system/cpu/cpu*/cpufreq/scaling_governor'
RemainAfterExit=yes

[Install]
WantedBy=multi-user.target
"""
            
            service_file = Path('/etc/systemd/system/vmware-cpu-performance.service')
            with open(service_file, 'w') as f:
                f.write(systemd_service)
            
            # Enable service
            try:
                subprocess.run(['systemctl', 'enable', 'vmware-cpu-performance.service'], 
                             check=True, capture_output=True)
                self.console.print("  [green]✓[/green] CPU performance mode will persist across reboots")
            except Exception:
                pass
            
            self.changes_made.append("CPU governor set to performance mode")
            return True
        
        return False
    
    def optimize_io_scheduler(self) -> bool:
        """Optimize I/O scheduler for NVMe/SSD"""
        if not self.hw_info['has_nvme']:
            return False
        
        self.console.print()
        self.console.print("[cyan]Optimizing I/O scheduler for NVMe devices...[/cyan]")
        
        # Create udev rule to set scheduler to 'none' for NVMe
        udev_rule = """# VMware optimization: Set scheduler to none for NVMe devices
ACTION=="add|change", KERNEL=="nvme[0-9]n[0-9]", ATTR{queue/scheduler}="none"
"""
        
        udev_file = Path('/etc/udev/rules.d/60-vmware-nvme-scheduler.rules')
        self.backup_file(udev_file)
        
        with open(udev_file, 'w') as f:
            f.write(udev_rule)
        
        # Apply immediately
        for nvme_dev in self.hw_info['nvme_devices']:
            scheduler_file = Path(f'/sys/block/{nvme_dev}/queue/scheduler')
            if scheduler_file.exists():
                try:
                    with open(scheduler_file, 'w') as f:
                        f.write('none')
                    self.console.print(f"  [green]✓[/green] Set {nvme_dev} scheduler to 'none'")
                except Exception:
                    pass
        
        # Reload udev rules
        try:
            subprocess.run(['udevadm', 'control', '--reload-rules'], check=True, capture_output=True)
            subprocess.run(['udevadm', 'trigger'], check=True, capture_output=True)
        except Exception:
            pass
        
        self.changes_made.append("I/O scheduler optimized for NVMe")
        return True
    
    def install_packages(self) -> bool:
        """Install performance-related packages"""
        self.console.print()
        self.console.print("[cyan]Installing performance packages...[/cyan]")
        
        packages = []
        install_cmd = []
        
        if self.distro_info['family'] in ['debian', 'ubuntu']:
            packages = ['cpufrequtils', 'linux-tools-generic', 'tuned']
            install_cmd = ['apt', 'install', '-y'] + packages
        elif self.distro_info['family'] in ['rhel', 'fedora']:
            packages = ['kernel-tools', 'tuned']
            install_cmd = ['dnf', 'install', '-y'] + packages
        elif self.distro_info['family'] == 'arch':
            packages = ['cpupower', 'tuned']
            install_cmd = ['pacman', '-S', '--noconfirm'] + packages
        else:
            self.console.print("  [yellow]Package installation not supported for this distribution[/yellow]")
            return False
        
        try:
            self.console.print(f"  Installing: {', '.join(packages)}")
            subprocess.run(install_cmd, check=True, capture_output=True)
            self.console.print("  [green]✓[/green] Performance packages installed")
            self.changes_made.append("Performance packages installed")
            return True
        except subprocess.CalledProcessError:
            self.console.print("  [yellow]Some packages may not have been installed[/yellow]")
            return False
    
    def apply_tuned_profile(self) -> bool:
        """Apply tuned virtual-host profile"""
        self.console.print()
        self.console.print("[cyan]Configuring tuned daemon...[/cyan]")
        
        # Check if tuned is available
        try:
            subprocess.run(['which', 'tuned-adm'], check=True, capture_output=True)
        except subprocess.CalledProcessError:
            self.console.print("  [yellow]tuned not available[/yellow]")
            return False
        
        # Enable and start tuned
        try:
            subprocess.run(['systemctl', 'enable', 'tuned'], check=True, capture_output=True)
            subprocess.run(['systemctl', 'start', 'tuned'], check=True, capture_output=True)
            
            # Set virtual-host profile (optimized for virtualization hosts)
            subprocess.run(['tuned-adm', 'profile', 'virtual-host'], check=True, capture_output=True)
            
            self.console.print("  [green]✓[/green] tuned configured with 'virtual-host' profile")
            self.changes_made.append("tuned daemon configured")
            return True
        except subprocess.CalledProcessError:
            self.console.print("  [yellow]Failed to configure tuned[/yellow]")
            return False
    
    def show_summary(self):
        """Show summary of changes"""
        self.console.print()
        self.console.print(Panel.fit(
            "[bold green]✓ System Optimization Complete![/bold green]",
            border_style=HYPHAED_GREEN
        ))
        self.console.print()
        
        if self.changes_made:
            self.console.print("[bold]Changes Applied:[/bold]")
            for change in self.changes_made:
                self.console.print(f"  • {change}")
            self.console.print()
        
        self.console.print("[bold yellow]⚠ REBOOT REQUIRED[/bold yellow]")
        self.console.print("  Most optimizations (especially GRUB changes) require a reboot to take effect.")
        self.console.print()
        self.console.print("[bold green]Please reboot your system manually to apply all changes.[/bold green]")
        self.console.print("  Command: [cyan]sudo reboot[/cyan]")
        self.console.print()
        
        self.console.print("[bold]Backup Location:[/bold]")
        self.console.print(f"  [cyan]{self.backup_dir}[/cyan]")
        self.console.print()
        
        self.console.print("[dim]To verify changes after reboot:[/dim]")
        self.console.print("  [dim]• Check huge pages: cat /proc/meminfo | grep Huge[/dim]")
        self.console.print("  [dim]• Check IOMMU: dmesg | grep -i iommu[/dim]")
        self.console.print("  [dim]• Check CPU governor: cat /sys/devices/system/cpu/cpu0/cpufreq/scaling_governor[/dim]")
        self.console.print()
    
    def run(self):
        """Main optimization flow"""
        try:
            # Check root
            if os.geteuid() != 0:
                self.console.print("[red]✗ This script must be run as root (use sudo)[/red]")
                return 1
            
            # Welcome
            self.show_banner()
            
            # Show hardware
            self.display_hardware_summary()
            
            # Show planned optimizations
            self.display_optimizations()
            
            # Confirm
            proceed = questionary.confirm(
                "Do you want to proceed with system optimization?",
                default=True,
                style=OPTIMIZER_STYLE,
                qmark="🚀"
            ).ask()
            
            if not proceed:
                self.console.print("[yellow]Optimization cancelled by user.[/yellow]")
                return 0
            
            self.console.print()
            self.console.print("[bold]Starting system optimization...[/bold]")
            
            # Run optimizations
            self.optimize_grub()
            self.optimize_sysctl()
            self.optimize_cpu_governor()
            self.optimize_io_scheduler()
            self.install_packages()
            self.apply_tuned_profile()
            
            # Summary
            self.show_summary()
            
            return 0
            
        except KeyboardInterrupt:
            self.console.print("\n\n[yellow]Optimization cancelled by user.[/yellow]")
            return 1
        except Exception as e:
            self.console.print(f"\n\n[red]Error: {e}[/red]")
            return 1


def main():
    """Entry point"""
    optimizer = SystemOptimizer()
    return optimizer.run()


if __name__ == "__main__":
    sys.exit(main())

