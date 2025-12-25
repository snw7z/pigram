"""
ASCII art module for TUI interface.
Contains logos, separators and decorative elements.
Optimized for Termux - minimalist and clean.
"""

from .colors import Colors, CYAN, GREEN, RESET, BRIGHT_CYAN


class AsciiArt:
    """Class to manage ASCII art."""
    
    @staticmethod
    def get_logo(width: int = 35) -> str:
        """Returns the ASCII logo of pigram (custom art)."""
        # Pigram ASCII Logo
        raw_lines = [
            "⠀⠀⠀   ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⣀⣤⣴⣾⣿⣿⣿⡄",
            "⠀   ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⠀⢀⣠⣴⣶⣿⣿⡿⠿⠛⢙⣿⣿⠃",
            "   ⠀⠀⠀⠀⠀⠀⠀⠀⢀⣀⣤⣶⣾⣿⣿⠿⠛⠋⠁⠀⠀⠀⣸⣿⣿⠀",
            "   ⠀⠀⠀⠀⣀⣤⣴⣾⣿⣿⡿⠟⠛⠉⠀⠀⣠⣤⠞⠁⠀⠀⣿⣿⡇⠀",
            "   ⠀⣴⣾⣿⣿⡿⠿⠛⠉⠀⠀⠀⢀⣠⣶⣿⠟⠁⠀⠀⠀⢸⣿⣿⠀⠀",
            "   ⠸⣿⣿⣿⣧⣄⣀⠀⠀⣀⣴⣾⣿⣿⠟⠁⠀⠀⠀⠀⠀⣼⣿⡿⠀⠀",
            "   ⠀⠈⠙⠻⠿⣿⣿⣿⣿⣿⣿⣿⠟⠁⠀⠀⠀⠀⠀⠀⢠⣿⣿⠇⠀⠀",
            "   ⠀ ⠀⠀⠀⠀⠘⣿⣿⣿⣿⡇⠀⣀⣄⡀⠀⠀⠀⠀⢸⣿⣿⠀⠀⠀",
            "  Pigram  ⠸⣿⣿⣿⣠⣾⣿⣿⣿⣦⡀⠀⠀⣿⣿⡏⠀⠀⠀",
            "   ⠀⠀⠀⠀⠀⠀⠀⠀⢿⣿⣿⣿⡿⠋⠈⠻⣿⣿⣦⣸⣿⣿⠁⠀⠀⠀",
            "   ⠀⠀⠀⠀⠀⠀⠀⠀⠀⠙⠛⠁⠀⠀⠀⠀⠈⠻⣿⣿⣿⠏⠀⠀⠀",
        ]

        # Apply colors to ASCII logo
        processed_lines = []
        for line in raw_lines:
            processed_lines.append(f"{BRIGHT_CYAN}{line}{RESET}")

        return "\n".join(processed_lines)
    
    @staticmethod
    def get_separator(width: int = 50, text: str = "") -> str:
        """Returns a minimalist decorative separator."""
        if text:
            # Separator with centered text
            text_len = len(text)
            dash_count = max(0, (width - text_len - 2) // 2)
            dashes = "─" * dash_count
            return f"{CYAN}{dashes} {BRIGHT_CYAN}{text}{CYAN} {dashes}{RESET}"
        else:
            # Simple separator
            return f"{CYAN}{'─' * width}{RESET}"
    
    @staticmethod
    def get_banner(text: str, width: int = 50) -> str:
        """Returns a minimalist banner with text."""
        # Simplified banner for Termux
        separator = AsciiArt.get_separator(width)
        text_separator = AsciiArt.get_separator(width, text)
        return f"{separator}\n{text_separator}\n{separator}"
    
    @staticmethod
    def clear_screen() -> str:
        """Returns ANSI code to clear screen."""
        return "\033[2J\033[H"
