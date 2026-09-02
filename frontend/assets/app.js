/**
 * AI-Me · 前端逻辑（豆包 / DeepSeek 风格 + 完整功能）
 * =====================================================
 *  - 流式 SSE 聊天
 *  - 思考过程可视化（步骤实时更新）
 *  - 每条 AI 回答下方显示意图徽章
 *  - 回答排版美化：首行缩进 2em、段落间距、引用样式
 */

// 本地直连后端（无 nginx 代理时使用 8000）
const API_BASE = (window.location.hostname === 'localhost' || window.location.hostname === '127.0.0.1')
  && window.location.port && window.location.port !== '8000'
  ? `http://localhost:${window.location.port === '5500' ? '8000' : '8000'}`
  : window.location.origin;

let currentSessionId = localStorage.getItem('ai_me_session_id') || generateUUID();
let isStreaming = false;
let abortController = null;

// ===== 滚动策略 =====
// 用户明确要求：不自动滚动。
// 无论用户发送消息还是 AI 流式输出新内容，都不主动滚动页面/内部容器。
// 用户可以自己滚动查看内容（页面滚动 + 内部滚动条）。
function smartScrollToBottom(_force) {
  // 故意不滚动，保持用户当前阅读位置。
}

function bindScrollListener() {
  // 不再检测"用户上滑"状态；该机制已不再使用。
}

// 启用中栏内部滚动。CSS 要求 .scrollable 类才会 overflow-y: auto。
function enableInternalScroll() {
  const scrollEl = document.getElementById('chat-scroll');
  if (!scrollEl) return;
  scrollEl.classList.add('scrollable');
}

// ===== 错误处理 =====
function _debugError(msg, err) {
  console.error('[AI-Me]', msg, err);
  const dbg = document.getElementById('debug-bar');
  if (dbg) {
    dbg.textContent = '[ERROR] ' + msg + ' ' + (err && err.message || err || '');
    dbg.style.display = 'block';
  }
}
window.addEventListener('error', (e) => _debugError('window error', e.error || e.message));
window.addEventListener('unhandledrejection', (e) => _debugError('unhandled rejection', e.reason));

// ===== 初始化 =====
function _init() {
  try { window.injectSvgIcons && window.injectSvgIcons(); } catch (e) { _debugError('svg failed', e); }
  try { initTheme(); } catch (e) { _debugError('theme failed', e); }
  try { bindEvents(); } catch (e) { _debugError('bindEvents failed', e); }
  try { bindScrollListener(); } catch (e) { _debugError('bindScroll failed', e); }
  try { enableInternalScroll(); } catch (e) { _debugError('enableScroll failed', e); }

  window.sendMessage = sendMessage;
  window.loadProjects = loadProjects;
  Object.defineProperty(window, 'isStreaming', { get: () => isStreaming });
  Object.defineProperty(window, '__isStreaming', { get: () => isStreaming });
  window.quickAsk = function(question) {
    const input = document.getElementById('input');
    if (input) input.value = question;
    if (window.sendMessage) window.sendMessage();
  };

  loadProjects();
  loadMetrics();
  loadEvalMetrics();

  const dbg = document.getElementById('debug-bar');
  if (dbg) dbg.style.display = 'none';
}

if (document.readyState === 'loading') {
  document.addEventListener('DOMContentLoaded', _init);
} else {
  _init();
}

// ===== 主题 =====
function initTheme() {
  const saved = localStorage.getItem('ai_me_theme');
  if (saved === 'dark' || (!saved && window.matchMedia('(prefers-color-scheme: dark)').matches)) {
    document.documentElement.classList.add('dark');
  }
  updateThemeIcon();
}

function toggleTheme() {
  document.documentElement.classList.toggle('dark');
  const isDark = document.documentElement.classList.contains('dark');
  localStorage.setItem('ai_me_theme', isDark ? 'dark' : 'light');
  updateThemeIcon();
  if (window.loadEvalMetrics) window.loadEvalMetrics();
}

function updateThemeIcon() {
  const isDark = document.documentElement.classList.contains('dark');
  const btn = document.getElementById('theme-toggle');
  if (btn) btn.innerHTML = `<i data-svg="${isDark ? 'sun' : 'moon'}" class="w-4 h-4"></i>`;
  if (window.injectSvgIcons) window.injectSvgIcons();
}

