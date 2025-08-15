// download-modal.js - 下载进度弹窗控制
import { openModal, closeModal } from '../modal.js';

export function showDownloadModal() {
  openModal('#downloadModal');
}

export function hideDownloadModal() {
  closeModal('#downloadModal');
}

export function updateProgress(percent) {
  const bar = document.getElementById('downloadProgress');
  if (bar) {
    bar.style.width = `${percent}%`;
    bar.innerText = `${percent}%`;
  }
}

export function appendLog(text) {
  const log = document.getElementById('downloadLog');
  if (log) {
    const p = document.createElement('div');
    p.textContent = text;
    log.appendChild(p);
    log.scrollTop = log.scrollHeight;
  }
}