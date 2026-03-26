#!/usr/bin/env python3
"""Standalone TeraBox Downloader Script.

This script fetches direct download links for TeraBox URLs using a provided cookie.
It has no external dependencies other than aiohttp and standard libraries.
"""

import asyncio
import logging
import argparse
import sys
import re
import urllib.parse
from typing import Any, Dict, List, Optional, Union
from urllib.parse import parse_qs, urlparse

import aiohttp

# ==============================================================================
# Constants & Utilities
# ==============================================================================

# Allowed TeraBox domains
ALLOWED_HOSTS: set[str] = {
    "terabox.app", "www.terabox.app", "teraboxshare.com", "www.teraboxshare.com",
    "terabox.com", "www.terabox.com", "1024terabox.com", "www.1024terabox.com",
    "teraboxlink.com", "terasharefile.com", "terafileshare.com", "terasharelink.com",
    "teraboxshare.com", "www.teraboxshare.com"
}

# Default HTTP headers for requests
headers: Dict[str, str] = {
    "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64; rv:121.0) Gecko/20100101 Firefox/121.0",
    "Accept": "*/*",
    "Accept-Language": "en-US,en;q=0.9",
    "Connection": "keep-alive",
}

def is_valid_share_url(u: str) -> bool:
    try:
        parsed = urlparse(u)
        if parsed.scheme not in ("http", "https"):
            return False
        host = parsed.netloc.lower()
        if host not in ALLOWED_HOSTS:
            return False
        return ("/s/" in parsed.path) or ("surl=" in (parsed.query or ""))
    except Exception:
        return False

def extract_thumbnail_dimensions(url: str) -> str:
    parsed = urlparse(url)
    params = parse_qs(parsed.query)
    size_param = params.get("size", [""])[0]

    if size_param:
        parts = size_param.replace("c", "").split("_u")
        if len(parts) == 2:
            return f"{parts[0]}x{parts[1]}"
    return "original"

def get_formatted_size(size_bytes: Union[int, str]) -> str:
    try:
        size_bytes = int(size_bytes)
        if size_bytes >= 1024 * 1024 * 1024:  # GB
            size = size_bytes / (1024 * 1024 * 1024)
            unit = "GB"
        elif size_bytes >= 1024 * 1024:  # MB
            size = size_bytes / (1024 * 1024)
            unit = "MB"
        elif size_bytes >= 1024:  # KB
            size = size_bytes / 1024
            unit = "KB"
        else:
            size = size_bytes
            unit = "bytes"

        return f"{size:.2f} {unit}"
    except Exception as e:
        return "Unknown"


# ==============================================================================
# TeraBox Logic
# ==============================================================================

async def fetch_download_link(url: str, cookies: dict, password: str = "") -> Union[List[Dict[str, Any]], Dict[str, Any]]:
    try:
        if not cookies:
            return {"error": "Authentication cookies missing.", "errno": -1}

        # Extract surl from URL
        parsed_url = urlparse(url)
        if "surl=" in parsed_url.query:
            surl = parse_qs(parsed_url.query)["surl"][0]
        elif "/s/" in parsed_url.path:
            surl = parsed_url.path.split("/s/")[1].split("/")[0].split("?")[0]
        else:
            return {"error": "Invalid URL format", "errno": -1}

        # Remove leading "1" if present
        if surl.startswith("1"):
            surl = surl[1:]

        async with aiohttp.ClientSession(cookies=cookies, headers=headers) as session:
            page_url = f"https://www.1024terabox.com/sharing/link?surl={surl}"
            async with session.get(page_url) as resp:
                html = await resp.text()

                # Extract jsToken
                js_token = None
                js_match = re.search(r'decodeURIComponent\(\`([^\`]+)\`\)', html)
                if js_match:
                    decoded = urllib.parse.unquote(js_match.group(1))
                    token_match = re.search(r'fn\(\"([^\"]+)\"\)', decoded)
                    if token_match:
                        js_token = token_match.group(1)

                if not js_token:
                    # Fallback to simple regex
                    js_match2 = re.search(r'\"jsToken\":\"([^\"]+)\"', html)
                    if js_match2:
                        js_token = js_match2.group(1)

            # Call TeraBox share/list
            api_url = f"https://www.1024terabox.com/share/list?app_id=250528&shorturl={surl}&root=1"
            if js_token:
                api_url += f"&jsToken={js_token}"
            if password:
                api_url += f"&pwd={password}"

            api_headers = headers.copy()
            api_headers["Referer"] = page_url

            async with session.get(api_url, headers=api_headers) as api_resp:
                if api_resp.status != 200:
                    return {"error": f"TeraBox API Error: {api_resp.status}", "errno": -1}

                api_response = await api_resp.json()
                errno = api_response.get("errno", -1)

                if errno != 0:
                    if errno == 400141:
                        return {"error": "This link requires a password or captcha verification.", "errno": 400141, "requires_password": True}
                    if errno == 4000020:
                         return {"error": "Authentication Failed. Your TeraBox cookie (ndus) has expired. Please update it.", "errno": 4000020}
                    if errno == 105:
                         return {"error": "Failed to extract jsToken securely. TeraBox changed their API structure.", "errno": 105}

                    return {"error": f"TeraBox API returned an error: errno {errno}", "errno": errno}

                files = api_response.get("list", [])

                # Fetch directory contents if it's a folder
                if files and files[0].get("isdir") == "1":
                    dir_url = f"https://www.1024terabox.com/share/list?app_id=250528&shorturl={surl}&dir={urllib.parse.quote(files[0]['path'])}&root=0"
                    if js_token:
                        dir_url += f"&jsToken={js_token}"
                    if password:
                        dir_url += f"&pwd={password}"

                    async with session.get(dir_url, headers=api_headers) as dir_resp:
                        if dir_resp.status == 200:
                            dir_data = await dir_resp.json()
                            if dir_data.get("errno") == 0 and "list" in dir_data:
                                files = dir_data["list"]

                return files

    except aiohttp.ClientResponseError as e:
        return {"error": f"HTTP error: {e.status}", "errno": -1}
    except Exception as e:
        return {"error": str(e), "errno": -1}