// ===== 事件绑定 =====
function bindEvents() {
  document.getElementById('theme-toggle').addEventListener('click', toggleTheme);

  document.getElementById('clear-btn').addEventListener('click', () => {
    if (confirm('开启新对话？当前对话将清空。')) {
      currentSessionId = generateUUID();
      localStorage.setItem('ai_me_session_id', currentSessionId);
      document.getElementById('messages').innerHTML = '';
      const scrollEl = document.getElementById('chat-scroll');
      if (scrollEl) {
        scrollEl.classList.add('scrollable');
        scrollEl.scrollTop = 0;
      }
      showWelcome();
    }
  });

  document.getElementById('export-btn').addEventListener('click', exportChat);

  document.getElementById('metrics-btn').addEventListener('click', openMetrics);
  document.getElementById('metrics-close').addEventListener('click', closeMetrics);
  document.getElementById('metrics-overlay').addEventListener('click', (e) => {
    if (e.target.id === 'metrics-overlay') closeMetrics();
  });

  const input = document.getElementById('input');
  input.addEventListener('input', () => {
    input.style.height = '36px';
    input.style.height = Math.min(input.scrollHeight, 128) + 'px';
  });

  document.addEventListener('keydown', (e) => {
    if (e.key === 'Escape') closeMetrics();
  });
}

function showWelcome() {
  const welcome = document.getElementById('welcome');
  if (welcome) welcome.style.display = '';
  const suggestions = document.getElementById('initial-suggestions');
  if (suggestions) suggestions.style.display = '';
  document.getElementById('recommend-area').classList.add('hidden');
}

// ===== 加载项目 =====
async function loadProjects() {
  try {
    const res = await fetch(`${API_BASE}/projects`);
    if (!res.ok) return;
    const data = await res.json();
    renderProjects(data.projects || []);
  } catch (e) {
    console.warn('Projects 加载失败：', e);
  }
}

function renderProjects(projects) {
  const grid = document.getElementById('project-grid');
  const count = document.getElementById('project-count');
  if (!grid) return;
  if (!projects.length) {
    grid.innerHTML = '<p class="text-xs text-zinc-400 col-span-2">暂无项目</p>';
    if (count) count.textContent = '0';
    return;
  }
  if (count) count.textContent = projects.length;
  grid.innerHTML = projects.map(p => `
    <a href="${p.repo || '#'}" target="_blank" class="project-card block">
      <div class="flex items-start justify-between mb-1.5">
        <h4 class="text-sm font-semibold">${escapeHtml(p.name)}</h4>
        ${p.repo ? '<i data-svg="arrow" class="w-3.5 h-3.5 text-zinc-400 flex-shrink-0"></i>' : ''}
      </div>
      <p class="text-xs text-zinc-500 dark:text-zinc-400 mb-2 line-clamp-2">${escapeHtml(p.summary || '')}</p>
      <div class="flex flex-wrap">
        ${(p.tech_stack || []).slice(0, 4).map(t => `<span class="tech-badge">${escapeHtml(t)}</span>`).join('')}
      </div>
    </a>
  `).join('');
  if (window.injectSvgIcons) window.injectSvgIcons();
}

// ===== 加载性能指标 =====
async function loadMetrics() {
  try {
    const res = await fetch(`${API_BASE}/metrics`);
    if (!res.ok) return;
    const m = await res.json();
    setText('ttft-p50', m.ttft_ms.p50);
    setText('ttft-p95', m.ttft_ms.p95);
    setText('ttft-p99', m.ttft_ms.p99);
    setText('total-p50', m.total_ms.p50);
    setText('total-p95', m.total_ms.p95);
    setText('total-p99', m.total_ms.p99);
    setText('intent-p50', m.per_stage_ms.intent.p50);
    setText('intent-p95', m.per_stage_ms.intent.p95);
    setText('retrieve-p50', m.per_stage_ms.retrieve.p50);
    setText('retrieve-p95', m.per_stage_ms.retrieve.p95);
    setText('rerank-p50', m.per_stage_ms.rerank.p50);
    setText('rerank-p95', m.per_stage_ms.rerank.p95);
    setText('generate-p50', m.per_stage_ms.generate.p50);
    setText('generate-p95', m.per_stage_ms.generate.p95);
    setText('total-requests', m.total_requests);
    setText('tokens-per-sec', m.tokens_per_sec);
  } catch (e) {
    console.warn('Metrics 加载失败：', e);
  }
}

