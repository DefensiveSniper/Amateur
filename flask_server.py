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

pending_threads = []
CONFIG_PATH = "config.json"
HISTORY_DIR = "chathistory"
os.makedirs(HISTORY_DIR, exist_ok=True)
PENDING_TASKS_PATH = "pending_summary_tasks.json"   # 新增：摘要待办队列

app = Flask(__name__)
CORS(app)  # 允许跨域请求

def process_all_untitled_files():
    for fname in os.listdir(HISTORY_DIR):
        if fname.endswith(".json") and "_untitled_" in fname:
            fpath = os.path.join(HISTORY_DIR, fname)
            try:
                with open(fpath, "r", encoding="utf-8") as f:
                    chat = json.load(f)
                summary = generate_summary_name(chat)
                safe_summary = "".join(c for c in summary if c.isalnum() or c in " _-")[:30]
                new_filename = f"{fname.split('_')[0]}_{safe_summary}.json"
                new_path = os.path.join(HISTORY_DIR, new_filename)
                os.rename(fpath, new_path)
                print(f"已补偿命名: {new_filename}")
            except Exception as e:
                print(f"摘要补偿失败({fname}): {e}")

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
        "provider": "openai",
        "model": "gpt-4o",
        "apiKeys": { "openai": "", "deepseek": "" }  # 记录不同 provider 的 API Key
    }

# 全局配置
config = load_config()

# 初始化 OpenAI 客户端
def create_client():
    base_urls = {
        "openai": "https://api.openai.com/v1",
        "deepseek": "https://api.deepseek.com/v1"
    }

    provider = config["provider"]
    api_key = config["apiKeys"].get(provider, "")

    return OpenAI(api_key=api_key, base_url=base_urls[provider])

client = create_client()

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
    
# 用大模型生成聊天标题
def generate_summary_name(chat):
    try:
        summary_prompt = (
            "请为以下聊天生成一个简洁的文件名（不超过20个字符，不含标点符号，概括聊天内容，不要加引号）：\n\n"
        )
        formatted = "\n".join(f"[{'用户' if msg['type']=='user' else 'AI'}]：{msg['text']}" for msg in chat[-10:])
        message = summary_prompt + formatted

        response = client.chat.completions.create(
            model=config["model"],
            messages=[{"role": "user", "content": message}],
        )
        suggestion = response.choices[0].message.content.strip()
        filename = "".join(c for c in suggestion if c.isalnum() or c in " _-")[:30]
        return filename or f"untitled_{uuid.uuid4().hex[:6]}"
    except Exception as e:
        print("生成聊天摘要失败:", e)
        return f"untitled_{uuid.uuid4().hex[:6]}"

# 暂时不生成标题，使用 UUID 命名
def async_save(chat, temp_filename):
    def do_save():
        try:
            # 保存聊天内容
            temp_path = os.path.join(HISTORY_DIR, temp_filename)
            with open(temp_path, "w", encoding="utf-8") as f:
                json.dump(chat, f, ensure_ascii=False, indent=2)
            # 跑摘要+命名
            summary = generate_summary_name(chat)
            safe_summary = "".join(c for c in summary if c.isalnum() or c in " _-")[:30]
            new_filename = f"{temp_filename.split('_')[0]}_{safe_summary}.json"
            new_path = os.path.join(HISTORY_DIR, new_filename)
            os.rename(temp_path, new_path)
            print(f"聊天记录保存并命名成功：{new_filename}")
        except Exception as e:
            print(f"异步保存失败（保留原始文件名）：{e}")
    # 启动普通线程（不是daemon）
    t = threading.Thread(target=do_save)
    t.start()
    pending_threads.append(t)

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
        async_save(chat, temp_filename)

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
    process_all_untitled_files()   # 自动补偿未命名聊天记录
    monitor_thread = Thread(target=monitor_parent, daemon=True)
    monitor_thread.start()
    app.run(port=6969)
