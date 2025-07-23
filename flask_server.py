import eventlet
eventlet.monkey_patch()
import os
import json
import signal
import time
import psutil
import asyncio
import requests
from flask import Flask, request, jsonify, render_template, Response
from flask_cors import CORS
from openai import OpenAI
from datetime import datetime
import uuid
from uuid import uuid4
from threading import Thread
import threading
from func.name_title import *
from func.download_aweme_list import *
import random
import urllib.parse
from flask_socketio import SocketIO, emit, join_room
from func.cookie_str_to_dict import cookie_str_to_dict
from playwright.async_api import async_playwright
from func.login_douyin import DouYinLogin
from func.get_a_bogus import *
from func.logger import logger

# 全局变量
pending_threads = []
CONFIG_PATH = "config.json"
HISTORY_DIR = "chathistory"
config = {}
os.makedirs(HISTORY_DIR, exist_ok=True)
PENDING_TASKS_PATH = "pending_summary_tasks.json"   # 新增：摘要待办队列

# 初始化 Flask 应用
app = Flask(__name__)
CORS(app)  # 允许跨域请求
socketio = SocketIO(app, cors_allowed_origins="*") # 初始化 SocketIO

# 设置模板目录
@app.route("/")
def index():
    return render_template("index.html")

# 读取配置
def load_config():
    global config
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            config = json.load(f)
            return
    config = {
        "chat": {
            "provider": "openai",
            "model": "gpt-4o",
            "apiKeys": {
                "openai": "",
                "deepseek": ""
            }
        },
        "tools": {
            "sec_user_id": "",
            "cookie_str": "",
            "user_agent": "",
            "max_dloads": "10"
        }
    }
    with open(CONFIG_PATH, "w", encoding="utf-8") as f:
        json.dump(config, f, indent=4, ensure_ascii=False)
load_config()

# 初始化 OpenAI 客户端
def create_client():
    base_urls = {
        "openai": "https://api.openai.com/v1",
        "deepseek": "https://api.deepseek.com/v1"
    }

    provider = config["chat"]["provider"]
    api_key = config["chat"]["apiKeys"].get(provider, "")

    return OpenAI(api_key=api_key, base_url=base_urls[provider])

client = create_client() # 初始化 API 客户端

# 获取配置
@app.route("/get_config", methods=["GET"])
def get_config():
    global config
    try:
        load_config()
        return jsonify(config), 200
    except Exception as e:
        return jsonify({"error": "获取配置参数失败", "details": str(e)}), 500

# 保存配置
@app.route("/save_config", methods=["POST"])
def save_config():
    try:
        data = request.json
        if not data:
            return jsonify({"error": "Invalid data"}), 400

        global config, client
        if not config:
            load_config()

        # 判断属于哪个部分并更新
        if "sec_user_id" in data:  # tools配置
            config["tools"] = data
        elif "provider" in data:   # chat配置
            config["chat"] = data
        else:
            return jsonify({"error": "未知配置类型（Unknown config type）"}), 400

        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(config, f, indent=4, ensure_ascii=False)

        client = create_client()  # 重新初始化 API 客户端

        return jsonify({"message": "设置保存成功（Config saved successfully）"}), 200

    except Exception as e:
        return jsonify({"error": "设置保存失败（Failed to save config）", "details": str(e)}), 500

# AI 聊天接口
@app.route('/chat', methods=['POST'])
def chat():
    try:
        data = request.json
        user_message = data.get("message", "")

        if not user_message:
            return jsonify({"error": "消息不能为空"}), 400

        def generate():
            response = client.chat.completions.create(
                model=config["chat"]["model"],
                messages=[{"role": "user", "content": user_message}],
                stream=True
            )
            yield "🤖："
            for chunk in response:
                if chunk.choices:
                    text = getattr(chunk.choices[0].delta, "content", "") or ""
                    yield text
                else:
                    yield "[Empty Response Chunk]"
        return Response(generate(), mimetype='text/plain')
    except Exception as e:
        print("Error in /chat:", str(e))
        return jsonify({"error": "服务器内部错误", "details": str(e)}), 500

