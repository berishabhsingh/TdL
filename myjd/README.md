# MyJDownloader API Client

This directory contains the library and tools for interacting with the MyJDownloader API, allowing you to manage JDownloader instances remotely.

## Overview

The `Myjdapi` class within `myjdapi.py` is the main component. It provides methods to connect, disconnect, and reconnect to the My.Jdownloader API, as well as fetch and interact with connected JDownloader devices.

## Features

-   **Connection Management**: Authenticates with My.Jdownloader using email and password, handling session tokens and encryption securely.
-   **Device Management**: Retrieves a list of connected JDownloader devices and allows interacting with individual devices.
-   **Linkgrabber**: Add packages/links to the Linkgrabber, query their status, start downloads, clean up lists, and more.
-   **Downloads List**: Monitor active downloads, query status, manage priority, pause/stop/resume downloads, and clean up lists.
-   **Configuration**: Access and modify JDownloader device settings, including advanced configurations.
-   **Captcha Handling**: Support for viewing and solving captchas.
-   **Direct Connections**: Support for establishing direct connections to JDownloader devices for faster communication when available.
