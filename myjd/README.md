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

## Usage Example

Below is a brief example of how an extension or script might utilize the `Myjdapi` to connect, get a device, add links, and query downloads.

```python
from myjd.myjdapi import Myjdapi

# Initialize and Connect
jd = Myjdapi()
jd.connect("your_email@example.com", "your_password")

# Get your JDownloader device by name or ID
device = jd.get_device(device_name="My Device Name")

# Check if it's connected
print(f"Connected to Device: {device.name}")

# Add Links to the Linkgrabber
device.linkgrabber.add_links([
    {
        "autostart": True,  # automatically start downloading
        "links": "https://example.com/file.zip",
        "packageName": "Example Package",
    }
])

# Query Active Downloads
downloads = device.downloads.query_links([
    {
        "bytesLoaded": True,
        "bytesTotal": True,
        "speed": True,
        "status": True,
        "url": True,
    }
])

for download in downloads:
    print(f"File: {download.get('name')} | Speed: {download.get('speed', 0)} bps")

# Disconnect
jd.disconnect()
```

## Structure

The `myjd` directory includes:
- **`myjdapi.py`**: The core API classes representing the different JDownloader components (System, Config, Linkgrabber, Downloads, Captcha, Jddevice).
- **`exception.py`**: Custom exception classes for handling API errors.
- **`const.py`**: Constants used in the API client.
