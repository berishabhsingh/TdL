# qBittorrent

This directory contains configuration files and setup details for integrating qBittorrent with the LeechxTool bot.

## Purpose

The bot utilizes qBittorrent to handle torrent downloads. It communicates with the local qBittorrent client via the `qbittorrent-api` module. The bot programmatically adds torrents, manages file priorities, and monitors download progress, which is then updated and sent to users on Telegram.

## Structure

The `qBittorrent/config/` directory includes the primary configuration file, `qBittorrent.conf`. This is the settings file loaded by `qbittorrent-nox` (the headless version of qBittorrent) when it starts up.

### `qBittorrent.conf` Details

This INI-style configuration file dictates how qBittorrent operates. It is divided into sections like `[Network]`, `[BitTorrent]`, `[Preferences]`, and `[WebUI]`. Some of the most critical settings include:

-   **Network Limits (`[BitTorrent]` and `[Preferences]`)**: This section defines connection limits, global upload/download speeds, and active torrent limits. If you need to tweak how aggressively the client downloads or seeds, you can modify these values (e.g., `Session\MaxActiveDownloads`, `Session\GlobalMaxRatio`).
-   **Web UI Integration (`[WebUI]`)**: The Web UI section is crucial. The bot interacts with qBittorrent via its Web API. This section configures the Web UI's port (`WebUI\Port=8090`), authentication settings, and whether the UI is enabled. Ensure `WebUI\LocalHostAuth` is set appropriately so the bot can connect without prompting for credentials, or make sure the bot uses the correct login details.
-   **Download Paths (`[Preferences]`)**: Defines the default save path for incomplete and complete downloads (`Downloads\SavePath` and `Downloads\TempPath`).

## Modifying Configurations

To modify qBittorrent settings:
1.  Open `qBittorrent/config/qBittorrent.conf`.
2.  Locate the setting you wish to change (e.g., `Session\MaxActiveDownloads`).
3.  Update the value.
4.  Restart the bot (or specifically the `qbittorrent-nox` process) for the new settings to take effect.
