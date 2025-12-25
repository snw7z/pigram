"""
Isolated TUI interface module (using Rich).
Manages all visual presentation and user interaction.
"""

import sys
import os  # Added to use os.system('clear')
from typing import List, Callable, Optional, Tuple
from rich.console import Console
from rich.text import Text
from rich.prompt import Prompt
from rich.table import Table  # Import Table class

from .colors import Colors, RESET, YELLOW
from .ascii_art import AsciiArt


class MenuItem:
    """Represents a menu item."""

    def __init__(self, key: str, label: str, callback: Optional[Callable] = None):
        self.key = key
        self.label = label
        self.callback = callback

    def __str__(self) -> str:
        # Minimalist format
        from .colors import GREEN, WHITE, RESET
        return f"  {GREEN}[{self.key}]{RESET} {WHITE}{self.label}{RESET}"
    
    def format_selected(self) -> str:
        """Returns the format of the item when selected."""
        from .colors import BRIGHT_CYAN, BOLD, RESET
        return f"  {BRIGHT_CYAN}▶ [{self.key}]{RESET} {BOLD}{BRIGHT_CYAN}{self.label}{RESET}"


class TUI:
    """Wrapper class for TUI interface."""

    def __init__(self, title: str = "PIGRAM"):
        self.title = title
        self.menu_items = []
        self.selected_index = 0  # Selected item index
        # Configure console to automatically detect terminal size
        # In Termux, Rich automatically detects screen size
        self.console = Console(force_terminal=True, width=None)  # width=None = auto detect

    def add_menu_item(self, key: str, label: str, callback: Optional[Callable] = None):
        """Adds an item to the menu."""
        self.menu_items.append(MenuItem(key, label, callback))

    def clear_screen(self):
        """Clears the screen using system 'clear' command."""
        # FIX: Use system 'clear' command to ensure history cleanup
        os.system('cls' if os.name == 'nt' else 'clear')

    def display_header(self):
        """Displays header with logo and minimalist banner - adjusted for terminal size."""
        # Get terminal width (Rich automatically detects in Termux)
        try:
            # Try to get terminal width from Rich
            terminal_width = self.console.width
        except (AttributeError, OSError):
            # Fallback: try to get via shutil or use default
            try:
                import shutil
                terminal_width = shutil.get_terminal_size().columns
            except (OSError, AttributeError):
                terminal_width = 80  # Safe default
        
        # Limit min and max width for logo (optimized for Termux)
        logo_width = min(max(terminal_width - 4, 30), 50)
        
        self.console.print(Text.from_ansi(AsciiArt.get_logo(logo_width)), justify="center")
        self.console.print()  # Space between logo and separator
        # Separator adjusted to terminal size
        separator_width = min(max(terminal_width - 10, 25), 40)
        self.console.print(Text.from_ansi(AsciiArt.get_separator(separator_width)), justify="center")
        self.console.print()

    def display_screen(self, selected_index: Optional[int] = None):
        """Clears screen and displays header and menu."""
        self.clear_screen()
        self.display_header()

        # Extra space between logo/title and buttons
        self.console.print()
        self.console.print()

        # Use provided index or current index
        if selected_index is not None:
            self.selected_index = selected_index
        
        # Ensure index is within bounds
        if self.selected_index < 0:
            self.selected_index = 0
        if self.selected_index >= len(self.menu_items):
            self.selected_index = len(self.menu_items) - 1

        # Display menu with highlight on selected item
        for i, item in enumerate(self.menu_items):
            is_selected = (i == self.selected_index)
            if is_selected:
                self.console.print(Text.from_ansi(item.format_selected()))
            else:
                self.console.print(Text.from_ansi(str(item)))
        
        # Extra space between buttons and instruction text
        self.console.print()
        self.console.print()
        
        # Minimalist navigation instructions
        from .colors import BRIGHT_BLACK
        self.console.print(Text.from_ansi(
            f"{BRIGHT_BLACK}↑↓ navigate  •  Enter select  •  Number/letter direct{RESET}"
        ), justify="center")

    def _get_key(self):
        """Reads a key from keyboard (compatible with Linux and Windows)."""
        try:
            # Linux/Unix
            import tty
            import termios
            
            fd = sys.stdin.fileno()
            old_settings = termios.tcgetattr(fd)
            
            try:
                tty.setraw(sys.stdin.fileno())
                ch = sys.stdin.read(1)
                
                # Detects escape sequences (arrows)
                if ch == '\x1b':  # ESC
                    ch2 = sys.stdin.read(1)
                    if ch2 == '[':
                        ch3 = sys.stdin.read(1)
                        if ch3 == 'A':  # Arrow up
                            return 'UP'
                        elif ch3 == 'B':  # Arrow down
                            return 'DOWN'
                        elif ch3 == '\r':  # Enter after ESC
                            return 'ENTER'
                
                # Enter
                if ch == '\r' or ch == '\n':
                    return 'ENTER'
                
                # Ctrl+C
                if ch == '\x03':
                    return 'CTRL_C'
                
                # Returns the character
                return ch
            finally:
                termios.tcsetattr(fd, termios.TCSADRAIN, old_settings)
                
        except (ImportError, AttributeError):
            # Windows
            try:
                import msvcrt
                
                if msvcrt.kbhit():
                    ch = msvcrt.getch()
                    
                    # On Windows, arrows are special sequences starting with 0xE0 or 0x00
                    if ch == b'\xe0' or ch == b'\x00':
                        ch2 = msvcrt.getch()
                        if ch2 == b'H':  # Arrow up
                            return 'UP'
                        elif ch2 == b'P':  # Arrow down
                            return 'DOWN'
                        elif ch2 == b'M':  # Arrow right
                            return None  # Not used, but captured
                        elif ch2 == b'K':  # Arrow left
                            return None  # Not used, but captured
                        return None
                    
                    # Convert bytes to string
                    if isinstance(ch, bytes):
                        ch = ch.decode('utf-8', errors='ignore')
                    
                    # Enter
                    if ch == '\r' or ch == '\n':
                        return 'ENTER'
                    
                    # Ctrl+C
                    if ch == '\x03':
                        return 'CTRL_C'
                    
                    # Returns the character
                    return ch
                return None
            except ImportError:
                return None

    def get_menu_choice(self) -> str:
        """Gets menu choice (arrow navigation or direct number/letter entry)."""
        if not self.menu_items:
            return 'x'
        
        choices = [item.key for item in self.menu_items]
        
        # Reset selected index when menu is displayed
        self.selected_index = 0
        
        # Display initial menu
        self.display_screen()
        
        # Navigation loop
        while True:
            key = self._get_key()
            
            if key is None:
                # If no input (Windows), try again
                import time
                time.sleep(0.05)
                continue
            
            # Arrow navigation
            if key == 'UP':
                self.selected_index = (self.selected_index - 1) % len(self.menu_items)
                self.display_screen()
                continue
            elif key == 'DOWN':
                self.selected_index = (self.selected_index + 1) % len(self.menu_items)
                self.display_screen()
                continue
            elif key == 'ENTER':
                return self.menu_items[self.selected_index].key
            elif key == 'CTRL_C':
                return 'x'
            
            # Direct entry by number/letter
            if key in choices:
                return key
            
            # 'x' to exit
            if key == 'x':
                return 'x'

    def get_input(self, message: str, is_password: bool = False) -> str:
        """Gets text input from user (synchronous)."""
        from .colors import CYAN, RESET
        # Using simple input to avoid loop conflicts
        # Remove trailing colon if present (to avoid double colon)
        message = message.rstrip(':')
        if is_password:
            import getpass
            user_input = getpass.getpass(f"{CYAN}{message}: {RESET}").strip()
        else:
            user_input = input(f"{CYAN}{message}: {RESET}").strip()

        return user_input

    def show_message(self, message: str, msg_type: str = "info"):
        """Displays a formatted message."""
        color_map = {
            "info": "cyan",
            "success": "green",
            "error": "red",
            "warning": "yellow"
        }
        color = color_map.get(msg_type, "cyan")
        self.console.print(f"\n[[bold {color}]{msg_type.upper()}[/bold {color}]] {message}\n")

    def display_table(self, data: List[List[str]]):
        """Displays a formatted table using Rich."""
        if not data:
            self.show_message("No data to display in table.", "warning")
            return

        table = Table(title=None, show_header=True, header_style="bold magenta")

        # Add columns (header is the first row)
        for header in data[0]:
            table.add_column(header, style="dim", justify="left")

        # Add rows (starting from second row)
        for row in data[1:]:
            table.add_row(*row)

        self.console.print(table)

    def wait_for_enter(self):
        """Waits for user to press Enter."""
        from .colors import BRIGHT_BLACK
        input(f"\n{BRIGHT_BLACK}Press Enter to continue...{RESET}")

    def execute_menu_action(self, choice: str):
        """Executes the action associated with a menu choice."""
        for item in self.menu_items:
            if item.key == choice:
                if item.callback:
                    return item.callback
                else:
                    self.show_message(f"Function '{item.label}' not yet implemented.", "warning")
                    self.wait_for_enter()
                return True

        self.show_message(f"Invalid option: {choice}", "error")
        self.wait_for_enter()
        return False
