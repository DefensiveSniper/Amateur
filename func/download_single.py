import requests
import re
import os
import random
import string
from func.get_a_bogus import *
import urllib.parse
import asyncio
from func.get_aweme_id import *
from func.logger import logger
from uuid import uuid4
from flask_socketio import SocketIO, emit, join_room

async def download_single(share_link: str, cookies: str, msToken: str, log=lambda x: None, task_id=None):
    log(f"开始下载： {share_link}", task_id)
    logger.info(f"开始下载： {share_link}")
    
    aweme_id, url = get_aweme_id(share_link)
    
    headers = {
        'referer': f'https://www.douyin.com/video/{aweme_id}',
        'user-agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36',
        'cookie': cookies,
    }

    commom_params = {
        'device_platform': 'webapp',
        'aid': '6383',
        'channel': 'channel_pc_web',
        'aweme_id': f'{aweme_id}',
        'update_version_code': '170400',
        'pc_client_type': '1',
        'pc_libra_divert': 'Windows',
        'support_h265': '1',
        'support_dash': '1',
        'cpu_core_num': '20',
        'version_code': '190500',
        'version_name': '19.5.0',
        'cookie_enabled': 'true',
        'screen_width': '1920',
        'screen_height': '1080',
        'browser_language': 'zh-CN',
        'browser_platform': 'Win32',
        'browser_name': 'Chrome',
        'browser_version': '138.0.0.0',
        'browser_online': 'true',
        'engine_name': 'Blink',
        'engine_version': '138.0.0.0',
        'os_name': 'Windows',
        'os_version': '10',
        'device_memory': '8',
        'platform': 'PC',
        'downlink': '10',
        'effective_type': '4g',
        'round_trip_time': '0',
        'webid': get_web_id(),
        'msToken': msToken,
    }
    
    params = commom_params
    params_string = urllib.parse.urlencode(params)
    params['a_bogus'] = await get_a_bogus(url, params_string, headers['user-agent'])

    try:
        response = requests.get('https://www.douyin.com/aweme/v1/web/aweme/detail/', params=params, headers=headers)
        JSON = response.json()
    except Exception as e:
        log(f"请求失败: {e}", task_id)
        logger.info(f"请求失败: {e}")
        return

    data = JSON['aweme_detail']
    author = data['author']['nickname']
    os.makedirs(f"./media/单独下载", exist_ok=True)

    item_title = data['item_title'].strip().split('\n')[0] # 获取标题
    caption = data['caption'].strip().split('\n')[0]
    title = "" + item_title + caption
    if not title:
        title = ''.join(random.choices(string.ascii_letters + string.digits, k=8))  # 如果标题为空，生成随机标题
    title_ulti = re.sub('[\/:*?"<>|]', '', title) # 替换非法字符
    
    if data['images'] is None:
        try:
            video_url = data['video']['play_addr']['url_list'][0]
            res_video = requests.get(video_url, headers=headers).content
            with open(f"media/单独下载/{title_ulti}.mp4", "wb") as f:
                f.write(res_video)
                log(f"视频: {title_ulti} 下载完成", task_id)
                return True
        except Exception as e:
            log(f"<{title_ulti}> 视频下载出错: {e}", task_id)
            return False

    else:
        try:
            for idx, i in enumerate(data['images']):
                try:
                    gif_url = i['video']['play_addr']['url_list'][0]
                    res_gif = requests.get(gif_url, headers=headers).content
                    filename = f"{title_ulti}_{idx}"
                    with open(f"media/单独下载/{filename}.mp4", "wb") as f:
                        f.write(res_gif)
                        log(f"动图: {filename} 下载完成", task_id)   
                except:
                    log(f"<{filename}> 动图下载出错", task_id)
                    return False
            
                try:
                    image_url = i['url_list'][0]
                    res_image = requests.get(image_url, headers=headers).content
                    filename = f"{title_ulti}_{idx}"
                    with open(f"media/单独下载/{filename}.webp", 'wb') as f:
                        f.write(res_image)
                        log(f"图片：{filename} 下载完成", task_id)
                except Exception as e:
                    log(f"<{filename}> 也不是图片。报错信息：{e}", task_id)
                    return False
            return True
        except Exception as e:
            log(f"下载出错: {e}", task_id)
            return False
        