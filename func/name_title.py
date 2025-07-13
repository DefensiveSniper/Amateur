import os
import json
import uuid
import threading
from openai import OpenAI

# 用大模型生成聊天标题
def generate_summary_name(chat, client, config):
    print(client, flush=True)
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

# 补偿命名
def process_all_untitled_files(HISTORY_DIR, client, config):
    for fname in os.listdir(HISTORY_DIR):
        if fname.endswith(".json") and "_untitled_" in fname:
            fpath = os.path.join(HISTORY_DIR, fname)
            try:
                with open(fpath, "r", encoding="utf-8") as f:
                    chat = json.load(f)
                summary = generate_summary_name(chat, client, config)
                safe_summary = "".join(c for c in summary if c.isalnum() or c in " _-")[:30]
                new_filename = f"{fname.split('_')[0]}_{safe_summary}.json"
                new_path = os.path.join(HISTORY_DIR, new_filename)
                os.rename(fpath, new_path)
                print(f"已补偿命名: {new_filename}")
            except Exception as e:
                print(f"摘要补偿失败({fname}): {e}")
                
# 异步保存聊天记录
def async_save(chat, temp_filename, HISTORY_DIR, client, pending_threads, config):
    print("异步保存正在执行...", flush=True)
    def do_save():
        try:
            # 保存聊天内容
            temp_path = os.path.join(HISTORY_DIR, temp_filename)
            with open(temp_path, "w", encoding="utf-8") as f:
                json.dump(chat, f, ensure_ascii=False, indent=2)
            # 跑摘要+命名
            summary = generate_summary_name(chat, client, config)
            safe_summary = "".join(c for c in summary if c.isalnum() or c in " _-")[:30]
            new_filename = f"{temp_filename.split('_')[0]}_{safe_summary}.json"
            new_path = os.path.join(HISTORY_DIR, new_filename)
            os.rename(temp_path, new_path)
            print(f"聊天记录保存并命名成功：{new_filename}")
        except Exception as e:
            print(f"异步保存失败（保留原始文件名）：{e}")
    # 启动线程
    t = threading.Thread(target=do_save)
    t.start()
    pending_threads.append(t)