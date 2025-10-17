# PyTermGUI UI Upgrade

## Overview

The VMware Module Installation Wizard has been upgraded from the **Rich** library to **PyTermGUI**, a modern Python TUI (Terminal User Interface) framework with advanced features including:

- Full mouse support out of the box
- Window manager system with desktop-inspired interactions
- Modular widget system
- TIM (Terminal Interface Markup) language for expressive styling
- Zero configuration for mouse and keyboard interactions
- NO_COLOR support with intelligent color downgrading

## What Changed

### Replaced Libraries

| Before | After | Reason |
|--------|-------|--------|
| Rich + Questionary | PyTermGUI | Unified framework with better window management |
| Manual styling | TIM markup | More expressive and maintainable |
| Limited interactivity | Full mouse support | Better UX |

### Files Modified

1. **`scripts/vmware_ui.py`** - Complete rewrite using PyTermGUI
   - New window-based UI components
   - Interactive menus with mouse support
   - Confirmation dialogs
   - Input dialogs
   - Checklist widgets
   - Message boxes
   
2. **`scripts/vmware_wizard.py`** - Updated to use new PyTermGUI-based UI
   - Better visual hierarchy
   - More intuitive interactions
   - Smoother transitions between steps
   - Enhanced progress indicators

3. **`scripts/install-vmware-modules.sh`** - Updated dependency management
   - Installs `pytermgui` instead of `rich` and `questionary`
   - Simplified dependency checking

### New Features

#### 1. Interactive Menus
Users can now navigate menus using:
- Arrow keys (↑/↓)
- Mouse clicks
- Enter to select

#### 2. Window Management
All UI elements are now displayed in properly managed windows:
- Centered dialogs
- Modal windows for important choices
- Consistent styling across all screens

