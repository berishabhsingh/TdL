# Web Interface

This directory contains the Flask-based web application component of the LeechxTool bot.

## Overview

The web application's primary function is to provide an interactive interface for users to select specific files from torrents being downloaded via Aria2 or qBittorrent before the download starts or completes. It runs concurrently with the Telegram bot.

## Components

- **`wserver.py`**: The core Flask application script. It defines the routing, authenticates users via pin codes, generates HTML responses by replacing placeholders in large string templates, and handles POST requests to update the respective torrent clients (Aria2/qBittorrent) with file selection priorities.
- **`nodes.py`**: A helper module containing functions to build the HTML structure for the web interface. Specifically, the `make_tree` function recursively iterates through a torrent's file list and generates a nested HTML unordered list (`<ul>`) representing folders and checkboxes for files.

## File Selection (Torrent) Workflow

1.  **Torrent Initiation**: A user initiates a torrent download (e.g., via `/mirror` or `/leech`). If the torrent has multiple files and the user hasn't specified auto-downloading, the bot generates a unique link to the web UI along with a 4-digit pin code.
2.  **Authentication**: The user visits the link (`/app/files/<torrent_hash_or_gid>`) and must enter the correct pin code in the `pin_code` query parameter or HTML form.
3.  **Dynamic HTML Generation**: The Flask route calls the torrent client's API (qBittorrent or Aria2) to fetch the file structure. It passes this structure to `make_tree` in `nodes.py`, which generates the HTML checkboxes.
4.  **Tree View UI**: The page presents a hierarchical tree view using embedded HTML, CSS, and jQuery. Users can select/deselect individual files or entire folders.
5.  **Submission**: Upon clicking submit, a POST request with the selected file IDs (`filenode_X=on`) is sent to the same URL.
6.  **Client Update**: The Flask route parses the POST data, identifies the paused and resumed files, and calls the respective torrent client's API (`torrents_file_priority` for qBittorrent, `change_option` for Aria2) to apply the selections.

## Modifying the UI (HTML/CSS)

The web interface does not use traditional Flask templates (like Jinja2 `.html` files in a `templates/` folder). Instead, the raw HTML, CSS, and JavaScript are embedded directly as large multi-line strings within `wserver.py` (e.g., `rawindexpage`, `pin_entry`, `files_list`, `stlye1`, `stlye2`).

To modify the look and feel:
1.  Open `web/wserver.py`.
2.  Locate the multi-line string variables (e.g., `rawindexpage`, `stlye1`).
3.  Edit the HTML structure or CSS styles directly within these strings.
4.  The Python code dynamically replaces placeholders like `<!-- {My_content} -->` or `/* style1 */` before returning the response to the user.
