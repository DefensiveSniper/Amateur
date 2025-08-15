// toast.js - 轻提示
import { createEl } from './dom.js';

let container = null;

function ensure() {
  if (!container) {
    container = createEl('div', { className: 'toast-container' });
    document.body.appendChild(container);
  }
}

export function showToast(msg, duration=2000) {
  ensure();
  const item = createEl('div', { className: 'toast', innerText: msg });
  container.appendChild(item);
  requestAnimationFrame(() => item.classList.add('show'));
  setTimeout(() => {
    item.classList.remove('show');
    setTimeout(() => item.remove(), 300);
  }, duration);
}