async def fetch_direct_links(url: str, cookies: dict, password: str = "") -> Union[List[Dict[str, Any]], Dict[str, Any]]:
    try:
        files = await fetch_download_link(url, cookies, password)

        if isinstance(files, dict) and "error" in files:
            return files

        if not cookies:
            return {"error": "Authentication cookies missing.", "errno": -1}

        async with aiohttp.ClientSession(
            cookies=cookies,
            headers=headers,
            timeout=aiohttp.ClientTimeout(total=30, connect=10),
        ) as session:
            results = []
            for item in files or []:
                if not isinstance(item, dict):
                    continue

                dlink = item.get("dlink") or ""
                direct_link = None

                if dlink:
                    try:
                        async with session.head(dlink, allow_redirects=False) as response:
                            direct_link = response.headers.get("Location")
                    except Exception as e:
                        pass

                results.append({
                    "filename": item.get("server_filename", "Unknown"),
                    "size": get_formatted_size(item.get("size", 0)),
                    "size_bytes": item.get("size", 0),
                    "link": dlink,
                    "direct_link": direct_link,
                })

            return results

    except Exception as e:
        return {"error": str(e), "errno": -1}


# ==============================================================================
# CLI Entrypoint
# ==============================================================================

async def main():
    parser = argparse.ArgumentParser(description="Extract direct download links from a TeraBox share URL.")
    parser.add_argument("url", help="The TeraBox share URL to process.")
    parser.add_argument("-c", "--cookie", help="The ndus cookie value for authentication. (Can also be a full JSON string)", required=True)
    parser.add_argument("-p", "--password", help="The password for the protected link.", default="")

    args = parser.parse_args()

    url = args.url
    cookie_val = args.cookie
    password = args.password

    if not is_valid_share_url(url):
        print(f"Error: Invalid TeraBox URL provided: {url}")
        sys.exit(1)

    print(f"Processing URL: {url}")
    print("Fetching direct links...")

    # Process cookie
    cookies = {}
    try:
        import json
        parsed_cookie = json.loads(cookie_val)
        if isinstance(parsed_cookie, dict):
            cookies = parsed_cookie
    except Exception:
        # Treat as raw ndus string
        cookies = {"ndus": cookie_val}

    results = await fetch_direct_links(url, cookies, password)

    if isinstance(results, dict) and "error" in results:
        print(f"\nError: {results['error']}")
        sys.exit(1)

    print(f"\nSuccessfully found {len(results)} files:\n")
    for i, file in enumerate(results, 1):
        print(f"[{i}] {file['filename']} ({file['size']})")
        print(f"    Direct Link: {file['direct_link'] or file['link'] or 'Not found'}")
        print("-" * 50)

if __name__ == "__main__":
    # Configure logging
    logging.basicConfig(level=logging.ERROR, format="%(levelname)s: %(message)s")

    try:
        asyncio.run(main())
    except KeyboardInterrupt:
        print("\nOperation cancelled by user.")
        sys.exit(0)
