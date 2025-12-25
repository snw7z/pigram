"""
Telegram groups and chats cloning module.
Uses Telethon to access and clone content.
"""

import asyncio
import os
from pathlib import Path
from typing import Optional, List, Dict, Callable
from telethon import TelegramClient, errors
from telethon.tl.types import MessageService

from config.settings import Settings


class GroupCloner:
    """Manages Telegram groups cloning."""

    def __init__(self, client: TelegramClient):
        self.client = client

    async def list_groups(self) -> List[Dict]:
        """
        Lists all available groups and channels.

        Returns:
            List of dictionaries with group/channel information
        """
        groups_list = []

        async for dialog in self.client.iter_dialogs():
            if dialog.is_group or dialog.is_channel:
                groups_list.append({
                    "id": dialog.id,
                    "title": dialog.title,
                    "type": "CHANNEL" if dialog.is_channel else "GROUP",
                    "username": dialog.entity.username if hasattr(dialog.entity, 'username') else "N/A"
                })

        return groups_list

    def clone_group(self, group_id: int, target_name: str) -> bool:
        # TODO: Implement group cloning
        print(f"[GroupCloner] Cloning group {group_id} to '{target_name}'")
        return True


class ChatCloner:
    """Manages Telegram private chats cloning."""

    def __init__(self, client: TelegramClient):
        self.client = client
        self.is_running = False
        self.checkpoint_dir = Settings.PIGRAM_DIR / "checkpoints"
        self.checkpoint_dir.mkdir(exist_ok=True)

    def _get_checkpoint_file(self, source_id: str, target_id: str) -> Path:
        filename = f"checkpoint_{source_id}_{target_id}.txt"
        return self.checkpoint_dir / filename

    def _load_checkpoint(self, checkpoint_file: Path) -> int:
        if checkpoint_file.exists():
            try:
                with open(checkpoint_file, "r", encoding="utf-8") as f:
                    return int(f.read().strip())
            except Exception:
                return 0
        return 0

    def _save_checkpoint(self, checkpoint_file: Path, message_id: int):
        try:
            with open(checkpoint_file, "w", encoding="utf-8") as f:
                f.write(str(message_id))
        except Exception as e:
            print(f"[ChatCloner] Error saving checkpoint: {e}")

    async def clone_chat(
        self,
        source_chat_id: str,
        target_chat_id: str,
        batch_size: int = 100,
        delay_between_messages: float = 0.8,
        pause_every_n: int = 3000,
        pause_duration: int = 500,
        source_topic_id: Optional[int] = None,
        target_topic_id: Optional[int] = None,
        progress_callback: Optional[Callable] = None,
        status_callback: Optional[Callable] = None
    ) -> Dict:
        self.is_running = True
        checkpoint_file = self._get_checkpoint_file(source_chat_id, target_chat_id)
        last_id = self._load_checkpoint(checkpoint_file)

        global_counter = 0
        total_sent = 0
        errors_count = 0

        if status_callback:
            status_callback(f"📥 Starting cloning from {source_chat_id} to {target_chat_id}")
            if last_id > 0:
                status_callback(f"Resuming from ID {last_id}...")

        try:
            source_entity = await self.client.get_entity(int(source_chat_id))
            target_entity = await self.client.get_entity(int(target_chat_id))

            if status_callback:
                status_callback(f"✅ Source: {getattr(source_entity, 'title', getattr(source_entity, 'first_name', 'Unknown'))}")
                status_callback(f"✅ Target: {getattr(target_entity, 'title', getattr(target_entity, 'first_name', 'Unknown'))}")

        except Exception as e:
            if status_callback:
                status_callback(f"❌ Error getting chat entities: {e}")
            return {"success": False, "total_messages": 0, "errors": 1, "error": str(e)}

        while self.is_running:
            topic_info = f" (source topic {source_topic_id})" if source_topic_id else ""

            # Fix for status "flood": use print with \r to overwrite line
            if status_callback:
                print(f"\r🔍 Searching up to {batch_size} messages from ID {last_id}{topic_info}...", end="", flush=True)

            try:
                # Fix for infinite loop: use min_id and reverse=True (as in original Bot.py)
                messages = await self.client.get_messages(
                    source_entity,
                    min_id=last_id,
                    limit=batch_size,
                    reverse=True,
                    reply_to=source_topic_id
                )

            except Exception as e:
                if status_callback:
                    print()  # New line after search
                    status_callback(f"❌ Error fetching messages: {e}")
                break

            if not messages:
                if status_callback:
                    print()  # New line after search
                    status_callback("✅ No new messages found. Finishing.")
                break

            # Order is now from oldest to newest, so we don't need to reverse
            for msg in messages:
                if not self.is_running:
                    if status_callback:
                        status_callback("⏸️ Cloning paused by user.")
                    break

                if isinstance(msg, MessageService):
                    continue

                try:
                    global_counter += 1

                    await self.client.send_message(
                        entity=target_entity,
                        message=msg,
                        reply_to=target_topic_id
                    )

                    total_sent += 1
                    last_id = msg.id
                    self._save_checkpoint(checkpoint_file, last_id)

                    if progress_callback:
                        progress_callback(global_counter, msg.id)

                    await asyncio.sleep(delay_between_messages)

                    # Pause every 3000 messages (exactly as in Bot.py)
                    if total_sent >= pause_every_n:
                        if status_callback:
                            print()  # New line before pause
                            status_callback(f"💤 Pausing {pause_duration}s after {pause_every_n} messages...")
                        await asyncio.sleep(pause_duration)
                        total_sent = 0  # Reset counter after pause

                except errors.FloodWaitError as e:
                    if status_callback:
                        print()  # New line before FloodWait
                        status_callback(f"⏳ FloodWait: waiting {e.seconds}s...")
                    await asyncio.sleep(e.seconds + 5)

                except errors.AuthKeyError:
                    # Session was invalidated - stop cloning
                    if status_callback:
                        print()  # New line before error
                        status_callback(f"❌ CRITICAL ERROR: Session invalidated! Cloning interrupted.")
                        status_callback(f"💡 You need to login again.")
                    self.is_running = False
                    break

                except errors.RPCError as e:
                    # Check if it's authorization invalidated error
                    error_msg = str(e).lower()
                    if ("authorization" in error_msg and ("invalidated" in error_msg or "terminated" in error_msg)) or \
                       "session revoked" in error_msg or \
                       "user deactivated" in error_msg:
                        if status_callback:
                            print()  # New line before error
                            status_callback(f"❌ CRITICAL ERROR: Authorization invalidated! Cloning interrupted.")
                            status_callback(f"💡 Telegram terminated your session. Please login again.")
                        self.is_running = False
                        break
                    else:
                        # Other RPC error - log but continue
                        errors_count += 1
                        if status_callback:
                            print()  # New line before error
                            status_callback(f"❌ RPC Error ID {msg.id}: {e}")

                except Exception as e:
                    error_msg = str(e).lower()
                    # Check if it's authorization error even if not RPCError
                    if ("authorization" in error_msg and ("invalidated" in error_msg or "terminated" in error_msg)) or \
                       "session revoked" in error_msg or \
                       "user deactivated" in error_msg:
                        if status_callback:
                            print()  # New line before error
                            status_callback(f"❌ CRITICAL ERROR: Authorization invalidated! Cloning interrupted.")
                            status_callback(f"💡 Telegram terminated your session. Please login again.")
                        self.is_running = False
                        break
                    else:
                        errors_count += 1
                        if status_callback:
                            print()  # New line before error
                            status_callback(f"❌ Unexpected error ID {msg.id}: {e}")

        if status_callback:
            print()  # Ensure a new line at the end
            status_callback(f"\n🏁 Cloning finished!")
            status_callback(f"📊 Total messages copied: {global_counter}")
            status_callback(f"❌ Errors: {errors_count}")

        return {
            "success": True,
            "total_messages": global_counter,
            "errors": errors_count,
            "last_id": last_id
        }

    def stop_cloning(self):
        self.is_running = False

    async def get_total_messages(self, chat_id: str) -> int:
        """Gets the total number of messages in a chat."""
        try:
            entity = await self.client.get_entity(int(chat_id))
            # Telethon uses .total_messages to get total messages
            # in channels/groups. For private chats, it can be 0 or None.
            # We use get_messages(limit=0) to force count if necessary,
            # but entity's total_messages is more efficient.
            if hasattr(entity, 'total_messages') and entity.total_messages is not None:
                return entity.total_messages

            # Less efficient alternative for private chats or where total_messages is not available
            # messages = await self.client.get_messages(entity, limit=0)
            # return messages.total

            # For now, return 0 to avoid slow calls, focusing on channels/groups
            return 0
        except Exception as e:
            print(f"[ChatCloner] Error getting total messages for {chat_id}: {e}")
            return 0

    async def list_chats(self) -> List[Dict]:
        chats_list = []
        async for dialog in self.client.iter_dialogs():
            if dialog.is_user:
                chats_list.append({
                    "id": dialog.id,
                    "name": dialog.name,
                    "username": dialog.entity.username if hasattr(dialog.entity, 'username') else "N/A"
                })
        return chats_list
