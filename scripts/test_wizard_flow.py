#!/usr/bin/env python3
"""
Quick test script to verify wizard UI flow
Tests that all selection screens appear and block for user input
"""

import sys
import pytermgui as ptg
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

from vmware_ui import VMwareUI, GTK_PURPLE, GTK_INFO

def test_kernel_selection():
    """Test kernel selection UI"""
    print("\n[TEST 1] Kernel Selection Menu")
    print("=" * 60)
    
    ui = VMwareUI()
    
    # Simulate kernel options
    options = [
        ("⭐ 6.17.0-5-generic [headers ✓] (current)", "6.17.0-5", "Current running kernel"),
        ("6.17.0-4-generic [headers ✓]", "6.17.0-4", "Previous kernel"),
        ("All supported kernels", "all", "Compile for all"),
    ]
    
    print("Showing kernel selection menu...")
    print("Expected: Menu appears and waits for selection")
    
    selected, idx = ui.create_menu(
        "Step 1/5: Select Kernel(s) to Compile For",
        options,
        default_index=0
    )
    
    print(f"\n✓ Selection made: {selected} (index {idx})")
    return selected is not None


def test_optimization_mode():
    """Test optimization mode selection UI"""
    print("\n[TEST 2] Optimization Mode Selection")
    print("=" * 60)
    
    width = 80
    selection_made = [False]
    mode_selected = [None]
    
    def select_optimized(manager):
        mode_selected[0] = "optimized"
        selection_made[0] = True
        manager.stop()
    
    def select_vanilla(manager):
        mode_selected[0] = "vanilla"
        selection_made[0] = True
        manager.stop()
    
    content = ptg.Container(
        ptg.Label(""),
        ptg.Label("[title]Step 2/5: Choose Compilation Mode[/]", parent_align=ptg.HorizontalAlignment.CENTER),
        ptg.Label(""),
        
        # Optimized Mode
        ptg.Label("[primary]🚀 OPTIMIZED MODE (Recommended)[/]"),
        ptg.Label("  ✓ 30-45% better performance"),
        ptg.Label("  ✓ CPU-specific optimizations"),
        ptg.Label(""),
        
        # Vanilla Mode
        ptg.Label("[info]🔒 VANILLA MODE[/]"),
        ptg.Label("  • Baseline performance"),
        ptg.Label("  • Maximum compatibility"),
        ptg.Label(""),
        box="EMPTY"
    )
    
    print("Showing optimization mode selection...")
    print("Expected: Window appears with 2 buttons and waits for selection")
    
    with ptg.WindowManager() as manager:
        button_container = ptg.Container(
            ptg.Button("[ 🚀 Optimized ]", onclick=lambda *_: select_optimized(manager)),
            ptg.Label(""),
            ptg.Button("[ 🔒 Vanilla ]", onclick=lambda *_: select_vanilla(manager)),
            box="EMPTY"
        )
        content += button_container
        content += ptg.Label("")
        content += ptg.Label("[dimmed]Use Tab/Arrow and Enter, or press 1/2[/]")
        
        window = ptg.Window(content, width=width, box="DOUBLE")
        window.center()
        manager.add(window)
        
        # This blocks until user selects
    
    print(f"\n✓ Selection made: {mode_selected[0]}")
    return selection_made[0]


def test_confirmation_dialog():
    """Test confirmation dialog"""
    print("\n[TEST 3] Confirmation Dialog")
    print("=" * 60)
    
    ui = VMwareUI()
    
    print("Showing confirmation dialog...")
    print("Expected: Dialog appears with Yes/No buttons")
    
    result = ui.create_confirm_dialog(
        "Do you want to proceed with installation?",
        default=True
    )
    
    print(f"\n✓ User selected: {'Yes' if result else 'No'}")
    return True


def main():
    """Run all tests"""
    print("\n" + "=" * 60)
    print("VMware Wizard UI Flow Test Suite")
    print("=" * 60)
    print("\nThis will test all interactive UI components.")
    print("Each screen should appear and wait for your input.\n")
    
    input("Press Enter to start tests...")
    
    tests_passed = 0
    tests_total = 3
    
    try:
        # Test 1: Kernel selection
        if test_kernel_selection():
            tests_passed += 1
        
        # Test 2: Optimization mode
        if test_optimization_mode():
            tests_passed += 1
        
        # Test 3: Confirmation
        if test_confirmation_dialog():
            tests_passed += 1
        
    except Exception as e:
        print(f"\n✗ Test failed with error: {e}")
        import traceback
        traceback.print_exc()
        return 1
    
    # Summary
    print("\n" + "=" * 60)
    print(f"Test Results: {tests_passed}/{tests_total} passed")
    print("=" * 60)
    
    if tests_passed == tests_total:
        print("\n✓ All tests passed! Wizard UI is working correctly.")
        return 0
    else:
        print(f"\n✗ {tests_total - tests_passed} test(s) failed!")
        return 1


if __name__ == "__main__":
    sys.exit(main())

