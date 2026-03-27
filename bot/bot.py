import os
import asyncio
import logging
import aiohttp
import aiofiles
import pyrogram

from pyrogram import Client, filters
from pyrogram.enums import ParseMode
from pyrogram.errors import FloodWait
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery
from dotenv import load_dotenv

import time

from flowapi import get_flowvideo_links
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
        DUMP_CHANNEL_ID = int(DUMP_CHANNEL_ID.strip())
    except (ValueError, AttributeError):
        logger.error(f"Invalid DUMP_CHANNEL_ID format: {DUMP_CHANNEL_ID}")
        DUMP_CHANNEL_ID = None

# Concurrency control for downloads/uploads (max concurrent operations)
MAX_CONCURRENT_TASKS = 100
semaphore = asyncio.Semaphore(MAX_CONCURRENT_TASKS)

# Track running tasks by user_id for cancellation
user_tasks = {}

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

import subprocess

def get_video_duration(filepath):
    try:
        # First try using ffprobe (requires ffmpeg installed on host)
        result = subprocess.run(
            ["ffprobe", "-v", "error", "-show_entries",
             "format=duration", "-of",
             "default=noprint_wrappers=1:nokey=1", filepath],
            stdout=subprocess.PIPE,
            stderr=subprocess.STDOUT
        )
        duration = float(result.stdout)
        return int(duration)
    except Exception as ffmpeg_err:
        logger.warning(f"ffprobe failed for {filepath}: {ffmpeg_err}, falling back to hachoir")
        # Fallback to hachoir
        try:
            parser = createParser(filepath)
            if not parser:
                return 0
            metadata = extractMetadata(parser)
            if metadata and metadata.has("duration"):
                return metadata.get("duration").seconds
        except Exception as e:
            logger.warning(f"Failed to extract video duration for {filepath} with hachoir: {e}")
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

async def fast_download(url, headers, filepath, status_msg, action_text, start_time, last_update_time, max_concurrent=4):
    """Downloads a file fast by using multiple concurrent connections if the server supports range requests."""
    async with aiohttp.ClientSession() as session:
        # Check if the server supports range requests
        async with session.head(url, headers=headers, allow_redirects=True) as resp:
            total_size = int(resp.headers.get("content-length", 0))
            accept_ranges = resp.headers.get("accept-ranges", "none")

        if total_size > 0 and accept_ranges == "bytes":
            # Concurrent download
            chunk_size = total_size // max_concurrent
            ranges = []
            for i in range(max_concurrent):
                start = i * chunk_size
                end = total_size - 1 if i == max_concurrent - 1 else (i + 1) * chunk_size - 1
                ranges.append((start, end))

            downloaded = [0] * max_concurrent

            async def download_chunk(i, start, end):
                chunk_headers = headers.copy()
                chunk_headers["Range"] = f"bytes={start}-{end}"
                async with session.get(url, headers=chunk_headers) as chunk_resp:
                    part_file = f"{filepath}.part{i}"
                    async with aiofiles.open(part_file, "wb") as f:
                        while True:
                            chunk = await chunk_resp.content.read(4 * 1024 * 1024)
                            if not chunk:
                                break
                            await f.write(chunk)
                            downloaded[i] += len(chunk)
                            total_downloaded = sum(downloaded)
                            await progress_bar(total_downloaded, total_size, status_msg, action_text, start_time, last_update_time)

            tasks = [download_chunk(i, start, end) for i, (start, end) in enumerate(ranges)]
            await asyncio.gather(*tasks)

            # Combine parts
            async with aiofiles.open(filepath, "wb") as outfile:
                for i in range(max_concurrent):
                    part_file = f"{filepath}.part{i}"
                    async with aiofiles.open(part_file, "rb") as infile:
                        while True:
                            chunk = await infile.read(10 * 1024 * 1024)
                            if not chunk:
                                break
                            await outfile.write(chunk)
                    os.remove(part_file)
            return True
        else:
            # Fallback to single-connection chunked download
            async with session.get(url, headers=headers, allow_redirects=True) as resp:
                if resp.status != 200:
                    return False
                total_size = int(resp.headers.get("content-length", 0))
                downloaded = 0
                async with aiofiles.open(filepath, "wb") as f:
                    while True:
                        chunk = await resp.content.read(4 * 1024 * 1024)
                        if not chunk:
                            break
                        await f.write(chunk)
                        downloaded += len(chunk)
                        if total_size > 0:
                            await progress_bar(downloaded, total_size, status_msg, action_text, start_time, last_update_time)
                return True

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

    markup = InlineKeyboardMarkup(
        [[InlineKeyboardButton("🛑 Cancel", callback_data="cancel_tasks")]]
    )

    try:
        await status_msg.edit_text(text, parse_mode=ParseMode.HTML, reply_markup=markup)
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

