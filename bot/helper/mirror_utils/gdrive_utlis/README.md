# GDrive Utilities

This directory contains specialized wrappers and classes for interacting with the Google Drive API. Since Google Drive is a primary upload and download destination for LeechxTool, these utilities manage everything from authentication to complex folder operations.

## Key Features

- **Authentication**: Handles OAuth 2.0 flows, refreshing access tokens, and managing multiple Service Accounts (SAs) to bypass daily upload quotas.
- **Uploading**: Implements chunked, resumable uploads for large files (to avoid timeouts), folder creation, and handling nested directory structures when mirroring entire torrents or folders.
- **Downloading**: Fetches files from Google Drive (e.g., using a provided Google Drive link) directly to the bot's local storage for further processing or leeching to Telegram.
- **Cloning**: Implements "server-side copying" (cloning). This allows the bot to copy a file or folder from one Google Drive location to another (e.g., from a public link to the user's personal drive) *without* downloading the file locally, making it incredibly fast.
- **Counting & Searching**: Provides utilities to count the total size or number of files within a Google Drive folder and search for files by name.
- **Permissions**: Handles making uploaded files public or accessible only to specific users/groups based on configuration.

## Dependencies

These utilities typically rely heavily on the `google-api-python-client`, `google-auth-httplib2`, and `google-auth-oauthlib` packages to handle the underlying HTTP requests and authentication with Google's servers.
