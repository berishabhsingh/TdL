import asyncio
from bot.helper.mirror_utils.download_utils.direct_link_generator import direct_link_generator

async def test_dl():
    url = "https://terasharefile.com/s/1Wt3_1KxekhOMuBAFm8mpYw"
    try:
        print(f"Testing URL: {url}")
        result = direct_link_generator(url)
        print("Success! Details:")
        print(result)
    except Exception as e:
        print(f"Failed: {e}")

if __name__ == "__main__":
    asyncio.run(test_dl())
