// modal.js - 通用 Modal/Overlay
import { qs, addClass, removeClass } from './dom.js';

export function openModal(sel) {
  const el = qs(sel);
  if (!el) return;
  el.style.display = 'flex';
  setTimeout(() => addClass(el, 'show'));
}

export function closeModal(sel) {
  const el = qs(sel);
  if (!el) return;
  removeClass(el, 'show');
  setTimeout(() => el.style.display = 'none', 300);
}

export function bindOverlayClose(sel) {
  const el = qs(sel);
  if (!el) return;
  el.addEventListener('click', (e) => {
    if (e.target === el) closeModal(sel);
  });
}

export function bindEscClose(sel) {
  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') closeModal(sel);
  });
}