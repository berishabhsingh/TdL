# DDL Bypass Utilities

This directory contains specialized logic and scrapers designed to bypass various "Direct Download Link" (DDL) protectors, link shorteners, and file-hosting websites that obscure the actual file URL behind captchas, timers, or multiple redirect pages.

## Purpose

When a user provides a link to the bot (e.g., `/mirror https://some-file-host.com/file123`), the bot needs the final, direct `.mp4`, `.zip`, or `.rar` URL to feed into Aria2 or qBittorrent. If the provided link is a protector (like a URL shortener or a site that makes you wait 30 seconds), Aria2 will simply download the HTML page instead of the file.

These bypass scripts act as a "middleman," taking the original URL, simulating a user's browser (handling cookies, JavaScript, or specific POST requests), and returning the final, direct download link to the bot's core download engine.

## Supported Sites

The scripts in this directory are typically categorized by the specific site or type of protector they are designed to bypass. This might include:
- Common URL shorteners (e.g., bit.ly, adf.ly, ouo.io)
- File hosting sites that require clicking "Generate Link" or waiting.
- Sites that require specific headers, referrers, or session cookies to access the file.

## Implementation Details

These scripts often employ techniques like:
- **HTTP Request Manipulation**: Using libraries like `requests` or `aiohttp` to send customized headers, manage sessions, and follow redirects.
- **HTML Parsing**: Using libraries like `BeautifulSoup` to find hidden form fields, extract JavaScript variables, or locate the final download button's link.
- **JavaScript Execution**: In more complex cases, simulating a browser environment (e.g., using `playwright` or specialized JS executors) to solve captchas or execute obfuscated code that generates the download link.
- **Custom APIs**: Utilizing third-party APIs (like the custom `flowapi.py` module for bypassing TeraBox anti-bot protections) to fetch direct links.
