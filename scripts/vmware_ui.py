#!/usr/bin/env python3
"""
VMware Installer UI Components
Using questionary for all interactions + rich for beautiful output
Styled with GTK4-inspired purple theme
"""

from rich.console import Console
from rich.panel import Panel
from rich.table import Table
from rich.text import Text
from rich.align import Align
from rich.theme import Theme
import questionary
from questionary import Style as QuestionaryStyle, Choice
from typing import List, Tuple, Optional, Any

# GTK4-inspired purple color scheme
GTK_PURPLE = "#b580d1"        # Primary purple
GTK_PURPLE_LIGHT = "#d8b4e2"  # Light purple for highlights
GTK_PURPLE_DARK = "#7e3f9e"   # Dark purple for borders
GTK_ACCENT = "#9c6fb9"        # Accent purple
GTK_BG_DARK = "#1e1e1e"       # Dark background
GTK_BG = "#262626"            # Background
GTK_FG = "#ffffff"            # Foreground text (bright white)
GTK_FG_DIM = "#7c7c7c"        # Dimmed text (medium gray)
GTK_SUCCESS = "#87d787"       # Success green
GTK_WARNING = "#ffff87"       # Warning yellow
GTK_ERROR = "#ff87af"         # Error red/pink
GTK_INFO = "#5fafd7"          # Info blue

# Rich theme with GTK4 colors
GTK_THEME = Theme({
    "primary": f"bold {GTK_PURPLE}",
    "accent": GTK_ACCENT,
    "success": f"bold {GTK_SUCCESS}",
    "error": f"bold {GTK_ERROR}",
    "warning": f"bold {GTK_WARNING}",
    "info": GTK_INFO,
    "title": f"bold {GTK_PURPLE_LIGHT}",
    "dimmed": f"dim {GTK_FG_DIM}",
    "border": GTK_PURPLE_DARK,
})

# Questionary style with GTK4 colors (this is what makes questionary beautiful!)
QUESTIONARY_STYLE = QuestionaryStyle([
    ('qmark', f'fg:{GTK_PURPLE} bold'),              # Question mark
    ('question', f'fg:{GTK_FG} bold'),               # Question text
    ('answer', f'fg:{GTK_PURPLE_LIGHT} bold'),       # Selected answer
    ('pointer', f'fg:{GTK_PURPLE} bold'),            # Selection pointer (►)
    ('highlighted', f'fg:{GTK_PURPLE_LIGHT} bold'),  # Highlighted option
    ('selected', f'fg:{GTK_PURPLE} bold'),           # Selected item
    ('separator', f'fg:{GTK_PURPLE_DARK}'),          # Separator lines
    ('instruction', f'fg:{GTK_FG_DIM}'),             # Instructions (Use arrow keys, etc.)
    ('text', f'fg:{GTK_FG}'),                        # Default text
    ('disabled', f'fg:{GTK_FG_DIM} italic'),         # Disabled items
    ('checkbox-selected', f'fg:{GTK_SUCCESS} bold'), # Selected checkbox [✓]
    ('checkbox', f'fg:{GTK_FG}'),                    # Unselected checkbox [ ]
])


