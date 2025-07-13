import os
import json
import signal
import time
import psutil
from flask import Flask, request, jsonify, render_template, Response
from flask_cors import CORS
from openai import OpenAI
from datetime import datetime
import uuid
from threading import Thread
import threading
from func.name_title import *
from func.download_aweme_list import *
import random

# 全局变量
pending_threads = []
CONFIG_PATH = "config.json"
HISTORY_DIR = "chathistory"
os.makedirs(HISTORY_DIR, exist_ok=True)
PENDING_TASKS_PATH = "pending_summary_tasks.json"   # 新增：摘要待办队列

# 初始化 Flask 应用
app = Flask(__name__)
CORS(app)  # 允许跨域请求

# 设置模板目录
@app.route("/")
def index():
    return render_template("index.html")

# 读取配置
def load_config():
    if os.path.exists(CONFIG_PATH):
        with open(CONFIG_PATH, "r", encoding="utf-8") as f:
            return json.load(f)
    return {
        "provider" : "openai",
        "model" : "gpt-4o",
        "apiKeys" : { "openai": "", "deepseek": "" },  # 记录不同 provider 的 API Key
        
        "cookie_str" : "",
        "user_agent" : ""
    }

config = load_config() # 全局配置

# 初始化 OpenAI 客户端
def create_client():
    base_urls = {
        "openai": "https://api.openai.com/v1",
        "deepseek": "https://api.deepseek.com/v1"
    }

    provider = config["provider"]
    api_key = config["apiKeys"].get(provider, "")

    return OpenAI(api_key=api_key, base_url=base_urls[provider])

client = create_client() # 初始化 API 客户端

# 将 cookie 字符串转换为结构化列表
def cookie_str_to_dict(cookie):
    result = {}
    for item in cookie.split("; "):
        if "=" in item:
            k, v = item.split("=", 1)
            result[k] = v
    return result

# 获取配置
@app.route("/get_config", methods=["GET"])
def get_config():
    try:
        return jsonify(config), 200
    except Exception as e:
        return jsonify({"error": "Failed to load config", "details": str(e)}), 500

# 保存配置
@app.route("/save_config", methods=["POST"])
def save_config():
    try:
        data = request.json
        if not data:
            return jsonify({"error": "Invalid data"}), 400

        with open(CONFIG_PATH, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4, ensure_ascii=False)

        global config, client
        config = data
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
                model=config["model"],
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

# 抖音视频下载
@app.route("/douyin_download", methods=["POST"])
def douyin_download():
    try:
        data = request.json
        sec_user_id = data.get("sec_user_id", "")
        cookie_str = data.get("cookies", "")
        user_agent = data.get("user_agent", "")
        max_download_num = int(data.get("max_dloads", "1")) + 1
        
        headers = {
            "user-agent": user_agent,
            "accept": "application/json, text/plain, */*",
            "referer": f"https://www.douyin.com/user/{sec_user_id}",
        }
        cookies = cookie_str_to_dict(cookie_str)
        
        max_cursor = 0 # 初始游标
        has_more = True # 是否有更多数据
        already_download_nums = 0 # 已下载数量
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
                # 下面三个参数建议每次抓包更新，能用多久看实际测试（校验很强时需每次刷新）
                f"&webid=7526129557382022696"
                f"&uifid=1b474bc7e0db9591e645dd8feb8c65aae4845018effd0c2743039a380ee647407b11caad055db1101605067df5d71c1a962911ed6ec8b6ccbf1f312aa53ebfef0b1b08a0a379c2967276081e6eb2e887dd1edefc03b5c507eafc9acca21d21f0c0ccfee80641703082ca7fbde935977c0ab08cb4add9c8ccb23b96ab45dc05da4d75f7dcd72110cca17f9b06cfcf87abf7f134a21a857cfcac83b5c96934ac01"
                f"&verifyFp=verify_md029wd2_3kS1wqVh_n9fd_4Nm1_9t6m_UYfSfFJ3CEyZ"
                f"&fp=verify_md029wd2_3kS1wqVh_n9fd_4Nm1_9t6m_UYfSfFJ3CEyZ"
                f"&msToken=6E6fKhXCwb9q87wwnupNSMh-82Yvi5ReoyzcnMvROzhp7uEKaTfqQdstIuTJE9jq4OlayRWVZOQ0BNj81DbxMvjX975r2_C7V4TgJhXCh2RZPlATJiwrtSddasLTnEvDzpKzHAP0yjXnzBE12MFNG1lpj2qt73_Rg_RGJYXnLe2V"
                f"&a_bogus=O60RhqyLQxRfFdFGmOra93clMyoArBSyBPTxRF%2FPCNY4G1Fa2SN7iPbcnxFaBqPLk8BskCIHfne%2FYdncKGXzZo9kLmkvSmwfZU%2Fcnz8o8qZdb4Jh7r8LebGEqiTY0CGYYQI9iZWRAsMC2dOWnrCwABI7u%2F3xRcEdFH3XV%2FYnY9u4USujin%2FVa3t2O7JqUD%3D%3D"
            )
            try:
                r = requests.get(url, headers=headers, cookies=cookies, timeout=10)
                r.raise_for_status()
                data = r.json()
            except Exception as e:
                print("请求失败：", e)
                break

            aweme_list = data.get("aweme_list", [])
            if not aweme_list:
                print("无更多作品")
                break

            # 下载当前页数据
            nums = download_aweme_list(
                aweme_list, headers, already_download_nums, max_download_num
            )
            already_download_nums += nums
            if already_download_nums >= max_download_num:
                print(f"已达到最大下载数量 {max_download_num - 1}，停止下载。")
                break

            # 翻页判断
            has_more = data.get("has_more", 0) == 1 and already_download_nums < max_download_num
            max_cursor = data.get("max_cursor", 0)
            time.sleep(1)  # 防ban
            
        return jsonify({"success": "下载完成", "total": already_download_nums}), 200
    except Exception as e:
        return jsonify({"error": "下载失败", "details": str(e)}), 500

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
    app.run(port=6969)
