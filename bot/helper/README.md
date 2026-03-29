# Bot Helpers

This directory contains the foundational logic, wrappers, utilities, and helper classes that the Telegram bot relies upon. It abstracts the complexity of connecting to external APIs, managing the database, and wrapping complex download/upload mechanisms so that the command modules (`bot/modules/`) remain clean and readable.

## Structure

The helper directory is subdivided into specialized utility folders:

- **`ddl_bypass/`**: Logic for bypassing direct download links (DDLs) to retrieve the final downloadable file URL. This involves circumventing timers, captchas, and link shorteners.
- **`ext_utils/`**: General external utilities. This is one of the most critical folders. It houses:
  - Database handlers (`db_handler.py`).
  - Formatting, timing, and string manipulation utilities.
  - Core async task wrappers (`bot_utils.py`).
  - Short URL generators and telegraph integration.
- **`listeners/`**: Contains event listeners for download clients (like Aria2 and qBittorrent) that trigger bot actions upon download start, progress, and completion.
- **`mirror_utils/`**: The core engine for downloading and uploading. It abstracts interactions with:
  - Aria2 and qBittorrent.
  - JDownloader (`myjd`).
  - Cloud uploaders (Google Drive, Rclone, Telegram).
- **`stream_utils/`**: Utilities related to streaming media or handling streamable file properties.
- **`telegram_helper/`**: Pyrogram-specific wrappers. It includes helper classes to create inline keyboards (`button_build.py`), manage messages (`message_utils.py`), parse incoming commands, and custom Pyrogram filters (`filters.py`).
- **`video_utils/`**: FFmpeg wrappers and tools to extract video metadata, generate thumbnails, take screenshots, or manipulate video streams before uploading.

## `common.py`

The root of the `helper/` directory contains `common.py` (and `__init__.py`). `common.py` typically houses shared enumerations, data structures (like status dictionaries), or globally needed functions that bridge multiple helper sub-modules together without causing circular imports.
