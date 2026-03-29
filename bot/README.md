# Bot

This directory contains the main source code for the Telegram bot, which is a key component of the LeechxTool project. It is responsible for interacting with users via Telegram, handling commands, and managing various background tasks.

## Contents

- **`__main__.py`**: The main entry point for starting the bot. It initializes the Telegram client, sets up command handlers, and starts background services like the web server, Aria2 listener, and Rclone serve.
- **`modules/`**: Contains the implementations of individual bot commands and features (e.g., `/mirror`, `/leech`, `/clone`, `/search`, etc.).
- **`helper/`**: Contains utility functions and classes used throughout the bot, including database interaction, external API integration, and file management.

## Functionality

The bot handles user requests to mirror, leech, clone, and download files from various sources to either Telegram, Google Drive, or Rclone supported cloud storages. It also supports downloading from YouTube and other supported websites via `yt-dlp` and managing torrent downloads via Aria2 and qBittorrent.