#### 3. Custom Color Scheme
The "Hyphaed Green" (#B0D56A) color scheme is fully integrated:
- Success messages
- Highlights
- Titles and headers
- Interactive elements

#### 4. TIM Markup Aliases
Custom markup aliases for consistent styling:
- `[success]` - Green success text
- `[error]` - Red error text
- `[warning]` - Yellow warning text
- `[info]` - Cyan info text
- `[hyphaed]` - Brand green color
- `[title]` - Bright green titles
- `[dimmed]` - Gray dimmed text

## Installation

PyTermGUI is automatically installed by the installation script:

```bash
# Via the main installation script (automatic)
sudo bash scripts/install-vmware-modules.sh

# Manual installation in conda environment
$HOME/.miniforge3/envs/vmware-optimizer/bin/python -m pip install pytermgui
```

## Testing

### Static Tests (Non-Interactive)

Run static tests to verify component creation without requiring a TTY:

```bash
$HOME/.miniforge3/envs/vmware-optimizer/bin/python scripts/test_ui_static.py
```

This tests:
- PyTermGUI import
- VMware UI initialization
- Component creation (banners, messages, tables, panels, sections)
- Wizard module import

### Interactive Tests (Requires TTY)

To test the full interactive wizard:

```bash
sudo $HOME/.miniforge3/envs/vmware-optimizer/bin/python scripts/vmware_wizard.py
```

This tests:
- Interactive menus
- Confirmation dialogs
- Input fields
- Window management
- Mouse interactions

## API Reference

### VMwareUI Class

#### Core Methods

**`show_banner(title: str, subtitle: str = "") -> ptg.Container`**
- Displays a branded ASCII banner with title and optional subtitle

**`show_section(title: str) -> ptg.Container`**
- Creates a section header with border

**`show_info/success/warning/error(message: str) -> ptg.Label`**
- Display styled status messages with icons

**`create_table(title: str, headers: List[str], rows: List[List[str]]) -> ptg.Container`**
- Creates a formatted table with headers and rows

**`show_panel(content: str, title: str = "") -> ptg.Container`**
- Displays content in a bordered panel with optional title

#### Interactive Methods

**`create_menu(title: str, options: List[tuple], default_index: int = 0) -> tuple`**
- Creates an interactive menu with arrow key and mouse support
- Returns: `(selected_value, selected_index)`

**`create_confirm_dialog(message: str, default: bool = True) -> bool`**
- Yes/No confirmation dialog
- Returns: `True` for Yes, `False` for No

**`create_input_dialog(prompt: str, default: str = "") -> Optional[str]`**
- Text input dialog
- Returns: Input string or `None` if cancelled

**`show_message_box(title: str, message: str, box_type: str = "info")`**
- Modal message box requiring acknowledgment
- Types: "info", "success", "warning", "error"

**`create_checklist(title: str, items: List[tuple], selected_indices: List[int] = None) -> List[Any]`**
- Multi-select checklist
- Returns: List of selected values

## Migration Guide

### For Developers

If you're extending the UI, here's how to migrate from Rich to PyTermGUI:

#### Before (Rich)
```python
from rich.console import Console
from rich.panel import Panel

console = Console()
console.print(Panel("Hello", border_style="green"))
```

#### After (PyTermGUI)
```python
import pytermgui as ptg

with ptg.WindowManager() as manager:
    window = ptg.Window(
        ptg.Label("Hello"),
        box="ROUNDED"
    )
    window.center()
    manager.add(window)
```

#### Using VMwareUI Wrapper
```python
from vmware_ui import VMwareUI

ui = VMwareUI()
panel = ui.show_panel("Hello", "Title")

with ptg.WindowManager() as manager:
    window = ptg.Window(panel, box="DOUBLE")
    window.center()
    manager.add(window)
```

## Benefits

### User Experience
- **Better Navigation**: Mouse and keyboard support
- **Clearer Hierarchy**: Window-based UI with proper focus management
- **Instant Feedback**: Visual highlights on hover and selection
- **Professional Look**: Consistent styling and smooth animations

### Developer Experience
- **Less Code**: Unified framework reduces complexity
- **Better Abstractions**: Window manager handles layout automatically
- **Easier Maintenance**: TIM markup is more readable than escape codes
- **Type Safety**: Better type hints and documentation

### Performance
- **Efficient Rendering**: PyTermGUI uses smart terminal updates
- **Low Latency**: Direct terminal control for instant response
- **Resource Light**: Minimal memory footprint

## Compatibility

### Terminal Requirements
- VT100/ANSI compatible terminal
- UTF-8 encoding support
- Mouse support (optional but recommended)

### Tested Terminals
- ✓ GNOME Terminal
- ✓ Konsole
- ✓ Alacritty
- ✓ Kitty
- ✓ xterm
- ✓ tmux
- ✓ screen

### SSH/Remote Sessions
PyTermGUI works over SSH if the terminal supports ANSI escape codes and mouse reporting (most modern terminals do).

## Troubleshooting

### "Inappropriate ioctl for device"
This error occurs when running in a non-TTY environment (e.g., during CI/CD).

**Solution**: Use the static test suite for automated testing:
```bash
python scripts/test_ui_static.py
```

### Mouse Not Working
Check if your terminal supports mouse reporting:
```bash
echo -e '\e[?1003h\e[?1006h'  # Enable mouse
# Click anywhere
echo -e '\e[?1003l\e[?1006l'  # Disable mouse
```

### Colors Look Wrong
PyTermGUI automatically downgrade colors for older terminals. If colors look off:
1. Check terminal's TERM variable: `echo $TERM`
2. Try: `export TERM=xterm-256color`
3. For monochrome: `export NO_COLOR=1`

## Future Enhancements

Potential improvements for future versions:

1. **Progress Bars**: Real-time compilation progress
2. **Graphs**: Visual CPU/memory usage during compilation
3. **Themes**: Multiple color schemes (light/dark modes)
4. **Keybindings**: Configurable keyboard shortcuts
5. **Help System**: Built-in F1 help screens
6. **Logs Viewer**: Real-time log tailing in split pane

## References

- [PyTermGUI Documentation](https://ptg.bczsalba.com)
- [PyTermGUI GitHub](https://github.com/bczsalba/pytermgui)
- [TIM Markup Language](https://ptg.bczsalba.com/tim)
- [Window Manager Guide](https://ptg.bczsalba.com/widgets/window-manager)

## Credits

- **PyTermGUI** by bczsalba - Modern Python TUI framework
- **VMware Module Patches** - Linux 6.16/6.17 compatibility
- **Hyphaed Green** (#B0D56A) - Brand color scheme

---

**Last Updated**: October 17, 2025  
**PyTermGUI Version**: 7.7.4  
**Status**: ✓ Production Ready

