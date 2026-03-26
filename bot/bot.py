import os
import asyncio
import logging
import aiohttp
import aiofiles
import pyrogram
from pyrogram import Client, filters
from pyrogram.enums import ParseMode
from pyrogram.errors import FloodWait
from pyrogram.types import Message
from dotenv import load_dotenv

import time

from hachoir.parser import createParser
from hachoir.metadata import extractMetadata

# Load environment variables
load_dotenv()

# Setup logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(name)s - %(levelname)s - %(message)s"
)
logger = logging.getLogger(__name__)

# Bot configuration
BOT_TOKEN = os.getenv("BOT_TOKEN")
API_ID = os.getenv("BOT_API_ID")
API_HASH = os.getenv("BOT_API_HASH")
DUMP_CHANNEL_ID = os.getenv("DUMP_CHANNEL_ID")
API_URL = os.getenv("API_URL", "https://td-l.vercel.app/api2")

if DUMP_CHANNEL_ID:
    try:
        DUMP_CHANNEL_ID = int(DUMP_CHANNEL_ID)
    except ValueError:
        pass

# Concurrency control for downloads/uploads (max concurrent operations)
MAX_CONCURRENT_TASKS = 100
semaphore = asyncio.Semaphore(MAX_CONCURRENT_TASKS)

if not BOT_TOKEN or not API_ID or not API_HASH:
    logger.warning("Bot credentials are not fully set. Please check your .env file.")

def format_bytes(size):
    size = int(size)
    power = 2**10
    n = 0
    power_labels = {0: '', 1: 'K', 2: 'M', 3: 'G', 4: 'T'}
    while size > power:
        size /= power
        n += 1
    return f"{size:.2f} {power_labels[n]}B"

def get_video_duration(filepath):
    try:
        parser = createParser(filepath)
        if not parser:
            return 0
        metadata = extractMetadata(parser)
        if metadata and metadata.has("duration"):
            return metadata.get("duration").seconds
    except Exception as e:
        logger.warning(f"Failed to extract video duration for {filepath}: {e}")
    return 0

def format_time(seconds):
    seconds = int(seconds)
    m, s = divmod(seconds, 60)
    h, m = divmod(m, 60)
    if h > 0:
        return f"{h}h {m}m {s}s"
    elif m > 0:
        return f"{m}m {s}s"
    return f"{s}s"

async def progress_bar(current, total, status_msg, action_text, start_time, last_update_time):
    now = time.time()
    # Update every 2 seconds
    if now - last_update_time[0] < 2.0 and current != total:
        return

    last_update_time[0] = now

    if total == 0:
        total = 1 # Prevent division by zero

    percentage = current * 100 / total
    speed = current / (now - start_time) if now - start_time > 0 else 0
    eta = (total - current) / speed if speed > 0 else 0

    progress_str = "[{0}{1}] {2}%\n".format(
        ''.join(["●" for i in range(int(percentage / 10))]),
        ''.join(["○" for i in range(10 - int(percentage / 10))]),
        round(percentage, 2)
    )

    text = f"🔄 <b>{action_text}</b>\n\n"
    text += f"{progress_str}"
    text += f"📦 <b>Size:</b> {format_bytes(current)} / {format_bytes(total)}\n"
    text += f"🚀 <b>Speed:</b> {format_bytes(speed)}/s\n"
    text += f"⏳ <b>ETA:</b> {format_time(eta)}"

    try:
        await status_msg.edit_text(text, parse_mode=ParseMode.HTML)
    except FloodWait as e:
        await asyncio.sleep(e.value)
    except Exception:
        pass


# Initialize bot client
app = Client(
    "terabox_bot",
    api_id=API_ID,
    api_hash=API_HASH,
    bot_token=BOT_TOKEN,
)

@app.on_message(filters.command("start"))
async def start_command(client: Client, message: Message):
    await message.reply_text(
        "👋 Welcome! I am a TeraBox downloader bot.\n\n"
        "Send me a TeraBox link and I'll send you the file directly here.\n"
        "Supported domains: terabox.com, teraboxapp.com, etc."
    )

