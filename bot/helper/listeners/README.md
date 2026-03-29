# Event Listeners

This directory contains the core event-driven logic that orchestrates the bot's workflow. It essentially acts as the "glue" between the downloading phase and the uploading phase of a mirror or leech task.

## Purpose

When a user issues a command (like `/mirror`), the bot starts a download via Aria2, qBittorrent, or another tool. The bot then needs a way to know:
-   When did the download start?
-   Is it making progress?
-   Did it fail?
-   **When did it finish so the upload can begin?**

The classes and functions in `listeners/` are responsible for answering these questions. They "listen" for specific events emitted by the download clients and trigger the appropriate next steps in the bot's workflow.

## Key Listeners

-   **`aria2_listener.py`**: Interacts with the Aria2 RPC interface. It registers callbacks for events like `onDownloadComplete`, `onDownloadError`, and `onDownloadStart`. When Aria2 fires one of these events, this listener catches it, updates the database/task manager, and initiates the upload process (e.g., calling the Google Drive or Telegram upload utilities).
-   **`qbit_listener.py`**: Similar to the Aria2 listener but tailored for the qBittorrent API. Since qBittorrent doesn't push events in real-time like Aria2 RPC, this listener typically employs a polling mechanism (checking the torrent's status every few seconds) to determine when a download has completed or errored.
-   **Task Listeners (General)**: There are often generic task listeners or base classes that handle the common logic for *any* type of download (like `yt-dlp` or a simple `requests` download). They track the overall state (Downloading, Uploading, Cloning, Finished, Cancelled) and notify the user via Telegram messages when the state changes.

## Workflow Integration

1.  A download is started (e.g., via `Aria2Download()`).
2.  An instance of the appropriate listener (e.g., `Aria2Listener`) is created and attached to that specific download task.
3.  The listener waits for the download to finish.
4.  Once the download completes successfully, the listener retrieves the local file path.
5.  The listener then automatically invokes the correct upload utility (e.g., `GoogleDriveHelper().upload()`) based on the user's initial command and preferences.
