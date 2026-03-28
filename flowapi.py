from curl_cffi import requests
import re
import sys
import json

import time
import random

def get_flowvideo_links(target_url: str):
    impersonates = ["chrome120", "chrome110", "safari15_3", "safari15_5"]

    for attempt in range(3):
        try:
            browser = random.choice(impersonates)
            session = requests.Session(impersonate=browser)

            # 1. Fetch main page to get tokens
            resp = session.get("https://flowvideoplayer.com/")
            if resp.status_code != 200:
                if resp.status_code in [403, 429] and attempt < 2:
                    time.sleep(random.uniform(0.5, 1.5))
                    continue
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
                 if api_resp.status_code in [403, 429] and attempt < 2:
                     time.sleep(random.uniform(0.5, 1.5))
                     continue
                 return {"error": f"API returned status {api_resp.status_code}"}

            data = api_resp.json()
            return data

        except Exception as e:
            if attempt < 2:
                time.sleep(random.uniform(0.5, 1.5))
                continue
            return {"error": str(e)}

if __name__ == "__main__":
    if len(sys.argv) < 2:
        print(json.dumps({"error": "No URL provided"}))
        sys.exit(1)

    url = sys.argv[1]
    result = get_flowvideo_links(url)
    print(json.dumps(result))