// ===== 加载 RAGAS 评估 =====
async function loadEvalMetrics() {
  try {
    const res = await fetch(`${API_BASE}/metrics/eval`);
    if (!res.ok) return;
    const data = await res.json();
    renderRadar(data.metrics, 'radar', 90, 14);
    renderRadar(data.metrics, 'radar-full', 110, 18);
    setText('eval-avg', data.average);
  } catch (e) {
    console.warn('Eval 加载失败：', e);
  }
}

function renderRadar(metrics, svgId = 'radar', R = 90, labelGap = 14) {
  const svg = document.getElementById(svgId);
  if (!svg || !metrics) return;
  const N = metrics.length;
  const isDark = document.documentElement.classList.contains('dark');
  const accent = '#5b5fc7';
  const gridColor = isDark ? '#3f3f46' : '#e4e4e7';
  const textColor = isDark ? '#a1a1aa' : '#71717a';

  let html = '';
  for (let i = 1; i <= 5; i++) {
    const r = (R * i) / 5;
    const pts = Array.from({length: N}, (_, j) => {
      const a = (Math.PI * 2 * j) / N - Math.PI / 2;
      return `${(r * Math.cos(a)).toFixed(1)},${(r * Math.sin(a)).toFixed(1)}`;
    }).join(' ');
    html += `<polygon points="${pts}" fill="none" stroke="${gridColor}" stroke-width="0.5"/>`;
  }
  for (let j = 0; j < N; j++) {
    const a = (Math.PI * 2 * j) / N - Math.PI / 2;
    html += `<line x1="0" y1="0" x2="${(R * Math.cos(a)).toFixed(1)}" y2="${(R * Math.sin(a)).toFixed(1)}" stroke="${gridColor}" stroke-width="0.5"/>`;
  }
  const dataPts = metrics.map((m, j) => {
    const a = (Math.PI * 2 * j) / N - Math.PI / 2;
    const r = R * m.score;
    return `${(r * Math.cos(a)).toFixed(1)},${(r * Math.sin(a)).toFixed(1)}`;
  }).join(' ');
  html += `<polygon points="${dataPts}" fill="${accent}" fill-opacity="0.2" stroke="${accent}" stroke-width="1.5"/>`;
  metrics.forEach((m, j) => {
    const a = (Math.PI * 2 * j) / N - Math.PI / 2;
    const r = R * m.score;
    html += `<circle cx="${(r * Math.cos(a)).toFixed(1)}" cy="${(r * Math.sin(a)).toFixed(1)}" r="2.5" fill="${accent}"/>`;
  });
  const shortNames = {
    context_precision: 'Precision', context_relevance: 'Relevance',
    faithfulness: 'Faith', answer_relevancy: 'Relevancy',
    answer_correctness: 'Correct', answer_similarity: 'Similar',
  };
  const fontSize = R < 100 ? 8 : 9;
  const scoreFontSize = R < 100 ? 7 : 8;
  metrics.forEach((m, j) => {
    const a = (Math.PI * 2 * j) / N - Math.PI / 2;
    const labelR = R + labelGap;
    const x = labelR * Math.cos(a);
    const y = labelR * Math.sin(a);
    const label = shortNames[m.name] || m.name;
    html += `<text x="${x.toFixed(1)}" y="${y.toFixed(1)}" fill="${textColor}" font-size="${fontSize}" text-anchor="middle" dominant-baseline="middle" font-family="Menlo, monospace">${label}</text>`;
    html += `<text x="${x.toFixed(1)}" y="${(y + labelGap * 0.6).toFixed(1)}" fill="${accent}" font-size="${scoreFontSize}" text-anchor="middle" dominant-baseline="middle" font-family="Menlo, monospace" font-weight="600">${m.score.toFixed(2)}</text>`;
  });
  svg.innerHTML = html;
}

function openMetrics() {
  document.getElementById('metrics-overlay').classList.remove('hidden');
  loadMetrics();
  loadEvalMetrics();
}

function closeMetrics() {
  document.getElementById('metrics-overlay').classList.add('hidden');
}

