// load-page.js - 页面片段动态加载
const pageCache = new Map();

export async function loadPage(page) {
  if (pageCache.has(page)) return pageCache.get(page);
  
  try {
    const resp = await fetch(`/templates/pages/${page}.html`);
    if (!resp.ok) throw new Error(`Failed to load ${page}`);
    const html = await resp.text();
    pageCache.set(page, html);
    return html;
  } catch (err) {
    console.error('Load page error:', err);
    return getStaticPage(page);
  }
}

// 静态页面内容作为降级方案
function getStaticPage(page) {
  const pages = {
    home: `<iframe src="https://hzihao.icu" class="iframe-content"></iframe>
           <div class="main-tail">
             <a href="https://hzihao.icu" target="_blank"><p>Amateur发电的地方</p></a>
           </div>`,
    
    tools: `<div class="main-header fade-in">
              <h2>一些可能有用的玩意</h2>
            </div>
            <div class="cards-wrapper" id="cards-wrapper">
              <div class="card"><img src="/static/images/ela.png" alt="图片1"></div>
              <div class="card douyin-card" style="cursor: pointer;">
                <img src="/static/images/tiktok_card.png" alt="抖音视频下载" style="width: 100%; height: 100%; object-fit: cover; border-radius: 16px;">
                <div style="position: absolute; bottom: 20px; left: 50%; transform: translateX(-50%); background: rgba(255,255,255,0.9); padding: 8px 16px; border-radius: 8px; font-weight: 600; color: #2c3e50;">抖音视频下载</div>
              </div>
              <div class="card"><img src="/static/images/ela.png" alt="图片3"></div>
            </div>
            
            <!-- 抖音下载弹窗 -->
            <div id="douyinModal" class="douyin-modal" style="display: none;">
              <div class="douyin-modal-content">
                <div class="douyin-modal-header">
                  <h2>抖音视频下载</h2>
                  <button id="openDownloadPathBtn" class="open-path-btn" title="打开下载路径">
                    <svg width="16" height="16" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
                      <path d="M3 7v10a2 2 0 0 0 2 2h14a2 2 0 0 0 2-2V9a2 2 0 0 0-2-2h-6l-2-2H5a2 2 0 0 0-2 2z"></path>
                    </svg>
                    打开路径
                  </button>
                  <span class="douyin-modal-close">&times;</span>
                </div>
                
                <!-- 切换按钮 -->
                <div class="douyin-tab-buttons" style="display: flex; border-bottom: 1px solid #e0e0e0; margin-bottom: 20px;">
                  <button type="button" class="douyin-tab-btn active" data-tab="homepage" style="flex: 1; padding: 12px; border: none; background: none; cursor: pointer; font-weight: 500; border-bottom: 2px solid #007bff;">主页视频</button>
                  <button type="button" class="douyin-tab-btn" data-tab="specific" style="flex: 1; padding: 12px; border: none; background: none; cursor: pointer; font-weight: 500; border-bottom: 2px solid transparent;">指定视频</button>
                </div>
                
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
              </div>
            </div>`,
    
    chat: `<div class="chat-container">
            <div class="button-container">
              <button class="button-item" id="newChatButton">
                <div class="button-icon">
                  <img src="/static/images/newchat.png" alt="newchat">
                </div>
                新聊天
              </button>
              <button class="button-item" id="configApiButton">
                <div class="button-icon">
                  <img src="/static/images/setting.png" alt="setting">
                </div>
                配置
              </button>
              <button class="button-item" id="historyButton">
                <div class="button-icon">
                  <img src="/static/images/history.png" alt="history">
                </div>
                回忆录
              </button>
            </div>
            <div class="chat-box" id="chat-box"></div>
            <div class="chat-input">
                <input type="text" id="userInput" placeholder="输入你的问题 (Shift+Enter 换行)">
                <button id="sendButton">发送</button>
            </div>
        </div>
        <!-- 配置模态框 -->
        <div class="modal-overlay" id="modalOverlay"></div>
        <div class="modal" id="configModal">
            <h3>API 配置</h3>
            <label>提供方：
                <select id="provider">
                    <option value="openai">OpenAI</option>
                    <option value="deepseek">DeepSeek</option> 
                </select>
            </label>
            <br><br>
            <label>模型：
                <select id="model">
                    <!-- 默认选项 -->
                </select>
            </label>
            <br><br>
            <label>
                API Key:
                <input type="text" id="apiKey" placeholder="输入API Key">
            </label>
            <br><br>
            <button id="saveConfig">保存</button>
            <button id="closeModal">取消</button>
        </div>
        <!-- 回忆录模态框 -->
        <div class="modal" id="historyModal">
          <h3>聊天历史</h3>
          <div id="historyList" style="max-height: 300px; overflow-y: auto; margin: 10px 0;"></div>
          <button id="closeHistory">关闭</button>
        </div>
        <!-- 删除确认模态框 -->
        <div class="modal" id="deleteConfirmModal">
          <h3 id="deleteConfirmText">确认删除？</h3>
          <button id="confirmDeleteBtn">确认</button>
          <button id="cancelDeleteBtn">取消</button>
        </div>`,
    
    about: `<div class="page-content">
              <div class="main-header fade-in"><h2>一些可能有用的信息</h2></div>
              <div class="about-content"><p>本应用由Amateur个人独立使用AI开发。</p></div>
            </div>`
  };
  
  return pages[page] || '<div>页面不存在</div>';
}