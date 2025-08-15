// douyin-ui.js - 负责 Modal 打开/关闭与 Tab 切换
import { openModal, closeModal } from '../modal.js';

export function bindDouyinUI() {
  const openCard = document.querySelector('.douyin-card');
  if (openCard) openCard.addEventListener('click', () => openModal('#douyinModal'));

  const closeBtn = document.querySelector('.douyin-modal-close');
  if (closeBtn) closeBtn.addEventListener('click', () => closeModal('#douyinModal'));

  const tabs = document.querySelectorAll('.douyin-tab-btn');
  const forms = document.querySelectorAll('.douyin-form-content');
  tabs.forEach(btn => btn.addEventListener('click', () => {
    const tab = btn.getAttribute('data-tab');
    tabs.forEach(b => { b.classList.remove('active'); b.style.borderBottomColor='transparent'; });
    btn.classList.add('active');
    btn.style.borderBottomColor = '#007bff';
    forms.forEach(f => f.style.display = 'none');
    const active = document.querySelector(`[data-form="${tab}"]`);
    if (active) active.style.display = 'flex';
  }));
}