// ===== 发送消息（核心：思考 + 流式 + 徽章） =====
async function sendMessage() {
  const input = document.getElementById('input');
  const question = input.value.trim();
  if (!question || isStreaming) return;

  // 隐藏欢迎区
  hideWelcome();
  appendUserMessage(question);
  input.value = '';
  input.style.height = '36px';

  // 创建 AI 消息结构
  const aiMsg = createAiMessage();
  isStreaming = true;
  abortController = new AbortController();

  // 切换按钮为停止
  const sendBtn = document.getElementById('send-btn');
  sendBtn.innerHTML = '<i data-svg="stop" class="w-4 h-4"></i>';
  if (window.injectSvgIcons) window.injectSvgIcons();
  sendBtn.onclick = () => abortController && abortController.abort();

  try {
    const res = await fetch(`${API_BASE}/chat/stream`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ question, session_id: currentSessionId }),
      signal: abortController.signal,
    });

    const reader = res.body.getReader();
    const decoder = new TextDecoder();
    let buffer = '';
    let fullAnswer = '';
    let intentVal = '';
    let recommendations = [];
    let lastEvent = null;

    while (true) {
      const { done, value } = await reader.read();
      if (done) break;
      buffer += decoder.decode(value, { stream: true });
      const lines = buffer.split('\n');
      buffer = lines.pop();

      let i = 0;
      while (i < lines.length) {
        const line = lines[i];
        if (line.startsWith('event:')) {
          const eventType = line.slice(6).trim();
          const dataLine = lines[i + 1];
          if (dataLine && dataLine.startsWith('data:')) {
            const data = dataLine.slice(5).trim();
            try {
              const payload = JSON.parse(data);
              lastEvent = eventType;

              // 实时更新思考步骤
              if (eventType === 'intent') {
                intentVal = typeof payload === 'string' ? payload : (payload.intent || 'profile_qa');
                updateThinking(aiMsg.thinkingEl, {
                  icon: '🎯',
                  text: `意图分类: ${intentVal}`,
                  status: `已识别意图（${intentVal}）`
                });
              } else if (eventType === 'retrieve') {
                updateThinking(aiMsg.thinkingEl, {
                  icon: '🔍',
                  text: `检索: 找到 ${payload.count || 0} 个相关文档`,
                  status: `检索完成（${payload.count} 个文档）`
                });
              } else if (eventType === 'rerank') {
                updateThinking(aiMsg.thinkingEl, {
                  icon: '📊',
                  text: `重排: 保留 ${payload.kept || 0} 个最相关`,
                  status: `正在生成回答...`
                });
              } else if (eventType === 'token') {
                fullAnswer += payload.text || '';
                setAiContent(aiMsg.contentEl, fullAnswer, false);
                // 收到第一个 token 后立即隐藏思考区（不需要等）
                if (aiMsg.thinkingEl && aiMsg.thinkingEl.parentNode) {
                  updateStatusName(aiMsg.thinkingEl, '正在生成回答...');
                  hideThinking(aiMsg.thinkingEl);
                }
              } else if (eventType === 'done') {
                fullAnswer = payload.answer || fullAnswer;
                recommendations = payload.recommended_questions || [];
                setAiContent(aiMsg.contentEl, fullAnswer, true);
                if (window.hljs) window.hljs.highlightAll();
                // 强制从 DOM 移除思考区（兜底）
                if (aiMsg.thinkingEl && aiMsg.thinkingEl.parentNode) {
                  aiMsg.thinkingEl.parentNode.removeChild(aiMsg.thinkingEl);
                }
                // 显示意图徽章 + 延迟徽章
                renderAiFooter(aiMsg.footerEl, intentVal, payload.timing);
              } else if (eventType === 'error') {
                setAiContent(aiMsg.contentEl, '⚠️ ' + payload.message, true);
              }
            } catch (e) { /* ignore */ }
            i += 2;
          } else { i += 1; }
        } else { i += 1; }
      }
    }
    if (!fullAnswer && lastEvent !== 'done') {
      setAiContent(aiMsg.contentEl, '（未生成回答）', true);
    }
    // 推荐追问
    if (recommendations.length > 0) renderRecommendations(recommendations);
  } catch (err) {
    if (err.name === 'AbortError') {
      setAiContent(aiMsg.contentEl, '_已停止生成_', true);
    } else {
      setAiContent(aiMsg.contentEl, '⚠️ 出错了：' + err.message, true);
    }
  } finally {
    isStreaming = false;
    abortController = null;
    sendBtn.innerHTML = '<i data-svg="send" class="w-4 h-4"></i>';
    if (window.injectSvgIcons) window.injectSvgIcons();
    sendBtn.onclick = () => window.sendMessage && window.sendMessage();
    loadMetrics();
  }
}