# Ensure dump channel is accessible on startup (fixes new session issues)
@app.on_startup
async def ensure_dump_channel(client: Client):
    if not DUMP_CHANNEL_ID:
        return
    try:
        chat = await client.get_chat(DUMP_CHANNEL_ID)
        logger.info(f"Dump channel ready: {chat.title} ({chat.id})")
    except Exception as e:
        logger.error(f"Failed to access dump channel {DUMP_CHANNEL_ID}: {e}")

@app.on_message(filters.command("start"))
async def start_command(client: Client, message: Message):
    await message.reply_text(
        "🎉 Welcome! I am a high-speed TeraBox downloader bot.\n\n"
        "🔗 Send me a TeraBox link and I'll securely download and send you the file directly here.\n"
        "🛑 Use /cancel to stop all your active downloads.\n"
        "🌐 Supported domains: terabox.com, teraboxapp.com, etc."
    )

@app.on_message(filters.command("cancel"))
async def cancel_command(client: Client, message: Message):
    user_id = message.from_user.id
    if user_id in user_tasks and user_tasks[user_id]:
        for task in user_tasks[user_id]:
            task.cancel()
        user_tasks[user_id] = []
        await message.reply_text("🛑 <b>All your tasks have been cancelled.</b>", parse_mode=ParseMode.HTML)
    else:
        await message.reply_text("You have no running tasks.")

@app.on_callback_query(filters.regex("^cancel_tasks$"))
async def cancel_callback(client: Client, callback_query: CallbackQuery):
    user_id = callback_query.from_user.id
    if user_id in user_tasks and user_tasks[user_id]:
        for task in user_tasks[user_id]:
            task.cancel()
        user_tasks[user_id] = []
        await callback_query.message.edit_text("🛑 <b>Task Cancelled.</b>", parse_mode=ParseMode.HTML)
    else:
        await callback_query.answer("No running tasks to cancel.", show_alert=True)

