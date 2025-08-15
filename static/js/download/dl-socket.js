// dl-socket.js - socket.io 连接与监听
import { showDownloadModal, updateProgress, appendLog, hideDownloadModal } from './download-modal.js';

let socket = null;
let joined = new Set();

function ensureSocket() {
  if (!socket) {
    socket = io();
  }
  return socket;
}

export function joinDownloadRoom(taskId) {
  const s = ensureSocket();
  if (joined.has(taskId)) return;
  s.emit('join_download', { task_id: taskId });
  joined.add(taskId);
}

export function bindDownloadEvents(taskId) {
  const s = ensureSocket();
  joinDownloadRoom(taskId);
  showDownloadModal();

  s.on('dlog', (data) => {
    if (!data || (data.task_id && data.task_id !== taskId)) return;
    if (data.text) appendLog(data.text);
  });

  s.on('dprogress', (data) => {
    if (!data || (data.task_id && data.task_id !== taskId)) return;
    if (typeof data.percent === 'number') updateProgress(Math.max(0, Math.min(100, data.percent)));
  });

  s.on('dfinish', (data) => {
    if (!data || (data.task_id && data.task_id !== taskId)) return;
    if (data.text || data.msg) appendLog(data.text || data.msg);
    setTimeout(() => hideDownloadModal(), 1000);
  });
}