// ===== 用户消息 =====
function appendUserMessage(content) {
  const messagesDiv = document.getElementById('messages');
  const wrapper = document.createElement('div');
  wrapper.className = 'msg-user fade-in';

  const bubble = document.createElement('div');
  bubble.className = 'bubble-user';
  bubble.textContent = content;
  wrapper.appendChild(bubble);

  messagesDiv.appendChild(wrapper);
  // 不滚动，保持用户当前阅读位置
  smartScrollToBottom(true);
}

function hideWelcome() {
  const welcome = document.getElementById('welcome');
  if (welcome) welcome.style.display = 'none';
  const suggestions = document.getElementById('initial-suggestions');
  if (suggestions) suggestions.style.display = 'none';
}

// ===== 创建 AI 消息结构（含思考、回答、徽章） =====
function createAiMessage() {
  const messagesDiv = document.getElementById('messages');

  const wrapper = document.createElement('div');
  wrapper.className = 'msg-ai fade-in';

  // 1. 头部（头像 + 状态）
  const header = document.createElement('div');
  header.className = 'msg-ai-header';
  header.innerHTML = `
    <div class="msg-avatar">AI</div>
    <div class="msg-ai-header-text">
      <div class="msg-ai-name">谭修诚 AI 数字分身</div>
      <div class="msg-ai-status">正在思考...</div>
    </div>
  `;
  wrapper.appendChild(header);

  // 2. 思考过程区
  const thinkingEl = document.createElement('div');
  thinkingEl.className = 'msg-thinking';
  thinkingEl.innerHTML = `
    <div class="msg-thinking-header">
      <span class="thinking-dot"></span>
      <span class="thinking-dot"></span>
      <span class="thinking-dot"></span>
      <span class="thinking-text">思考中...</span>
    </div>
    <div class="msg-thinking-steps"></div>
  `;
  wrapper.appendChild(thinkingEl);

  // 3. 回答内容区
  const contentEl = document.createElement('div');
  contentEl.className = 'msg-content';
  contentEl.innerHTML = '<span class="typing"><span></span><span></span><span></span></span>';
  wrapper.appendChild(contentEl);

  // 4. 底部徽章
  const footerEl = document.createElement('div');
  footerEl.className = 'msg-footer hidden';
  wrapper.appendChild(footerEl);

  messagesDiv.appendChild(wrapper);
  // 不滚动
  smartScrollToBottom(true);
  return { wrapper, thinkingEl, contentEl, footerEl };
}

function updateThinking(thinkingEl, step) {
  if (!thinkingEl || !step) return;
  const stepsContainer = thinkingEl.querySelector('.msg-thinking-steps');
  if (stepsContainer) {
    const stepEl = document.createElement('div');
    stepEl.className = 'msg-thinking-step';
    stepEl.innerHTML = `<span class="step-icon">${step.icon || '✓'}</span> <span>${escapeHtml(step.text)}</span>`;
    stepsContainer.appendChild(stepEl);
  }
  const text = thinkingEl.querySelector('.thinking-text');
  if (text && step.status) text.textContent = step.status;
}

function hideThinking(thinkingEl) {
  if (!thinkingEl) return;
  // 1. 立即加 .hiding class（CSS 动画让它 0.3s 内消失）
  thinkingEl.classList.add('hiding');
  // 2. 300ms 后彻底从 DOM 移除
  setTimeout(() => {
    if (thinkingEl.parentNode) {
      thinkingEl.parentNode.removeChild(thinkingEl);
    }
  }, 300);
}

function updateStatusName(thinkingEl, name) {
  if (!thinkingEl) return;
  const status = thinkingEl.querySelector('.msg-ai-status');
  if (status) status.textContent = name;
}

