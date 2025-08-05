import requests
import re
import logging
logger = logging.getLogger(__name__)
logging.basicConfig(level=logging.INFO)

'''
正则里点号（.）有特殊含义，写成 \.，表示普通的点

\S+: 
    \S 代表任意非空白字符（不是空格、制表符、换行等）。
    + 表示前面的字符出现一次或多次，也就是“至少有一个非空白字符”。
'''

def get_aweme_id(share_link):
    headers = {
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36',
    }

    pattern = r"https://v\.douyin\.com/\S+/"
    match = re.search(pattern, share_link)
    short_url = ''
    if match:
        short_url = match.group()
    logger.info(f"短链：{short_url}")

    # 通过短链获取最终定向链接
    resp = requests.get(short_url, headers=headers, allow_redirects=True)
    url = resp.url
    url = url.split('?')[0]
    logger.info(f"最终短链：{url}")
    aweme_id = url.split('/')[-1]
    return aweme_id, url