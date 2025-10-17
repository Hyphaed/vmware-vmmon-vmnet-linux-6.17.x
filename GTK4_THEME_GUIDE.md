# GTK4 Theme Implementation Guide

## 🎨 Color Scheme

The VMware Module Installation Wizard now features a modern **GTK4-inspired purple theme** similar to GNOME's system installers and package managers.

### Primary Colors

| Color Name | Hex Code | Usage |
|------------|----------|-------|
| GTK_PURPLE | `#9141AC` | Primary purple - borders, highlights, titles |
| GTK_PURPLE_LIGHT | `#B565D8` | Light purple - selected items, bright accents |
| GTK_PURPLE_DARK | `#613583` | Dark purple - subtle borders, shadows |
| GTK_ACCENT | `#C061CB` | Accent purple - special highlights |

### Background Colors

| Color Name | Hex Code | Usage |
|------------|----------|-------|
| GTK_BG_DARK | `#242424` | Dark background - window fills |
| GTK_BG | `#2D2D2D` | Standard background - containers |

### Text Colors

| Color Name | Hex Code | Usage |
|------------|----------|-------|
| GTK_FG | `#FFFFFF` | Primary text - white |
| GTK_FG_DIM | `#AAAAAA` | Dimmed text - gray for secondary info |

### Semantic Colors

| Color Name | Hex Code | Usage |
|------------|----------|-------|
| GTK_SUCCESS | `#8FF0A4` | Success messages, checkmarks (✓) |
| GTK_WARNING | `#F9F06B` | Warning messages, caution icons (⚠) |
| GTK_ERROR | `#FF6C6B` | Error messages, error icons (✗) |
| GTK_INFO | `#62A0EA` | Info messages, info icons (ℹ) |

## 📐 Layout Specifications

### Window Dimensions (GTK4-Style)

```python
# Width: 90% of terminal width (min 60 columns)
window_width = int(terminal_width * 0.90)

# Height: 30% of terminal height (min 10 lines)
window_height = int(terminal_height * 0.30)
```

This creates a large, prominent window that feels like a full GTK4 application dialog.

### Banner Dimensions

- Width: Same as window (90% of terminal)
- Rounded borders using `╭─╮` and `╰─╯`
- Icon + Title centered
- Subtitle below title (optional)

## 🎭 Visual Components

### 1. Banner (Header)

```
╭──────────────────────────────────────────────────────────╮
│                                                          │
│            ⚙️  VMware Module Installation Wizard         │
│           Python-Powered Hardware Detection              │
│                                                          │
╰──────────────────────────────────────────────────────────╯
```

**Features:**
- Rounded corners (╭╮╰╯)
- Purple borders
- Centered icon + title
- Responsive width (90% of terminal)

### 2. Selection Menu (Radio-style)

```
◉ Option 1 - Selected (purple highlight)
○ Option 2 - Unselected (gray)
○ Option 3 - Unselected (gray)
```

**Features:**
- Filled circle (◉) for selected
- Empty circle (○) for unselected
- Purple color for selected items
- Gray for unselected items

### 3. Buttons

```
[primary]◉ Start Installation[/]
```

**Features:**
- Purple text color
- Filled bullet point (◉) for primary actions
- Keyboard navigation with visual feedback

### 4. Panels

```
╭─ Panel Title ─╮
│               │
│  Panel content│
│               │
╰───────────────╯
```

**Features:**
- Rounded borders
- Purple title bar
- Responsive width

## 🎹 Interactive Elements

### Selection States