function setAiContent(contentEl, content, isFinal = false) {
  if (!contentEl) return;
  let displayContent = content;
  if (isFinal) {
    displayContent = content
      .replace(/<think>[\s\S]*?<\/think>/g, '')
      .replace(/<thinking>[\s\S]*?<\/thinking>/g, '')
      .replace(/<reflection>[\s\S]*?<\/reflection>/g, '')
      .replace(/<answer>([\s\S]*?)<\/answer>/g, '$1')
      .trim();
  }
  if (isFinal && window.marked) {
    let html = marked.parse(displayContent);
    // 把 [N] 转成带样式的上标引用（带悬浮提示）
    html = html.replace(/\[(\d+)\]/g, '<sup class="citation" title="参考来源 [$1]">[$1]</sup>');
    contentEl.innerHTML = html;
  } else {
    contentEl.innerHTML = escapeHtml(displayContent);
  }
  // 不滚动，保持用户当前阅读位置
  smartScrollToBottom(false);
}

function renderAiFooter(footerEl, intent, timing) {
  if (!footerEl) return;
  footerEl.classList.remove('hidden');
  const parts = [];

  if (intent) {
    const intentLabels = {
      profile_qa: '💼 个人信息',
      project_detail: '🚀 项目细节',
      skill_assessment: '🧠 技术原理',
      small_talk: '💬 闲聊',
      meta_question: '🤖 关于AI-Me',
    };
    const label = intentLabels[intent] || intent;
    parts.push(`<span class="intent-badge">${escapeHtml(label)}</span>`);
  }

  if (timing && timing.total_ms > 0) {
    const parts2 = [];
    if (timing.intent_ms > 0) parts2.push(`<span>⏱ ${Math.round(timing.intent_ms)}ms</span>`);
    if (timing.retrieve_ms > 0) parts2.push(`<span>🔍 ${Math.round(timing.retrieve_ms)}ms</span>`);
    if (timing.rerank_ms > 0) parts2.push(`<span>📊 ${Math.round(timing.rerank_ms)}ms</span>`);
    if (timing.generate_ms > 0) parts2.push(`<span>✨ ${Math.round(timing.generate_ms)}ms</span>`);
    if (timing.total_ms > 0) parts2.push(`<span>⏰ ${Math.round(timing.total_ms)}ms</span>`);
    if (parts2.length) {
      parts.push(`<span class="timing-group">${parts2.join('')}</span>`);
    }
  }

  footerEl.innerHTML = parts.join('');
}

function renderRecommendations(questions) {
  const area = document.getElementById('recommend-area');
  const list = document.getElementById('recommend-list');
  if (!questions || !questions.length) {
    area.classList.add('hidden');
    return;
  }
  area.classList.remove('hidden');
  list.innerHTML = questions.map(q =>
    `<button type="button" class="suggestion-card" onclick="window.quickAsk && window.quickAsk('${escapeHtml(q.question || q).replace(/'/g, "\\'")}')">
${escapeHtml(q.question || q)}
</button>`
  ).join('');
}

// 兼容旧函数名
function appendMessage(role, content) {
  if (role === 'user') {
    appendUserMessage(content);
  }
}

function renderAiText(el, content, isFinal = false) {
  setAiContent(el, content, isFinal);
}

function renderThinking(intentData) {
  // 不再单独使用
}

function renderTimingBadges(el, timing) {
  // 由 footer 负责
}

// ===== 导出 =====
async function exportChat() {
  try {
    const res = await fetch(`${API_BASE}/export`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ session_id: currentSessionId, format: 'markdown' }),
    });
    const data = await res.json();
    const blob = new Blob([data.content], { type: 'text/markdown' });
    const url = URL.createObjectURL(blob);
    const a = document.createElement('a');
    a.href = url;
    a.download = data.filename || 'ai-me-chat.md';
    a.click();
    URL.revokeObjectURL(url);
  } catch (err) {
    alert('导出失败：' + err.message);
  }
}

// ===== 工具 =====
function generateUUID() {
  return 'xxxxxxxx-xxxx-4xxx-yxxx-xxxxxxxxxxxx'.replace(/[xy]/g, c => {
    const r = Math.random() * 16 | 0;
    return (c === 'x' ? r : (r & 0x3 | 0x8)).toString(16);
  });
}

function escapeHtml(s) {
  if (typeof s !== 'string') return '';
  return s.replace(/[&<>"']/g, c => ({
    '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
  }[c]));
}

function setText(id, val) {
  const el = document.getElementById(id);
  if (el) el.textContent = val;
}