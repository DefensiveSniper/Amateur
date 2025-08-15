// chat-api.js - 聊天 API 与 SSE 封装
async function jsonFetch(url, opts = {}) {
  const res = await fetch(url, { headers: { 'Content-Type': 'application/json' }, ...opts });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

// 使用 fetch + ReadableStream 解析 SSE（服务端采用 text/event-stream 输出 data: 行）
export function createSSEClient(messages, onMessage, onError, onComplete) {
  return new Promise(async (resolve, reject) => {
    try {
      const response = await fetch('/chat', {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify({ messages })
      });
      if (!response.ok || !response.body) {
        throw new Error(`HTTP ${response.status}`);
      }

      const reader = response.body.getReader();
      const decoder = new TextDecoder('utf-8');
      let buffer = '';

      const processBuffer = () => {
        let sepIndex;
        while ((sepIndex = buffer.indexOf('\n\n')) !== -1) {
          const eventBlock = buffer.slice(0, sepIndex);
          buffer = buffer.slice(sepIndex + 2);

          const lines = eventBlock.split('\n');
          let isError = false;
          let dataLines = [];
          for (const line of lines) {
            if (line.startsWith('event:')) {
              const evt = line.slice(6).trim();
              if (evt === 'error') isError = true;
            } else if (line.startsWith('data:')) {
              dataLines.push(line.slice(5).trimStart());
            }
          }
          const data = dataLines.join('\n');
          if (isError) {
            const err = new Error(data || 'SSE error');
            onError?.(err);
            reject(err);
            return false;
          } else if (data) {
            onMessage?.(data);
          }
        }
        return true;
      };

      while (true) {
        const { value, done } = await reader.read();
        if (done) break;
        buffer += decoder.decode(value, { stream: true });
        const ok = processBuffer();
        if (!ok) return; // 已触发错误并 reject
      }

      // 处理结束时残留
      if (buffer) {
        processBuffer();
      }

      onComplete?.();
      resolve();
    } catch (err) {
      onError?.(err);
      reject(err);
    }
  });
}

export const chatApi = {
  // 配置管理
  getConfig: () => jsonFetch('/get_config'),
  saveConfig: (data) => jsonFetch('/save_config', { method: 'POST', body: JSON.stringify(data) }),

  // 历史记录管理
  getHistory: () => jsonFetch('/get_history'),
  loadHistory: (filename) => jsonFetch(`/load_history?filename=${encodeURIComponent(filename)}`),
  saveHistory: (chat, filename) => jsonFetch('/save_history', {
    method: 'POST',
    body: JSON.stringify({ chat, filename })
  }),
  deleteHistory: (filename) => jsonFetch('/delete_history', {
    method: 'POST',
    body: JSON.stringify({ filename })
  }),

  // 流式聊天
  chat: createSSEClient
};