# Rclone Utilities

This directory contains the wrappers and utilities for interacting with the `rclone` command-line tool, enabling the bot to transfer files to and from dozens of different cloud storage providers (e.g., OneDrive, Dropbox, Mega, WebDAV, FTP).

## Features

- **Configuration Setup**: Provides tools to read, parse, and utilize an `rclone.conf` file provided by the user or admin, establishing connections to named "remotes."
- **Uploading**: Wraps the `rclone copy` or `rclone sync` commands to transfer locally downloaded files to a specified remote path. This often includes flags for handling chunk sizes, parallel transfers, and retries to optimize upload speed.
- **Serving**: Uses `rclone serve` to expose remote files via HTTP or WebDAV. This is useful for sharing large files directly from the cloud without moving them through Telegram's servers.
- **Listing/Searching**: Wraps the `rclone ls` and `rclone lsf` commands to browse the contents of a remote storage account, allowing users to select paths or search for specific files.

## Workflow

When an upload to Rclone is triggered:
1. The bot verifies the existence and validity of the `rclone.conf` file.
2. It constructs an `rclone` command using the `subprocess` module.
3. It executes the command, parsing the stdout/stderr to extract upload speed, ETA, and progress percentages.
4. It updates the user's status message with the current progress.
5. Upon completion, it returns the link to the uploaded file (if supported by the remote).
