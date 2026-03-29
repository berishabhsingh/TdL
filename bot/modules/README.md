# Bot Modules

This directory contains the implementations of all the Telegram bot commands. Each file here maps directly to one or more user-facing commands (like `/mirror`, `/clone`, `/search`) and acts as the "controller" connecting Telegram users to the core download/upload logic found in `bot/helper/`.

## Architecture

Modules in this directory are structured as Pyrogram `MessageHandler` callbacks. They define decorators (e.g., `@bot.on_message(filters.command(...))`) that instruct the bot to execute a specific function when a matching command is received.

A typical module flow is:
1. **Command Reception**: Receives `/mirror <url>` via Pyrogram.
2. **Parsing & Validation**: Uses `bot/helper/telegram_helper/` to parse the command arguments, check user authorization, and handle edge cases (like missing URLs).
3. **Execution Delegation**: Calls the appropriate logic in `bot/helper/mirror_utils/` or `bot/helper/ext_utils/` to actually begin the download or task.
4. **Response**: Sends an initial "Downloading..." message back to the user, and attaches progress callbacks.

## Key Modules

- **`mirror_leech.py`**: The heart of the bot. Handles the `/mirror` (download then upload to Cloud) and `/leech` (download then upload to Telegram) commands. It supports direct links, torrents, magnets, and Google Drive links.
- **`clone.py`**: Handles `/clone` commands for directly copying files between cloud storage (e.g., Google Drive to Google Drive, or Rclone to Rclone) without downloading them locally first.
- **`ytdlp.py`**: Handles `/ytdl` and `/ytdlleech` commands. It parses YouTube or supported site URLs, allows quality selection via inline buttons, and utilizes `yt-dlp` to download the media before uploading.
- **`status.py`**: Implements the `/status` command. It aggregates data from all active downloads/uploads across Aria2, qBittorrent, and Telegram, formats it into a single readable message, and sends it. It also manages updating this message periodically.
- **`cancel_task.py`**: Handles the `/cancel` command, allowing users or admins to stop a specific ongoing download or upload by its unique ID.
- **`bot_settings.py` & `user_settings.py`**: Interactive menus for managing configuration. `bot_settings` allows admins to tweak global variables, while `user_settings` allows individual authorized users to configure their specific upload destinations, preferred video qualities, or leech settings.
- **`authorize.py`**: Admin commands (`/authorize`, `/unauthorize`, `/users`) to manage which Telegram users or chats are allowed to use the bot.
- **`torrent_search.py`**: Implements the `/search` command, utilizing plugins to query public and private torrent trackers and returning the results to the user.