# 获取聊天记录
@app.route('/get_history', methods=['GET'])
def get_history():
    try:
        files = [f for f in os.listdir(HISTORY_DIR) if f.endswith(".json")]
        files.sort()  # 文件名以时间戳开头，排序即为时间顺序
        histories = []
        for fname in files:
            fpath = os.path.join(HISTORY_DIR, fname)
            with open(fpath, 'r', encoding='utf-8') as f:
                chat = json.load(f)
            # 简略摘要
            summary = next((item['text'] for item in chat if item['type'] == 'user'), 'No User Message')
            histories.append({
                "filename": fname,
                "summary": summary,
                "timestamp": fname.split("_")[0]
            })
        return jsonify(histories)
    except Exception as e:
        return jsonify({"error": "Failed to get history", "details": str(e)}), 500

# 保存聊天记录
@app.route('/save_history', methods=['POST'])
def save_history():
    try:
        data = request.json
        chat = data.get("chat")
        filename = data.get("filename")  # 接收前端传来的filename

        if not isinstance(chat, list):
            return jsonify({"error": "Invalid data format"}), 400
        if not chat or all(not item.get("text", "").strip() for item in chat):
            return jsonify({"error": "Empty or meaningless history, not saved."}), 400

        if filename and os.path.exists(os.path.join(HISTORY_DIR, filename)):
            # 覆盖已有的聊天
            temp_filename = filename
        else:
            # 新建
            timestamp = datetime.now().strftime("%Y%m%d%H%M%S")
            temp_filename = f"{timestamp}_untitled_{uuid.uuid4().hex[:6]}.json"
        
        # 启动后台线程保存并命名
        async_save(chat, temp_filename, HISTORY_DIR, client, pending_threads, config)

        return jsonify({"message": "History saving started", "filename": temp_filename})
    except Exception as e:
        return jsonify({"error": "Failed to start save task", "details": str(e)}), 500

# 加载聊天记录
@app.route("/load_history", methods=["GET"])
def load_history():
    filename = request.args.get("filename")
    if not filename:
        return jsonify({"error": "Missing filename"}), 400
    filepath = os.path.join(HISTORY_DIR, filename)
    if not os.path.exists(filepath):
        return jsonify({"error": "File not found"}), 404
    with open(filepath, "r", encoding="utf-8") as f:
        data = json.load(f)
    return jsonify(data)

# 删除聊天记录
@app.route("/delete_history", methods=["POST"])
def delete_history():
    try:
        data = request.json
        filename = data.get("filename", "")
        if not filename or not filename.endswith(".json"):
            return jsonify({"error": "Invalid filename"}), 400

        filepath = os.path.join(HISTORY_DIR, filename)
        if os.path.exists(filepath):
            os.remove(filepath)
            return jsonify({"message": "Deleted successfully"})
        else:
            # 文件不存在也返回成功
            return jsonify({"message": "File already deleted"})
    except Exception as e:
        return jsonify({"error": "Failed to delete", "details": str(e)}), 500

