"""
ANSI colors module for TUI interface.
Retro/hacker style with vibrant colors.
"""

# Basic ANSI colors
RESET = "\033[0m"
BOLD = "\033[1m"

# Text colors
BLACK = "\033[30m"
RED = "\033[31m"
GREEN = "\033[32m"
YELLOW = "\033[33m"
BLUE = "\033[34m"
MAGENTA = "\033[35m"
CYAN = "\033[36m"
WHITE = "\033[37m"

# Bright colors
BRIGHT_BLACK = "\033[90m"
BRIGHT_RED = "\033[91m"
BRIGHT_GREEN = "\033[92m"
BRIGHT_YELLOW = "\033[93m"
BRIGHT_BLUE = "\033[94m"
BRIGHT_MAGENTA = "\033[95m"
BRIGHT_CYAN = "\033[96m"  # Added BRIGHT_CYAN
BRIGHT_WHITE = "\033[97m"

# Background colors
BG_BLACK = "\033[40m"
BG_RED = "\033[41m"
BG_GREEN = "\033[42m"
BG_YELLOW = "\033[43m"
BG_BLUE = "\033[44m"
BG_MAGENTA = "\033[45m"
BG_CYAN = "\033[46m"
BG_WHITE = "\033[47m"


class Colors:
    """Class to manage theme colors - minimalist for Termux."""

    # Minimalist and clean theme
    LOGO_PRIMARY = CYAN
    LOGO_SECONDARY = BRIGHT_CYAN
    SEPARATOR = CYAN
    BANNER = BRIGHT_CYAN
    MENU_NUMBER = GREEN
    MENU_TEXT = WHITE
    PROMPT = CYAN
    ERROR = BRIGHT_RED
    SUCCESS = GREEN
    INFO = CYAN
    WARNING = YELLOW
    HIGHLIGHT = BRIGHT_CYAN  # To highlight selected item

    @staticmethod
    def colorize(text: str, color: str) -> str:
        """Applies color to text."""
        return f"{color}{text}{RESET}"

    @staticmethod
    def bold(text: str) -> str:
        """Applies bold to text."""
        return f"{BOLD}{text}{RESET}"

    @staticmethod
    def menu_item(number: str, text: str) -> str:
        """Formats a menu item."""
        return f"{GREEN}[ {number} ]{RESET} {YELLOW}{text}{RESET}"
