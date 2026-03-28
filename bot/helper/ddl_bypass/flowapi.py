from curl_cffi import requests
import re
import sys
import json

def get_flowvideo_links(target_url: str):
    try:
        session = requests.Session(impersonate="safari15_5")

        # 1. Fetch main page to get tokens
        headers_get = {
            "User-Agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/605.1.15 (KHTML, like Gecko) Version/15.5 Safari/605.1.15",
            "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
            "Accept-Language": "en-US,en;q=0.9",
            "Connection": "keep-alive",
            "Upgrade-Insecure-Requests": "1"
        }
        resp = session.get("https://flowvideoplayer.com/", headers=headers_get)
        if resp.status_code != 200:
            return {"error": f"Failed to access flowvideoplayer.com: {resp.status_code}"}

        html = resp.text

        csrf_match = re.search(r'meta name="csrf-token" content="([^"]+)"', html)
        token_match = re.search(r'let TOKEN = "([^"]+)";', html)

        if not csrf_match or not token_match:
            return {"error": "Failed to extract CSRF or X-Token from flowvideoplayer.com"}

        csrf_token = csrf_match.group(1)
        x_token = token_match.group(1)

        # 2. Make the API request
        api_url = "https://flowvideoplayer.com/telegram/bot/search/video"
        headers = {
            "Content-Type": "application/json",
            "X-CSRF-TOKEN": csrf_token,
            "x-token": x_token,
            "Origin": "https://flowvideoplayer.com",
            "Referer": "https://flowvideoplayer.com/",
            "Sec-Fetch-Dest": "empty",
            "Sec-Fetch-Mode": "cors",
            "Sec-Fetch-Site": "same-origin"
        }

        payload = {"url": target_url}
        api_resp = session.post(api_url, headers=headers, json=payload)

        if api_resp.status_code != 200:
             return {"error": f"API returned status {api_resp.status_code}"}

        data = api_resp.json()
        return data

    except Exception as e:
        return {"error": str(e)}

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"error": "No URL provided"}))
        sys.exit(1)

    url = sys.argv[1]
    result = get_flowvideo_links(url)
    print(json.dumps(result))
