// douyin-init.js - tools 页面装载后绑定事件
import { bindDouyinUI } from './douyin-ui.js';
import { saveCache, loadCache } from './douyin-state.js';
import { api } from './douyin-api.js';
import { bindDownloadEvents } from '../download/dl-socket.js';

export function initDouyin() {
  // 先注入 Tab 与表单内容，再绑定事件
  injectDouyinContents();
  bindDouyinUI();
  restoreForm();
  bindForms();
  const openBtn = document.getElementById('openDownloadPathBtn');
  if (openBtn) openBtn.addEventListener('click', onOpenPath);
}

function onOpenPath() {
  api.openDownloadPath().catch(console.error);
}

function injectDouyinContents() {
  const tabsWrap = document.getElementById('douyinTabButtons');
  const formsWrap = document.getElementById('douyinFormsContainer');
  if (!tabsWrap || !formsWrap) return;

  tabsWrap.innerHTML = `
    <div class="douyin-tab-buttons" style="display: flex; border-bottom: 1px solid #e0e0e0; margin-bottom: 20px; gap: 8px;">
      <button type="button" class="douyin-tab-btn active" data-tab="homepage" style="flex: 1; padding: 12px; border: none; background: none; cursor: pointer; font-weight: 500; border-bottom: 2px solid #007bff;">主页视频</button>
      <button type="button" class="douyin-tab-btn" data-tab="specific" style="flex: 1; padding: 12px; border: none; background: none; cursor: pointer; font-weight: 500; border-bottom: 2px solid transparent;">指定视频</button>
    </div>
  `;

  formsWrap.innerHTML = `
    <!-- 主页视频表单 -->
    <form id="douyin-download-form" class="douyin-form-content" data-form="homepage" style="display: flex; flex-direction: column; gap: 22px; padding: 0 20px 20px 20px;">
      <label>
        <span style="font-weight:500;">sec_user_id(主页链接中'user/'后的字符串MS4开头)</span>
        <input type="text" name="sec_user_id" id="sec_user_id" class="input-field" placeholder="请输入sec_user_id" required>
      </label>
      <label>
        <span style="font-weight:500;">cookies</span>
        <input type="text" name="cookies" id="cookies" class="input-field" placeholder="放空则进行扫码自动填充">
      </label>
      <label>
        <span style="font-weight:500;">msToken</span>
        <input type="text" name="msToken" id="msToken" class="input-field" placeholder="放空则进行扫码自动填充">
      </label>
      <label>
        <span style="font-weight:500;">最大下载视频数</span>
        <input type="number" name="max_dloads" id="max_dloads" class="input-field" placeholder="请输入最大下载视频数" min="1" required value="10">
      </label>
      <div style="display: flex; flex-direction: row; gap: 18px;">
        <button type="submit" id="start_dload" class="main-btn" style="flex: 7;">开始下载</button>
        <button type="button" id="saveConfigBtn" class="main-btn" style="flex: 3;">保存</button>
      </div>
    </form>

    <!-- 指定视频表单 -->
    <form id="douyin-specific-form" class="douyin-form-content" data-form="specific" style="display: none; flex-direction: column; gap: 22px; padding: 0 20px 20px 20px;">
      <label>
        <span style="font-weight:500;">视频分享链接</span>
        <input type="text" name="share_url" id="share_url" class="input-field" placeholder="请输入视频分享链接" required>
      </label>
      <label>
        <span style="font-weight:500;">cookies</span>
        <input type="text" name="cookies_specific" id="cookies_specific" class="input-field" placeholder="放空则进行扫码自动填充">
      </label>
      <label>
        <span style="font-weight:500;">msToken</span>
        <input type="text" name="msToken_specific" id="msToken_specific" class="input-field" placeholder="放空则进行扫码自动填充">
      </label>
      <div style="display: flex; flex-direction: row; gap: 18px;">
        <button type="submit" id="start_dload_specific" class="main-btn" style="flex: 7;">开始下载</button>
        <button type="button" id="saveConfigBtn_specific" class="main-btn" style="flex: 3;">保存</button>
      </div>
    </form>
  `;
}

async function restoreForm() {
  // 先取后端配置，再叠加本地缓存，确保 config.json 的值能正确“导入到 div”（表单控件）
  let serverTools = {};
  try {
    const cfg = await api.getConfig();
    serverTools = (cfg && cfg.tools) || {};
  } catch (e) {
    console.warn('获取后端配置失败，使用本地缓存回填', e);
  }
  const cache = loadCache();
   const f1 = document.getElementById('douyin-download-form');
   if (f1) {
     const keys = ['sec_user_id','cookies','msToken','max_dloads'];
     keys.forEach(k => {
       const val = (cache[k] && String(cache[k]).trim() !== '') ? cache[k] : serverTools[k];
       if (val != null) f1[k].value = val;
     });
   }
   const f2 = document.getElementById('douyin-specific-form');
   if (f2) {
     const keys = ['share_url','cookies_specific','msToken_specific'];
     keys.forEach(k => {
       let val = null;
       if (k === 'cookies_specific') {
         val = (cache[k] && String(cache[k]).trim() !== '') ? cache[k]
               : (serverTools[k] && String(serverTools[k]).trim() !== '') ? serverTools[k]
               : serverTools['cookies'];
       } else if (k === 'msToken_specific') {
         val = (cache[k] && String(cache[k]).trim() !== '') ? cache[k]
               : (serverTools[k] && String(serverTools[k]).trim() !== '') ? serverTools[k]
               : serverTools['msToken'];
       } else {
         val = (cache[k] && String(cache[k]).trim() !== '') ? cache[k] : serverTools[k];
       }
       if (val != null) f2[k].value = val;
     });
   }
}

function bindForms() {
  const f1 = document.getElementById('douyin-download-form');
  if (f1) {
    f1.addEventListener('submit', async (e) => {
      e.preventDefault();
      const data = Object.fromEntries(new FormData(f1).entries());
      saveCache({ ...loadCache(), ...data });
      try {
        const response = await api.douyinUserDownload(data);
        const taskId = response.task_id;
        bindDownloadEvents(taskId);
      } catch (error) {
        console.error('下载启动失败:', error);
      }
    });
    const saveBtn = document.getElementById('saveConfigBtn');
    if (saveBtn) saveBtn.addEventListener('click', () => {
      const data = Object.fromEntries(new FormData(f1).entries());
      saveCache({ ...loadCache(), ...data });
      api.saveConfig(data).catch(console.error);
    });
  }

  const f2 = document.getElementById('douyin-specific-form');
  if (f2) {
    f2.addEventListener('submit', async (e) => {
      e.preventDefault();
      const data = Object.fromEntries(new FormData(f2).entries());
      saveCache({ ...loadCache(), ...data });
      try {
        const response = await api.douyinSpecificDownload(data);
        const taskId = response.task_id;
        bindDownloadEvents(taskId);
      } catch (error) {
        console.error('指定视频下载启动失败:', error);
      }
    });
    const saveBtn2 = document.getElementById('saveConfigBtn_specific');
    if (saveBtn2) saveBtn2.addEventListener('click', () => {
      const data = Object.fromEntries(new FormData(f2).entries());
      saveCache({ ...loadCache(), ...data });
      api.saveConfig(data).catch(console.error);
    });
  }
}