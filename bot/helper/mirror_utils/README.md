# Mirror Utilities

This is the core execution engine of the bot. The term "mirror" in this context refers to the process of transferring a file from a source (like a direct link or torrent) to a destination (like Google Drive, Rclone, or Telegram).

## Structure

This directory is divided into specialized sub-modules based on the phase of the mirroring process:

-   **`download_utils/`**: Contains the logic and clients for acquiring the files locally. This includes wrappers for Aria2, qBittorrent, Telegram (for leeching), and `yt-dlp`.
-   **`upload_utils/`**: Contains the logic for taking the locally downloaded files and pushing them to their final destination (Google Drive, Rclone remotes, or back to Telegram).
-   **`gdrive_utils/`**: Specific, deep integration with the Google Drive API. This includes authentication, counting files, deleting, cloning (server-side copy), and handling nested folder uploads.
-   **`rclone_utils/`**: Wrappers for the `rclone` command-line tool, used to interface with dozens of different cloud storage providers.
-   **`status_utils/`**: Utilities specific to tracking the progress (speed, ETA, downloaded size) of active mirror tasks, formatting them into human-readable strings for the bot to display.

## Execution Flow

When a user initiates a `/mirror` or `/leech` command:
1.  The command handler in `bot/modules/` parses the request.
2.  It delegates the downloading to the appropriate module in `download_utils/` based on the link type.
3.  Once the download completes, a listener (in `bot/helper/listeners/`) is triggered.
4.  The listener then invokes the appropriate module in `upload_utils/` to transfer the file to the chosen destination.
