"""TeraBox API client module.

This module handles all interactions with the TeraBox API,
including fetching file information, download links, and formatting responses.
"""

import asyncio
import logging
from typing import Any, Dict, List, Optional, Union
from urllib.parse import parse_qs, urlparse

import aiohttp

from config import headers, load_cookies
from utils import find_between, extract_thumbnail_dimensions, get_formatted_size


async def fetch_download_link(
    url: str, password: str = ""
) -> Union[List[Dict[str, Any]], Dict[str, Any]]:
    """Fetch file information from TeraBox share link directly using TeraBox API."""
    try:
        cookies = load_cookies()

        async with aiohttp.ClientSession(cookies=cookies, headers=headers) as session:
            # Step 1: Get the share page and extract tokens
            logging.info(f"Fetching share page: {url}")
            async with session.get(url) as response1:
                response1.raise_for_status()
                response_data = await response1.text()

                # Extract required tokens
                js_token = find_between(response_data, "fn%28%22", "%22%29")
                log_id = find_between(response_data, "dp-logid=", "&")

                if not js_token or not log_id:
                    logging.error("Failed to extract required tokens")
                    return {
                        "error": "Failed to extract authentication tokens",
                        "errno": -1,
                    }

                request_url = str(response1.url)

                # Extract surl from URL
                if "surl=" in request_url:
                    surl = request_url.split("surl=")[1].split("&")[0]
                elif "/s/" in request_url:
                    surl = request_url.split("/s/")[1].split("?")[0]
                else:
                    logging.error("Could not extract surl from URL")
                    return {"error": "Invalid URL format", "errno": -1}

                # Remove leading "1" if present (TeraBox shortcode format)
                if surl.startswith("1"):
                    surl = surl[1:]

                logging.info(f"Extracted surl: {surl}, logid: {log_id}")

                # Update headers with the actual referer
                session_headers = headers.copy()
                session_headers["Referer"] = request_url

                # Step 2: Fetch file list
                params = {
                    "app_id": "250528",
                    "web": "1",
                    "channel": "dubox",
                    "clienttype": "0",
                    "jsToken": js_token,
                    "dplogid": log_id,
                    "page": "1",
                    "num": "20",
                    "order": "time",
                    "desc": "1",
                    "site_referer": request_url,
                    "shorturl": surl,
                    "root": "1",
                }

                if password:
                    params["pwd"] = password

                list_url = "https://www.terabox.app/share/list"
                logging.info(f"Fetching file list from: {list_url}")

                async with session.get(
                    list_url, params=params, headers=session_headers
                ) as response2:
                    response_data2 = await response2.json()

                    errno = response_data2.get("errno", -1)
                    logging.info(f"Response errno: {errno}")

                    # Handle verification required
                    if errno == 400141:
                        logging.warning("Link requires verification")
                        return {
                            "error": "Verification required",
                            "errno": 400141,
                            "message": "This link requires password or captcha verification",
                            "surl": surl,
                            "requires_password": True,
                        }

                    # Handle other errors
                    if errno != 0:
                        error_msg = response_data2.get("errmsg", "Unknown error")
                        logging.error(f"API error {errno}: {error_msg}")
                        return {"error": error_msg, "errno": errno}

                    # Check if we got the file list
                    if "list" not in response_data2:
                        logging.error("No file list in response")
                        return {"error": "No files found in response", "errno": -1}

                    files = response_data2["list"]
                    logging.info(f"Found {len(files)} items")

                    # Step 3: If it's a directory, fetch its contents
                    if files and files[0].get("isdir") == "1":
                        logging.info("Fetching directory contents")
                        params.update(
                            {
                                "dir": files[0]["path"],
                                "order": "asc",
                                "by": "name",
                                "dplogid": log_id,
                            }
                        )
                        params.pop("desc", None)
                        params.pop("root", None)

                        async with session.get(
                            list_url, params=params, headers=session_headers
                        ) as response3:
                            response_data3 = await response3.json()

                            if "list" not in response_data3:
                                logging.warning("Failed to parse directory contents, returning folder info")
                            else:
                                files = response_data3["list"]
                                logging.info(f"Found {len(files)} files in directory")

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

            # The download link in Terabox contains the fast download and stream links
            download = (
                item.get("direct_link")
                or item.get("download_link")
                or item.get("link")
                or item.get("dlink")
                or ""
            )

            direct_link = item.get("direct_link", "")
            fast_download_link = download
            thumbs: Dict[str, str] = {}
            thumb_single = item.get("thumbnail") or (item.get("thumbs") or {}).get("url3")
            if thumb_single:
                thumbs["original"] = thumb_single
            formatted = {
                "filename": filenamestr,
                "size": size_h,
                "size_bytes": size_b,
                "download_link": download,
                "fast_download_link": fast_download_link,
                "stream_link": direct_link if direct_link else download,
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
