// app.js - 入口：挂事件、注册路由、页面装载、全局初始化
import { loadPage } from './pages/load-page.js';
import { initRouter, navigateTo } from './router.js';
import { qs } from './dom.js';
import { initTheme } from './theme/theme.js';
import { initSettings } from './settings/settings.js';

window.App = {
  navigateTo,
};

function mountSidebarHandlers() {
  const items = document.querySelectorAll('.menu-item');
  items.forEach(it => {
    it.addEventListener('click', () => {
      items.forEach(mi => mi.classList.remove('active'));
      it.classList.add('active');
      const page = it.getAttribute('data-page');
      navigateTo(page);
    });
  });
}

async function boot() {
  initTheme();
  initRouter(async (page) => {
    const html = await loadPage(page);
    const el = qs('.main-content');
    if (el) el.innerHTML = html;

    // 页面级初始化
    if (page === 'tools') {
      const { initDouyin } = await import('./douyin/douyin-init.js');
      initDouyin();
    } else if (page === 'chat') {
      const { initChat } = await import('./chat/chat-ui.js');
      initChat();
    }
  });
  mountSidebarHandlers();
  initSettings();
  navigateTo('home');
}

document.addEventListener('DOMContentLoaded', boot);