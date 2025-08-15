// chat-config.js - 配置面板逻辑
import { chatApi } from './chat-api.js';
import { qs } from '../dom.js';

const modelsByProvider = {
  openai: ['gpt-4o', 'gpt-4o-mini', 'gpt-4.1-mini'],
  deepseek: ['deepseek-chat', 'deepseek-reasoner']
};

// 缓存一次从后端获取到的配置，便于 provider 切换时读取对应 API Key
let serverCfg = null;

export function initConfig() {
  bindModalButtons();
  loadConfigToForm();
}

function bindModalButtons() {
  const modal = qs('#configModal');
  const overlay = qs('#modalOverlay');
  const closeBtn = qs('#closeModal');
  const saveBtn = qs('#saveConfig');
  const providerSel = qs('#provider');
  const modelSel = qs('#model');

  function close() {
    // 关闭所有模态框，避免有残留阻挡点击
    document.querySelectorAll('.modal').forEach(m => {
      m.classList.remove('active');
      m.style.display = 'none';
    });
    if (overlay) {
      overlay.classList.remove('active');
      overlay.style.display = 'none';
    }
  }

  closeBtn?.addEventListener('click', close);
  overlay?.addEventListener('click', close);

  saveBtn?.addEventListener('click', async () => {
    const provider = providerSel.value;
    const model = modelSel.value;
    const apiKey = qs('#apiKey').value.trim();
    const systemPrompt = '';

    const payload = {
      provider,
      model,
      systemPrompt,
      apiKeys: { [provider]: apiKey }
    };

    try {
      await chatApi.saveConfig(payload);
      close();
    } catch (e) {
      console.error('保存配置失败', e);
      alert('保存配置失败：' + (e.message || '未知错误'));
    }
  });

  providerSel?.addEventListener('change', () => {
    const p = providerSel.value;
    populateModels(p);
    // 当切换 provider 时，从后端配置里拿该 provider 的 key 进行回填
    const apiKeyInput = qs('#apiKey');
    const key = serverCfg?.chat?.apiKeys?.[p] || '';
    apiKeyInput.value = key;
  });
}

async function loadConfigToForm() {
  try {
    serverCfg = await chatApi.getConfig();
    const providerSel = qs('#provider');
    const modelSel = qs('#model');
    const apiKeyInput = qs('#apiKey');

    // 渲染 provider 下拉
    const selectedProvider = serverCfg.chat?.provider || 'openai';
    populateProviders(selectedProvider);

    // 渲染模型列表并选择
    populateModels(providerSel.value);
    const model = serverCfg.chat?.model || modelsByProvider[providerSel.value][0];
    modelSel.value = model;

    // 回填对应 provider 的 API Key
    const key = serverCfg.chat?.apiKeys?.[providerSel.value] || '';
    apiKeyInput.value = key;
  } catch (e) {
    console.error('加载配置失败', e);
  }
}

function populateProviders(selected) {
  const providerSel = qs('#provider');
  if (!providerSel) return;
  providerSel.innerHTML = '';
  Object.keys(modelsByProvider).forEach(p => {
    const opt = document.createElement('option');
    opt.value = p;
    opt.textContent = p.charAt(0).toUpperCase() + p.slice(1);
    providerSel.appendChild(opt);
  });
  // 默认或指定选中
  if (selected && Object.keys(modelsByProvider).includes(selected)) {
    providerSel.value = selected;
  } else {
    providerSel.value = 'openai';
  }
}

function populateModels(provider) {
  const modelSel = qs('#model');
  modelSel.innerHTML = '';
  (modelsByProvider[provider] || []).forEach(m => {
    const opt = document.createElement('option');
    opt.value = m;
    opt.textContent = m;
    modelSel.appendChild(opt);
  });
}