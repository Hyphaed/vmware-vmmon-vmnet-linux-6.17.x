#!/usr/bin/env python3
"""
Test script for PyTermGUI-based VMware UI
Tests all UI components without requiring root access
"""

import sys
from pathlib import Path

# Add scripts directory to path
sys.path.insert(0, str(Path(__file__).parent))

try:
    import pytermgui as ptg
    print("✓ PyTermGUI imported successfully")
except ImportError:
    print("✗ PyTermGUI not found. Installing...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "pytermgui"])
    import pytermgui as ptg
    print("✓ PyTermGUI installed and imported")

from vmware_ui import VMwareUI

def test_banner():
    """Test banner display"""
    print("\n=== Testing Banner ===")
    ui = VMwareUI()
    
    with ptg.WindowManager() as manager:
        window = ptg.Window(
            ui.show_banner("VMWARE UI TEST", "PyTermGUI Framework"),
            ptg.Label(""),
            ptg.Label("[success]Banner component works![/]"),
            ptg.Label(""),
            ptg.Button("Continue", lambda *_: manager.stop()),
            box="DOUBLE"
        )
        window.center()
        manager.add(window)
    
    print("✓ Banner test passed")

def test_messages():
    """Test message types"""
    print("\n=== Testing Messages ===")
    ui = VMwareUI()
    
    with ptg.WindowManager() as manager:
        window = ptg.Window(
            ptg.Label("[title]Message Types Test[/]"),
            ptg.Label(""),
            ui.show_info("This is an info message"),
            ui.show_success("This is a success message"),
            ui.show_warning("This is a warning message"),
            ui.show_error("This is an error message"),
            ptg.Label(""),
            ptg.Button("Continue", lambda *_: manager.stop()),
            box="DOUBLE"
        )
        window.center()
        manager.add(window)
    
    print("✓ Messages test passed")

def test_table():
    """Test table creation"""
    print("\n=== Testing Table ===")
    ui = VMwareUI()
    
    table = ui.create_table(
        title="Sample Data Table",
        headers=["Component", "Status", "Version"],
        rows=[
            ["PyTermGUI", "[success]✓ Working[/]", "7.7.4"],
            ["VMware UI", "[success]✓ Active[/]", "1.0.0"],
            ["Wizard", "[success]✓ Ready[/]", "1.0.0"],
        ]
    )
    
    with ptg.WindowManager() as manager:
        window = ptg.Window(
            table,
            ptg.Label(""),
            ptg.Button("Continue", lambda *_: manager.stop()),
            box="DOUBLE"
        )
        window.center()
        manager.add(window)
    
    print("✓ Table test passed")

def test_menu():
    """Test interactive menu"""
    print("\n=== Testing Menu ===")
    ui = VMwareUI()
    
    options = [
        ("Option 1 - Optimized", "opt1", "Best performance"),
        ("Option 2 - Vanilla", "opt2", "Maximum compatibility"),
        ("Option 3 - Custom", "opt3", "Advanced settings"),
    ]
    
    selected, idx = ui.create_menu("Select a Mode", options, default_index=0)
    
    print(f"✓ Menu test passed - Selected: {selected} (index: {idx})")

def test_confirm_dialog():
    """Test confirmation dialog"""
    print("\n=== Testing Confirm Dialog ===")
    ui = VMwareUI()
    
    result = ui.create_confirm_dialog("Do you want to continue with the tests?", default=True)
    
    print(f"✓ Confirm dialog test passed - Result: {result}")
    
    if not result:
        print("User chose not to continue. Stopping tests.")
        return False
    
    return True

def test_input_dialog():
    """Test input dialog"""
    print("\n=== Testing Input Dialog ===")
    ui = VMwareUI()
    
    result = ui.create_input_dialog("Enter your name", default="Test User")
    
    if result:
        print(f"✓ Input dialog test passed - Input: {result}")
        ui.show_message_box("Input Received", f"You entered: {result}", "success")
    else:
        print("✓ Input dialog test passed - User cancelled")

def test_message_box():
    """Test message box"""
    print("\n=== Testing Message Box ===")
    ui = VMwareUI()
    
    ui.show_message_box(
        "Test Complete",
        "All basic UI components have been tested successfully!",
        "success"
    )
    
    print("✓ Message box test passed")

def test_checklist():
    """Test checklist"""
    print("\n=== Testing Checklist ===")
    ui = VMwareUI()
    
    items = [
        ("Kernel 6.17.0-5-generic", "kernel1", True),
        ("Kernel 6.16.8-generic", "kernel2", True),
        ("Kernel 5.15.0-generic", "kernel3", False),  # Disabled
    ]
    
    selected = ui.create_checklist(
        "Select Kernels to Compile",
        items,
        selected_indices=[0]
    )
    
    print(f"✓ Checklist test passed - Selected: {selected}")

def test_panel():
    """Test panel display"""
    print("\n=== Testing Panel ===")
    ui = VMwareUI()
    
    panel = ui.show_panel(
        "This is content inside a panel.\n" +
        "Panels are great for grouping related information.\n" +
        "[success]✓[/] They support markup too!",
        title="Test Panel"
    )
    
    with ptg.WindowManager() as manager:
        window = ptg.Window(
            panel,
            ptg.Label(""),
            ptg.Button("Continue", lambda *_: manager.stop()),
            box="DOUBLE"
        )
        window.center()
        manager.add(window)
    
    print("✓ Panel test passed")

def test_section():
    """Test section headers"""
    print("\n=== Testing Section Headers ===")
    ui = VMwareUI()
    
    with ptg.WindowManager() as manager:
        window = ptg.Window(
            ui.show_section("Section 1"),
            ptg.Label("Content for section 1"),
            ptg.Label(""),
            ui.show_section("Section 2"),
            ptg.Label("Content for section 2"),
            ptg.Label(""),
            ptg.Button("Continue", lambda *_: manager.stop()),
            box="DOUBLE"
        )
        window.center()
        manager.add(window)
    
    print("✓ Section headers test passed")

def main():
    """Run all tests"""
    print("╔══════════════════════════════════════════════════════════════╗")
    print("║                                                              ║")
    print("║        VMWARE UI PYTERMGUI TEST SUITE                       ║")
    print("║                                                              ║")
    print("╚══════════════════════════════════════════════════════════════╝")
    print()
    
    tests = [
        ("Banner", test_banner),
        ("Messages", test_messages),
        ("Table", test_table),
        ("Panel", test_panel),
        ("Section Headers", test_section),
        ("Menu", test_menu),
        ("Confirm Dialog", test_confirm_dialog),
        ("Input Dialog", test_input_dialog),
        ("Checklist", test_checklist),
        ("Message Box", test_message_box),
    ]
    
    passed = 0
    failed = 0
    
    for name, test_func in tests:
        try:
            result = test_func()
            if result is False:
                print(f"\n[!] Test suite stopped by user")
                break
            passed += 1
        except Exception as e:
            print(f"✗ {name} test failed: {e}")
            failed += 1
    
    print("\n" + "="*60)
    print(f"Test Results: {passed} passed, {failed} failed")
    print("="*60)
    
    if failed == 0:
        print("\n✓ All tests passed! PyTermGUI UI is working correctly.")
        return 0
    else:
        print(f"\n✗ {failed} test(s) failed.")
        return 1

if __name__ == "__main__":
    sys.exit(main())

