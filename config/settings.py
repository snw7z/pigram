# Content of config/settings.py

"""
pigram configuration module.
Manages general application settings.
"""

import os
import json
from pathlib import Path


class Settings:
    """Application settings class."""

    # Directories
    BASE_DIR = Path(__file__).parent.parent

    # Session directories
    HOME_DIR = Path.home()
    PIGRAM_DIR = HOME_DIR / ".pigram"
    SESSION_PATH = PIGRAM_DIR / "session.session"  # Session file path
    CONFIG_FILE = PIGRAM_DIR / "config.json"  # Configuration file

    # Telegram API - initializes empty, will be loaded from file or env
    API_ID = ""
    API_HASH = ""

    # Application settings
    APP_NAME = "pigram"
    APP_VERSION = "0.1.0"

    @classmethod
    def ensure_directories(cls):
        """Ensures necessary directories exist."""
        try:
            cls.PIGRAM_DIR.mkdir(parents=True, exist_ok=True)
        except Exception as e:
            # If can't create, try to create parent directory
            raise RuntimeError(f"Could not create directory {cls.PIGRAM_DIR}: {e}")

    @classmethod
    def load_config(cls):
        """Loads configuration from file or environment variables."""
        # Try to load from config file first
        if cls.CONFIG_FILE.exists():
            try:
                with open(cls.CONFIG_FILE, 'r', encoding='utf-8') as f:
                    config = json.load(f)
                    cls.API_ID = str(config.get("api_id", ""))
                    cls.API_HASH = config.get("api_hash", "")
            except Exception:
                # If error reading file, try environment variables
                cls.API_ID = os.getenv("TELEGRAM_API_ID", "")
                cls.API_HASH = os.getenv("TELEGRAM_API_HASH", "")
        else:
            # If file doesn't exist, try environment variables
            cls.API_ID = os.getenv("TELEGRAM_API_ID", "")
            cls.API_HASH = os.getenv("TELEGRAM_API_HASH", "")

    @classmethod
    def save_credentials(cls, api_id: str, api_hash: str):
        """Saves API credentials to config file."""
        cls.ensure_directories()
        try:
            config = {
                "api_id": api_id,
                "api_hash": api_hash
            }
            with open(cls.CONFIG_FILE, 'w', encoding='utf-8') as f:
                json.dump(config, f, indent=2)
            cls.API_ID = api_id
            cls.API_HASH = api_hash
        except Exception as e:
            # If can't save, at least update in memory
            cls.API_ID = api_id
            cls.API_HASH = api_hash

    @classmethod
    def is_configured(cls) -> bool:
        """Checks if application is configured."""
        return bool(cls.API_ID and cls.API_HASH)


# Initialize directories on import
# Settings.ensure_directories() # Removed to avoid circular import issues. Called in run.py