@app.on_message(filters.text & filters.regex(r"http[s]?://[^\s]+"))
async def handle_link(client: Client, message: Message):
    # Extract url and optional password (e.g., "https://terabox.com/s/123 mypass")
    parts = message.text.split(maxsplit=1)
    url = parts[0]
    password = parts[1] if len(parts) > 1 else ""

    # Simple check if url contains terabox
    if "tera" not in url.lower() and "1024" not in url.lower():
        return

    status_msg = await message.reply_text("🔄 Processing your link...", disable_web_page_preview=True)

    async with semaphore:
        try:
            # 1. Fetch direct links via external API
            api_endpoint = f"{API_URL}?url={url}"
            if password:
                api_endpoint += f"&pwd={password}"

            links = None
            async with aiohttp.ClientSession() as session:
                async with session.get(api_endpoint) as resp:
                    if resp.status != 200:
                        links = {"error": f"API returned status {resp.status}"}
                    else:
                        data = await resp.json()
                        if data.get("status") == "success":
                            links = data.get("files", [])
                        else:
                            links = {"error": data.get("message", "Unknown API error")}

            if isinstance(links, dict) and "error" in links:
                error_msg = links.get('error')
                await status_msg.edit_text(f"❌ <b>Error:</b> {error_msg}", parse_mode=ParseMode.HTML)
                return

            if not links:
                await status_msg.edit_text("❌ No files found in this link.")
                return

            # 2. Process each file
            for file_info in links:
                direct_link = (file_info.get("direct_link") or file_info.get("download_link") or file_info.get("link") or "")
                direct_link = direct_link.strip()
                if not direct_link:
                    await message.reply_text(
                        f"❌ <b>Could not extract the download link for:</b> {file_info.get('filename', 'Unknown')}\n"
                        "<i>The link may be password-protected, geo-blocked, or the configured cookies have expired.</i>",
                        parse_mode=ParseMode.HTML
                    )
                    continue

                await status_msg.edit_text(f"📥 Downloading: {file_info.get('filename', 'File')}\nSize: {file_info.get('size', 'Unknown')}")

                # Download and upload file
                direct_link = file_info["direct_link"]
                filename = file_info.get("filename", "downloaded_file")

                # We can stream download to memory if small, or directly pass the url to Pyrogram if supported,
                # but usually Pyrogram doesn't stream from arbitrary URLs with auth.
                # Let's download locally and then upload.

                # Sanitize filename to prevent path traversal
                safe_filename = os.path.basename(filename)
                temp_file = f"temp_{message.id}_{safe_filename}"
                temp_thumb = f"thumb_{message.id}.jpg"

                try:
                    download_headers = {
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
                        "Accept": "*/*",
                        "Accept-Language": "en-US,en;q=0.9",
                        "Connection": "keep-alive",
                    }

                    # No cookies are passed, TeraBox direct links usually work without them for the specific short-lived token
                    async with aiohttp.ClientSession() as session:
                        # Download main file
                        async with session.get(direct_link, headers=download_headers, allow_redirects=True) as resp:
                            if resp.status != 200:
                                await status_msg.edit_text(f"❌ Failed to download {filename} (Status: {resp.status})\nMake sure your API server's cookies are valid.")
                                continue


                            total_size = int(resp.headers.get("content-length", 0))
                            downloaded = 0
                            start_time = time.time()
                            last_update_time = [0]
                            action_text = f"Downloading: {filename}"

                            async with aiofiles.open(temp_file, "wb") as f:
                                while True:
                                    chunk = await resp.content.read(8192)
                                    if not chunk:
                                        break
                                    await f.write(chunk)
                                    downloaded += len(chunk)
                                    if total_size > 0:
                                        await progress_bar(downloaded, total_size, status_msg, action_text, start_time, last_update_time)

                        # Download thumbnail if available
                        thumbnail_url = file_info.get("thumbnail")
                        has_thumb = False
                        if thumbnail_url:
                            try:
                                async with session.get(thumbnail_url, headers=download_headers) as thumb_resp:
                                    if thumb_resp.status == 200:
                                        async with aiofiles.open(temp_thumb, "wb") as tf:
                                            await tf.write(await thumb_resp.read())
                                            has_thumb = True
                            except Exception as e:
                                logger.warning(f"Failed to download thumbnail for {filename}: {e}")

                    await status_msg.edit_text(f"📤 Uploading: {filename}...")


                    # Determine media type for proper upload
                    ext = filename.lower().split('.')[-1] if '.' in filename else ''

                    kwargs = {
                        "caption": f"File: {filename}\nSize: {file_info.get('size', 'Unknown')}\nURL: {url}" if DUMP_CHANNEL_ID else f"File: {filename}\nSize: {file_info.get('size', 'Unknown')}",
                        "file_name": filename
                    }

                    if has_thumb and os.path.exists(temp_thumb):
                        kwargs["thumb"] = temp_thumb

                    # Upload to dump channel first if configured
                    target_chat = DUMP_CHANNEL_ID if DUMP_CHANNEL_ID else message.chat.id

                    if ext in ['mp4', 'mkv', 'avi', 'mov', 'webm']:
                        duration = get_video_duration(temp_file)
                        if duration > 0:
                            kwargs["duration"] = duration
                        uploaded_msg = await client.send_video(chat_id=target_chat, video=temp_file, **kwargs)
                    elif ext in ['jpg', 'jpeg', 'png', 'webp']:
                        # send_photo does not support file_name parameter in Pyrogram
                        photo_kwargs = kwargs.copy()
                        photo_kwargs.pop("file_name", None)
                        photo_kwargs.pop("thumb", None) # send_photo uses photo directly, no thumb param
                        uploaded_msg = await client.send_photo(chat_id=target_chat, photo=temp_file, **photo_kwargs)
                    elif ext in ['mp3', 'm4a', 'flac', 'wav']:
                        uploaded_msg = await client.send_audio(chat_id=target_chat, audio=temp_file, **kwargs)
                    else:
                        uploaded_msg = await client.send_document(chat_id=target_chat, document=temp_file, **kwargs)

                    # Forward to user if sent to dump channel
                    if DUMP_CHANNEL_ID:
                        await uploaded_msg.copy(message.chat.id)
                finally:
                    # Cleanup temp file
                    if os.path.exists(temp_file):
                        os.remove(temp_file)
                    if os.path.exists(temp_thumb):
                        os.remove(temp_thumb)

            await status_msg.delete()

        except FloodWait as e:
            logger.warning(f"FloodWait encountered: sleeping for {e.value} seconds.")
            await status_msg.edit_text(f"⏳ Rate limited by Telegram. Waiting for {e.value} seconds...")
            await asyncio.sleep(e.value)
            await status_msg.edit_text("🔄 Retrying...")
            # Ideally retry logic should be implemented, but sleeping is a start
        except Exception as e:
            logger.error(f"Error processing {url}: {e}", exc_info=True)
            await status_msg.edit_text(f"❌ An unexpected error occurred.")

if __name__ == "__main__":
    logger.info("Starting bot...")
    app.run()
