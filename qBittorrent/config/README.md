# qBittorrent Config

This directory contains the essential configuration files that dictate how the `qbittorrent-nox` (headless) client operates when started by the LeechxTool bot.

## `qBittorrent.conf` Details

The primary file here is `qBittorrent.conf`. This is an INI-style configuration file read by qBittorrent on startup. It is organized into several key sections:

### `[Network]`
Controls how qBittorrent interacts with the internet.
- **Port Forwarding**: Settings like `PortForwardingEnabled` and `ListenPort` determine if and how qBittorrent accepts incoming connections from peers.

### `[BitTorrent]`
Controls the core torrenting behavior.
- **Limits**: `Session\MaxActiveDownloads`, `Session\MaxActiveTorrents`, and `Session\MaxActiveUploads` dictate how many torrents can be active simultaneously.
- **Speed Limits**: `Session\GlobalMaxRatio`, `Session\GlobalMaxSeedingMinutes` (often set to stop seeding immediately after download for a leech bot), and `Session\GlobalDownloadRateLimit` (to throttle bandwidth if needed).
- **Privacy**: Settings related to DHT, PeX, and Local Peer Discovery.

### `[Preferences]`
General application preferences.
- **Directories**: `Downloads\SavePath` and `Downloads\TempPath` are crucial. They tell qBittorrent where to save incomplete files and where to move them once finished. The bot relies on these paths to locate the files for uploading.
- **Mail Notification**: (Rarely used in this bot context, but available).

### `[WebUI]`
This is the most critical section for the bot's integration. The bot does not use a GUI; it communicates with qBittorrent entirely via its Web API.
- **`WebUI\Port`**: The port the API listens on (e.g., `8090`).
- **`WebUI\LocalHostAuth`**: Often set to `false` in containerized environments or `true` if running locally, dictating if authentication is required for requests coming from `127.0.0.1`.
- **`WebUI\Username` & `WebUI\Password_PBKDF2`**: The credentials the bot must use to authenticate with the API if `LocalHostAuth` is required.

## Modifying Settings

If you need to change how qBittorrent behaves (e.g., increasing the maximum number of concurrent downloads or changing the Web UI port to avoid a conflict):
1.  Stop the bot (and the `qbittorrent-nox` process).
2.  Edit `qBittorrent.conf`.
3.  Save the file.
4.  Restart the bot. The new settings will take effect immediately.
