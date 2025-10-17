#!/usr/bin/env python3
"""
Quick test to verify questionary + rich UI works
"""

import sys
from pathlib import Path

# Add current directory
sys.path.insert(0, str(Path(__file__).parent))

from vmware_ui import VMwareUI

def main():
    ui = VMwareUI()
    
    # Test banner
    ui.show_banner(
        "VMware Module Installation Wizard",
        "Testing questionary + rich UI",
        icon="🧪"
    )
    
    # Test steps
    steps = [
        "Kernel Selection",
        "Optimization Mode",
        "Compilation",
    ]
    ui.show_welcome_steps(steps)
    
    # Test confirmation
    if not ui.confirm("Do you want to continue with the test?", default=True):
        ui.show_warning("Test cancelled")
        return 1
    
    # Test selection
    ui.show_step(1, 3, "Kernel Selection Test")
    
    kernel_choices = [
        ("⭐ 6.17.0-5-generic (current)", "6.17.0-5"),
        ("6.17.0-4-generic", "6.17.0-4"),
        ("All kernels", "all"),
    ]
    
    selected = ui.select(
        "Which kernel do you want to test?",
        kernel_choices,
        default="6.17.0-5"
    )
    
    ui.show_success(f"You selected: {selected}")
    
    # Test comparison table
    ui.show_step(2, 3, "Optimization Mode Test")
    
    ui.show_comparison_table(
        "Mode Comparison",
        optimized_features=[
            "✓ 30-45% faster",
            "✓ CPU optimizations",
            "⚠ CPU-specific",
        ],
        vanilla_features=[
            "• Baseline performance",
            "• Generic build",
            "✓ Portable",
        ]
    )
    
    mode_choices = [
        ("🚀 Optimized", "optimized"),
        ("🔒 Vanilla", "vanilla"),
    ]
    
    mode = ui.select(
        "Which mode do you want?",
        mode_choices,
        default="optimized"
    )
    
    ui.show_success(f"You selected: {mode.upper()} mode")
    
    # Test panel
    ui.show_panel(
        f"Test Summary:\n\n  • Kernel: {selected}\n  • Mode: {mode}\n  • Status: All tests passed!",
        title="✓ Test Complete"
    )
    
    ui.console.print()
    ui.show_success("All UI tests passed! Questionary + Rich are working perfectly.")
    
    return 0

if __name__ == "__main__":
    sys.exit(main())

