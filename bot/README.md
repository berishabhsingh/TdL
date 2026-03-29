# Bot

This directory contains the main source code for the Telegram bot, which is the core interface of the LeechxTool project. It is built using the `pyrogram` framework.

## Architecture

The bot is designed to handle user requests via Telegram, parse them, and execute complex background tasks such as downloading, mirroring, and cloning files.

### Key Components

- **`__main__.py`**: The main entry point. It initializes the Pyrogram `Client`, sets up all command handlers, and starts essential background services asynchronously (e.g., the Flask web server, Aria2 listener, and Rclone serve).
- **`modules/`**: This directory contains individual Python files for each major feature or set of commands (e.g., `mirror_leech.py`, `clone.py`, `search.py`). This modular structure keeps the code organized.
- **`helper/`**: Contains sub-directories for specific utilities:
  - `ext_utils/`: External utilities like database handlers, configurations, and bot utilities.
  - `mirror_utils/`: Specific utilities for mirroring tasks (Aria2, qBittorrent, etc.).
  - `telegram_helper/`: Pyrogram-specific helpers like filters, message editing, and button builders.

## How to Add a New Command

To add a new feature or command to the bot, follow these steps:

1. **Create a Module**: If the feature is large, create a new file in `bot/modules/` (e.g., `my_new_feature.py`). If it's small, you might add it to an existing related module like `misc_tools.py`.
2. **Define the Handler**: Write an async function that accepts a `Client` and `Message` object.
   ```python
   from pyrogram import Client, filters
   from bot import bot

   @bot.on_message(filters.command('mycommand'))
   async def my_handler(client: Client, message):
       await message.reply_text('Hello World!')
   ```
3. **Import the Module**: Ensure your new module is imported in `bot/modules/__init__.py` or `bot/__main__.py` so that Pyrogram registers the handler when the bot starts.
4. **Update Help Menu**: If the command should be public, add it to the `HelpString` utility in `bot/helper/ext_utils/help_messages.py`.

## Background Services

The bot relies on several external tools running alongside it. `__main__.py` typically handles ensuring these listeners or processes are started:
- **Aria2**: Managed via `aria2p` or custom wrappers for handling torrents and direct downloads.
- **qBittorrent**: Managed via `qbittorrent-api`.
- **yt-dlp**: Used for fetching videos and media from supported sites.
- **Web Server**: A Flask server (`web/wserver.py`) is started in the background to handle the file selection UI for torrents.