# 抖音登录
@app.route("/douyin_login", methods=["POST"])
async def douyin_login():
    try:
        data = request.json
        cookie_str = data.get("cookies", "")
        msToken = data.get("msToken", "")
        if cookie_str == "" or msToken == "":
            async with async_playwright() as p:
                # 启动浏览器
                browser = await p.chromium.launch(
                    headless = False,
                    # executable_path="C:\\Program Files\\Google\\Chrome\\Application\\chrome.exe",
                    args = [
                        "--disable-blink-features=AutomationControlled"
                    ]
                )
                context = await browser.new_context()
                page = await context.new_page()
                await page.goto("https://www.douyin.com/")

                # 实例化 DouYinLogin
                login = DouYinLogin(
                    login_type = "qrcode",
                    browser_context = context,                      # Playwright 浏览器上下文
                    context_page = page,                            # Playwright 页面对象
                    login_phone = "",
                    cookie_str = ""
                )

                # 开始登录流程
                await login.begin()
                
                # 初始化变量
                cookie_str = ""
                msToken = ""
                
                # 登录扫码成功后
                if login.LOGIN_TYPE != "cookie":
                    await page.goto("https://www.douyin.com/")
                    
                    # 获取 cookies
                    cookies = await context.cookies()
                    cookie_str = "; ".join([f"{c['name']}={c['value']}" for c in cookies if c['name']])
                    data["cookies"] = cookie_str
                    # logger.info(f"] 获取到的cookies: {cookie_str[:100]}...")

                    # 获取 params 中的 msToken
                    local_storage: Dict = await page.evaluate("() => window.localStorage")
                    msToken = local_storage.get("xmst", "")
                    data["msToken"] = msToken
                    # logger.info(f"获取到的msToken: {msToken}")
                
                # 保存配置（只有在获取到有效数据时才保存）
                if cookie_str and msToken:
                    logger.info(f"开始保存配置到config.json")
                    with open("config.json", "r") as f:
                        cfg = json.load(f)
                    cfg["tools"]["cookies"] = cookie_str
                    cfg["tools"]["msToken"] = msToken
                    with open("config.json", "w") as f:
                        json.dump(cfg, f, indent=4, ensure_ascii=False)
                    logger.info(f"配置保存完成")
                else:
                    logger.info(f"未获取到有效的cookies或msToken，跳过保存")
                    
                return jsonify({"success": True, "tools": data})
        else:
            # 如果cookies和msToken都不为空，直接返回成功
            return jsonify({"success": True, "tools": data})
    except Exception as e:
        return jsonify({"error": "登录失败", "details": str(e)}), 500
    