@app.on_message(filters.text & filters.regex(r"http[s]?://[^\s]+"))
async def handle_link(client: Client, message: Message):
    user_id = message.from_user.id
    current_task = asyncio.current_task()

    if user_id not in user_tasks:
        user_tasks[user_id] = []
    user_tasks[user_id].append(current_task)

    # Extract url and optional password (e.g., "https://terabox.com/s/123 mypass")
    parts = message.text.split(maxsplit=1)
    url = parts[0]
    password = parts[1] if len(parts) > 1 else ""

    # Simple check if url contains terabox
    if "tera" not in url.lower() and "1024" not in url.lower():
        if current_task in user_tasks[user_id]:
            user_tasks[user_id].remove(current_task)
        return

    markup = InlineKeyboardMarkup(
        [[InlineKeyboardButton("🛑 Cancel", callback_data="cancel_tasks")]]
    )
    status_msg = await message.reply_text("🔄 Processing your link...", disable_web_page_preview=True, reply_markup=markup)

    try:
        async with semaphore:
            # 1. Fetch direct links via external API (using flowapi.py)
            links = None
            try:
                # Offload synchronous requests to a separate thread to not block event loop
                data = await asyncio.to_thread(get_flowvideo_links, url)

                if isinstance(data, dict) and data.get("error"):
                    links = {"error": data.get("error", "Unknown API error")}
                elif "data" in data:
                    # Map flowvideoplayer output structure to bot expected structure
                    links = [
                        {
                            "filename": item.get("file_name", "Unknown"),
                            "size": item.get("file_size", "Unknown"),
                            "direct_link": item.get("download_url") or item.get("stream_final_url"),
                            "thumbnail": item.get("thumbnail")
                        }
                        for item in data["data"]
                    ]
                else:
                    links = {"error": "Invalid API response format"}
            except Exception as e:
                links = {"error": f"Failed to fetch data: {e}"}

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
                # The flowvideoplayer API often provides files via .zip download to bypass browser restrictions
                # We should extract the actual filename to remove .zip if it exists for the message
                safe_filename = os.path.basename(filename)

                # The file might be downloaded as a ZIP from the proxy API
                download_is_zip = False
                if direct_link.endswith(".zip") or "file_name=" in direct_link and direct_link.split("file_name=")[-1].endswith(".zip"):
                    download_is_zip = True

                temp_file = f"temp_{message.id}_{safe_filename}"
                temp_file_dl = temp_file + (".zip" if download_is_zip and not temp_file.endswith(".zip") else "")
                temp_thumb = f"thumb_{message.id}.jpg"

                try:
                    download_headers = {
                        "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
                        "Accept": "*/*",
                        "Accept-Language": "en-US,en;q=0.9",
                        "Connection": "keep-alive",
                    }

                    start_time = time.time()
                    last_update_time = [0]
                    action_text = f"Downloading: {filename}"

                    # Download main file fast
                    # No cookies are passed, TeraBox direct links usually work without them for the specific short-lived token
                    success = await fast_download(
                        direct_link,
                        download_headers,
                        temp_file_dl,
                        status_msg,
                        action_text,
                        start_time,
                        last_update_time,
                        max_concurrent=4
                    )

                    if not success:
                        await status_msg.edit_text(f"❌ Failed to download {filename}\nMake sure your API server's cookies are valid.")
                        continue

                    # Extract zip if necessary
                    if download_is_zip:
                        await status_msg.edit_text(f"📦 Extracting: {filename}...")
                        import zipfile
                        import tempfile
                        import shutil
                        try:
                            # Offload synchronous unzip to a thread
                            def extract_file():
                                with zipfile.ZipFile(temp_file_dl, 'r') as zip_ref:
                                    # Assume it's a single file archive as packaged by flowvideo
                                    info_list = zip_ref.infolist()
                                    if info_list:
                                        # Create a unique temporary directory to avoid race conditions
                                        with tempfile.TemporaryDirectory() as temp_dir:
                                            extracted_path = zip_ref.extract(info_list[0], path=temp_dir)
                                            shutil.move(extracted_path, temp_file)
                                            return True
                                return False

                            success = await asyncio.to_thread(extract_file)
                            if not success:
                                # Fallback to rename if extraction fails
                                os.rename(temp_file_dl, temp_file)
                            else:
                                # Cleanup original zip
                                os.remove(temp_file_dl)
                        except Exception as e:
                            logger.error(f"Failed to unzip {temp_file_dl}: {e}")
                            # Fallback rename
                            os.rename(temp_file_dl, temp_file)
                    elif temp_file_dl != temp_file:
                        os.rename(temp_file_dl, temp_file)

                    # Download thumbnail if available
                    thumbnail_url = file_info.get("thumbnail")
                    has_thumb = False
                    if thumbnail_url:
                        try:
                            async with aiohttp.ClientSession() as session:
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

                    # Set up caption for dump channel with user info, and a clean caption for the user
                    user_mention = message.from_user.mention
                    user_id_text = f"#ID{message.from_user.id}"

                    dump_caption = (f"📄 File: {filename}\n📦 Size: {file_info.get('size', 'Unknown')}\n"
                                    f"👤 By: {user_mention}\n🆔 {user_id_text}")
                    user_caption = f"📄 File: {filename}\n📦 Size: {file_info.get('size', 'Unknown')}"

                    kwargs = {
                        "caption": dump_caption if DUMP_CHANNEL_ID else user_caption,
                        "file_name": filename
                    }

                    if has_thumb and os.path.exists(temp_thumb):
                        kwargs["thumb"] = temp_thumb

                    # Upload to dump channel first if configured
                    target_chat = DUMP_CHANNEL_ID if DUMP_CHANNEL_ID else message.chat.id

                    try:
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
                            await uploaded_msg.copy(message.chat.id, caption=user_caption)
                    except pyrogram.errors.PeerIdInvalid:
                        logger.error("PeerIdInvalid - Dump channel not accessible in this session")
                        await message.reply_text("❌ Dump channel error (Peer ID invalid). Please restart the bot or send /start first.")
                        continue
                    except pyrogram.errors.ChannelInvalid:
                        logger.error("ChannelInvalid - Dump channel not accessible")
                        await message.reply_text("❌ Dump channel error (Channel invalid). Make sure the bot is admin in the channel.")
                        continue
                    except Exception as upload_err:
                        logger.error(f"Upload failed to dump channel: {upload_err}", exc_info=True)
                        await message.reply_text(f"❌ Upload error: {str(upload_err)[:300]}")
                        continue

                finally:
                    # Cleanup temp file
                    if os.path.exists(temp_file):
                        os.remove(temp_file)
                    if 'temp_file_dl' in locals() and os.path.exists(temp_file_dl):
                        os.remove(temp_file_dl)
                    if os.path.exists(temp_thumb):
                        os.remove(temp_thumb)

            await status_msg.delete()

    except asyncio.CancelledError:
        logger.info(f"Task for user {user_id} was cancelled.")
        await status_msg.edit_text("🛑 <b>Task Cancelled.</b>", parse_mode=ParseMode.HTML)
    except FloodWait as e:
        logger.warning(f"FloodWait encountered: sleeping for {e.value} seconds.")
        await status_msg.edit_text(f"⏳ Rate limited by Telegram. Waiting for {e.value} seconds...")
        await asyncio.sleep(e.value)
        await status_msg.edit_text("🔄 Retrying...")
        # Ideally retry logic should be implemented, but sleeping is a start
    except Exception as e:
        logger.error(f"Error processing {url}: {e}", exc_info=True)
        await status_msg.edit_text(f"❌ An unexpected error occurred.")
    finally:
        if current_task in user_tasks[user_id]:
            user_tasks[user_id].remove(current_task)

if __name__ == "__main__":
    logger.info("Starting bot...")
    app.run()