class VMwareUI:
    """VMware installer UI using questionary + rich with GTK4 theme"""
    
    def __init__(self):
        self.console = Console(theme=GTK_THEME)
        self.width = self.console.width
    
    def get_responsive_width(self, percentage: float = 0.90) -> int:
        """Get responsive width based on terminal size"""
        return max(60, int(self.width * percentage))
    
    # ============================================================================
    # RICH OUTPUT METHODS (for beautiful printing)
    # ============================================================================
    
    def show_banner(self, title: str, subtitle: str = "", icon: str = "⚙️") -> None:
        """Display a beautiful GTK4-styled banner"""
        banner_text = Text()
        banner_text.append(f"{icon}  ", style=f"bold {GTK_PURPLE}")
        banner_text.append(title, style=f"bold {GTK_PURPLE_LIGHT}")
        
        if subtitle:
            banner_text.append("\n")
            banner_text.append(subtitle, style=f"italic {GTK_FG_DIM}")
        
        panel = Panel(
            Align.center(banner_text),
            border_style=GTK_PURPLE_DARK,
            padding=(1, 2),
            width=self.get_responsive_width()
        )
        self.console.print(panel)
    
    def show_section(self, title: str, subtitle: str = "") -> None:
        """Display a section header"""
        self.console.print()
        self.console.print(f"[title]{'═' * 60}[/]")
        self.console.print(f"[title]{title}[/]")
        if subtitle:
            self.console.print(f"[dimmed]{subtitle}[/]")
        self.console.print(f"[title]{'═' * 60}[/]")
        self.console.print()
    
    def show_step(self, step_num: int, total_steps: int, title: str) -> None:
        """Display a step header"""
        self.console.print()
        self.console.print(f"[primary]╭{'─' * 58}╮[/]")
        self.console.print(f"[primary]│[/] [title]Step {step_num}/{total_steps}: {title}[/]")
        self.console.print(f"[primary]╰{'─' * 58}╯[/]")
        self.console.print()
    
    def show_info(self, message: str) -> None:
        """Display info message"""
        self.console.print(f"[info]ℹ[/] {message}")
    
    def show_success(self, message: str) -> None:
        """Display success message"""
        self.console.print(f"[success]✓[/] {message}")
    
    def show_warning(self, message: str) -> None:
        """Display warning message"""
        self.console.print(f"[warning]⚠[/] {message}")
    
    def show_error(self, message: str) -> None:
        """Display error message"""
        self.console.print(f"[error]✗[/] {message}")
    
    def show_panel(self, content: str, title: str = "", border_color: str = GTK_PURPLE_DARK) -> None:
        """Display content in a panel"""
        panel = Panel(
            content,
            title=f"[title]{title}[/]" if title else None,
            border_style=border_color,
            padding=(1, 2),
            width=self.get_responsive_width()
        )
        self.console.print(panel)
    
    def create_table(self, title: str, headers: List[str], **kwargs) -> Table:
        """Create a styled table with GTK4 theme"""
        table = Table(
            title=title,
            title_style=f"bold {GTK_PURPLE_LIGHT}",
            border_style=GTK_PURPLE_DARK,
            header_style=f"bold {GTK_PURPLE}",
            show_header=True,
            show_lines=True,
            padding=(0, 1),
            width=self.get_responsive_width(),
            **kwargs
        )
        
        for header in headers:
            table.add_column(header)
        
        return table
    
    def show_table(self, table: Table) -> None:
        """Display a table"""
        self.console.print(table)
    
    def show_welcome_steps(self, steps: List[str]) -> None:
        """Show installation steps overview"""
        self.console.print()
        self.console.print("[title]Installation Steps:[/]")
        self.console.print()
        for i, step in enumerate(steps, 1):
            self.console.print(f"  [primary]{i}.[/] {step}")
        self.console.print()
        self.console.print("[dimmed]Full keyboard navigation • Arrow keys ↑↓, Enter ⏎, Number shortcuts 1-9[/]")
        self.console.print()
    
    def show_hardware_summary(self, hw_data: dict) -> None:
        """Display hardware summary in a beautiful table"""
        if not hw_data:
            self.show_warning("Hardware detection data not available")
            return
        
        table = self.create_table("🖥️  Hardware Configuration", ["Component", "Details"])
        rows_added = 0
        
        # CPU
        cpu = hw_data.get('cpu', {})
        if cpu and cpu.get('model'):
            cpu_text = f"{cpu.get('model', 'Unknown')}\n"
            cpu_text += f"Cores: {cpu.get('cores', 0)} / Threads: {cpu.get('threads', 0)}\n"
            features = []
            if cpu.get('has_avx512f') or cpu.get('has_avx512'): features.append("AVX-512")
            if cpu.get('has_avx2'): features.append("AVX2")
            if cpu.get('has_aes_ni'): features.append("AES-NI")
            if features:
                cpu_text += f"SIMD: {', '.join(features)}"
            table.add_row("CPU", cpu_text)
            rows_added += 1
        
        # Virtualization
        virt = hw_data.get('virtualization', {})
        if virt:
            virt_text = f"Intel VT-x: {'✓' if virt.get('has_vtx') or virt.get('vtx_supported') else '✗'}\n"
            virt_text += f"EPT: {'✓' if virt.get('has_ept') or virt.get('ept_supported') else '✗'}"
            table.add_row("Virtualization", virt_text)
            rows_added += 1
        
        # Memory
        memory = hw_data.get('memory', {})
        if memory and memory.get('total_gb'):
            mem_text = f"{memory.get('total_gb', 0):.1f} GB\n"
            mem_text += f"Huge Pages: {'✓' if memory.get('hugepages_2mb') or memory.get('has_hugepages') else '○'}"
            table.add_row("Memory", mem_text)
            rows_added += 1
        
        # Storage
        storage = hw_data.get('storage_devices', [])
        if storage:
            storage_text = f"{len(storage)} NVMe device(s)\n"
            for dev in storage[:2]:  # Show first 2
                storage_text += f"• {dev.get('model', 'Unknown')} ({dev.get('size_gb', 0):.0f} GB)\n"
            table.add_row("Storage", storage_text.rstrip())
            rows_added += 1
        
        # GPU
        gpu = hw_data.get('gpu', {})
        if gpu and gpu.get('vendor'):
            gpu_text = f"{gpu.get('vendor', '')} {gpu.get('model', '')}\n"
            if gpu.get('vram_gb'):
                gpu_text += f"VRAM: {gpu.get('vram_gb', 0):.1f} GB"
            table.add_row("GPU", gpu_text)
            rows_added += 1
        
        # Only print table if we have data
        if rows_added > 0:
            self.console.print(table)
        else:
            self.show_info("Hardware details: Basic detection completed")
    
    def show_comparison_table(self, title: str, optimized_features: List[str], vanilla_features: List[str]) -> None:
        """Show a comparison table between two modes"""
        table = self.create_table(title, ["🚀 Optimized Mode", "🔒 Vanilla Mode"])
        
        max_rows = max(len(optimized_features), len(vanilla_features))
        for i in range(max_rows):
            opt_text = optimized_features[i] if i < len(optimized_features) else ""
            van_text = vanilla_features[i] if i < len(vanilla_features) else ""
            table.add_row(opt_text, van_text)
        
        self.console.print(table)
    
    # ============================================================================
    # QUESTIONARY INTERACTION METHODS (for user input - THE CORE!)
    # ============================================================================
    
    def select(
        self,
        message: str,
        choices: List[Tuple[str, Any]],
        default: Any = None,
        instruction: str = None
    ) -> Any:
        """Create a selection menu (single choice)"""
        # Convert to questionary choices
        q_choices = [Choice(title=title, value=value) for title, value in choices]
        
        return questionary.select(
            message,
            choices=q_choices,
            default=default,
            style=QUESTIONARY_STYLE,
            instruction=instruction or "(Use arrow keys ↑↓ or number shortcuts, press Enter to select)",
            use_shortcuts=True,
            use_arrow_keys=True,
            use_jk_keys=True,  # Vim keys
            show_selected=True,
        ).ask()
    
    def checkbox(
        self,
        message: str,
        choices: List[Tuple[str, Any]],
        default: List[Any] = None,
        instruction: str = None
    ) -> List[Any]:
        """Create a checkbox menu (multiple choice)"""
        # Convert to questionary choices with checked state
        q_choices = []
        for title, value in choices:
            is_checked = default and value in default
            q_choices.append(Choice(title=title, value=value, checked=is_checked))
        
        return questionary.checkbox(
            message,
            choices=q_choices,
            style=QUESTIONARY_STYLE,
            instruction=instruction or "(Use arrow keys ↑↓, Space to select, Enter to confirm)",
            use_shortcuts=True,
            use_jk_keys=True,
        ).ask()
    
    def confirm(self, message: str, default: bool = True) -> bool:
        """Create a yes/no confirmation"""
        return questionary.confirm(
            message,
            default=default,
            style=QUESTIONARY_STYLE,
            auto_enter=False,
        ).ask()
    
    def input_text(self, message: str, default: str = "", validate: Any = None) -> str:
        """Create a text input"""
        return questionary.text(
            message,
            default=default,
            style=QUESTIONARY_STYLE,
            validate=validate,
        ).ask()
    
    def password(self, message: str) -> str:
        """Create a password input (hidden)"""
        return questionary.password(
            message,
            style=QUESTIONARY_STYLE,
        ).ask()
    
    def path(self, message: str, default: str = "", only_directories: bool = False) -> str:
        """Create a path input with autocomplete"""
        return questionary.path(
            message,
            default=default,
            only_directories=only_directories,
            style=QUESTIONARY_STYLE,
        ).ask()


# Convenience functions for standalone use
def print_banner(title: str, subtitle: str = "", icon: str = "⚙️"):
    """Quick banner print"""
    ui = VMwareUI()
    ui.show_banner(title, subtitle, icon)


def print_section(title: str, subtitle: str = ""):
    """Quick section header"""
    ui = VMwareUI()
    ui.show_section(title, subtitle)


def print_success(message: str):
    """Quick success message"""
    ui = VMwareUI()
    ui.show_success(message)


def print_error(message: str):
    """Quick error message"""
    ui = VMwareUI()
    ui.show_error(message)


def print_info(message: str):
    """Quick info message"""
    ui = VMwareUI()
    ui.show_info(message)


def print_warning(message: str):
    """Quick warning message"""
    ui = VMwareUI()
    ui.show_warning(message)
