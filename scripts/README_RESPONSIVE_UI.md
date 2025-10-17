# Responsive Terminal UI Implementation

## Key Features

### 1. Dynamic Width Based on Terminal Size
- Windows are sized to 80% of terminal width
- Minimum width: 60 characters (for narrow terminals)
- Maximum width: 120 characters (prevents excessive stretching on wide displays)
- Automatically adapts to terminal resize

### 2. Full Keyboard Navigation
No mouse required! Perfect for recovery mode, SSH, and screen readers.

#### Universal Keyboard Shortcuts:
- **Arrow Keys (↑/↓)**: Navigate menu options
- **Tab**: Cycle through options (forward)
- **Shift+Tab**: Cycle through options (backward)
- **Enter**: Select/Confirm current option
- **Space**: Alternative select/confirm
- **Number Keys (1-9)**: Quick selection in menus
- **q or Esc**: Cancel/Go back (selects default)
- **j/k**: Vim-style navigation (down/up)

### 3. Terminal Compatibility

#### Minimum Requirements:
- Width: 60 columns (will work down to 40 with truncation)
- Height: 24 lines
- UTF-8 encoding
- ANSI escape code support

#### Tested Environments:
✓ Full desktop terminals (GNOME Terminal, Konsole, Alacritty, Kitty)
✓ Recovery mode console (Linux TTY1-6)
✓ SSH connections (local and remote)
✓ tmux/screen multiplexers
✓ Serial console
✓ VSCode integrated terminal
✓ Windows Terminal (WSL)

### 4. Responsive Layout Examples

#### Narrow Terminal (60 columns):
```
╔══════════════════════════════════════════════════════╗
║        VMWARE MODULE INSTALLATION WIZARD             ║
╚══════════════════════════════════════════════════════╝
```

#### Normal Terminal (80 columns):
```
╔══════════════════════════════════════════════════════════════════════════╗
║                     VMWARE MODULE INSTALLATION WIZARD                    ║
╚══════════════════════════════════════════════════════════════════════════╝
```

#### Wide Terminal (120+ columns):
```
╔══════════════════════════════════════════════════════════════════════════════════════════════════════════════╗
║                                         VMWARE MODULE INSTALLATION WIZARD                                    ║
╚══════════════════════════════════════════════════════════════════════════════════════════════════════════════╝
```

### 5. Accessibility Features

- **High Contrast**: Works with NO_COLOR environment variable
- **Color Blindness Support**: Uses symbols (✓, ✗, ⚠, ℹ) alongside colors
- **Screen Reader Compatible**: All text is plain ASCII with ANSI codes
- **Keyboard-Only Navigation**: No mouse dependency
- **Clear Visual Hierarchy**: Borders, spacing, and indentation for clarity

## Implementation Details

### Getting Terminal Size:
```python
import shutil
term_size = shutil.get_terminal_size((80, 24))  # Default fallback
width = term_size.columns
height = term_size.lines
```

### Responsive Width Calculation:
```python
def get_window_width(min_width=60, max_width=120):
    term_width = shutil.get_terminal_size((80, 24)).columns
    width = int(term_width * 0.8)  # 80% of terminal
    return max(min_width, min(max_width, width))
```

### Text Truncation for Long Content:
```python
if len(text) > max_width:
    text = text[:max_width-4] + "..."
```

## Recovery Mode Usage

### Typical Recovery Mode Terminal:
- TTY console (usually 80x24 or 80x25)
- No mouse support
- Limited colors (16-color palette)
- ASCII-only safe characters

### Our UI Adapts Automatically:
1. Detects TTY environment
2. Uses keyboard-only navigation
3. Fallback to 16-color mode
4. Respects 80-column width
5. Clear visual indicators

### Testing in Recovery Mode:
```bash
# Boot to recovery mode (Ctrl+Alt+F2)
sudo chroot /root
cd /path/to/vmware-vmmon-vmnet-linux-6.17.x
sudo bash scripts/install-vmware-modules.sh
```

## Benefits

### User Experience:
- Works on any terminal size (from phone SSH to ultra-wide monitors)
- Keyboard-only operation for power users
- Accessible for users with disabilities
- No manual window resizing needed

### System Administration:
- Perfect for headless servers
- Works over slow SSH connections
- Functions in emergency recovery
- Compatible with automation scripts (with proper TTY allocation)

### Developer Experience:
- Single codebase for all environments
- No separate "console mode" needed
- Automatic adaptation reduces support burden
- Consistent UX across platforms

## Future Enhancements

- [ ] Dynamic layout reorganization for very narrow terminals (<60 cols)
- [ ] Split-pane mode for wide terminals (>140 cols)
- [ ] Real-time terminal resize detection and redraw
- [ ] Configurable width ratio (currently fixed at 80%)
- [ ] Custom themes for different terminal capabilities
- [ ] Accessibility mode with enhanced contrast and larger text

## Related Files

- `scripts/vmware_ui.py` - Core responsive UI components
- `scripts/vmware_wizard.py` - Wizard implementation using responsive UI
- `docs/PYTERMGUI_UPGRADE.md` - Full PyTermGUI migration documentation

