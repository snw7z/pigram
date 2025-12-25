"""
pigram - Telegram Cloner
Main entry point of the application.
"""

import sys
import asyncio
from pathlib import Path
from typing import List, Dict, Any, Optional

# Add project directory to path
sys.path.insert(0, str(Path(__file__).parent))

from tui.interface import TUI
from tui.colors import Colors, RESET, CYAN
from rich.text import Text
from core.session import SessionManager
from core.cloner import GroupCloner, ChatCloner
from core.analyzer import FileAnalyzer
from config.settings import Settings


class PigramApp:
    """Main class of the pigram application."""

    def __init__(self):
        self.tui = TUI(title="PIGRAM")
        self.session_manager = SessionManager()
        self.group_cloner: Optional[GroupCloner] = None
        self.chat_cloner = None
        self.file_analyzer = FileAnalyzer()
        self.source_chat_id: Optional[str] = None
        self.target_chat_id: Optional[str] = None
        self.analyze_target_id: Optional[str] = None

    def setup_menu(self):
        """Setup main menu."""
        self.tui.menu_items = []
        self.tui.add_menu_item("1", "Clone Groups", self.clone_groups)
        self.tui.add_menu_item("2", "Clone Chats", self.clone_chats)
        self.tui.add_menu_item("3", "Analyze Files", self.analyze_files)
        self.tui.add_menu_item("4", "Login/Status", self.login_menu)
        self.tui.add_menu_item("x", "Exit", self.exit_app)

    async def login_menu(self):
        """Login/status session menu."""

        is_logged_in = await self.session_manager.check_session()

        while True:
            self.tui.menu_items = []

            if is_logged_in:
                user_display_name = self.session_manager.get_user_display_name()
                self.tui.title = f"LOGGED IN AS: {user_display_name}"
                self.tui.add_menu_item("1", "Delete Session", self.logout_session)
                self.tui.add_menu_item("x", "Back", self.setup_menu)
            else:
                self.tui.title = "LOGIN"
                self.tui.add_menu_item("1", "Login", self.perform_login)
                self.tui.add_menu_item("x", "Back", self.setup_menu)

            self.tui.display_screen()  # Clear and display menu
            choice = self.tui.get_menu_choice()  # Synchronous with Rich

            if choice == 'x':
                break

            callback = self.tui.execute_menu_action(choice)

            if callback:
                if callback == self.setup_menu:
                    self.setup_menu()
                    break

                if asyncio.iscoroutinefunction(callback):
                    await callback()
                else:
                    callback()

                is_logged_in = await self.session_manager.check_session()

        self.tui.title = "PIGRAM"
        self.setup_menu()

    async def perform_login(self):
        """Function to perform login to Telegram."""
        self.tui.clear_screen()
        self.tui.display_header()
        # Extra space for better visualization
        self.tui.console.print()
        self.tui.console.print()
        
        api_id = self.tui.get_input("Enter your API ID")

        self.tui.clear_screen()
        self.tui.display_header()
        self.tui.console.print()
        self.tui.console.print()
        api_hash = self.tui.get_input("Enter your API Hash")

        self.tui.clear_screen()
        self.tui.display_header()
        self.tui.console.print()
        self.tui.console.print()
        phone_number = self.tui.get_input("Enter your phone number:")

        if not all([api_hash, api_id, phone_number]):
            self.tui.clear_screen()
            self.tui.display_header()
            self.tui.console.print()
            self.tui.console.print()
            self.tui.show_message("Incomplete credentials. Login cancelled.", "warning")
            self.tui.wait_for_enter()
            return

        def otp_callback():
            self.tui.clear_screen()
            self.tui.display_header()
            self.tui.console.print()
            self.tui.console.print()
            from tui.colors import BRIGHT_CYAN, RESET
            self.tui.console.print(Text.from_ansi(f"{BRIGHT_CYAN}📱 Two-step verification{RESET}"), justify="center")
            self.tui.console.print()
            return self.tui.get_input("Enter verification code (OTP)")

        def password_callback():
            self.tui.clear_screen()
            self.tui.display_header()
            self.tui.console.print()
            self.tui.console.print()
            from tui.colors import BRIGHT_CYAN, RESET
            self.tui.console.print(Text.from_ansi(f"{BRIGHT_CYAN}🔐 2FA Authentication{RESET}"), justify="center")
            self.tui.console.print()
            return self.tui.get_input("Enter your two-step verification password (2FA)", is_password=True)

        self.tui.clear_screen()
        self.tui.display_header()
        self.tui.console.print()
        self.tui.console.print()
        self.tui.show_message("Attempting login...", "info")
        success, message = await self.session_manager.login(
            api_id=api_id,
            api_hash=api_hash,
            phone_number=phone_number,
            otp_callback=otp_callback,
            password_callback=password_callback
        )

        self.tui.clear_screen()
        self.tui.display_header()
        self.tui.console.print()
        self.tui.console.print()
        if success:
            self.tui.show_message(message, "success")
        else:
            self.tui.show_message(message, "error")

        self.tui.wait_for_enter()

    async def logout_session(self):
        """Function to delete session (logout)."""
        self.tui.clear_screen()
        self.tui.display_header()
        # Extra space for better visualization
        self.tui.console.print()
        self.tui.console.print()

        self.tui.show_message("Deleting session...", "info")
        success = await self.session_manager.logout()

        self.tui.clear_screen()
        self.tui.display_header()
        self.tui.console.print()
        self.tui.console.print()
        if success:
            self.tui.show_message("Session deleted successfully!", "success")
        else:
            self.tui.show_message("Error deleting session.", "error")

        self.tui.wait_for_enter()

    async def clone_groups(self):
        """Function to clone groups."""
        if not await self.session_manager.check_session():
            self.tui.show_message("You need to login first!", "warning")
            self.tui.wait_for_enter()
            return

        self.tui.clear_screen()
        self.tui.display_header()
        self.tui.show_message("Searching groups and channels...", "info")

        client = self.session_manager.get_client()
        if not client:
            self.tui.show_message("Error: Telethon client is not active.", "error")
            self.tui.wait_for_enter()
            return

        self.group_cloner = GroupCloner(client)

        try:
            groups = await self.group_cloner.list_groups()

            self.tui.clear_screen()
            self.tui.display_header()

            if not groups:
                self.tui.show_message("No groups or channels found.", "warning")
            else:
                self.tui.show_message(f"Groups and Channels Found ({len(groups)}):", "info")

                table_data = [["#", "Title", "Type", "Username"]]
                for i, group in enumerate(groups):
                    table_data.append([
                        str(i + 1),
                        group["title"],
                        group["type"],
                        group["username"]
                    ])

                self.tui.display_table(table_data)
                self.tui.show_message("Cloning functionality itself is still in development.", "info")

        except Exception as e:
            self.tui.show_message(f"Error listing groups: {e}", "error")

        self.tui.wait_for_enter()

    async def clone_chats(self):
        """Function to clone chats."""
        if not await self.session_manager.check_session():
            self.tui.show_message("You need to login first!", "warning")
            self.tui.wait_for_enter()
            return

        await self.clone_chats_menu()

    async def clone_chats_menu(self):
        """Menu to configure chat cloning."""

        while True:
            self.tui.menu_items = []
            self.tui.title = "CLONE CHATS"

            from tui.colors import CYAN, RESET

            source_display = f" {CYAN}> {self.source_chat_id} <{RESET}" if self.source_chat_id else ""
            target_display = f" {CYAN}> {self.target_chat_id} <{RESET}" if self.target_chat_id else ""

            self.tui.add_menu_item("1", f"Source{source_display}", lambda: self.set_chat_id("source"))
            self.tui.add_menu_item("2", f"Target{target_display}", lambda: self.set_chat_id("target"))

            if self.source_chat_id and self.target_chat_id:
                self.tui.add_menu_item("3", "Start", self.start_cloning)

            self.tui.add_menu_item("x", "Back", self.setup_menu)

            self.tui.display_screen()
            choice = self.tui.get_menu_choice()

            if choice == 'x':
                break

            callback = self.tui.execute_menu_action(choice)

            if callback:
                if callback == self.setup_menu:
                    self.setup_menu()
                    break

                if asyncio.iscoroutinefunction(callback):
                    await callback()
                else:
                    callback()

        self.tui.title = "PIGRAM"
        self.setup_menu()

    def set_chat_id(self, chat_type: str):
        """Function to request and set chat ID."""
        self.tui.clear_screen()
        self.tui.display_header()

        prompt = f"Enter {chat_type} chat ID (e.g., -1001234567890 or @username)"
        chat_id = self.tui.get_input(prompt)

        if chat_type == "source":
            self.source_chat_id = chat_id
            self.tui.show_message(f"Source ID set to: {chat_id}", "success")
        elif chat_type == "target":
            self.target_chat_id = chat_id
            self.tui.show_message(f"Target ID set to: {chat_id}", "success")

        self.tui.wait_for_enter()

    async def start_cloning(self):
        """Starts the chat cloning process."""
        self.tui.clear_screen()
        self.tui.display_header()

        self.tui.show_message("Starting message cloning...", "info")
        self.tui.show_message(f"Source: {self.source_chat_id}", "info")
        self.tui.show_message(f"Target: {self.target_chat_id}", "info")
        print()  # Blank line

        client = self.session_manager.get_client()
        if not client:
            self.tui.show_message("Error: Telethon client is not active.", "error")
            self.tui.wait_for_enter()
            return

        if not self.chat_cloner:
            self.chat_cloner = ChatCloner(client)

        # Get total messages for progress bar
        total_messages = await self.chat_cloner.get_total_messages(self.source_chat_id)

        def progress_callback(counter: int, msg_id: int):
            # Use carriage return to overwrite line and avoid "flood"
            # Rich/TUI doesn't handle \r well, so use simple print for progress
            # Status bar implementation with asterisks
            if total_messages > 0:
                percent = (counter / total_messages) * 100
                progress_bar = int(percent // 2) * "*" + (50 - int(percent // 2)) * "#"
                print(f"\r  [{progress_bar}] {percent:.2f}% - Msg {counter}/{total_messages} (ID {msg_id})", end="", flush=True)
            else:
                print(f"\r  Msg {counter} - ID {msg_id} copied.", end="", flush=True)

        def status_callback(message: str):
            # Use Rich to display formatted status messages
            self.tui.show_message(message, "info")

        try:
            result = await self.chat_cloner.clone_chat(
                source_chat_id=self.source_chat_id,
                target_chat_id=self.target_chat_id,
                batch_size=100,
                delay_between_messages=0.8,  # Same delay as Bot.py that works
                pause_every_n=3000,  # Pause every 3000 messages (as in Bot.py)
                pause_duration=500,  # 500 seconds pause (as in Bot.py)
                progress_callback=progress_callback,
                status_callback=status_callback
            )

            print()  # New line after progress

            if result["success"]:
                self.tui.show_message(
                    f"Cloning completed! Total: {result['total_messages']} messages, Errors: {result['errors']}",
                    "success"
                )
            else:
                self.tui.show_message(
                    f"Cloning failed: {result.get('error', 'Unknown error')}",
                    "error"
                )

        except Exception as e:
            self.tui.show_message(f"Error during cloning: {e}", "error")

        self.tui.wait_for_enter()

    async def analyze_files(self):
        """Function to analyze files."""
        if not await self.session_manager.check_session():
            self.tui.show_message("You need to login first!", "warning")
            self.tui.wait_for_enter()
            return
        
        await self.analyze_files_menu()

    async def analyze_files_menu(self):
        """Menu to configure file analysis."""
        while True:
            self.tui.menu_items = []
            self.tui.title = "ANALYZE FILES"
            
            from tui.colors import CYAN, RESET
            target_display = f" {CYAN}> {self.analyze_target_id} <{RESET}" if self.analyze_target_id else ""
            
            self.tui.add_menu_item("1", f"Target{target_display}", lambda: self.set_analyze_target())
            
            # Add Start button if target is set
            if self.analyze_target_id:
                self.tui.add_menu_item("2", "Start", self.perform_analysis)
            
            self.tui.add_menu_item("x", "Back", self.setup_menu)
            
            self.tui.display_screen()
            choice = self.tui.get_menu_choice()
            
            if choice == 'x':
                break
            
            callback = self.tui.execute_menu_action(choice)
            
            if callback:
                if callback == self.setup_menu:
                    self.setup_menu()
                    break
                
                if callback == self.perform_analysis:
                    await self.perform_analysis()
                    break
                
                if asyncio.iscoroutinefunction(callback):
                    await callback()
                else:
                    callback()
        
        self.tui.title = "PIGRAM"
        self.setup_menu()

    def set_analyze_target(self):
        """Function to request and set target ID for analysis."""
        self.tui.clear_screen()
        self.tui.display_header()
        
        prompt = "Enter target chat/group/channel ID or @username (for topics, use format: chat_id#topic_id)"
        target_id = self.tui.get_input(prompt)
        
        # Handle topic format (chat_id#topic_id)
        if '#' in target_id:
            parts = target_id.split('#')
            if len(parts) == 2:
                self.analyze_target_id = parts[0]
                self.analyze_topic_id = int(parts[1])
            else:
                self.analyze_target_id = target_id
                self.analyze_topic_id = None
        else:
            self.analyze_target_id = target_id
            self.analyze_topic_id = None
        
        self.tui.show_message(f"Target ID set to: {target_id}", "success")
        self.tui.wait_for_enter()

    async def perform_analysis(self):
        """Performs the analysis of the target chat."""
        self.tui.clear_screen()
        self.tui.display_header()
        
        client = self.session_manager.get_client()
        if not client:
            self.tui.show_message("Error: Telethon client is not active.", "error")
            self.tui.wait_for_enter()
            return
        
        self.file_analyzer.set_client(client)
        
        self.tui.show_message("Starting analysis...", "info")
        self.tui.show_message(f"Target: {self.analyze_target_id}", "info")
        if hasattr(self, 'analyze_topic_id') and self.analyze_topic_id:
            self.tui.show_message(f"Topic: {self.analyze_topic_id}", "info")
        
        # Progress callback with Rich Progress
        from rich.progress import Progress, SpinnerColumn, BarColumn, TextColumn, TimeRemainingColumn
        
        progress_obj = None
        progress_task = None
        
        def progress_callback(data):
            nonlocal progress_obj, progress_task
            
            if isinstance(data, tuple):
                if data[0] == "start_progress":
                    # Start progress bar with known total
                    _, total, description = data
                    progress_obj = Progress(
                        SpinnerColumn(),
                        TextColumn("[progress.description]{task.description}"),
                        BarColumn(),
                        TextColumn("[progress.percentage]{task.percentage:>3.0f}%"),
                        TextColumn("({task.completed}/{task.total})"),
                        TimeRemainingColumn(),
                        console=self.tui.console
                    )
                    progress_obj.start()
                    progress_task = progress_obj.add_task(description, total=total)
                    
                elif data[0] == "start_spinner":
                    # Start spinner (unknown total)
                    _, description = data
                    progress_obj = Progress(
                        SpinnerColumn(),
                        TextColumn("[progress.description]{task.description}"),
                        console=self.tui.console
                    )
                    progress_obj.start()
                    progress_task = progress_obj.add_task(description, total=None)
                    
                elif data[0] == "update_progress":
                    # Update progress bar
                    _, current = data
                    if progress_obj and progress_task is not None:
                        progress_obj.update(progress_task, completed=current)
                        
                elif data[0] == "update_spinner":
                    # Update spinner text
                    _, description = data
                    if progress_obj and progress_task is not None:
                        progress_obj.update(progress_task, description=description)
                        
                elif data[0] == "stop_progress":
                    # Stop progress
                    if progress_obj:
                        progress_obj.stop()
        
        # Perform analysis
        self.tui.console.print()
        result = await self.file_analyzer.analyze_chat(
            chat_id=self.analyze_target_id,
            topic_id=getattr(self, 'analyze_topic_id', None),
            progress_callback=progress_callback
        )
        
        # Ensure progress is stopped
        if progress_obj:
            progress_obj.stop()
        
        if "error" in result:
            self.tui.show_message(f"Error: {result['error']}", "error")
            self.tui.wait_for_enter()
            return
        
        # Show results and options
        await self.show_analysis_results()

    async def show_analysis_results(self):
        """Shows analysis results and options to copy/save."""
        data = self.file_analyzer.analysis_data
        
        # Show menu with Copy and Save options
        while True:
            self.tui.clear_screen()
            self.tui.display_header()
            
            # Display statistics
            stats_text = f"""
[bold cyan]Analysis Results: {data['entity_name']}[/bold cyan]

Total Messages: {data['total_messages']:,}
Text Messages: {data['text_messages']:,}
Media Messages: {data['media_messages']:,}

Total Storage: {data['total_size_mb']:.2f} MB ({data['total_size_gb']:.2f} GB)

File Types:
"""
            for ftype, count in data['file_types'].items():
                stats_text += f"  {ftype}: {count:,}\n"
            
            self.tui.console.print(stats_text)
            self.tui.console.print()
            
            self.tui.menu_items = []
            self.tui.title = "ANALYSIS RESULTS"
            
            self.tui.add_menu_item("1", "Copy (Clipboard)", self.copy_chart)
            self.tui.add_menu_item("2", "Save (PNG Image)", self.save_chart_menu)
            self.tui.add_menu_item("x", "Back", self.setup_menu)
            
            # Display menu items
            for i, item in enumerate(self.tui.menu_items):
                self.tui.console.print(Text.from_ansi(str(item)))
            
            self.tui.console.print()
            
            choice = self.tui.get_menu_choice()
            
            if choice == 'x':
                break
            
            callback = self.tui.execute_menu_action(choice)
            
            if callback:
                if callback == self.setup_menu:
                    self.setup_menu()
                    break
                
                if asyncio.iscoroutinefunction(callback):
                    await callback()
                else:
                    callback()
        
        self.tui.title = "PIGRAM"
        self.setup_menu()

    def copy_chart(self):
        """Shows statistics text for manual copy (more reliable on Linux)."""
        self.tui.clear_screen()
        self.tui.display_header()
        
        # Get statistics text first
        data = self.file_analyzer.analysis_data
        if not data:
            self.tui.show_message("No analysis data available", "error")
            self.tui.wait_for_enter()
            return
        
        file_types = data['file_types']
        files_list = ""
        if file_types:
            for ftype, count in file_types.items():
                files_list += f"  {ftype:12s} {count:>8,}\n"
        else:
            files_list = "  No files found\n"
        
        stats_text = f"""STATISTICS
========================================
Total Messages:     {data['total_messages']:>12,}
Text Messages:      {data['text_messages']:>12,}
Media Messages:     {data['media_messages']:>12,}

STORAGE
========================================
Total Size:         {data['total_size_mb']:>12,.2f} MB
Total Size:         {data['total_size_gb']:>12,.2f} GB

FILES
========================================
{files_list}"""
        
        # Try to copy using system command (more reliable on Linux)
        copied = False
        try:
            import subprocess
            import sys
            
            # Try xclip first (most common on Linux)
            process = subprocess.Popen(['xclip', '-selection', 'clipboard'], stdin=subprocess.PIPE, 
                                      stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
            process.communicate(input=stats_text.encode('utf-8'))
            if process.returncode == 0:
                copied = True
        except:
            pass
        
        if not copied:
            try:
                # Try xsel as fallback
                process = subprocess.Popen(['xsel', '--clipboard', '--input'], stdin=subprocess.PIPE,
                                          stderr=subprocess.DEVNULL, stdout=subprocess.DEVNULL)
                process.communicate(input=stats_text.encode('utf-8'))
                if process.returncode == 0:
                    copied = True
            except:
                pass
        
        if copied:
            self.tui.show_message("Statistics copied to clipboard!", "success")
        else:
            self.tui.show_message("Clipboard not available. Text displayed below - select and copy manually.", "warning")
        
        # Always show the text for manual copy (left-aligned with internal formatting)
        self.tui.console.print("\n[bold cyan]Statistics:[/bold cyan]\n")
        self.tui.console.print("[bold white]" + stats_text + "[/bold white]")
        if not copied:
            self.tui.console.print("\n[yellow]Select the text above and press Ctrl+Shift+C (or right-click Copy)[/yellow]\n")
        
        self.tui.wait_for_enter()

    def save_chart_menu(self):
        """Saves chart as PNG image."""
        self.tui.clear_screen()
        self.tui.display_header()
        
        self.tui.show_message("Generating and saving chart...", "info")
        
        try:
            output_path = self.file_analyzer.save_chart()
            self.tui.show_message(f"Chart saved successfully!", "success")
            self.tui.show_message(f"Location: {output_path}", "info")
        except Exception as e:
            self.tui.show_message(f"Error saving chart: {e}", "error")
        
        self.tui.wait_for_enter()

    async def exit_app(self):
        """Function to exit the application."""
        await self.session_manager.stop_client()

    async def run(self):
        """Main application loop."""
        self.setup_menu()

        while True:
            self.tui.display_screen()

            choice = self.tui.get_menu_choice()

            if choice == 'x':
                await self.exit_app()
                self.tui.clear_screen()  # Clear screen before exit
                break

            callback = self.tui.execute_menu_action(choice)

            if callback:
                if callback == self.login_menu:
                    await self.login_menu()
                    continue

                if asyncio.iscoroutinefunction(callback):
                    await callback()
                else:
                    callback()


def main():
    """Main function."""
    try:
        Settings.ensure_directories()
        Settings.load_config()  # Load saved credentials

        app = PigramApp()
        asyncio.run(app.run())

    except KeyboardInterrupt:
        # Clear screen on Ctrl+C
        import os
        os.system('cls' if os.name == 'nt' else 'clear')
        sys.exit(0)
    except Exception as e:
        # Clear screen on fatal error
        import os
        os.system('cls' if os.name == 'nt' else 'clear')
        print(f"\n{Colors.colorize(f'Fatal error: {e}', Colors.ERROR)}{RESET}")
        sys.exit(1)


if __name__ == "__main__":
    main()
