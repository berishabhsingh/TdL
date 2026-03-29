# Video Utilities

This directory contains specialized utilities for interacting with and manipulating video files. It heavily relies on the `ffmpeg` and `ffprobe` command-line tools.

## Key Features

- **Metadata Extraction**: Uses `ffprobe` to determine video properties (resolution, duration, codecs, frame rate, etc.). This information is crucial for accurately uploading media to Telegram or other cloud services so that the files are properly recognized as playable videos rather than generic documents.
- **Thumbnail Generation**: Can generate video thumbnails by capturing a frame from the middle of the video. These thumbnails are often attached when uploading a video back to Telegram.
- **Video Manipulation**: Might include tools for removing audio tracks, muxing, or demuxing, or resizing videos based on user-defined limits (e.g., compressing files to fit Telegram's upload limits).
- **Screenshotting**: Generates screenshots of the video at specific intervals or requested times.

## Dependencies

The functions in this directory rely on the host system having `ffmpeg` installed and accessible in the system's PATH. Ensure this is configured properly, especially when deploying on a VPS or via Docker.
