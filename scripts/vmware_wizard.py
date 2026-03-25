#!/usr/bin/env python3
"""
VMware Module Installation Wizard
Interactive terminal UI for hardware detection and module installation
Powered by questionary + rich for reliability and beauty
"""

import os
import sys
import json
import subprocess
import time
import semver
from dataclasses import dataclass, asdict
from typing import List, Dict, Optional
from pathlib import Path

# Import our custom UI library
sys.path.insert(0, str(Path(__file__).parent))
from vmware_ui import VMwareUI


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
        self.ui = VMwareUI()
        self.detected_kernels: List[KernelInfo] = []
        self.selected_kernels: List[KernelInfo] = []
        self.optimization_mode: str = "optimized"
        self.hw_capabilities: Dict = {}
    
    def detect_installed_kernels(self) -> List[KernelInfo]:
        """Detect all installed kernels"""
        kernels = []
        current_kernel = os.uname().release
        
        # Check /lib/modules for installed kernels
        modules_dir = Path("/lib/modules")
        if not modules_dir.exists():
            return kernels
        
        for kernel_dir in sorted(modules_dir.iterdir()):
            if not kernel_dir.is_dir():
                continue
            
            full_version = kernel_dir.name
            
            # Parse version
            try:
                ver = semver.Version.parse(full_version)
                major = int(ver.major)
                minor = int(ver.minor) if len(str(ver.minor)) > 1 else 0
                patch = int(ver.patch) if len(str(ver.patch)) > 2 else 0
                version = f"{major}.{minor}"
            except (ValueError, IndexError):
                print("Semver identification error for: ", full_version)
                continue
            
            # Check if supported (6.16, 6.17, 6.18 or 6.19)
            supported = (major == 6 and minor in [16, 17, 18, 19])
            
            # Check for headers
            headers_path = kernel_dir / "build"
            headers_installed = headers_path.exists() and headers_path.is_dir()
            
            is_current = (full_version == current_kernel)
            
            kernels.append(KernelInfo(
                version=version,
                full_version=full_version,
                major=major,
                minor=minor,
                patch=patch,
                headers_installed=headers_installed,
                headers_path=str(headers_path),
                is_current=is_current,
                supported=supported
            ))
        
        return kernels
    
    def run_hardware_detection(self):
        """Run hardware detection script"""
        script_dir = Path(__file__).parent
        detect_script = script_dir / "detect_hardware.py"
        
        if not detect_script.exists():
            self.ui.show_warning(f"Hardware detection script not found at {detect_script}")
            self.hw_capabilities = {}
            return
        
        try:
            # Run detection script
            result = subprocess.run(
                [sys.executable, str(detect_script)],
                capture_output=True,
                text=True,
                timeout=30
            )
            
            # Read JSON output
            json_files = [
                Path("/tmp/vmware_hw_capabilities.json"),
                Path(f"/tmp/vmware_hw_capabilities_{os.getpid()}.json")
            ]
            
            for json_file in json_files:
                if json_file.exists():
                    with open(json_file, 'r') as f:
                        self.hw_capabilities = json.load(f)
                    break
            
        except Exception as e:
            self.ui.show_warning(f"Hardware detection failed: {e}")
            self.hw_capabilities = {}
    
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
            'offer_system_tuning': True
        }
        
        config_file = Path("/tmp/vmware_wizard_config.json")
        with open(config_file, 'w') as f:
            json.dump(config, f, indent=2)
        
        self.ui.show_success(f"Configuration saved successfully")
    
    def check_and_fix_memory_saturation(self):
        """Check for memory saturation (huge pages) and fix automatically"""
        try:
            # Call the shared Python script
            script_dir = Path(__file__).parent
            memory_checker = script_dir / "check_and_fix_memory.py"
            
            if memory_checker.exists():
                result = subprocess.run(
                    ['sudo', 'python3', str(memory_checker)],
                    capture_output=False,  # Show output directly
                    check=False
                )
                
                if result.returncode == 0:
                    # Memory was fixed
                    time.sleep(2)  # Let user see the message
                # If returncode == 1, no issue found (continue silently)
                # If returncode == 2, error occurred (continue anyway)
                
        except Exception as e:
            # If check fails, continue silently
            pass
    
    def run(self):
        """Main wizard flow"""
        try:
            # Check and fix memory saturation first
            self.check_and_fix_memory_saturation()
            
            # Welcome banner
            self.ui.show_banner(
                "VMware Module Installation Wizard",
                "Automated Kernel Module Compilation for Linux 6.16/6.17/6.18/6.19",
                icon="⚙️"
            )
            
            # Show installation steps
            steps = [
                "Kernel Detection & Selection",
                "Hardware Detection & Analysis",
                "Optimization Mode Selection (Optimized vs Vanilla + IOMMU)",
                "Module Compilation & Installation",
            ]
            self.ui.show_welcome_steps(steps)
            
            # Confirm to start
            if not self.ui.confirm("Ready to start the installation?", default=True):
                self.ui.show_warning("Installation cancelled by user")
                return 1
            
            # STEP 1: Kernel Detection & Selection
            self.ui.show_step(1, 4, "Kernel Detection & Selection")
            
            self.detected_kernels = self.detect_installed_kernels()
            if not self.detected_kernels:
                self.ui.show_error("No kernels detected!")
                return 1
            
            # Filter supported kernels with headers
            supported_kernels = [k for k in self.detected_kernels if k.supported and k.headers_installed]
            
            if not supported_kernels:
                self.ui.show_error("No supported kernels (6.16.x, 6.17.x, 6.18.x or 6.19) with headers found!")
                self.ui.show_info("Please install kernel headers: sudo apt install linux-headers-$(uname -r)")
                return 1
            
            # Show available kernels
            self.ui.show_info(f"Found {len(supported_kernels)} supported kernel(s) with headers")
            
            # Let user select kernel(s)
            kernel_choices = []
            current_kernel_value = None
            
            for kernel in supported_kernels:
                marker = "⭐ " if kernel.is_current else "   "
                label = f"{marker}{kernel.full_version}"
                if kernel.is_current:
                    label += " (current)"
                    current_kernel_value = kernel
                kernel_choices.append((label, kernel))
            
            # Add "all" option
            kernel_choices.append(("All supported kernels with headers", "all"))
            
            selected_kernel = self.ui.select(
                "Which kernel do you want to compile modules for?",
                kernel_choices,
                default=current_kernel_value
            )
            
            if selected_kernel == "all":
                self.selected_kernels = supported_kernels
            else:
                self.selected_kernels = [selected_kernel]
            
            self.ui.show_success(f"Selected {len(self.selected_kernels)} kernel(s) for compilation")
            for k in self.selected_kernels:
                self.ui.show_info(f"  • {k.full_version} (kernel {k.version})")
            
            # STEP 2: Hardware Detection & Analysis
            self.ui.show_step(2, 4, "Hardware Detection & Analysis")
            self.ui.show_info("Analyzing your hardware...")
            
            self.run_hardware_detection()
            
            if self.hw_capabilities:
                self.ui.show_hardware_summary(self.hw_capabilities)
            
            # STEP 3: Optimization Mode Selection
            self.ui.show_step(3, 4, "Optimization Mode Selection")
            
            # Get recommendation
            recommended = self.hw_capabilities.get('optimization', {}).get('recommended_mode', 'optimized')
            opt_score = self.hw_capabilities.get('optimization', {}).get('optimization_score', 50)
            
            # Show comparison
            self.ui.show_comparison_table(
                "🎯 Compilation Mode Comparison",
                optimized_features=[
                    "✓ 30-45% better performance",
                    "✓ CPU-specific optimizations (AVX-512, AVX2, AES-NI)",
                    "✓ Enhanced VT-x/EPT features",
                    "✓ IOMMU auto-configuration (Intel VT-d/AMD-Vi in GRUB)",
                    "✓ Better Wayland integration (~90% success rate)",
                    "✓ Auto-hide toolbar fix included",
                    "✓ Branch prediction hints + cache alignment",
                    "✓ Prefetch optimizations",
                    "⚠ Modules only work on your CPU architecture",
                ],
                vanilla_features=[
                    "• Baseline performance",
                    "• No hardware-specific optimizations",
                    "• Standard VMware compilation",
                    "• No IOMMU auto-configuration",
                    "• Works on any x86_64 CPU",
                    "• Maximum portability",
                    "• Only kernel compatibility patches",
                    "• Standard Wayland support",
                    "✓ Safe for module sharing",
                ]
            )
            
            self.ui.console.print()
            self.ui.console.print(f"[title]💡 Recommendation:[/] [primary]{recommended.upper()}[/] mode (optimization score: {opt_score}/100)")
            self.ui.console.print()
            
            # Let user choose
            mode_choices = [
                ("🚀 Optimized - Faster Performance (30-45% improvement)", "optimized"),
                ("🔒 Vanilla - Maximum Compatibility", "vanilla"),
            ]
            
            default_mode = "optimized" if recommended == "optimized" else "vanilla"
            
            self.optimization_mode = self.ui.select(
                "Which compilation mode do you want to use?",
                mode_choices,
                default=default_mode
            )
            
            self.ui.show_success(f"Selected: {self.optimization_mode.upper()} mode")
            
            # STEP 4: Final Review & Confirmation
            self.ui.show_step(4, 4, "Final Review & Confirmation")
            self.ui.console.print()
            self.ui.show_panel(
                f"[primary]Installation Plan:[/]\n\n"
                f"  • Kernels: {', '.join([k.full_version for k in self.selected_kernels])}\n"
                f"  • Mode: {self.optimization_mode.upper()}\n"
                f"  • Patches: {'All optimizations + VT-x/EPT + IOMMU' if self.optimization_mode == 'optimized' else 'Kernel compatibility only'}\n"
                f"  • IOMMU: {'✓ Automatic (enabled in GRUB)' if self.optimization_mode == 'optimized' else '✗ Not configured'}\n"
                f"  • initramfs: Will be updated after compilation\n",
                title="🚀 Ready to Start"
            )
            
            # Final confirmation
            if not self.ui.confirm("Proceed with installation?", default=True):
                self.ui.show_warning("Installation cancelled by user")
                return 1
            
            # Export configuration including tuning decision
            config = {
                'selected_kernels': [{
                    'full_version': k.full_version,
                    'version': k.version,
                    'major': k.major,
                    'minor': k.minor,
                    'patch': k.patch,
                    'is_current': k.is_current
                } for k in self.selected_kernels],
                'optimization_mode': self.optimization_mode,
                'hw_capabilities': self.hw_capabilities,
                'timestamp': time.time(),
                'auto_configure_iommu': (self.optimization_mode == 'optimized'),  # IOMMU is part of optimized mode
            }
            
            config_file = Path("/tmp/vmware_wizard_config.json")
            with open(config_file, 'w') as f:
                json.dump(config, f, indent=2)
            
            self.ui.console.print()
            self.ui.show_success("Configuration saved successfully!")
            self.ui.console.print()
            self.ui.show_info("📋 Next steps: Compilation → IOMMU configuration → initramfs update → Done!")
            
            return 0
            
        except KeyboardInterrupt:
            self.ui.console.print()
            self.ui.show_warning("Installation cancelled by user (Ctrl+C)")
            return 1
        except Exception as e:
            self.ui.console.print()
            self.ui.show_error(f"An error occurred: {str(e)}")
            import traceback
            traceback.print_exc()
            return 1


def main():
    """Entry point"""
    # Check if running as root
    if os.geteuid() != 0:
        print("✗ This script must be run as root (use sudo)")
        return 1
    
    wizard = VMwareWizard()
    return wizard.run()


if __name__ == "__main__":
    sys.exit(main())
