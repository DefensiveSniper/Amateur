// douyin-api.js - 后端接口封装
async function jsonFetch(url, opts={}) {
  const res = await fetch(url, { headers: { 'Content-Type': 'application/json' }, ...opts });
  if (!res.ok) throw new Error(await res.text());
  return res.json();
}

export const api = {
  openDownloadPath: () => jsonFetch('/open_download_path', { method: 'POST' }),
  saveConfig: (data) => jsonFetch('/save_config', { method: 'POST', body: JSON.stringify(data) }),
  getConfig: () => jsonFetch('/get_config'),
  douyinLogin: () => jsonFetch('/douyin_login', { method: 'POST' }),
  douyinUserDownload: (data) => jsonFetch('/douyin_user_download', { method: 'POST', body: JSON.stringify(data) }),
  douyinSpecificDownload: (data) => jsonFetch('/douyin_specific_download', { method: 'POST', body: JSON.stringify(data) }),
};