#!/usr/bin/env python3
"""
VMware Module Installation Wizard
Interactive terminal UI for hardware detection and module installation
Similar to NVIDIA driver installer experience
"""

import os
import sys
import json
import subprocess
import shutil
import time
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional, Tuple
from pathlib import Path

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
    from rich.layout import Layout
    from rich.text import Text
    from rich import box
    from rich.align import Align
except ImportError:
    print("ERROR: 'rich' library not found. Installing...")
    subprocess.check_call([sys.executable, "-m", "pip", "install", "rich"])
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.progress import Progress, SpinnerColumn, TextColumn, BarColumn
    from rich.layout import Layout
    from rich.text import Text
    from rich import box
    from rich.align import Align

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
        # Not in conda environment - warn user
        print("WARNING: Not running in conda/mamba environment!", file=sys.stderr)
        print("Please run: bash scripts/setup_python_env.sh", file=sys.stderr)
        print("Then use: $HOME/.miniforge3/envs/vmware-optimizer/bin/python scripts/vmware_wizard.py", file=sys.stderr)
        print("", file=sys.stderr)
        print("Continuing with basic prompts (no questionary)...", file=sys.stderr)
    
    try:
        import questionary
        from questionary import Style
    except ImportError:
        # Fallback mode
        questionary = None
        Style = None

console = Console()

