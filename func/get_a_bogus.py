# -*- coding: utf-8 -*-
# @Author  : relakkes@gmail.com
# @Name    : 程序员阿江-Relakkes
# @Time    : 2024/6/10 02:24
# @Desc    : 获取 a_bogus 参数, 学习交流使用，请勿用作商业用途，侵权联系作者删除

import random
import execjs
import os
import sys
from playwright.async_api import Page

# douyin_sign_obj = execjs.compile(open('libs/douyin.js', encoding='utf-8-sig').read())
def resource_path(relative_path):
    # PyInstaller 兼容处理：开发环境时返回原路径；打包后走 _MEIPASS 虚拟路径
    if hasattr(sys, '_MEIPASS'):
        return os.path.join(sys._MEIPASS, relative_path)
    return relative_path

douyin_js_path = resource_path("libs/douyin.js")
douyin_sign_obj = execjs.compile(open(douyin_js_path, encoding='utf-8-sig').read())

# 获取当前文件的目录，然后构建JS文件的绝对路径
# current_dir = os.path.dirname(os.path.abspath(__file__))
# parent_dir = os.path.dirname(current_dir)
# douyin_js_path = os.path.join(parent_dir, 'libs', 'douyin.js')

# douyin_sign_obj = execjs.compile(open(douyin_js_path, encoding='utf-8-sig').read())

def get_web_id():
    """
    生成随机的webid
    Returns:

    """

    def e(t):
        if t is not None:
            return str(t ^ (int(16 * random.random()) >> (t // 4)))
        else:
            return ''.join(
                [str(int(1e7)), '-', str(int(1e3)), '-', str(int(4e3)), '-', str(int(8e3)), '-', str(int(1e11))]
            )

    web_id = ''.join(
        e(int(x)) if x in '018' else x for x in e(None)
    )
    return web_id.replace('-', '')[:19]



async def get_a_bogus(url: str, params: str, user_agent: str):
    """
    获取 a_bogus 参数, 目前不支持post请求类型的签名
    """
    return get_a_bogus_from_js(url, params, user_agent)

def get_a_bogus_from_js(url: str, params: str, user_agent: str):
    """
    通过js获取 a_bogus 参数
    Args:
        url:
        params:
        user_agent:

    Returns:

    """
    sign_js_name = "sign_datail"
    if "/reply" in url:
        sign_js_name = "sign_reply"
    return douyin_sign_obj.call(sign_js_name, params, user_agent)

async def get_a_bogus_from_playright(params: str, post_data: dict, user_agent: str, page: Page):
    """
    通过playright获取 a_bogus 参数
    playwright版本已失效
    Returns:

    """
    if not post_data:
        post_data = ""
    a_bogus = await page.evaluate(
        "([params, post_data, ua]) => window.bdms.init._v[2].p[42].apply(null, [0, 1, 8, params, post_data, ua])",
        [params, post_data, user_agent])

    return a_bogus
