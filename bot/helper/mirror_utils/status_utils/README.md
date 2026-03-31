# Status Utilities

This directory contains logic and classes specifically tailored to tracking the status of ongoing tasks (downloads, uploads, cloning, extracting) and generating the human-readable strings displayed by the `/status` command.

## Purpose

The bot manages many long-running asynchronous tasks. Users need a way to see what the bot is currently doing, how fast it's doing it, and when it will finish. These utilities bridge the raw data from download clients (Aria2, qBittorrent, etc.) and upload clients (Google Drive API, Rclone, Pyrogram) into a unified format.

## Core Components

- **Status Classes**: Often, there are specific classes representing the status of different types of tasks (e.g., `Aria2Status`, `QbStatus`, `TgUploadStatus`, `GdriveStatus`). These classes typically inherit from a base `Status` class and implement methods to retrieve specific metrics like:
  - `name()`: The name of the file or task.
  - `size()`: The total size of the file.
  - `progress()`: The percentage completed.
  - `speed()`: The current download/upload speed (formatted).
  - `eta()`: The estimated time to completion (formatted).
  - `status()`: A string indicating the current state (e.g., "Downloading", "Uploading", "Extracting").

- **Formatting Functions**: Helper functions to generate progress bars (e.g., `[■■■■■■■□□□] 70%`), convert bytes to human-readable strings (e.g., "1.5 GB", "500 KB/s"), and format seconds into hours/minutes/seconds.

## Interaction

The `/status` command handler in `bot/modules/status.py` periodically iterates through all active tasks (often stored in a global dictionary or managed by `bot/helper/ext_utils/task_manager.py`), calls these status classes to get the latest metrics, and compiles them into a single message string that is edited in the user's chat.
