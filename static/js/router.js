// router.js - 简易路由/页面切换（基于 data-page）
import { qs } from './dom.js';

let handler = null;

export function initRouter(onNavigate) {
  handler = onNavigate;
}

export function navigateTo(page) {
  if (!handler) return;
  handler(page);
  // 维护 hash，便于刷新还原
  location.hash = `#${page}`;
}

export function currentPage() {
  return (location.hash || '#home').replace('#', '');
}