// markdown.js - 轻量级 Markdown 解析器
export function markdownToHtml(text) {
  if (!text || typeof text !== 'string') return '';
  
  // 对特殊 HTML 字符转义
  const escapeHtml = (str) => {
    const div = document.createElement('div');
    div.textContent = str;
    return div.innerHTML;
  };
  
  // 先转义 HTML，再进行 Markdown 解析
  let html = escapeHtml(text);
  
  // 代码块（三个反引号）
  html = html.replace(/```(\w*)\n([\s\S]*?)```/g, (match, lang, code) => {
    const language = lang ? ` data-lang="${lang}"` : '';
    return `<pre class="code-block"${language}><code>${code.trim()}</code></pre>`;
  });
  
  // 行内代码
  html = html.replace(/`([^`]+)`/g, '<code class="inline-code">$1</code>');
  
  // 标题 (H1-H6)
  html = html.replace(/^(#{1,6})\s+(.+)$/gm, (match, hashes, text) => {
    const level = hashes.length;
    return `<h${level} class="markdown-h${level}">${text}</h${level}>`;
  });
  
  // 粗体
  html = html.replace(/\*\*(.*?)\*\*/g, '<strong>$1</strong>');
  html = html.replace(/__(.*?)__/g, '<strong>$1</strong>');
  
  // 斜体
  html = html.replace(/\*(.*?)\*/g, '<em>$1</em>');
  html = html.replace(/_(.*?)_/g, '<em>$1</em>');
  
  // 链接
  html = html.replace(/\[([^\]]+)\]\(([^)]+)\)/g, '<a href="$2" target="_blank" rel="noopener noreferrer">$1</a>');
  
  // 无序列表
  html = html.replace(/^[-*+]\s+(.+)$/gm, '<li class="markdown-li">$1</li>');
  html = html.replace(/(<li class="markdown-li">.*?<\/li>)/gs, '<ul class="markdown-ul">$1</ul>');
  
  // 有序列表
  html = html.replace(/^\d+\.\s+(.+)$/gm, '<li class="markdown-oli">$1</li>');
  html = html.replace(/(<li class="markdown-oli">.*?<\/li>)/gs, '<ol class="markdown-ol">$1</ol>');
  
  // 水平分割线
  html = html.replace(/^---$/gm, '<hr class="markdown-hr">');
  html = html.replace(/^\*\*\*$/gm, '<hr class="markdown-hr">');
  
  // 引用
  html = html.replace(/^>\s+(.+)$/gm, '<blockquote class="markdown-quote">$1</blockquote>');
  
  // 段落：连续非空行为一个段落
  const lines = html.split('\n');
  const paragraphs = [];
  let currentParagraph = [];
  
  for (const line of lines) {
    const trimmed = line.trim();
    
    // 如果是空行或者已经是块级元素，结束当前段落
    if (!trimmed || 
        trimmed.startsWith('<h') || 
        trimmed.startsWith('<pre') || 
        trimmed.startsWith('<ul') || 
        trimmed.startsWith('<ol') || 
        trimmed.startsWith('<blockquote') || 
        trimmed.startsWith('<hr')) {
      
      if (currentParagraph.length > 0) {
        paragraphs.push(`<p class="markdown-p">${currentParagraph.join(' ')}</p>`);
        currentParagraph = [];
      }
      
      if (trimmed) {
        paragraphs.push(trimmed);
      }
    } else {
      currentParagraph.push(trimmed);
    }
  }
  
  // 处理最后一个段落
  if (currentParagraph.length > 0) {
    paragraphs.push(`<p class="markdown-p">${currentParagraph.join(' ')}</p>`);
  }
  
  return paragraphs.join('\n');
}

// 为代码块添加复制功能
export function addCodeCopyButtons() {
  const codeBlocks = document.querySelectorAll('.ai-message pre.code-block');
  
  codeBlocks.forEach(block => {
    // 避免重复添加按钮
    if (block.querySelector('.copy-btn')) return;
    
    const copyBtn = document.createElement('button');
    copyBtn.className = 'copy-btn';
    copyBtn.textContent = '复制';
    copyBtn.style.cssText = `
      position: absolute;
      top: 8px;
      right: 8px;
      background: rgba(255, 255, 255, 0.9);
      border: 1px solid #ddd;
      border-radius: 4px;
      padding: 4px 8px;
      font-size: 12px;
      cursor: pointer;
      z-index: 1;
    `;
    
    // 设置相对定位以便按钮定位
    block.style.position = 'relative';
    
    copyBtn.addEventListener('click', async () => {
      const code = block.querySelector('code');
      if (code) {
        try {
          await navigator.clipboard.writeText(code.textContent);
          copyBtn.textContent = '已复制';
          setTimeout(() => {
            copyBtn.textContent = '复制';
          }, 2000);
        } catch (err) {
          console.error('复制失败:', err);
          copyBtn.textContent = '复制失败';
          setTimeout(() => {
            copyBtn.textContent = '复制';
          }, 2000);
        }
      }
    });
    
    block.appendChild(copyBtn);
  });
}