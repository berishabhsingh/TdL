# Download Utilities

This directory contains the logic and wrappers for acquiring files locally on the bot's host machine before they are uploaded to their final destination.

## Clients & Methods

The bot utilizes several distinct tools depending on the source URL or protocol:

- **Aria2**: Used for direct HTTP/HTTPS links, FTP, and general-purpose downloading. It is often the default choice due to its speed and multi-connection capabilities.
- **qBittorrent**: Specifically handles torrents and magnet links. It provides granular control over file selection and robust DHT/tracker support.
- **Telegram (Leeching)**: If a user replies to a Telegram file (document, video, audio) with `/mirror`, the bot uses the Pyrogram client to download that file locally.
- **JDownloader (`myjd`)**: If configured, the bot can use an external JDownloader instance to bypass captchas, wait times, or handle complex hosters that Aria2 cannot manage natively.
- **yt-dlp**: Used when the user provides a link to YouTube, Instagram, Twitter, or hundreds of other supported video/audio streaming sites. It extracts the direct media URLs and downloads them.
- **Direct Link Extractors**: Some files are direct links but require special handling, cookies, or headers to download.

## Lifecycle

When a download is started, the relevant utility in this folder:
1. Validates the input link.
2. Initializes the download client.
3. Attaches an event listener (from `bot/helper/listeners/`) to the task. This listener periodically polls the client to update the user on the download speed, ETA, and overall progress.
4. Handles cleanup if the download fails or is canceled.
