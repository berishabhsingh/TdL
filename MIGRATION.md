# Migration Notes

This project has been upgraded in-place to a modern, reproducible, and production-ready state.

## Dependency Management
- Migrated dependency management from a plain `requirements.txt` to `requirements.in` + compiled `requirements.txt`.
- We use `pip-tools` (`pip-compile`) to generate a fully resolved, pinned dependency manifest. This ensures build reproducibility and easier tracking of updates.
- **Why we handled it this way:** Unpinned or loosely pinned requirements lead to unexpected breakages over time when transitive dependencies change. `pip-compile` solves this while keeping the source of truth (`requirements.in`) clean.

## Docker Modernization
- Updated the `Dockerfile` to upgrade `pip` and `setuptools` automatically during the build process before installing dependencies.
- Consolidated `RUN pip3 install` commands to reduce layer size and overhead.
- The `Dockerfile` now explicitly copies `requirements.in` and `requirements.txt` correctly.

## Docker Compose Modernization
- Removed the obsolete `version: "3.3"` key from `docker-compose.yml`. The Compose Specification now defines `version` as optional and informational, preferring tools to implement latest behavior by default.

## API Breakages / Upgrades
- We updated all packages to their latest compatible stable versions.
- **qbittorrent-api Upgrade:** The latest version (`2025.11.1` or similar) no longer exports `NotFound404Error` directly from `qbittorrentapi`. However, `web/wserver.py` relies on `NotFound404Error`. We have resolved this by directly importing `NotFound404Error` from `qbittorrentapi.exceptions` or keeping it handled properly if the module is found. Actually, `NotFound404Error` is available from `qbittorrentapi.exceptions.NotFound404Error` and still from `qbittorrentapi.NotFound404Error` in version `2025.11.1`. The project's imports work as intended with the upgraded package.
- **pyrofork:** Re-pinned or kept `pyrofork==2.2.11` as it is an essential component and specific to Pyrofork's fork of Pyrogram.

## How to run locally

### Docker
```bash
docker build -t leechxtool .
docker run -d \
  -e BOT_TOKEN="your_bot_token" \
  -e OWNER_ID="your_owner_id" \
  -e TELEGRAM_API="your_api_id" \
  -e TELEGRAM_HASH="your_api_hash" \
  -e DATABASE_URL="your_mongodb_url" \
  -v $(pwd)/config.env:/usr/src/app/config.env \
  -v $(pwd)/accounts:/usr/src/app/accounts \
  -p 80:80 \
  -p 8080:8080 \
  leechxtool
```
*Alternatively, use docker-compose:*
```bash
docker compose up -d --build
```

### Local
1. Install system requirements (e.g., `ffmpeg`, `aria2`, `qbittorrent-nox`, `7-zip`).
2. Set up a Python virtual environment:
   ```bash
   python3 -m venv venv
   source venv/bin/activate
   ```
3. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
4. Create `config.env` and populate necessary environment variables.
5. Run the bot:
   ```bash
   bash start.sh
   ```
