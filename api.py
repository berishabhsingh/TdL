"""TeraBox API Gateway - Main Flask Application.

This module defines the Flask application and all API route handlers.
Flask 3.x is used for native async route support.
Business logic has been separated into dedicated modules:
- config.py: Configuration and constants
- utils.py: Utility functions
- terabox_client.py: TeraBox API client logic
"""

from flask import Flask, request, jsonify, Response
from datetime import datetime, timezone
import logging
import time
import aiohttp
import os

# Import from our modules
from config import (
    headers,
    load_cookies,
)
from utils import is_valid_share_url
from terabox_client import (
    fetch_download_link,
    fetch_direct_links,
    _gather_format_file_info,
    _normalize_api2_items,
)
from rate_limiter import rate_limit
import cache



def format_response_time(seconds: float) -> str:
    """Format response time with appropriate unit (s or m).

    Args:
        seconds: Time in seconds

    Returns:
        Formatted string with 's' or 'm' suffix
    """
    if seconds >= 60:
        minutes = round(seconds / 60, 2)
        return f"{minutes}m"
    else:
        return f"{round(seconds, 3)}s"


def create_app() -> Flask:
    """Create and configure the Flask application.

    This factory keeps a top-level `app` available for Vercel (module import)
    while allowing local development with `python api.py`.
    """

    app = Flask(__name__, static_folder="public", static_url_path="/public")
    return app


# Create module-level `app` so Vercel/Gunicorn can import it: `from api import app`
app = create_app()


# Basic CORS for browser clients (no extra dependency)
@app.after_request
def add_cors_headers(resp: Response) -> Response:
    resp.headers["Access-Control-Allow-Origin"] = "*"
    resp.headers["Access-Control-Allow-Methods"] = "GET, OPTIONS"
    resp.headers["Access-Control-Allow-Headers"] = "Content-Type, Authorization"
    return resp


# Optional blueprint registration: if endpoints.bp exists, register it.
try:
    from endpoints import bp as endpoints_bp  # type: ignore

    app.register_blueprint(endpoints_bp)
except ImportError:
    # No blueprint found; continue with routes defined below
    pass


# =============== API ROUTES ===============


@app.route("/")
def index():
    """API information endpoint"""
    return jsonify(
        {
            "name": "TeraBox API",
            "version": "2.0",
            "status": "operational",
            "endpoints": {
                "/": "API information",
                "/api": "Unified endpoint - file listing and proxy modes (resolve, page, api, stream, segment)",
                "/api2": "Fetch files with direct download links",
                "/help": "Detailed usage instructions",
                "/health": "Health check",
            },
            "contact": "@Saahiyo",
            "timestamp": datetime.now(timezone.utc).isoformat(),
        }
    )


@app.route("/health")
def health():
    """Health check endpoint"""
    return jsonify({"status": "healthy", "timestamp": datetime.now(timezone.utc).isoformat()})




