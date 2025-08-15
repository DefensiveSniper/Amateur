// chat-ui.js - 聊天页面入口
import { initChatState } from './chat-state.js';
import { initConfig } from './chat-config.js';
import { loadHistoryList } from './chat-history.js';

export function initChat() {
  initChatState();
  bindButtons();
  initConfig();
  loadHistoryList();
}

function bindButtons() {
  const newBtn = document.getElementById('newChatButton');
  const cfgBtn = document.getElementById('configApiButton');
  const hisBtn = document.getElementById('historyButton');
  
  newBtn?.addEventListener('click', () => {
    console.log('新聊天按钮被点击');
    window.dispatchEvent(new CustomEvent('chat:new'));
  });
  
  cfgBtn?.addEventListener('click', () => {
    console.log('配置按钮被点击');
    openConfigModal();
  });
  
  hisBtn?.addEventListener('click', () => {
    console.log('历史按钮被点击');
    openHistoryModal();
  });
}

function openConfigModal() {
  const modal = document.getElementById('configModal');
  const overlay = document.getElementById('modalOverlay');
  
  if (modal && overlay) {
    overlay.style.display = 'block';
    overlay.classList.add('active');
    modal.style.display = 'block';
    modal.classList.add('active');
  }
}

function openHistoryModal() {
  const modal = document.getElementById('historyModal');
  const overlay = document.getElementById('modalOverlay');
  
  if (modal && overlay) {
    overlay.style.display = 'block';
    overlay.classList.add('active');
    modal.style.display = 'block';
    modal.classList.add('active');
  }
}