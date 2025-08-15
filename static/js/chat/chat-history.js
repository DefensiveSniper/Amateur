// chat-history.js - 历史记录列表
import { chatApi } from './chat-api.js';
import { qs } from '../dom.js';
import { loadChatHistory } from './chat-state.js';

let pendingDeleteFilename = null;

function openDeleteConfirm(filename) {
  pendingDeleteFilename = filename;
  const modal = qs('#deleteConfirmModal');
  const overlay = qs('#modalOverlay');
  const text = qs('#deleteConfirmText');
  if (text) text.textContent = `确认删除该聊天记录？\n${filename}`;
  if (overlay) {
    overlay.style.display = 'block';
    overlay.classList.add('active');
  }
  if (modal) {
    modal.style.display = 'block';
    modal.classList.add('active');
  }
}

function closeDeleteConfirm() {
  const modal = qs('#deleteConfirmModal');
  const overlay = qs('#modalOverlay');
  if (modal) {
    modal.classList.remove('active');
    modal.style.display = 'none';
  }
  if (overlay) {
    overlay.classList.remove('active');
    overlay.style.display = 'none';
  }
  pendingDeleteFilename = null;
}

async function doConfirmDelete() {
  if (!pendingDeleteFilename) return;
  try {
    await chatApi.deleteHistory(pendingDeleteFilename);
    await loadHistoryList();
  } catch (err) {
    console.error('删除失败', err);
    alert('删除失败：' + (err.message || '未知错误'));
  } finally {
    closeDeleteConfirm();
  }
}

export async function loadHistoryList() {
  const listEl = qs('#historyList');
  if (!listEl) return;
  listEl.innerHTML = '加载中...';

  try {
    const items = await chatApi.getHistory();
    if (!Array.isArray(items) || items.length === 0) {
      listEl.innerHTML = '<div style="color:#666;">暂无历史</div>';
      return;
    }

    listEl.innerHTML = '';
    items.reverse().forEach(h => {
      const row = document.createElement('div');
      row.className = 'history-row';
      row.style.display = 'flex';
      row.style.justifyContent = 'space-between';
      row.style.alignItems = 'center';
      row.style.gap = '8px';
      row.style.padding = '6px 0';
      row.style.borderBottom = '2px solid #eee';

      const title = document.createElement('div');
      const fn = h.filename || '';
      const underscoreIndex = fn.indexOf('_');
      const namePart = underscoreIndex >= 0 ? fn.slice(underscoreIndex + 1).replace(/\.json$/i, '') : fn.replace(/\.json$/i, '');
      title.textContent = namePart || fn;
      title.style.flex = '1';
      title.style.cursor = 'pointer';
      title.title = h.filename;
      title.addEventListener('click', async () => {
        const data = await chatApi.loadHistory(h.filename);
        loadChatHistory(data, h.filename);
        closeHistoryModal();
      });

      const delBtn = document.createElement('button');
      delBtn.textContent = '删除';
      delBtn.style.marginLeft = '8px';
      delBtn.addEventListener('click', async (e) => {
        e.stopPropagation();
        openDeleteConfirm(h.filename);
      });

      row.appendChild(title);
      row.appendChild(delBtn);
      listEl.appendChild(row);
    });
  } catch (e) {
    console.error('加载历史失败', e);
    listEl.innerHTML = '<div style="color:#c00;">加载失败</div>';
  }

  const closeBtn = document.getElementById('closeHistory');
  closeBtn?.addEventListener('click', closeHistoryModal);

  // 绑定删除确认弹窗按钮（幂等绑定，不会重复效果）
  const confirmBtn = qs('#confirmDeleteBtn');
  const cancelBtn = qs('#cancelDeleteBtn');
  confirmBtn?.removeEventListener('click', doConfirmDelete);
  confirmBtn?.addEventListener('click', doConfirmDelete);
  cancelBtn?.removeEventListener('click', closeDeleteConfirm);
  cancelBtn?.addEventListener('click', closeDeleteConfirm);
}

function closeHistoryModal() {
  const modal = document.getElementById('historyModal');
  const overlay = document.getElementById('modalOverlay');
  if (modal) {
    modal.classList.remove('active');
    modal.style.display = 'none';
  }
  if (overlay) {
    overlay.classList.remove('active');
    overlay.style.display = 'none';
  }
}