@app.route("/api", methods=["GET"])
@rate_limit
async def api():
    """API endpoint - fetch file information"""
    try:
        start_time = time.time()
        url = request.args.get("url")

        if not url:
            return (
                jsonify(
                    {
                        "status": "error",
                        "message": "Missing required parameter: url",
                        "example": "/api?url=https://teraboxshare.com/s/...",
                    }
                ),
                400,
            )
        if not is_valid_share_url(url):
            return (
                jsonify(
                    {
                        "status": "error",
                        "message": "Invalid TeraBox share URL",
                        "example": "/api?url=https://teraboxshare.com/s/XXXXXXXX",
                    }
                ),
                400,
            )

        password = request.args.get("pwd", "")
        logging.info(f"API request for URL: {url}")

        # Check cache first
        cached = cache.get(url, password)
        if cached is not None:
            formatted_files = await _normalize_api2_items(cached)
            response_time = format_response_time(time.time() - start_time)
            return jsonify(
                {
                    "status": "success",
                    "url": url,
                    "files": formatted_files,
                    "total_files": len(formatted_files),
                    "response_time": response_time,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
            )

        # Fetch file data with direct links (for fast download & streaming)
        link_data = await fetch_direct_links(url, password)

        # Check if error occurred
        if isinstance(link_data, dict) and "error" in link_data:
            status_code = 401 if link_data.get("requires_password") else 500
            return (
                jsonify(
                    {
                        "status": "error",
                        "url": url,
                        "error": link_data["error"],
                        "errno": link_data.get("errno"),
                        "message": link_data.get("message", ""),
                        "requires_password": link_data.get("requires_password", False),
                    }
                ),
                status_code,
            )

        # Format file information
        if link_data:
            cache.put(url, link_data, password)
            formatted_files = await _normalize_api2_items(link_data)
            response_time = format_response_time(time.time() - start_time)

            return jsonify(
                {
                    "status": "success",
                    "url": url,
                    "files": formatted_files,
                    "total_files": len(formatted_files),
                    "response_time": response_time,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
            )
        else:
            return (
                jsonify({"status": "error", "message": "No files found", "url": url}),
                404,
            )

    except Exception as e:
        logging.error(f"API error: {e}", exc_info=True)
        return (
            jsonify(
                {"status": "error", "message": str(e), "params": dict(request.args)}
            ),
            500,
        )


@app.route("/api2", methods=["GET"])
@rate_limit
async def api2():
    """Alternative API endpoint - with direct download links."""
    try:
        start_time = time.time()
        url = request.args.get("url")

        if not url:
            return (
                jsonify(
                    {
                        "status": "error",
                        "message": "Missing required parameter: url",
                        "example": "/api2?url=https://teraboxshare.com/s/...",
                    }
                ),
                400,
            )
        if not is_valid_share_url(url):
            return (
                jsonify(
                    {
                        "status": "error",
                        "message": "Invalid TeraBox share URL",
                        "example": "/api2?url=https://teraboxshare.com/s/XXXXXXXX",
                    }
                ),
                400,
            )

        logging.info(f"API2 request for URL: {url}")

        password = request.args.get("pwd", "")

        link_data = await fetch_direct_links(url, password)

        # Check if error occurred
        if isinstance(link_data, dict) and "error" in link_data:
            return (
                jsonify(
                    {
                        "status": "error",
                        "url": url,
                        "error": link_data["error"],
                        "errno": link_data.get("errno"),
                    }
                ),
                500,
            )

        if link_data:
            # Normalize file objects to match /api shape and include direct_link when available
            formatted_files = await _normalize_api2_items(link_data)
            response_time = format_response_time(time.time() - start_time)
            return jsonify(
                {
                    "status": "success",
                    "url": url,
                    "files": formatted_files,
                    "total_files": len(formatted_files),
                    "response_time": response_time,
                    "timestamp": datetime.now(timezone.utc).isoformat(),
                }
            )
        else:
            return (
                jsonify({"status": "error", "message": "No files found", "url": url}),
                404,
            )

    except Exception as e:
        logging.error(f"API2 error: {e}", exc_info=True)
        return (
            jsonify({"status": "error", "message": str(e), "url": request.args.get("url", "")} ),
            500,
        )


@app.route("/help", methods=["GET"])
def help_page():
    """Help and documentation endpoint"""
    return jsonify(
        {
            "TeraBox API Documentation": {
                "version": "2.0",
                "description": "Extract file information from TeraBox share links",
                "Endpoints": {
                    "/api": {
                        "method": "GET",
                        "description": "API endpoint - file information",
                        "parameters": {
                            "url": "Required - TeraBox share link",
                            "pwd": "Optional - Password for protected links",
                        },
                        "example": "/api?url=https://teraboxshare.com/s/1ABC...",
                    },
                    "/api2": {
                        "method": "GET",
                        "description": "Fetch files with direct download links",
                        "parameters": {
                            "url": "Required - TeraBox share link",
                            "pwd": "Optional - Password for protected links",
                        },
                        "example": "/api2?url=https://teraboxshare.com/s/1ABC...",
                    },
                },
                "Error Codes": {
                    "0": "Success",
                    "-1": "General error",
                    "400141": "Verification required (password/captcha)",
                },
                "Response Format": {
                    "success": {
                        "status": "success",
                        "url": "The requested URL",
                        "files": "Array of file objects",
                        "total_files": "Number of files",
                        "timestamp": "ISO timestamp",
                    },
                    "error": {
                        "status": "error",
                        "message": "Error description",
                        "errno": "Error code",
                    },
                },
                "Notes": [
                    "Cookies must be updated regularly (they expire)",
                    "Links requiring passwords need pwd parameter",
                    "Some links may require captcha verification",
                    "Rate limiting may apply",
                ],
                "Contact": "@Saahiyo",
            }
        }
    )

if __name__ == "__main__":
    app.run(debug=True, host="0.0.0.0", port=5000)