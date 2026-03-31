# Telegram Helper

This directory provides utility functions and classes specifically tailored to wrapping Pyrogram, the asynchronous MTProto framework used by the bot to communicate with the Telegram API.

## Core Components

- **`bot_commands.py`**: Defines a central class or dictionary containing all the commands the bot responds to (e.g., `START`, `MIRROR`, `STATUS`). This centralizes command strings, making it easy to change them globally or add prefixes.
- **`button_build.py`**: A highly utilized helper class for constructing Telegram Inline Keyboards. It abstracts the verbose Pyrogram syntax for creating rows and columns of buttons into a simple interface.
- **`filters.py`**: Custom Pyrogram filters used extensively in the command handlers (`bot/modules/`). These filters determine if a command should be processed based on conditions like:
  - Is the user authorized (an admin or a member of a specific chat)?
  - Is the bot configured to accept commands from this user's ID or chat ID?
  - Does the message contain a valid URL, document, or specific keywords?
- **`message_utils.py`**: Wrappers around Pyrogram's `send_message`, `edit_message_text`, `send_document`, `copy_message`, and other methods. These utilities often add automatic retry logic (to handle Telegram's `FloodWait` errors), automatic message deletion (to keep groups clean), and HTML/Markdown formatting validation.

## Purpose

By centralizing these Telegram-specific operations, the core logic of the bot (mirroring, cloning, etc.) remains decoupled from the specific implementation details of the Pyrogram library. This makes the code cleaner, easier to maintain, and less prone to API-specific errors.
