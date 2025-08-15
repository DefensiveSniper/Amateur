// douyin-state.js - 本地缓存
const KEY = 'douyinFormCache';

export function saveCache(data) {
  localStorage.setItem(KEY, JSON.stringify(data||{}));
}

export function loadCache() {
  try { return JSON.parse(localStorage.getItem(KEY) || '{}'); }
  catch { return {}; }
}