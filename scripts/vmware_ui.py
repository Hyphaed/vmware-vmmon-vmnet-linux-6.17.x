#!/usr/bin/env python3
"""
VMware UI Library
Shared UI components for all VMware scripts
Provides beautiful terminal interfaces using rich library
"""

import sys
import os
from pathlib import Path
from typing import List, Dict, Optional, Any
from datetime import datetime

try:
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.text import Text
    from rich import box
    from rich.align import Align
    from rich.progress import Progress, SpinnerColumn, TextColumn
except ImportError:
    print("ERROR: 'rich' library not found. Installing...")
    import subprocess
    subprocess.check_call([sys.executable, "-m", "pip", "install", "rich"])
    from rich.console import Console
    from rich.panel import Panel
    from rich.table import Table
    from rich.text import Text
    from rich import box
    from rich.align import Align
    from rich.progress import Progress, SpinnerColumn, TextColumn

try:
    import questionary
    from questionary import Style
except ImportError:
    import subprocess
    import shutil
    
    print("Questionary not found. Attempting to install in conda environment...", file=sys.stderr)
    
    # Check if we're in a conda/mamba environment
    conda_prefix = os.environ.get('CONDA_PREFIX')
    if conda_prefix:
        # We're in a conda environment, use conda/mamba to install
        try:
            # Try mamba first (faster), then conda
            if shutil.which('mamba'):
                subprocess.check_call(['mamba', 'install', '-y', '-c', 'conda-forge', 'questionary'])
            elif shutil.which('conda'):
                subprocess.check_call(['conda', 'install', '-y', '-c', 'conda-forge', 'questionary'])
            else:
                # Fallback to pip within conda environment (safe)
                subprocess.check_call([sys.executable, "-m", "pip", "install", "questionary"])
        except subprocess.CalledProcessError:
            print("Warning: Could not install questionary in conda environment.", file=sys.stderr)
    else:
        # Not in conda environment - warn user but continue
        print("Warning: Not running in conda/mamba environment. Using basic prompts.", file=sys.stderr)
    
    try:
        import questionary
        from questionary import Style
    except ImportError:
        # Fallback mode
        questionary = None
        Style = None

# Hyphaed green color
HYPHAED_GREEN = "#B0D56A"

# Custom Questionary style matching Hyphaed green theme
VMWARE_STYLE = Style([
    ('qmark', 'fg:#B0D56A bold'),           # Question mark - Hyphaed green
    ('question', 'fg:#ffffff bold'),         # Question text - white
    ('answer', 'fg:#B0D56A bold'),          # Answer - Hyphaed green
    ('pointer', 'fg:#B0D56A bold'),         # Pointer - Hyphaed green
    ('highlighted', 'fg:#B0D56A bold'),     # Highlighted option - Hyphaed green
    ('selected', 'fg:#00ffff'),              # Selected - cyan
    ('separator', 'fg:#6C6C6C'),            # Separator - gray
    ('instruction', 'fg:#858585'),           # Instructions - light gray
    ('text', 'fg:#ffffff'),                  # Text - white
    ('disabled', 'fg:#858585 italic')       # Disabled - gray italic
])

