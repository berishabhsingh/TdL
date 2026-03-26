from curl_cffi.requests import AsyncSession
import re

async def get_flowvideo_links(target_url: str):
    try:
        async with AsyncSession(impersonate="chrome120") as session:
            # 1. Fetch main page to get tokens
            resp = await session.get("https://flowvideoplayer.com/")
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
            api_resp = await session.post(api_url, headers=headers, json=payload)

            if api_resp.status_code != 200:
                 return {"error": f"API returned status {api_resp.status_code}"}

            data = api_resp.json()
            return data

    except Exception as e:
        return {"error": str(e)}
