# Stream Utilities

This directory provides the functionality to generate direct streaming links for media files hosted on Telegram. Instead of forcing users to download large media files completely before viewing, these utilities allow users to stream video or audio files directly within their browser or a compatible media player (like VLC).

## Components

-   **`web_services.py`**: Contains the core logic for setting up an HTTP server (typically an `aiohttp` or Flask-based web server) that can stream chunks of a Telegram file dynamically. It handles Range requests, allowing for seeking within the media file.
-   **`file_properties.py`**: Utilities to extract the necessary properties of a Telegram file (file ID, size, MIME type) to generate a valid streaming URL.
-   **`template/`**: A subdirectory containing HTML templates used to render a web page with an embedded video player when a user visits a streaming link in their browser.

## Workflow

When a user requests a streaming link for a file, the bot generates a unique URL pointing to the web server defined here. When the user's browser or media player requests this URL, `web_services.py` fetches the file chunks sequentially from Telegram's servers and proxies them to the user in real-time.
