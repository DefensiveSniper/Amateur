// settings.js - 设置弹窗开关（UI 与过渡）
import { openModal, closeModal, bindOverlayClose, bindEscClose } from '../modal.js';

export function initSettings() {
  const trigger = document.getElementById('menusettingsButton');
  const modal = document.getElementById('settingsPopup');
  const closeBtn = document.getElementById('closeSettingsPopup');
  if (!trigger || !modal || !closeBtn) return;

  trigger.addEventListener('click', () => openModal('#settingsPopup'));
  closeBtn.addEventListener('click', () => closeModal('#settingsPopup'));
  bindOverlayClose('#settingsPopup');
  bindEscClose('#settingsPopup');
}