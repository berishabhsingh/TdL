# LeechxTool - The Ultimate Telegram Bot for Downloading & Uploading

Hello! Welcome to LeechxTool.

If you're wondering how this code actually works, here's a super simple explanation, designed so that even a **class 6 boy** can understand what's happening under the hood!

## How the Code Works (A Simple Story)

Imagine you are a busy manager (that's the `Telegram Bot`) working in an office. You have a few specialist workers helping you out:
1. **The Downloader (Aria2 & qBittorrent):** These guys are experts at downloading files from the internet fast.
2. **The Video Guy (Yt-Dlp & FFmpeg):** This guy loves watching videos. You give him a YouTube link, and he brings the video file to your desk.
3. **The Web Assistant (Flask):** This person handles web pages, like a simple website you might visit.
4. **The Memory Bank (MongoDB):** This is your giant filing cabinet where you store all your settings.

### Step-by-Step Breakdown: `bot/__init__.py` (The Manager's Morning Routine)
When we type `bash start.sh` to start the bot, the very first major file that runs is `bot/__init__.py`. Here is exactly what happens when that file runs:

1. **Waking Up (Imports):** The bot brings in all the tools it needs to work (like `sleep`, `time`, and `os`).
2. **Reading the To-Do List (Environment Variables):** The bot reads a secret file called `config.env` using `load_dotenv`. This file has your secrets like `BOT_TOKEN` (the manager's ID badge) and `DATABASE_URL` (the key to the filing cabinet).
3. **Checking the Filing Cabinet (MongoDB):** The bot connects to the MongoDB database to see if you saved any custom settings previously. If it finds settings, it loads them up.
4. **Starting the Web Assistant:** It runs a web server using `gunicorn` so you can use certain website features.
5. **Waking up the Downloaders:** The bot starts `qbittorrent-nox` (for torrents) and `aria2` (for direct downloads). It even fetches a list of "trackers" from the internet to make torrent downloads faster!
6. **Logging In to Telegram (Pyrogram):** Finally, it uses a library called `Pyrofork` (a version of Pyrogram) to log in to Telegram. It says: "Hello Telegram! I am ready to receive messages!"
7. **Listening for Messages:** From this point on, the bot sits quietly, waiting for you to type commands like `/mirror` or `/leech`.

When you type a command, the Manager (Bot) gives the task to the right specialist (Downloader or Video Guy), and when they finish, the Manager uploads the file to Google Drive or sends it back to you on Telegram!

---

## Features

- **Mirroring**: Download from direct links, Torrents, YouTube, Mega, Google Drive, and more to Google Drive or Rclone.
- **Terabox API Integration**: Seamlessly fetches direct links using the `tdl-production.up.railway.app` API, eliminating the need for `terabox.txt` cookies.
- **Leeching**: Upload downloaded files directly to Telegram.
- **Clone**: Clone files between Google Drive, Rclone, and other supported cloud storages.
- **Yt-Dlp Support**: Download videos from YouTube and supported sites with custom quality selection.
- **JDownloader Support**: Download files using JDownloader.
- **Torrents**: Support for public and private trackers, magnet links, and torrent files.
- **Search**: Built-in torrent search feature.
- **RSS Feed**: Automated downloading via RSS feeds.
- **User Management**: Authorize specific users or chats.
- **Bot Management**: Extensive control over bot settings via commands.

## Deployment

### Docker (Recommended)

We are now using a standard `python:3.12-slim` image, so everything is fully customizable!

1.  **Clone the repository:**
    ```bash
    git clone https://github.com/YourUsername/LeechxTool.git
    cd LeechxTool
    ```

2.  **Build the Docker image:**
    ```bash
    docker build -t leechxtool .
    ```

3.  **Run the container:**
    ```bash
    docker run -d \
      -e BOT_TOKEN="your_bot_token" \
      -e OWNER_ID="your_owner_id" \
      -e TELEGRAM_API="your_api_id" \
      -e TELEGRAM_HASH="your_api_hash" \
      -v $(pwd)/config.env:/usr/src/app/config.env \
      -v $(pwd)/accounts:/usr/src/app/accounts \
      -p 80:80 \
      -p 8080:8080 \
      leechxtool
    ```

### VPS / Local Machine

1.  **Install System Dependencies:**
    -   Python 3.12+
    -   FFmpeg
    -   Aria2
    -   qBittorrent-nox
    -   p7zip-full
    -   curl, wget, git, build-essential

2.  **Install Python Packages:**
    ```bash
    pip install -r requirements.txt
    ```

3.  **Configure:**
    -   Create a `config.env` file in the root directory and fill in the values below.

4.  **Run:**
    ```bash
    bash start.sh
    ```

## Configuration (`config.env`)

| Variable | Description |
| :--- | :--- |
| `BOT_TOKEN` | Your Telegram Bot Token. |
| `OWNER_ID` | Your Telegram User ID. |
| `TELEGRAM_API` | Your Telegram API ID. |
| `TELEGRAM_HASH` | Your Telegram API Hash. |
| `DATABASE_URL` | MongoDB Connection String. |
| `DOWNLOAD_DIR` | Directory for downloads (default: `/usr/src/app/downloads/`). |
| `GDRIVE_ID` | Google Drive Folder ID for uploads. |
| `RCLONE_PATH` | Rclone remote path (e.g., `remote:path`). |
| `DEFAULT_UPLOAD` | `gd` (Google Drive) or `rc` (Rclone). |
| `UPSTREAM_REPO` | Git URL for bot updates. |
| `FSUB_CHANNEL_ID` | Channel ID for forced subscription. |

*See `bot/__init__.py` for the full list of optional configurations.*

## Commands

| Command | Description |
| :--- | :--- |
| `/start` | Start the bot. |
| `/mirror`, `/m` | Mirror file/link to Cloud. |
| `/leech`, `/l` | Leech file/link to Telegram. |
| `/ytdl`, `/y` | Download via Yt-Dlp to Cloud. |
| `/ytdlleech`, `/yl` | Download via Yt-Dlp to Telegram. |
| `/clone` | Clone Google Drive/Rclone files. |
| `/status` | Show status of current tasks. |
| `/cancel` | Cancel a task. |
| `/list` | Search files in Drive/Rclone. |
| `/search` | Search torrents. |
| `/authorize` | Authorize a chat or user. |
| `/unauthorize` | Revoke authorization. |
| `/users` | List authorized users. |
| `/log` | Get log file. |
| `/stats` | Show system and bot stats. |
| `/restart` | Restart the bot. |
| `/help` | Show help message. |

*Add your `CMD_SUFFIX` (if set) to these commands.*

## Credits

-   Based on various open-source leech bots.
