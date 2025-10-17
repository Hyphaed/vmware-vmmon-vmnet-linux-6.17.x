#!/usr/bin/env python3
"""
Minimal test to verify PyTermGUI works
"""

import sys

print("Testing PyTermGUI import...", file=sys.stderr)

try:
    import pytermgui as ptg
    print(f"✓ PyTermGUI imported successfully (version: {ptg.__version__})", file=sys.stderr)
except Exception as e:
    print(f"✗ Failed to import PyTermGUI: {e}", file=sys.stderr)
    sys.exit(1)

print("\nTesting simple window...", file=sys.stderr)

try:
    with ptg.WindowManager() as manager:
        window = ptg.Window(
            ptg.Label("Hello from PyTermGUI!"),
            ptg.Label(""),
            ptg.Button("OK", onclick=lambda *_: manager.stop()),
            box="DOUBLE"
        )
        window.center()
        manager.add(window)
    
    print("✓ Window test passed!", file=sys.stderr)
except Exception as e:
    print(f"✗ Window test failed: {e}", file=sys.stderr)
    import traceback
    traceback.print_exc(file=sys.stderr)
    sys.exit(1)

print("\n✓ All tests passed! PyTermGUI is working correctly.", file=sys.stderr)
sys.exit(0)

