// theme.js - 主题切换逻辑
import { qs } from '../dom.js';

let current = 'pink';

export function initTheme() {
  document.body.classList.add('pink-theme');
  const btn = qs('#themeToggleButton');
  if (btn) {
    btn.style.background = 'linear-gradient(135deg, #ffb3d9 0%, #ff99cc 100%)';
    const icon = btn.querySelector('img');
    if (icon) { icon.src = '/static/images/sun.svg'; icon.alt = '太阳'; }
    btn.addEventListener('click', () => switchTheme());
  }
}

function switchTheme() {
  const body = document.body;
  const btn = qs('#themeToggleButton');
  const icon = btn?.querySelector('img');
  if (current === 'pink') {
    body.classList.remove('pink-theme');
    body.classList.add('blue-theme');
    if (btn) btn.style.background = 'linear-gradient(135deg, #4a90e2 0%, #357abd 100%)';
    if (icon) { icon.src = '/static/images/moon.svg'; icon.alt = '月亮'; }
    current = 'blue';
  } else {
    body.classList.remove('blue-theme');
    body.classList.add('pink-theme');
    if (btn) btn.style.background = 'linear-gradient(135deg, #ffb3d9 0%, #ff99cc 100%)';
    if (icon) { icon.src = '/static/images/sun.svg'; icon.alt = '太阳'; }
    current = 'pink';
  }
}