"""
Telethon session management module.
"""

import asyncio
from pathlib import Path
from typing import Optional, Tuple, Dict, Any, Callable

from telethon import TelegramClient
from telethon.errors import (
    SessionPasswordNeededError,
    PhoneCodeInvalidError,
    PhoneCodeExpiredError,
    FloodWaitError,
    PasswordHashInvalidError,
    AuthKeyError,
    RPCError
)
from telethon.tl.functions.users import GetFullUserRequest

from config.settings import Settings


class SessionManager:
    """Manages Telethon session."""

    def __init__(self):
        self.client: Optional[TelegramClient] = None
        self.user_info: Dict[str, Any] = {}

    def get_client(self) -> Optional[TelegramClient]:
        """Returns the Telethon client instance."""
        return self.client

    def get_user_display_name(self) -> str:
        """Returns username or full name for display."""
        if self.user_info.get("username"):
            return f"@{self.user_info['username']}"
        elif self.user_info.get("first_name"):
            name = self.user_info['first_name']
            if self.user_info.get("last_name"):
                name += f" {self.user_info['last_name']}"
            return name
        return "Unknown User"

    async def check_session(self) -> bool:
        """Checks if session file exists and if client is connected."""
        session_file = Settings.SESSION_PATH.with_suffix('.session')
        if not session_file.exists():
            return False

        # Check if API_ID and API_HASH are configured
        if not Settings.API_ID or not Settings.API_HASH:
            # Don't delete session if only configuration is missing
            return False

        try:
            # Ensure directory exists before creating client
            Settings.ensure_directories()
            
            if not self.client:
                session_path_without_ext = str(
                    Settings.SESSION_PATH.parent / Settings.SESSION_PATH.stem
                )
                # Convert API_ID to int if necessary
                api_id_int = int(Settings.API_ID) if Settings.API_ID else None
                self.client = TelegramClient(
                    session=session_path_without_ext,
                    api_id=api_id_int,
                    api_hash=Settings.API_HASH
                )

            if not self.client.is_connected():
                await self.client.connect()

            if await self.client.is_user_authorized():
                me = await self.client.get_me()
                self.user_info = {
                    "username": me.username,
                    "first_name": me.first_name,
                    "last_name": me.last_name
                }
                return True

            return False

        except AuthKeyError:
            # Invalid authentication key - delete corrupted session
            try:
                if session_file.exists():
                    session_file.unlink()
            except Exception:
                pass
            return False
        except Exception as e:
            # Other errors (connection, timeout, etc.) - DON'T delete session
            # Just return False to try again later
            # This avoids losing session due to temporary network issues
            return False

    async def stop_client(self):
        """Stops Telethon client if running."""
        if self.client and self.client.is_connected():
            await self.client.disconnect()
        self.client = None

    async def login(
        self,
        api_id: str,
        api_hash: str,
        phone_number: str,
        otp_callback: Callable,
        password_callback: Callable
    ) -> Tuple[bool, str]:
        """Performs login to Telegram in a non-interactive way."""

        await self.stop_client()
        
        # Ensure directory exists before creating client
        Settings.ensure_directories()

        session_path_without_ext = str(
            Settings.SESSION_PATH.parent / Settings.SESSION_PATH.stem
        )

        # Convert api_id to int if necessary
        api_id_int = int(api_id) if api_id else None
        
        try:
            self.client = TelegramClient(
                session=session_path_without_ext,
                api_id=api_id_int,
                api_hash=api_hash
            )
        except Exception as e:
            await self.stop_client()
            return False, f"Error creating Telegram client: {e}. Check if directory {Settings.PIGRAM_DIR} exists and has write permissions."

        try:
            await self.client.connect()

            if not await self.client.is_user_authorized():
                await self.client.send_code_request(phone_number)

                code = otp_callback()

                try:
                    await self.client.sign_in(phone_number, code)
                except SessionPasswordNeededError:
                    password = password_callback()
                    await self.client.sign_in(password=password)

            me = await self.client.get_me()
            self.user_info = {
                "username": me.username,
                "first_name": me.first_name,
                "last_name": me.last_name
            }

            # Save API_ID and API_HASH to config file for future use
            Settings.save_credentials(api_id, api_hash)

            return True, f"Login successful as {self.get_user_display_name()}."

        except PhoneCodeInvalidError:
            await self.stop_client()
            return False, "Invalid OTP code."
        except PhoneCodeExpiredError:
            await self.stop_client()
            return False, "OTP code expired."
        except PasswordHashInvalidError:
            await self.stop_client()
            return False, "Invalid 2FA password."
        except FloodWaitError as e:
            await self.stop_client()
            return False, f"FloodWait: wait {e.seconds} seconds."
        except AuthKeyError:
            await self.stop_client()
            return False, "Invalid API ID or API HASH."
        except RPCError as e:
            await self.stop_client()
            return False, f"RPC Error: {e}"
        except Exception as e:
            await self.stop_client()
            return False, f"Unexpected error: {e}"

    async def logout(self) -> bool:
        """Deletes session and session file."""
        try:
            if self.client and self.client.is_connected():
                await self.client.log_out()

            session_file = Settings.SESSION_PATH.with_suffix('.session')
            if session_file.exists():
                session_file.unlink()

            self.client = None
            self.user_info = {}
            return True
        except Exception:
            return False
