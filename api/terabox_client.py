"""TeraBox API client module.

This module handles all interactions with the TeraBox API,
including fetching file information, download links, and formatting responses.
"""

import asyncio
import logging
import re
import urllib.parse
from typing import Any, Dict, List, Optional, Union
from urllib.parse import parse_qs, urlparse

import aiohttp

from config import headers, load_cookies
from utils import find_between, extract_thumbnail_dimensions, get_formatted_size


async def fetch_download_link(
    url: str, password: str = ""
) -> Union[List[Dict[str, Any]], Dict[str, Any]]:
    """Fetch file information from TeraBox share link using unified proxy API.

    This function uses the unified Cloudflare Worker proxy with mode=resolve,
    which automatically handles jsToken extraction and API calls in a single request.

    Args:
        url: TeraBox share URL
        password: Optional password for protected links

    Returns:
        Union[List[Dict[str, Any]], Dict[str, Any]]: List of files or error dict
    """
    try:
        from config import PROXY_BASE_URL, PROXY_MODE_RESOLVE

        cookies = load_cookies()

        if not cookies:
            logging.error("No cookies found. You MUST specify a valid COOKIE_JSON in .env for this bot to function.")
            return {"error": "Authentication cookies missing. Please set COOKIE_JSON in .env.", "errno": -1}
        # Extract surl from URL
        parsed_url = urlparse(url)
        if "surl=" in parsed_url.query:
            surl = parse_qs(parsed_url.query)["surl"][0]
        elif "/s/" in parsed_url.path:
            surl = parsed_url.path.split("/s/")[1].split("/")[0].split("?")[0]
        else:
            logging.error("Could not extract surl from URL")
            return {"error": "Invalid URL format", "errno": -1}

        # Remove leading "1" if present
        if surl.startswith("1"):
            surl = surl[1:]

        # Direct-to-terabox API logic using our cookies
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

                # If errno is 105, it might mean jsToken wasn't accepted or referer was bad.
                # Since the user specifically stated their cookie was failing with the shakir proxy,
                # direct API is the requested method. If it fails, we will fall back to tera-core API.
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
        logging.error(f"HTTP error: {e.status} - {e.message}")
        return {"error": f"HTTP error: {e.status}", "errno": -1}
    except Exception as e:
        logging.error(f"Unexpected error: {e}", exc_info=True)
        return {"error": str(e), "errno": -1}


async def format_file_info(file_data: Dict[str, Any]) -> Dict[str, Any]:
    """Format file information for API response.

    Args:
        file_data: Raw file data from TeraBox API

    Returns:
        Dict[str, Any]: Formatted file information
    """
    thumbnails = {}
    if "thumbs" in file_data:
        for key, url in file_data["thumbs"].items():
            if url:
                dimensions = extract_thumbnail_dimensions(url)
                thumbnails[dimensions] = url

    return {
        "filename": file_data.get("server_filename", "Unknown"),
        "size": get_formatted_size(file_data.get("size", 0)),
        "size_bytes": file_data.get("size", 0),
        "download_link": file_data.get("dlink", ""),
        "is_directory": file_data.get("isdir") == "1",
        "thumbnails": thumbnails,
        "path": file_data.get("path", ""),
        "fs_id": file_data.get("fs_id", ""),
    }


async def fetch_direct_links(
    url: str, password: str = ""
) -> Union[List[Dict[str, Any]], Dict[str, Any]]:
    """Fetch files with direct download links (alternative method).

    Args:
        url: TeraBox share URL
        password: Optional password for protected links

    Returns:
        Union[List[Dict[str, Any]], Dict[str, Any]]: List of files with direct links or error dict
    """

    try:
        files = await fetch_download_link(url, password)

        if isinstance(files, dict) and "error" in files:
            return files

        # Load cookies for the session (previous code referenced undefined `cookies`)
        session_cookies = load_cookies()

        if not session_cookies:
            return {"error": "Authentication cookies missing.", "errno": -1}

        async with aiohttp.ClientSession(
            cookies=session_cookies,
            headers=headers,
            timeout=aiohttp.ClientTimeout(total=30, connect=10),
        ) as session:
            results = []
            for item in files or []:
                # Ensure each item is a dict; skip otherwise

                if not isinstance(item, dict):
                    logging.warning(f"Skipping non-dict item in files: {type(item)}")

                    continue

                # Get direct link by following redirect

                dlink = item.get("dlink") or ""
                logging.info(f"Direct link: {dlink}")

                direct_link = None

                if dlink:
                    try:
                        async with session.head(
                            dlink, allow_redirects=False
                        ) as response:
                            direct_link = response.headers.get("Location")

                    except Exception as e:
                        logging.error(f"Error getting direct link: {e}")

                results.append(
                    {
                        "filename": item.get("server_filename", "Unknown"),
                        "size": get_formatted_size(item.get("size", 0)),
                        "size_bytes": item.get("size", 0),
                        "link": dlink,
                        "direct_link": direct_link,
                        "thumbnail": (item.get("thumbs") or {}).get("url3", ""),
                    }
                )

            return results

    except Exception as e:
        logging.error(f"Error in fetch_direct_links: {e}")

        return {"error": str(e), "errno": -1}


async def _gather_format_file_info(files: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Helper to run format_file_info concurrently for a list of file dicts.

    Args:
        files: List of file data dictionaries

    Returns:
        List[Dict[str, Any]]: List of formatted file information
    """
    tasks = [format_file_info(item) for item in files if isinstance(item, dict)]
    if not tasks:
        return []
    results = await asyncio.gather(*tasks)
    return results


async def _normalize_api2_items(items: List[Dict[str, Any]]) -> List[Dict[str, Any]]:
    """Normalize items returned by fetch_direct_links to the /api response shape.

    Args:
        items: List of items from fetch_direct_links

    Returns:
        List[Dict[str, Any]]: Normalized list of file information
    """
    out: List[Dict[str, Any]] = []
    for item in items or []:
        try:
            if not isinstance(item, dict):
                continue
            filenamestr = item.get("filename") or item.get("server_filename", "Unknown")
            size_h = (
                item.get("size")
                if isinstance(item.get("size"), str)
                else get_formatted_size(item.get("size", 0))
            )
            size_b = item.get("size_bytes", item.get("size", 0))
            download = (
                item.get("direct_link")
                or item.get("download_link")
                or item.get("link")
                or item.get("dlink")
                or ""
            )
            thumbs: Dict[str, str] = {}
            thumb_single = item.get("thumbnail") or (item.get("thumbs") or {}).get("url3")
            if thumb_single:
                thumbs["original"] = thumb_single
            formatted = {
                "filename": filenamestr,
                "size": size_h,
                "size_bytes": size_b,
                "download_link": download,
                "is_directory": item.get("is_directory", False),
                "thumbnails": thumbs,
                "path": item.get("path", ""),
                "fs_id": item.get("fs_id", ""),
            }
            if item.get("direct_link"):
                formatted["direct_link"] = item["direct_link"]
            out.append(formatted)
        except Exception:
            continue
    return out