class VMwareUI:
    """Shared UI components for VMware scripts"""
    
    def __init__(self):
        self.console = Console()
    
    def show_banner(self, title: str, subtitle: str = ""):
        """Display a branded banner"""
        banner_text = Text()
        banner_text.append("╔══════════════════════════════════════════════════════════════╗\n", style="bold")
        banner_text.append("║                                                              ║\n", style="bold")
        
        # Center the title
        padding = (62 - len(title)) // 2
        banner_text.append("║" + " " * padding, style="bold")
        banner_text.append(title, style=f"bold {HYPHAED_GREEN}")
        banner_text.append(" " * (62 - len(title) - padding) + "║\n", style="bold")
        
        if subtitle:
            sub_padding = (62 - len(subtitle)) // 2
            banner_text.append("║" + " " * sub_padding, style="bold")
            banner_text.append(subtitle, style=f"italic {HYPHAED_GREEN}")
            banner_text.append(" " * (62 - len(subtitle) - sub_padding) + "║\n", style="bold")
        
        banner_text.append("║                                                              ║\n", style="bold")
        banner_text.append("╚══════════════════════════════════════════════════════════════╝", style="bold")
        
        self.console.print()
        self.console.print(Align.center(banner_text))
        self.console.print()
    
    def show_section(self, title: str):
        """Display a section header"""
        self.console.print()
        self.console.print(Panel.fit(
            f"[bold cyan]{title}[/bold cyan]",
            border_style=HYPHAED_GREEN
        ))
        self.console.print()
    
    def show_info(self, message: str):
        """Display info message"""
        self.console.print(f"[blue]ℹ[/blue] {message}")
    
    def show_success(self, message: str):
        """Display success message"""
        self.console.print(f"[green]✓[/green] {message}")
    
    def show_warning(self, message: str):
        """Display warning message"""
        self.console.print(f"[yellow]⚠[/yellow] {message}")
    
    def show_error(self, message: str):
        """Display error message"""
        self.console.print(f"[red]✗[/red] {message}")
    
    def create_table(self, title: str = "", headers: List[str] = None) -> Table:
        """Create a styled table"""
        table = Table(
            show_header=bool(headers),
            header_style=f"bold {HYPHAED_GREEN}",
            box=box.ROUNDED,
            border_style=HYPHAED_GREEN,
            title=title if title else None,
            title_style=f"bold {HYPHAED_GREEN}"
        )
        
        if headers:
            for header in headers:
                table.add_column(header)
        
        return table
    
    def show_panel(self, content: str, title: str = "", border_color: str = HYPHAED_GREEN):
        """Display content in a panel"""
        self.console.print(Panel(
            content,
            title=f"[bold]{title}[/bold]" if title else None,
            border_style=border_color
        ))
    
    def confirm(self, message: str, default: bool = True) -> bool:
        """Ask for confirmation"""
        return Confirm.ask(f"[{HYPHAED_GREEN}]{message}[/{HYPHAED_GREEN}]", default=default)
    
    def prompt(self, message: str, choices: List[str] = None, default: str = None) -> str:
        """Prompt for user input"""
        return Prompt.ask(
            f"[{HYPHAED_GREEN}]{message}[/{HYPHAED_GREEN}]",
            choices=choices,
            default=default
        )
    
    def show_progress(self, message: str):
        """Show a progress spinner"""
        return Progress(
            SpinnerColumn(),
            TextColumn("[progress.description]{task.description}"),
            console=self.console,
        )
    
    def format_timestamp(self, timestamp: float) -> str:
        """Format a timestamp for display"""
        dt = datetime.fromtimestamp(timestamp)
        return dt.strftime("%Y-%m-%d %H:%M:%S")
    
    def format_size(self, size_bytes: int) -> str:
        """Format file size for display"""
        for unit in ['B', 'KB', 'MB', 'GB']:
            if size_bytes < 1024.0:
                return f"{size_bytes:.1f} {unit}"
            size_bytes /= 1024.0
        return f"{size_bytes:.1f} TB"


def main():
    """Demo of UI components"""
    ui = VMwareUI()
    
    ui.show_banner("VMWARE UI LIBRARY", "Demonstration of UI Components")
    
    ui.show_section("Information Messages")
    ui.show_info("This is an info message")
    ui.show_success("This is a success message")
    ui.show_warning("This is a warning message")
    ui.show_error("This is an error message")
    
    ui.show_section("Table Example")
    table = ui.create_table(
        title="Sample Table",
        headers=["Column 1", "Column 2", "Column 3"]
    )
    table.add_row("Row 1", "Data A", "Value 1")
    table.add_row("Row 2", "Data B", "Value 2")
    ui.console.print(table)
    
    ui.show_section("Panel Example")
    ui.show_panel("This is content inside a panel", title="Panel Title")
    
    print()


if __name__ == "__main__":
    main()

