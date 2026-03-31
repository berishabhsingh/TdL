# External Utilities (`bot/helper/ext_utils/`)

This directory contains the essential utilities that bridge the core bot logic (in `bot/helper/`) with external services, databases, specific file parsing, and system-level interactions. It is the "glue" that holds the complex features of the LeechxTool together.

## Core Components

- **`bot_utils.py`**: Contains core wrapper functions and async utilities used extensively throughout the project. It often provides safe ways to run subprocesses, synchronize asynchronous tasks, and manage general execution contexts.
- **`db_handler.py`**: The central interface for interacting with the MongoDB database (if configured). It abstracts the PyMongo commands to manage user authorizations, user-specific settings, bot configurations, and incomplete task tracking.
- **`task_manager.py`**: Crucial for tracking and limiting the number of concurrent tasks (downloads/uploads) per user or globally to prevent overloading the server or bot limits.
- **`conf_loads.py`**: Handles loading, parsing, and verifying the `config.env` file. It sets default values for missing configurations and prepares them for the rest of the application.

## Specific Utilities

- **`files_utils.py`**: A robust set of functions for interacting with the local file system. It handles creating directories, moving files, cleaning up downloads after completion or failure, and safely parsing file names.
- **`links_utils.py`**: Parses and identifies the type of incoming links (e.g., direct download, Google Drive, Mega, Telegram file). It dictates which downloading mechanism should handle a specific URL.
- **`status_utils.py`**: Contains functions to calculate human-readable file sizes, ETAs, and progress bars. This is essential for the `/status` command and real-time updating messages.
- **`shortenurl.py`**: Integrates with external URL shortener APIs (like Bitly or custom shorteners) to condense long generated cloud links before sending them back to the user.
- **`telegraph_helper.py`**: Wraps the Telegraph API to create rich-text log pages or long-form output (such as search results or extensive error logs) that would exceed Telegram's message length limits.
- **`media_utils.py`**: Uses `ffprobe` (via FFmpeg) to extract metadata from downloaded audio and video files (like duration, resolution, codecs) before uploading them. This ensures the Telegram client displays them correctly.
- **`jdownloader_booter.py`**: Specifically handles the startup, configuration, and shutdown of a background JDownloader instance, working in tandem with the `myjd/` API client.
- **`ping.py` & `argo_tunnel.py`**: Utilities for checking connection latency, bypassing Cloudflare protections, or setting up secure tunnels for the bot's web interface.