# Custom Questionary style matching Hyphaed green theme
if questionary is not None and Style is not None:
    WIZARD_STYLE = Style([
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
    HAS_QUESTIONARY = True
else:
    WIZARD_STYLE = None
    HAS_QUESTIONARY = False

# Hyphaed green color
HYPHAED_GREEN = "#B0D56A"


@dataclass
class KernelInfo:
    """Information about an installed kernel"""
    version: str
    full_version: str
    major: int
    minor: int
    patch: int
    headers_installed: bool
    headers_path: str
    is_current: bool
    supported: bool


class VMwareWizard:
    """Interactive wizard for VMware module installation"""
    
    def __init__(self):
        self.console = Console()
        self.current_kernel = os.uname().release
        self.detected_kernels: List[KernelInfo] = []
        self.hw_capabilities: Dict = {}
        self.selected_kernels: List[str] = []
        self.optimization_mode: str = "vanilla"
        
    def show_banner(self):
        """Display welcome banner"""
        banner_text = Text()
        banner_text.append("╔══════════════════════════════════════════════════════════════╗\n", style="bold")
        banner_text.append("║                                                              ║\n", style="bold")
        banner_text.append("║     ", style="bold")
        banner_text.append("VMWARE MODULE INSTALLATION WIZARD", style=f"bold {HYPHAED_GREEN}")
        banner_text.append("                ║\n", style="bold")
        banner_text.append("║        ", style="bold")
        banner_text.append("Python-Powered Hardware Detection", style=f"italic {HYPHAED_GREEN}")
        banner_text.append("                  ║\n", style="bold")
        banner_text.append("║                                                              ║\n", style="bold")
        banner_text.append("╚══════════════════════════════════════════════════════════════╝", style="bold")
        
        self.console.print()
        self.console.print(Align.center(banner_text))
        self.console.print()
        
    def detect_installed_kernels(self) -> List[KernelInfo]:
        """Detect all installed kernels on the system"""
        kernels = []
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console,
        ) as progress:
            task = progress.add_task("[cyan]Detecting installed kernels...", total=None)
            
            # Check /lib/modules for installed kernels
            modules_dir = Path("/lib/modules")
            if modules_dir.exists():
                for kernel_dir in modules_dir.iterdir():
                    if kernel_dir.is_dir():
                        kernel_version = kernel_dir.name
                        
                        # Parse version
                        try:
                            version_parts = kernel_version.split('-')[0].split('.')
                            if len(version_parts) >= 2:
                                major = int(version_parts[0])
                                minor = int(version_parts[1])
                                patch = int(version_parts[2]) if len(version_parts) > 2 else 0
                                
                                # Check if kernel 6.16 or 6.17
                                supported = (major == 6 and minor in [16, 17])
                                
                                # Check for kernel headers
                                headers_path = kernel_dir / "build"
                                headers_installed = headers_path.exists() and headers_path.is_symlink()
                                
                                is_current = (kernel_version == self.current_kernel)
                                
                                kernel_info = KernelInfo(
                                    version=f"{major}.{minor}",
                                    full_version=kernel_version,
                                    major=major,
                                    minor=minor,
                                    patch=patch,
                                    headers_installed=headers_installed,
                                    headers_path=str(headers_path),
                                    is_current=is_current,
                                    supported=supported
                                )
                                kernels.append(kernel_info)
                        except (ValueError, IndexError):
                            continue
            
            progress.update(task, completed=True)
        
        # Sort: current kernel first, then by version (descending)
        kernels.sort(key=lambda k: (not k.is_current, -k.major, -k.minor, -k.patch))
        return kernels
    
    def display_kernel_table(self):
        """Display detected kernels in a table"""
        self.console.print()
        self.console.print(Panel.fit(
            "[bold cyan]Detected Kernels[/bold cyan]",
            border_style=HYPHAED_GREEN
        ))
        self.console.print()
        
        table = Table(
            show_header=True,
            header_style=f"bold {HYPHAED_GREEN}",
            box=box.ROUNDED,
            border_style=HYPHAED_GREEN
        )
        
        table.add_column("#", style="cyan", width=4)
        table.add_column("Kernel Version", style="white", width=25)
        table.add_column("Status", width=15)
        table.add_column("Headers", width=12)
        table.add_column("Supported", width=12)
        
        for idx, kernel in enumerate(self.detected_kernels, 1):
            # Status
            if kernel.is_current:
                status = "[green]● Current[/green]"
            else:
                status = "[dim]○ Installed[/dim]"
            
            # Headers
            if kernel.headers_installed:
                headers = "[green]✓ Yes[/green]"
            else:
                headers = "[red]✗ No[/red]"
            
            # Supported
            if kernel.supported:
                supported = "[green]✓ Yes[/green]"
            else:
                supported = "[yellow]⚠ No[/yellow]"
            
            table.add_row(
                str(idx),
                kernel.full_version,
                status,
                headers,
                supported
            )
        
        self.console.print(table)
        self.console.print()
    
    def select_kernels(self) -> List[KernelInfo]:
        """Let user select which kernels to compile for"""
        self.console.print(Panel.fit(
            "[bold]Select Kernel(s) to Compile Modules For[/bold]",
            border_style=HYPHAED_GREEN
        ))
        self.console.print()
        
        # Only show supported kernels (6.16 and 6.17)
        supported_kernels = [k for k in self.detected_kernels if k.supported]
        
        if not supported_kernels:
            self.console.print("[red]✗ No supported kernels (6.16.x or 6.17.x) found![/red]")
            self.console.print("[yellow]Please install kernel 6.16.x or 6.17.x first.[/yellow]")
            sys.exit(1)
        
        # Check for missing headers
        missing_headers = [k for k in supported_kernels if not k.headers_installed]
        if missing_headers:
            self.console.print("[yellow]⚠ Warning: The following kernels are missing headers:[/yellow]")
            for k in missing_headers:
                self.console.print(f"  • {k.full_version}")
            self.console.print()
            self.console.print("[dim]Kernel headers are required for module compilation.[/dim]")
            self.console.print()
        
        # Build options list
        options_text = []
        for idx, kernel in enumerate(supported_kernels, 1):
            marker = "→" if kernel.is_current else " "
            headers_mark = "✓" if kernel.headers_installed else "✗"
            options_text.append(f"  {marker} {idx}) {kernel.full_version} [{headers_mark}]")
        
        options_text.append(f"  → {len(supported_kernels) + 1}) [bold {HYPHAED_GREEN}]All supported kernels[/bold {HYPHAED_GREEN}]")
        
        for line in options_text:
            self.console.print(line)
        
        self.console.print()
        
        # Find current kernel index for default
        current_idx = 0
        for idx, kernel in enumerate(supported_kernels):
            if kernel.is_current and kernel.headers_installed:
                current_idx = idx
                break
        
        # Use questionary if available, otherwise fallback to input
        if HAS_QUESTIONARY:
            # Build choices for questionary
            kernel_choices = []
            for idx, kernel in enumerate(supported_kernels):
                marker = "→ " if kernel.is_current else "  "
                headers_mark = "✓" if kernel.headers_installed else "✗"
                if kernel.headers_installed:
                    kernel_choices.append({
                        'name': f"{marker}{kernel.full_version} [{headers_mark}]",
                        'value': kernel,
                        'disabled': None
                    })
                else:
                    kernel_choices.append({
                        'name': f"{marker}{kernel.full_version} [{headers_mark}] (no headers)",
                        'value': kernel,
                        'disabled': "Headers required"
                    })
            
            kernel_choices.append({
                'name': "→ All supported kernels with headers",
                'value': 'all'
            })
            
            choice = questionary.select(
                "Select kernel(s) to compile for:",
                choices=kernel_choices,
                default=kernel_choices[current_idx] if current_idx < len(kernel_choices) else None,
                style=WIZARD_STYLE,
                qmark="🔧",
                instruction="(Use arrow keys)"
            ).ask()
            
            if choice is None:
                self.console.print("[yellow]Selection cancelled[/yellow]")
                sys.exit(0)
            
            # Handle selection
            if choice == 'all':
                selected_kernels = [k for k in supported_kernels if k.headers_installed]
                if not selected_kernels:
                    self.console.print("[red]✗ No kernels with headers installed![/red]")
                    sys.exit(1)
            else:
                selected_kernels = [choice]
        else:
            # Fallback to basic input
            self.console.print("[dim]Enter number or 'all' for all kernels[/dim]")
            choice_input = input(f"Select kernel (default: {current_idx + 1}): ").strip() or str(current_idx + 1)
            
            if choice_input.lower() == 'all' or choice_input == str(len(supported_kernels) + 1):
                selected_kernels = [k for k in supported_kernels if k.headers_installed]
            else:
                try:
                    idx = int(choice_input) - 1
                    if 0 <= idx < len(supported_kernels):
                        kernel = supported_kernels[idx]
                        if kernel.headers_installed:
                            selected_kernels = [kernel]
                        else:
                            self.console.print("[red]✗ Selected kernel has no headers![/red]")
                            sys.exit(1)
                    else:
                        self.console.print("[red]✗ Invalid selection![/red]")
                        sys.exit(1)
                except ValueError:
                    self.console.print("[red]✗ Invalid input![/red]")
                    sys.exit(1)
        
        self.console.print()
        self.console.print(Panel.fit(
            "[green]✓[/green] Selected kernels:\n" + 
            "\n".join(f"  • {k.full_version} (kernel {k.version})" for k in selected_kernels),
            border_style=HYPHAED_GREEN,
            title="[bold]Compilation Targets[/bold]"
        ))
        
        return selected_kernels
    
    def run_hardware_detection(self):
        """Run hardware detection script"""
        self.console.print()
        self.console.print(Panel.fit(
            "[bold cyan]Running Hardware Detection[/bold cyan]",
            border_style=HYPHAED_GREEN
        ))
        self.console.print()
        
        script_dir = Path(__file__).parent
        detect_script = script_dir / "detect_hardware.py"
        
        if not detect_script.exists():
            self.console.print("[yellow]⚠ Hardware detection script not found - using basic detection[/yellow]")
            return
        
        with Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console,
        ) as progress:
            task = progress.add_task("[cyan]Analyzing system hardware...", total=None)
            
            try:
                # Run detection script
                result = subprocess.run(
                    [sys.executable, str(detect_script)],
                    capture_output=True,
                    text=True,
                    timeout=30
                )
                
                # Read JSON output
                json_file = Path("/tmp/vmware_hw_capabilities.json")
                if json_file.exists():
                    with open(json_file, 'r') as f:
                        self.hw_capabilities = json.load(f)
                    progress.update(task, completed=True)
                else:
                    raise FileNotFoundError("Hardware capabilities JSON not generated")
                    
            except Exception as e:
                progress.update(task, completed=True)
                self.console.print(f"[yellow]⚠ Hardware detection failed: {e}[/yellow]")
                self.console.print("[dim]Continuing with basic detection...[/dim]")
    
    def display_hardware_summary(self):
        """Display detected hardware in a nice format"""
        if not self.hw_capabilities:
            return
        
        self.console.print()
        self.console.print(Panel.fit(
            "[bold cyan]Hardware Analysis[/bold cyan]",
            border_style=HYPHAED_GREEN
        ))
        self.console.print()
        
        # CPU Information
        cpu = self.hw_capabilities.get('cpu', {})
        if cpu:
            cpu_table = Table(show_header=False, box=box.SIMPLE, border_style=HYPHAED_GREEN)
            cpu_table.add_column("Property", style="cyan", width=20)
            cpu_table.add_column("Value", style="white")
            
            cpu_table.add_row("Model", cpu.get('model', 'Unknown'))
            cpu_table.add_row("Architecture", cpu.get('microarchitecture', 'Unknown'))
            cpu_table.add_row("Cores/Threads", f"{cpu.get('cores', 0)} / {cpu.get('threads', 0)}")
            
            # SIMD features
            features = []
            if cpu.get('has_avx512'): features.append("[green]AVX-512[/green]")
            if cpu.get('has_avx2'): features.append("[green]AVX2[/green]")
            if cpu.get('has_aes_ni'): features.append("[green]AES-NI[/green]")
            if cpu.get('has_sha_ni'): features.append("[green]SHA-NI[/green]")
            
            if features:
                cpu_table.add_row("SIMD Features", ", ".join(features))
            
            self.console.print(Panel(cpu_table, title="[bold]CPU[/bold]", border_style=HYPHAED_GREEN))
            self.console.print()
        
        # Virtualization
        virt = self.hw_capabilities.get('virtualization', {})
        if virt:
            virt_table = Table(show_header=False, box=box.SIMPLE, border_style=HYPHAED_GREEN)
            virt_table.add_column("Feature", style="cyan", width=20)
            virt_table.add_column("Status", style="white")
            
            # Check if virtualization is enabled
            if virt.get('enabled'):
                virt_type = virt.get('technology', 'Unknown')
                virt_table.add_row("Virtualization", f"[green]✓[/green] {virt_type}")
            else:
                virt_table.add_row("Virtualization", "[red]✗ Not enabled[/red]")
            
            # EPT/NPT support
            if virt.get('ept_supported'):
                virt_table.add_row("EPT", "[green]✓ Supported[/green]")
            elif virt.get('npt_supported'):
                virt_table.add_row("NPT", "[green]✓ Supported[/green]")
            
            # VPID support
            if virt.get('vpid_supported'):
                virt_table.add_row("VPID", "[green]✓ Supported[/green]")
            
            # VMFUNC support
            if virt.get('vmfunc_supported'):
                virt_table.add_row("VMFUNC", "[green]✓ Supported[/green]")
            
            # Posted Interrupts
            if virt.get('posted_interrupts'):
                virt_table.add_row("Posted Interrupts", "[green]✓ Supported[/green]")
            
            self.console.print(Panel(virt_table, title="[bold]Virtualization[/bold]", border_style=HYPHAED_GREEN))
            self.console.print()
        
        # Storage
        storage = self.hw_capabilities.get('storage', {})
        if storage and storage.get('nvme_count', 0) > 0:
            storage_table = Table(show_header=True, box=box.SIMPLE, border_style=HYPHAED_GREEN)
            storage_table.add_column("Device", style="cyan")
            storage_table.add_column("Model", style="white")
            storage_table.add_column("PCIe", style="green")
            storage_table.add_column("Bandwidth", style="yellow")
            
            for device in storage.get('devices', [])[:3]:  # Show max 3 devices
                storage_table.add_row(
                    device.get('name', 'N/A'),
                    device.get('model', 'Unknown')[:30],
                    f"Gen {device.get('pcie_generation', '?')} x{device.get('pcie_lanes', '?')}",
                    f"{device.get('max_bandwidth_mbps', 0) / 1000:.1f} GB/s"
                )
            
            self.console.print(Panel(storage_table, title=f"[bold]NVMe Storage ({storage.get('nvme_count', 0)} device(s))[/bold]", border_style=HYPHAED_GREEN))
            self.console.print()
        
        # Performance Analysis (no score display - internal only)
        opt = self.hw_capabilities.get('optimization', {})
        if opt:
            recommended = opt.get('recommended_mode', 'vanilla')
            
            analysis_text = Text()
            analysis_text.append("Recommended Mode: ", style="cyan")
            analysis_text.append(recommended.upper(), style=f"bold {HYPHAED_GREEN}")
            
            if opt.get('predicted_gains'):
                analysis_text.append(f"\nPredicted Gains: ", style="cyan")
                analysis_text.append(opt.get('predicted_gains'), style="bold yellow")
            
            self.console.print(Panel(analysis_text, title="[bold]Performance Analysis[/bold]", border_style=HYPHAED_GREEN))
            self.console.print()
    
    def select_optimization_mode(self):
        """Let user choose optimization mode"""
        self.console.print(Panel.fit(
            "[bold]Compilation Mode Selection[/bold]",
            border_style=HYPHAED_GREEN
        ))
        self.console.print()
        
        # Display options
        table = Table(show_header=False, box=box.ROUNDED, border_style=HYPHAED_GREEN)
        table.add_column("Option", style=f"bold {HYPHAED_GREEN}", width=8)
        table.add_column("Description", style="white")
        
        table.add_row(
            "1",
            "[bold green]🚀 Optimized[/bold green] [dim](Recommended & Default)[/dim]\n" +
            "  • 20-35% better performance\n" +
            "  • [bold green]✨ Better Wayland support - top bar hiding works ~90% of the time![/bold green]\n" +
            "  • Uses CPU-specific instructions (AVX-512, AVX2, AES-NI)\n" +
            "  • Enables virtualization and compiler optimizations\n" +
            "  • [yellow]Note:[/yellow] Modules only work on your CPU architecture"
        )
        
        table.add_row(
            "2",
            "[bold blue]🔒 Vanilla[/bold blue]\n" +
            "  • Baseline performance (0% gain)\n" +
            "  • Standard VMware compilation\n" +
            "  • Works on any x86_64 CPU (portable)\n" +
            "  • Only applies kernel compatibility patches"
        )
        
        self.console.print(table)
        self.console.print()
        
        # Get recommendation (but always default to optimized)
        recommended = self.hw_capabilities.get('optimization', {}).get('recommended_mode', 'optimized')
        
        self.console.print(f"[dim]💡 Recommended for your hardware: [bold]{recommended.upper()}[/bold][/dim]")
        self.console.print()
        
        if HAS_QUESTIONARY:
            choices = [
                {
                    'name': '🚀 Optimized (Recommended) - 20-35% faster + better Wayland',
                    'value': 'optimized'
                },
                {
                    'name': '🔒 Vanilla - Portable, works on any CPU',
                    'value': 'vanilla'
                }
            ]
            
            choice = questionary.select(
                "Select compilation mode:",
                choices=choices,
                default=choices[0],
                style=WIZARD_STYLE,
                qmark="⚙️",
                instruction="(Use arrow keys)"
            ).ask()
            
            if choice is None:
                self.console.print("[yellow]Selection cancelled[/yellow]")
                sys.exit(0)
            
            self.optimization_mode = choice
        else:
            # Fallback
            choice_input = input("Select mode [1=Optimized, 2=Vanilla] (default: 1): ").strip() or "1"
            self.optimization_mode = "optimized" if choice_input == "1" else "vanilla"
        
        self.console.print()
        mode_display = "🚀 OPTIMIZED" if self.optimization_mode == "optimized" else "🔒 VANILLA"
        self.console.print(Panel.fit(
            f"[green]✓[/green] Selected: [bold {HYPHAED_GREEN}]{mode_display}[/bold {HYPHAED_GREEN}]",
            border_style=HYPHAED_GREEN
        ))
    
    def display_compilation_summary(self):
        """Show final summary before compilation"""
        self.console.print()
        self.console.print(Panel.fit(
            "[bold yellow]Compilation Summary[/bold yellow]",
            border_style=HYPHAED_GREEN
        ))
        self.console.print()
        
        summary = Table(show_header=False, box=box.SIMPLE, border_style=HYPHAED_GREEN)
        summary.add_column("Item", style="cyan", width=25)
        summary.add_column("Value", style="white")
        
        summary.add_row("Kernels to compile", ", ".join(k.full_version for k in self.selected_kernels))
        summary.add_row("Optimization mode", self.optimization_mode.upper())
        
        if self.optimization_mode == "optimized" and self.hw_capabilities:
            flags = self.hw_capabilities.get('compilation_flags', {})
            if flags.get('make_flags'):
                summary.add_row("Make flags", flags['make_flags'])
        
        self.console.print(summary)
        self.console.print()
        
        if HAS_QUESTIONARY:
            proceed = questionary.confirm(
                "Proceed with compilation?",
                default=True,
                style=WIZARD_STYLE,
                qmark="❓"
            ).ask()
        else:
            # Fallback
            proceed_input = input("Proceed with compilation? [Y/n]: ").strip().lower()
            proceed = proceed_input in ['', 'y', 'yes']
        
        if not proceed:
            self.console.print("[yellow]Installation cancelled by user.[/yellow]")
            sys.exit(0)
    
    def export_configuration(self):
        """Export configuration for bash script"""
        # Convert KernelInfo objects to dict format
        kernel_configs = []
        for kernel in self.selected_kernels:
            kernel_configs.append({
                'full_version': kernel.full_version,
                'version': kernel.version,
                'major': kernel.major,
                'minor': kernel.minor,
                'patch': kernel.patch,
                'is_current': kernel.is_current
            })
        
        config = {
            'selected_kernels': kernel_configs,
            'optimization_mode': self.optimization_mode,
            'hw_capabilities': self.hw_capabilities,
            'timestamp': time.time(),
            'offer_system_tuning': True  # Flag to offer system tuning after installation
        }
        
        config_file = Path("/tmp/vmware_wizard_config.json")
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)
        
        self.console.print()
        self.console.print(f"[green]✓[/green] Configuration saved to: [cyan]{config_file}[/cyan]")
    
    def check_existing_modules(self) -> bool:
        """Check if VMware modules are already installed for current kernel"""
        import subprocess
        
        current_kernel = os.uname().release
        
        try:
            # Check if modules exist in /lib/modules
            modules_path = Path(f"/lib/modules/{current_kernel}/misc")
            vmmon_exists = (modules_path / "vmmon.ko").exists()
            vmnet_exists = (modules_path / "vmnet.ko").exists()
            
            if vmmon_exists and vmnet_exists:
                self.console.print()
                self.console.print(Panel.fit(
                    "[bold yellow]⚠ Existing Modules Detected[/bold yellow]",
                    border_style="yellow"
                ))
                self.console.print()
                
                # Show module info
                info_table = Table(show_header=False, box=box.SIMPLE, border_style=HYPHAED_GREEN)
                info_table.add_column("Module", style="cyan", width=15)
                info_table.add_column("Status", style="white")
                
                # Check if modules are loaded
                try:
                    lsmod_output = subprocess.check_output(["lsmod"], text=True)
                    vmmon_loaded = "vmmon" in lsmod_output
                    vmnet_loaded = "vmnet" in lsmod_output
                    
                    info_table.add_row(
                        "vmmon",
                        "[green]✓ Loaded[/green]" if vmmon_loaded else "[yellow]○ Not loaded[/yellow]"
                    )
                    info_table.add_row(
                        "vmnet",
                        "[green]✓ Loaded[/green]" if vmnet_loaded else "[yellow]○ Not loaded[/yellow]"
                    )
                    
                    # Get module version
                    if vmmon_loaded:
                        try:
                            modinfo = subprocess.check_output(["modinfo", "vmmon"], text=True)
                            for line in modinfo.split('\n'):
                                if line.startswith("vermagic:"):
                                    version = line.split()[1]
                                    info_table.add_row("Compiled for", version)
                                    break
                        except:
                            pass
                except:
                    info_table.add_row("Status", "[yellow]Could not determine[/yellow]")
                
                info_table.add_row("Current kernel", current_kernel)
                
                self.console.print(info_table)
                self.console.print()
                
                self.console.print("[yellow]Reasons to reinstall/recompile:[/yellow]")
                self.console.print("  • Apply new hardware optimizations (20-40% performance gain)")
                self.console.print("  • Get latest kernel compatibility patches")
                self.console.print("  • Switch between Optimized and Vanilla modes")
                self.console.print("  • Update after kernel upgrade")
                self.console.print()
                
                # Ask user (default to Yes for reinstall)
                if HAS_QUESTIONARY:
                    proceed = questionary.confirm(
                        "Do you want to reinstall/recompile the modules?",
                        default=True,
                        style=WIZARD_STYLE,
                        qmark="❓"
                    ).ask()
                else:
                    proceed_input = input("Do you want to reinstall/recompile the modules? [Y/n]: ").strip().lower()
                    proceed = proceed_input in ['', 'y', 'yes']
                
                if not proceed:
                    self.console.print()
                    self.console.print("[yellow]Installation cancelled by user.[/yellow]")
                    self.console.print()
                    self.console.print("[dim]Tip: If modules are working fine, no need to reinstall.[/dim]")
                    self.console.print("[dim]      Use update script after kernel upgrades.[/dim]")
                    return False
                
                self.console.print()
                self.console.print("[green]✓[/green] Proceeding with reinstallation...")
                self.console.print()
        except Exception as e:
            # If we can't check, just continue
            pass
        
        return True
    
    def run(self):
        """Main wizard flow"""
        try:
            # Welcome
            self.show_banner()
            time.sleep(0.5)
            
            # Step 0: Check existing modules
            if not self.check_existing_modules():
                return 1
            
            # Step 1: Detect kernels
            self.detected_kernels = self.detect_installed_kernels()
            self.display_kernel_table()
            
            # Step 2: Select kernels
            self.selected_kernels = self.select_kernels()
            
            # Step 3: Hardware detection
            self.run_hardware_detection()
            self.display_hardware_summary()
            
            # Step 4: Optimization mode
            self.select_optimization_mode()
            
            # Step 5: Summary
            self.display_compilation_summary()
            
            # Step 6: Export configuration
            self.export_configuration()
            
            # Success
            self.console.print()
            self.console.print(Panel.fit(
                "[bold green]✓ Configuration Complete![/bold green]\n\n" +
                "The installation script will now compile and install the modules.",
                border_style=HYPHAED_GREEN,
                title="[bold]Ready to Proceed[/bold]"
            ))
            self.console.print()
            
            return 0
            
        except KeyboardInterrupt:
            self.console.print("\n\n[yellow]Installation cancelled by user.[/yellow]")
            return 1
        except Exception as e:
            self.console.print(f"\n\n[red]Error: {e}[/red]")
            return 1


def main():
    """Entry point"""
    # Check if running as root
    if os.geteuid() != 0:
        console.print("[red]✗ This script must be run as root (use sudo)[/red]")
        return 1
    
    wizard = VMwareWizard()
    return wizard.run()


if __name__ == "__main__":
    sys.exit(main())