| State | Visual | Color |
|-------|--------|-------|
| Selected | ◉ | GTK_PURPLE_LIGHT (#B565D8) |
| Unselected | ○ | GTK_FG_DIM (#AAAAAA) |
| Hover/Focus | ◉ | GTK_PURPLE_LIGHT (#B565D8) |

### Icons

| Purpose | Icon | Color |
|---------|------|-------|
| Configuration | ⚙️ | - |
| Package | 📦 | - |
| Success | ✓ | GTK_SUCCESS |
| Error | ✗ | GTK_ERROR |
| Warning | ⚠ | GTK_WARNING |
| Info | ℹ or ▶ | GTK_INFO |
| Selected | ◉ | GTK_PURPLE_LIGHT |
| Unselected | ○ | GTK_FG_DIM |

## 📱 Responsive Behavior

### Terminal Size Adaptation

| Terminal Width | Window Width | Behavior |
|----------------|--------------|----------|
| < 60 cols | 60 cols (minimum) | Fixed minimum |
| 60-200 cols | 90% of width | Scales proportionally |
| > 200 cols | 180 cols | Practical maximum |

### Terminal Height Adaptation

| Terminal Height | Window Height | Behavior |
|-----------------|---------------|----------|
| < 24 lines | 10 lines (minimum) | Fixed minimum |
| 24-100 lines | 30% of height | Scales proportionally |
| > 100 lines | 30 lines | Practical maximum |

## 🎨 TIM (Terminal Interface Markup) Aliases

PyTermGUI uses TIM markup for styling. Here are our custom aliases:

```python
[success]   # Green success text (#8FF0A4)
[error]     # Red error text (#FF6C6B)
[warning]   # Yellow warning text (#F9F06B)
[info]      # Blue info text (#62A0EA)
[primary]   # Purple primary text (#9141AC)
[accent]    # Purple accent text (#C061CB)
[title]     # Light purple title text (#B565D8)
[dimmed]    # Gray dimmed text (#AAAAAA)
```

### Usage Examples

```python
# Success message
ptg.Label("[success]✓[/] Module installed successfully")

# Error message
ptg.Label("[error]✗[/] Compilation failed")

# Info with icon
ptg.Label("[info]▶[/] Starting hardware detection...")

# Primary action button
ptg.Button("[primary]◉ Continue[/]", onclick=handler)

# Title
ptg.Label("[title]Configuration Options[/]")

# Dimmed secondary text
ptg.Label("[dimmed]Press Enter to continue[/]")
```

## 🖼️ Complete Example

Here's how a full GTK4-styled window looks:

```
╭────────────────────────────────────────────────────────────────────╮
│                                                                    │
│            ⚙️  VMware Module Installation Wizard                   │
│                Python-Powered Hardware Detection                   │
│                                                                    │
╰────────────────────────────────────────────────────────────────────╯

▶ Modern terminal interface with full keyboard navigation

                    ◉ Start Installation

────────────────────────────────────────────────────────────────────

Arrow keys / Tab: Navigate | Enter: Select | Numbers: Quick select
```

## 🎯 Design Principles

### 1. Modern & Clean
- Rounded corners instead of sharp boxes
- Ample whitespace
- Clear visual hierarchy

### 2. GTK4-Inspired
- Purple accent colors (GNOME style)
- Radio button selections
- Large, prominent windows (90% width)

### 3. Accessible
- High contrast colors
- Icons + text for all states
- Works in 16-color mode with fallbacks
- Keyboard-only navigation

### 4. Responsive
- Adapts to any terminal size
- Maintains proportions (90% x 30%)
- Minimum sizes prevent unusable layouts

### 5. Professional
- Consistent color usage
- Unified component styling
- Production-ready appearance

## 🛠️ Implementation Notes

### Creating Styled Components

```python
from vmware_ui import VMwareUI, GTK_PURPLE, GTK_SUCCESS

ui = VMwareUI()

# Create banner with icon
banner = ui.show_banner(
    "My Application",
    "Subtitle text",
    icon="🚀"
)

# Create GTK4-styled window
window = ui.create_window(
    banner,
    ptg.Label("[info]Welcome message[/]"),
    ptg.Button("[primary]◉ Start[/]", onclick=handler),
    title="Window Title"
)
```

### Window Sizing

Windows automatically use responsive dimensions:
- Width: 90% of terminal (min 60 cols)
- Height: 30% of terminal (min 10 lines)

Override if needed:
```python
window = ui.create_window(
    *widgets,
    width=100,  # Fixed width
    height=20,  # Fixed height
    title="Custom Size"
)
```

## 🎨 Color Psychology

**Why Purple?**
- **Modern**: Associated with contemporary design
- **Premium**: Conveys quality and sophistication
- **Calming**: Not as aggressive as red, not as cold as blue
- **GNOME**: Matches GNOME's installer/system tools
- **Professional**: Used by many system administration tools

## 📊 Comparison

### Before (Hyphaed Green Theme)
- Color: #B0D56A (green)
- Width: 80% of terminal
- Height: Auto-sized
- Borders: Sharp corners (╔╗╚╝)
- Style: Technical, developer-focused

### After (GTK4 Purple Theme)
- Color: #9141AC (purple)
- Width: **90% of terminal** (larger)
- Height: **30% of terminal** (fixed proportion)
- Borders: Rounded corners (╭╮╰╯)
- Style: Modern, GTK4-inspired, user-friendly

## 🚀 Ready to Use

The GTK4 theme is now active! Run the wizard to see it in action:

```bash
sudo bash scripts/install-vmware-modules.sh
```

Enjoy your modern, GTK4-styled terminal interface! 🎉

---

**Last Updated**: October 17, 2025  
**Theme Version**: GTK4-inspired Purple v1.0  
**Compatibility**: All terminals with 256-color support

