import sys
from bot.helper.mirror_utils.download_utils.flowapi import get_flowvideo_links
from bot.helper.mirror_utils.download_utils.direct_link_generator import terabox

url = "https://terasharefile.com/s/1Wt3_1KxekhOMuBAFm8mpYw"
try:
    print(f"Testing flowapi direct extraction with {url}")
    print(terabox(url))
except Exception as e:
    print(f"Error: {e}")
