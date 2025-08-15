// chat-state.js - 聊天状态管理
import { chatApi } from './chat-api.js';
import { qs } from '../dom.js';
import { markdownToHtml, addCodeCopyButtons } from './markdown.js';

let chatState = {
  messages: [],
  currentFilename: null,
  isStreaming: false,
  config: null
};

export function initChatState() {
  loadConfig();
  bindInputEvents();
  bindNewChatEvent();
}

async function loadConfig() {
  try {
    chatState.config = await chatApi.getConfig();
  } catch (err) {
    console.error('Failed to load config:', err);
  }
}

function bindInputEvents() {
  const input = qs('#userInput');
  const sendBtn = qs('#sendButton');
  
  if (!input || !sendBtn) return;
  
  // 回车发送，Shift+回车换行
  input.addEventListener('keydown', (e) => {
    if (e.key === 'Enter' && !e.shiftKey) {
      e.preventDefault();
      sendMessage();
    }
  });
  
  sendBtn.addEventListener('click', sendMessage);
}

function bindNewChatEvent() {
  window.addEventListener('chat:new', () => {
    startNewChat();
  });
}

function startNewChat() {
  chatState.messages = [];
  chatState.currentFilename = null;
  renderChatBox();
}

async function sendMessage() {
  const input = qs('#userInput');
  if (!input || chatState.isStreaming) return;
  
  const text = input.value.trim();
  if (!text) return;
  
  // 添加用户消息
  chatState.messages.push({ type: 'user', text });
  input.value = '';
  
  // 渲染用户消息
  renderChatBox();
  
  // 开始流式响应
  chatState.isStreaming = true;
  updateSendButton(true);
  
  const assistantMessage = { type: 'assistant', text: '' };
  chatState.messages.push(assistantMessage);
  renderChatBox();
  
  try {
    const messages = chatState.messages.map(msg => ({
      role: msg.type === 'user' ? 'user' : 'assistant',
      content: msg.text
    }));
    
    await chatApi.chat(
      messages,
      (chunk) => {
        // 收到流式数据
        assistantMessage.text += chunk;
        updateLastMessage(assistantMessage.text);
      },
      (error) => {
        // 错误处理
        console.error('Chat error:', error);
        assistantMessage.text += `\n[错误: ${error.message}]`;
        updateLastMessage(assistantMessage.text);
      },
      () => {
        // 完成
        chatState.isStreaming = false;
        updateSendButton(false);
        saveCurrentChat();
      }
    );
  } catch (err) {
    console.error('Send message error:', err);
    assistantMessage.text = `[错误: ${err.message}]`;
    updateLastMessage(assistantMessage.text);
    chatState.isStreaming = false;
    updateSendButton(false);
  }
}

function updateSendButton(streaming) {
  const sendBtn = qs('#sendButton');
  if (sendBtn) {
    sendBtn.textContent = streaming ? '发送中...' : '发送';
    sendBtn.disabled = streaming;
  }
}

function updateLastMessage(text) {
  const chatBox = qs('#chat-box');
  if (!chatBox) return;
  
  const lastMessage = chatBox.lastElementChild;
  if (lastMessage && lastMessage.classList.contains('assistant')) {
    const content = lastMessage.querySelector('.ai-message');
    if (content) {
      content.innerHTML = markdownToHtml(text);
      addCodeCopyButtons();
      // 滚动到底部，确保最新内容可见
      chatBox.scrollTop = chatBox.scrollHeight;
    }
  }
}

function renderChatBox() {
  const chatBox = qs('#chat-box');
  if (!chatBox) return;
  
  chatBox.innerHTML = '';
  
  chatState.messages.forEach(msg => {
    const msgEl = document.createElement('div');
    msgEl.className = `message ${msg.type}`;

    const innerClass = msg.type === 'user' ? 'user-message' : 'ai-message';
    const innerHtml = msg.type === 'user' ? escapeHtml(msg.text) : markdownToHtml(msg.text);
    msgEl.innerHTML = `
      <div class="${innerClass}">${innerHtml}</div>
    `;
    
    chatBox.appendChild(msgEl);
  });
  
  addCodeCopyButtons();
  // 滚动到底部
  chatBox.scrollTop = chatBox.scrollHeight;
}

function escapeHtml(text) {
  const div = document.createElement('div');
  div.textContent = text;
  return div.innerHTML.replace(/\n/g, '<br>');
}

async function saveCurrentChat() {
  if (chatState.messages.length === 0) return;
  
  try {
    const result = await chatApi.saveHistory(chatState.messages, chatState.currentFilename);
    if (result.filename) {
      chatState.currentFilename = result.filename;
    }
  } catch (err) {
    console.error('Failed to save chat:', err);
  }
}

export function loadChatHistory(messages, filename) {
  chatState.messages = messages || [];
  chatState.currentFilename = filename;
  renderChatBox();
}

export function getChatState() {
  return { ...chatState };
}