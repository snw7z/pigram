## pigram

A CLI tool with interactive TUI interface to automate Telegram-related tasks.

## Features

- 🎨 Retro/neon style TUI interface
- ⚡ Interactive navigation with arrow keys
- 🔐 Telethon integration for Telegram API
- 💾 Checkpoint system to resume cloning
- 🚀 Intelligent rate limiting

## Functionality

1. **Clone Groups**: List and clone Telegram groups (in development)
2. **Clone Chats**: Clone private conversations with checkpoint system
3. **Analyze Files**: Analyze Telegram files (in development)
4. **Login**: Complete session management with OTP and 2FA

## Installation

```bash
# Clone the repository
git clone https://github.com/snw7z/pigram.git
cd pigram

# Install dependencies
pip install -r requirements.txt
```

## Usage

```bash
python run.py
```

## Configuration

### Get Telegram API Credentials

1. Visit https://my.telegram.org
2. Log in with your phone number
3. Go to "API development tools"
4. Create a new application
5. Copy the **API ID** and **API Hash**

Credentials will be requested on first login and automatically saved to `~/.pigram/config.json`.

## Requirements

- Python 3.8+
- Termux (recommended) or any Linux terminal
- Telegram API credentials (API ID and API Hash)

## Project Structure

```
pigram/
├── run.py              # Main entry point
├── config/             # Configuration
│   └── settings.py     # Settings and paths
├── core/               # Main logic
│   ├── session.py      # Telethon session management
│   ├── cloner.py       # Group and chat cloning
│   └── analyzer.py     # File analysis
└── tui/                # User interface
    ├── interface.py    # Main TUI interface
    ├── colors.py       # ANSI color system
    └── ascii_art.py    # Logos and ASCII art
```

## Dependencies

- telethon>=1.24.0
- rich>=13.0.0
- prompt_toolkit>=3.0.36
- colorama>=0.4.6
- Pillow>=10.0.0
- numpy>=1.24.0
- matplotlib>=3.7.0
- pyperclip>=1.8.2


## Chat Cloning Features

- ✅ Checkpoint system (resumes from where it stopped)
- ✅ Batch processing
- ✅ Configurable rate limiting
- ✅ Automatic pause every N messages
- ✅ Automatic FloodWait handling
- ✅ Automatically ignores service messages
- ✅ Topic support

## Notes

- Sessions are saved in `~/.pigram/session.session`
- Credentials are saved in `~/.pigram/config.json`
- Checkpoints are saved in `~/.pigram/checkpoints/`

## License

MIT License
