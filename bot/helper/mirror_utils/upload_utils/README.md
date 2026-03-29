# Upload Utilities

This directory contains the logic and wrappers for taking files that have been successfully downloaded locally and pushing them to their final destination.

## Destinations

The bot supports uploading files to three primary targets, each requiring distinct handling:

- **Google Drive**: Handled via the `gdrive_utils/` sub-module. This requires authenticating with the Google Drive API via service accounts or OAuth tokens, handling chunked uploads for large files, creating folders, and extracting shareable links.
- **Rclone Remotes**: Handled via the `rclone_utils/` sub-module. This wraps the `rclone copy` command to transfer files to any supported cloud provider, parsing the output to track progress.
- **Telegram (Leeching)**: Uses the Pyrogram client to send files back to the user or a designated log channel. This involves specific Pyrogram methods like `send_document`, `send_video`, or `send_audio`.

## Workflow

When an upload is initiated (usually by a listener in `bot/helper/listeners/` after a download completes):
1. The relevant utility in this folder is invoked with the local file path and the desired destination.
2. The utility checks for any user-specific preferences (e.g., upload destination, thumbnail settings, metadata extraction).
3. The upload process begins. The utility attaches a progress callback or parses command output to calculate upload speed, ETA, and percentage.
4. The bot updates the user's status message periodically with these metrics.
5. Upon completion, the local file is typically deleted to free up disk space, and a message containing the link to the uploaded file (or the file itself if sent to Telegram) is sent to the user.