# 抖音视频下载
@app.route("/douyin_download", methods=["POST"])
def douyin_download():
    try:
        data = request.json
        sec_user_id = data.get("sec_user_id", "")
        cookie_str = data.get("cookies", "")
        msToken = data.get("msToken", "")
        max_download_num = int(data.get("max_dloads", 1))
        
        headers = {
            "user-agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/138.0.0.0 Safari/537.36 Edg/138.0.0.0",
            "accept": "application/json, text/plain, */*",
            "referer": f"https://www.douyin.com/user/{sec_user_id}",
            "cookie": cookie_str
        }
        # 获取随机 webid
        try:
            webid = get_web_id()
        except Exception as e:
            logger.info(f"获取 webid 失败: {str(e)}")
            return
        
        task_id = str(uuid4())
        def background_download():
            already_download_nums = 0
            max_cursor = 0
            has_more = True
            
            # 用于发日志/进度到前端
            def log_func(msg):
                socketio.emit("dlog", {"text": msg}, room=task_id)
            while has_more and already_download_nums < max_download_num:
                url = (
                    f"https://www.douyin.com/aweme/v1/web/aweme/post/"
                    f"?device_platform=webapp"
                    f"&aid=6383"
                    f"&channel=channel_pc_web"
                    f"&sec_user_id={sec_user_id}"
                    f"&max_cursor={max_cursor}"
                    f"&locate_query=false"
                    f"&show_live_replay_strategy=1"
                    f"&need_time_list=0"
                    f"&time_list_query=0"
                    f"&whale_cut_token="
                    f"&cut_version=1"
                    f"&count=18"
                    f"&publish_video_strategy_type=2"
                    f"&from_user_page=1"
                    f"&update_version_code=170400"
                    f"&pc_client_type=1"
                    f"&pc_libra_divert=Windows"
                    f"&support_h265=1"
                    f"&support_dash=1"
                    f"&cpu_core_num=20"
                    f"&version_code=290100"
                    f"&version_name=29.1.0"
                    f"&cookie_enabled=true"
                    f"&screen_width=1920"
                    f"&screen_height=1080"
                    f"&browser_language=zh-CN"
                    f"&browser_platform=Win32"
                    f"&browser_name=Chrome"
                    f"&browser_version=138.0.0.0"
                    f"&browser_online=true"
                    f"&engine_name=Blink"
                    f"&engine_version=138.0.0.0"
                    f"&os_name=Windows"
                    f"&os_version=10"
                    f"&device_memory=8"
                    f"&platform=PC"
                    f"&downlink=10"
                    f"&effective_type=4g"
                    f"&round_trip_time=0"
                    f"&webid={webid}"
                    f"&uifid=1b474bc7e0db9591e645dd8feb8c65aae4845018effd0c2743039a380ee647407b11caad055db1101605067df5d71c1a962911ed6ec8b6ccbf1f312aa53ebfef0b1b08a0a379c2967276081e6eb2e887dd1edefc03b5c507eafc9acca21d21f0c0ccfee80641703082ca7fbde935977c0ab08cb4add9c8ccb23b96ab45dc05da4d75f7dcd72110cca17f9b06cfcf87abf7f134a21a857cfcac83b5c96934ac01"
                    f"&verifyFp=verify_md029wd2_3kS1wqVh_n9fd_4Nm1_9t6m_UYfSfFJ3CEyZ"
                    f"&fp=verify_md029wd2_3kS1wqVh_n9fd_4Nm1_9t6m_UYfSfFJ3CEyZ"
                    f"&msToken={msToken}"
                )
                try:
                    response = requests.get(url, headers=headers, timeout=10)
                    response.raise_for_status()
                    data = response.json()
                except Exception as e:
                    log_func(f"请求失败：{e}")
                    break

                aweme_list = data.get("aweme_list", [])
                logger.info(f"当前页作品数量: {len(aweme_list)}")
                if not aweme_list:
                    log_func("无更多作品")
                    break

                # 下载
                nums, author = download_aweme_list(
                    aweme_list, headers, already_download_nums, max_download_num, log=log_func
                )
                already_download_nums += nums
                percent = min(100, already_download_nums / max_download_num * 100)
                socketio.emit("dprogress", {"percent": percent}, room=task_id)
                
                if already_download_nums >= max_download_num:
                    log_func(f"已达到最大下载数量 {max_download_num - 1}，停止下载。")
                    break

                # 翻页判断
                has_more = data.get("has_more", 0) == 1 and already_download_nums < max_download_num
                max_cursor = data.get("max_cursor", 0)
                time.sleep(1)  # 防ban
                
            log_func(f"用户 <{author}> 的作品下载完成，总计：{already_download_nums} 个")
            
            socketio.emit("dprogress", {"percent": 100}, room=task_id)
            socketio.emit("dfinish", {"msg": "全部下载完成"}, room=task_id)
        
        Thread(target=background_download, daemon=True).start()
        return jsonify({"success": "下载任务已启动", "task_id": task_id}), 200
    except Exception as e:
        return jsonify({"error": "下载失败", "details": str(e)}), 500

@socketio.on('join_download')
def handle_join_download(data):
    print(f"收到前端join_download: {data}")
    task_id = data.get("task_id")
    if task_id:
        join_room(task_id)
        emit("dlog", {"text": f"已加入下载任务房间: {task_id}"})

# 监听 SIGTERM 信号，优雅关闭 Flask 服务器
def shutdown_server(signum, frame):
    print("Shutting down Flask server... 等待所有聊天摘要命名任务完成...")
    # 等所有后台线程完成
    for t in pending_threads:
        t.join()
    print("所有聊天摘要命名任务已完成，安全退出。")
    os._exit(0)

signal.signal(signal.SIGTERM, shutdown_server)
signal.signal(signal.SIGINT, shutdown_server)

# 监视 Electron 是否退出
PARENT_PID = os.getppid()
def monitor_parent():
    while True:
        if not psutil.pid_exists(PARENT_PID):
            print("Electron 已退出，关闭 Flask 服务器")
            for t in pending_threads:
                t.join()
            print("所有聊天摘要命名任务已完成，安全退出。")
            os._exit(0)
        time.sleep(1)

if __name__ == '__main__':
    process_all_untitled_files(HISTORY_DIR, client, config)   # 自动补偿未命名聊天记录
    monitor_thread = Thread(target=monitor_parent, daemon=True)
    monitor_thread.start()
    # socketio.run(app, port=6969)
    app.run(port=6969)