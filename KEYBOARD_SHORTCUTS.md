# VMware Wizard - Keyboard Shortcuts Quick Reference

## 🎹 Universal Navigation

| Key | Action |
|-----|--------|
| **↑** / **↓** | Navigate up/down through options |
| **j** / **k** | Navigate down/up (Vim-style) |
| **Tab** | Move to next option |
| **Shift+Tab** | Move to previous option |
| **Enter** | Select/Confirm current option |
| **Space** | Alternative select/confirm |
| **1-9** | Quick select option by number |
| **q** / **Esc** | Cancel/Go back (uses default) |

## 📋 Specific Screens

### Main Menu / Kernel Selection
- **↑/↓** or **j/k**: Browse kernels
- **1-9**: Select kernel by number
- **Enter**: Confirm selection
- **q**: Cancel (uses current kernel)

### Optimization Mode Selection
- **↑/↓**: Toggle between Optimized/Vanilla
- **1**: Select Optimized mode
- **2**: Select Vanilla mode
- **Enter**: Confirm choice

### Yes/No Dialogs
- **←/→** or **Tab**: Switch between Yes/No
- **Enter**: Confirm
- **y**: Quick Yes
- **n**: Quick No

### Message Boxes
- **Enter** or **Space**: Acknowledge and close
- **Esc**: Close (if cancelable)

## 🚀 Pro Tips

### Speed Navigation
1. Use **number keys** (1-9) for instant selection in menus
2. Press **Enter** rapidly to use defaults and move quickly
3. Use **j/k** for fast Vim-style navigation

### Recovery Mode
- All mouse functions have keyboard equivalents
- Perfect for TTY consoles (Ctrl+Alt+F2)
- Works over SSH without X11 forwarding

### Accessibility
- Tab through all interactive elements
- Screen reader compatible
- High contrast mode with NO_COLOR=1

## 📖 Examples

### Fast Installation (Using Defaults)
```
Start screen: Enter
Kernel selection: Enter (uses current kernel)
Hardware detection: (automatic)
Mode selection: 1 or Enter (Optimized)
Confirmation: Enter
```

### Custom Selection
```
Start screen: Enter
Kernel selection: ↓↓ (or 3 for option 3), Enter
Hardware detection: (automatic)
Mode selection: ↓, Enter (Vanilla)
Confirmation: Enter
```

### Power User (Vim Style)
```
Start screen: Enter
Kernel selection: jj (down twice), Enter
Mode selection: k (up), Enter
```

## 🖥️ Terminal Requirements

### Minimum:
- Width: 60 columns
- Height: 24 lines
- UTF-8 encoding

### Recommended:
- Width: 80-120 columns
- Height: 30+ lines
- 256-color support

## 🆘 Troubleshooting

### Keys Not Working?
1. Check terminal emulator settings
2. Try alternative keys (j/k instead of arrows)
3. Ensure terminal has focus
4. Check if running in proper TTY

### Display Issues?
1. Resize terminal to at least 60 columns
2. Set TERM environment variable: `export TERM=xterm-256color`
3. For monochrome: `export NO_COLOR=1`

## 📱 Terminal Type Specific

### GNOME Terminal / Konsole
- All shortcuts work natively
- Mouse also available (optional)

### Recovery Mode (TTY)
- Keyboard only (mouse unavailable)
- Use arrow keys or j/k
- Number keys for quick selection

### SSH Session
- All shortcuts work
- No X11 forwarding needed
- Works over slow connections

### tmux / screen
- Prefix key may interfere
- Use tmux's copy mode: `Ctrl+b [`
- Or temporarily detach: `Ctrl+b d`

---

**Remember**: You can always use **q** or **Esc** to cancel and go back!

For full documentation, see: `docs/PYTERMGUI_UPGRADE.md`

