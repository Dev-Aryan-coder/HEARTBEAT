// BUG 5 FIX: Always use absolute URL — empty string breaks file:// protocol
const API_BASE = 'http://127.0.0.1:8000';

// ── STATE ────────────────────────────────────────────────────────────────────
// window.userId is locked to MASTER_USER
window.userId = 'MASTER_USER';
localStorage.setItem('hb_user_id', 'MASTER_USER');
console.log("[HEARTBEAT ULTIMATE] Identity Locked:", window.userId);

let currentChatId = null;
let isLoading = false;
let pendingClarificationCellId = null;
let allChats = [];
let pendingImageBase64 = null;
let pendingImageName = null;

// ── DOM REFS ─────────────────────────────────────────────────────────────────
const messagesEl = document.getElementById('messages');
const chatListEl = document.getElementById('chat-list');
const cellsListEl = document.getElementById('cells-list');
const userInputEl = document.getElementById('user-input');
const sendBtnEl = document.getElementById('send-btn');
const newChatBtnEl = document.getElementById('new-chat-btn');
const charCountEl = document.getElementById('char-count');
const welcomeEl = document.getElementById('welcome');
const topbarTitle = document.getElementById('topbar-title');
const clarifyBanner = document.getElementById('clarify-banner');
const clarifyText = document.getElementById('clarify-text');
const clarifyDismiss = document.getElementById('clarify-dismiss');
const userAvatar = document.getElementById('user-avatar');
const sidebarToggle = document.getElementById('sidebar-toggle');
const sidebar = document.getElementById('sidebar');
const attachBtn = document.getElementById('attach-btn');
const imageInput = document.getElementById('image-input');
const previewContainer = document.getElementById('image-preview-container');
const previewImg = document.getElementById('image-preview-img');
const previewRemove = document.getElementById('image-preview-remove');

// ── INIT ─────────────────────────────────────────────────────────────────────
document.addEventListener('DOMContentLoaded', async () => {
  if (userAvatar) userAvatar.textContent = 'A';
  const userDisp = document.getElementById('user-display');
  if (userDisp) userDisp.textContent = 'Aryan';

  await loadChatsFromServer();

  const lastChat = localStorage.getItem('hb_current_chat');
  if (lastChat && allChats.find(c => c.chat_id === lastChat)) {
    loadChat(lastChat);
  } else if (allChats.length > 0) {
    loadChat(allChats[0].chat_id);
  } else {
    startNewChat();
  }

  setInterval(refreshCells, 8000);
  refreshCells();
  autoResizeTextarea();
});

// ── CHAT SYNC (FIX 17) ────────────────────────────────────────────────────────
async function loadChatsFromServer() {
  try {
    const res = await fetch(`${API_BASE}/api/chats/${window.userId}`);
    if (res.ok) {
      const data = await res.json();
      console.log("[HEARTBEAT] Loaded chats:", data.chats?.length || 0);
      allChats = data.chats || [];
      renderChatList();
    }
  } catch (e) {
    console.warn('Failed to sync chats:', e);
  }
}

// ── NEW CHAT (FIX 18) ─────────────────────────────────────────────────────────
async function startNewChat() {
  currentChatId = 'C-' + Date.now();
  localStorage.setItem('hb_current_chat', currentChatId);

  if (messagesEl) {
    Array.from(messagesEl.children).forEach(child => {
      if (child.id !== 'welcome') child.remove();
    });
  }

  showWelcome();
  if (topbarTitle) topbarTitle.textContent = 'New conversation';
  setActiveChatInSidebar(null);
  hideClarify();
}
window.startNewChat = startNewChat;
if (newChatBtnEl) newChatBtnEl.addEventListener('click', startNewChat);

// ── CHAT LIST ─────────────────────────────────────────────────────────────────
function renderChatList() {
  if (!chatListEl) return;
  chatListEl.innerHTML = '';

  if (allChats.length === 0) {
    chatListEl.innerHTML = '<div class="chat-list-empty">No conversations yet</div>';
    return;
  }

  allChats.forEach(chat => {
    const item = document.createElement('div');
    item.className = 'chat-item' + (chat.chat_id === currentChatId ? ' active' : '');
    item.dataset.chatId = chat.chat_id;
    item.innerHTML = `
      <div class="chat-item-content" onclick="loadChat('${chat.chat_id}')">
        <div class="chat-item-title">${escHtml(chat.title)}</div>
        <div class="chat-item-time">${formatTime(chat.created_at)}</div>
      </div>
      <button class="chat-item-delete" onclick="deleteChat('${chat.chat_id}', event)" title="Delete">
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5"><line x1="18" y1="6" x2="6" y2="18"/><line x1="6" y1="6" x2="18" y2="18"/></svg>
      </button>
    `;
    chatListEl.appendChild(item);
  });
}

function setActiveChatInSidebar(chatId) {
  document.querySelectorAll('.chat-item').forEach(el => {
    el.classList.toggle('active', el.dataset.chatId === chatId);
  });
}

// ── DELETE CHAT (FIX 20) ──────────────────────────────────────────────────────
async function deleteChat(chatId, e) {
  if (e) e.stopPropagation();
  if (!confirm("Are you sure you want to delete this chat permanently?")) return;

  try {
    await fetch(`${API_BASE}/api/chats/${chatId}`, { method: 'DELETE' });
    allChats = allChats.filter(c => c.chat_id !== chatId);
    if (currentChatId === chatId) {
      startNewChat();
    } else {
      renderChatList();
    }
  } catch (e) {
    console.error("Delete failed:", e);
  }
}
window.deleteChat = deleteChat;

// ── INPUT HELPERS ─────────────────────────────────────────────────────────────
function setInput(text) {
  if (userInputEl) {
    userInputEl.value = text;
    userInputEl.focus();
    updateCharCount();
    autoResizeTextarea();
  }
}
window.setInput = setInput;

// ── LOAD CHAT ─────────────────────────────────────────────────────────────────
async function loadChat(chatId) {
  currentChatId = chatId;
  localStorage.setItem('hb_current_chat', chatId);

  const chat = allChats.find(c => c.chat_id === chatId);
  if (topbarTitle) topbarTitle.textContent = chat ? chat.title : 'Conversation';
  setActiveChatInSidebar(chatId);
  hideWelcome();

  if (messagesEl) {
    Array.from(messagesEl.children).forEach(child => {
      if (child.id !== 'welcome') child.remove();
    });
  }

  hideClarify();

  try {
    const res = await fetch(`${API_BASE}/api/history/${chatId}`);
    const data = await res.json();
    const msgs = data.messages || [];

    if (msgs.length === 0) {
      showWelcome();
    } else {
      msgs.forEach(m => appendMessage(m.role === 'user' ? 'user' : 'ai', m.content, null, m.image_url));
    }
  } catch (e) {
    showWelcome();
  }
  refreshCells();
}
window.loadChat = loadChat;

// ── SEND MESSAGE ──────────────────────────────────────────────────────────────
async function sendMessage(e) {
  if (e) e.preventDefault();
  const content = userInputEl.value.trim();
  const hasImage = pendingImageBase64 !== null;

  if ((!content && !hasImage) || isLoading) return;

  // FIX 21: Handle clarification response
  if (pendingClarificationCellId) {
    await sendClarification(content);
    return;
  }

  const isNewChat = !allChats.find(c => c.chat_id === currentChatId);

  hideWelcome();
  hideClarify();

  // Capture image before clearing
  const imageBase64 = pendingImageBase64;
  const imageName = pendingImageName;

  // Append user message with optional image
  appendMessage('user', content, null, imageBase64);

  userInputEl.value = '';
  clearPendingImage();
  updateCharCount();
  autoResizeTextarea();
  setSendLoading(true);

  const thinkingEl = appendThinking();

  try {
    const payload = {
      user_id: window.userId,
      chat_id: currentChatId,
      session_id: 'browser_' + window.userId,
      content: content || `[Image: ${imageName}]`
    };
    if (imageBase64) {
      payload.image_base64 = imageBase64;
      payload.image_name = imageName;
    }

    const res = await fetch(`${API_BASE}/api/message`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify(payload)
    });

    const data = await res.json();
    if (thinkingEl) thinkingEl.remove();

    // FIX 21: Clarification detection
    if (data.status === 'pending_clarification' || data.type === 'clarification') {
      pendingClarificationCellId = data.cell_id;
      const question = data.question || "I'm a bit unsure. Can you clarify that for me?";
      showClarify(question);
      appendMessage('ai', question);
    } else if (data.ai_response) {
      appendMessage('ai', data.ai_response, data.cell_id);

      // FIX 19: Update chat title on first message
      if (isNewChat) {
        const newTitle = content.length > 35
          ? content.slice(0, 35) + '...'
          : (imageName ? `[Image] ${imageName}` : 'New conversation');
        await fetch(`${API_BASE}/api/chats/${currentChatId}/title`, {
          method: 'PATCH',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ title: newTitle })
        });
        await loadChatsFromServer();
      }
    } else if (data.error || data.detail) {
      appendMessage('ai', 'Error: ' + (data.error || data.detail));
    }

    refreshCells();
  } catch (err) {
    if (thinkingEl) thinkingEl.remove();
    appendMessage('ai', '⚠️ Connection failed. Please check if backend is running.');
  }

  setSendLoading(false);
}

async function sendClarification(answer) {
  appendMessage('user', answer);
  userInputEl.value = '';
  setSendLoading(true);
  hideClarify();
  const thinkingEl = appendThinking();

  try {
    const res = await fetch(`${API_BASE}/api/clarify`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        cell_id: pendingClarificationCellId,
        user_answer: answer
      })
    });
    const data = await res.json();
    if (thinkingEl) thinkingEl.remove();
    appendMessage('ai', data.message || 'Thank you, I have updated my memory.');
    pendingClarificationCellId = null;
    refreshCells();
  } catch (err) {
    if (thinkingEl) thinkingEl.remove();
    appendMessage('ai', 'Failed to resolve memory ambiguity.');
  }
  setSendLoading(false);
}

// ── UI HELPERS ────────────────────────────────────────────────────────────────
function renderBubbleContent(content, isAi) {
  if (!content) return '';
  if (!isAi) {
    return escHtml(content);
  }
  if (typeof marked !== 'undefined') {
    try {
      const parser = typeof marked.parse === 'function' ? marked.parse : (typeof marked === 'function' ? marked : null);
      if (parser) {
        return parser(content, { breaks: true, gfm: true });
      }
    } catch (err) {
      console.warn('[marked] Failed to parse markdown:', err);
    }
  }
  return escHtml(content);
}

// ── CLIPBOARD COPY HELPERS ────────────────────────────────────────────────────
async function copyTextToClipboard(text, btnEl, successMsg = 'Copied to clipboard!') {
  if (!text) return;
  const originalHtml = btnEl ? btnEl.innerHTML : '';

  const showSuccess = () => {
    if (btnEl) {
      btnEl.classList.add('copied');
      btnEl.innerHTML = `
        <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2.5" stroke-linecap="round" stroke-linejoin="round">
          <polyline points="20 6 9 17 4 12"></polyline>
        </svg>
        <span>Copied!</span>`;
      setTimeout(() => {
        btnEl.classList.remove('copied');
        btnEl.innerHTML = originalHtml;
      }, 2000);
    }
    showPasteToast(`📋 ${successMsg}`);
  };

  try {
    if (navigator.clipboard && window.isSecureContext) {
      await navigator.clipboard.writeText(text);
      showSuccess();
      return;
    }
  } catch (err) {
    console.warn('[Clipboard] navigator.clipboard write failed, attempting fallback:', err);
  }

  try {
    const ta = document.createElement('textarea');
    ta.value = text;
    ta.style.position = 'fixed';
    ta.style.left = '-9999px';
    ta.style.top = '-9999px';
    document.body.appendChild(ta);
    ta.focus();
    ta.select();
    document.execCommand('copy');
    document.body.removeChild(ta);
    showSuccess();
  } catch (fallbackErr) {
    console.error('[Clipboard] Fallback copy failed:', fallbackErr);
    showPasteToast('⚠️ Could not copy text');
  }
}
window.copyTextToClipboard = copyTextToClipboard;

function copyMessageText(btnEl) {
  const row = btnEl.closest('.msg-row');
  if (!row) return;
  const rawContent = row.dataset.rawContent || '';
  const isAi = !row.classList.contains('user-row-msg');
  copyTextToClipboard(rawContent, btnEl, isAi ? 'AI response copied!' : 'Prompt copied!');
}
window.copyMessageText = copyMessageText;

function attachCodeCopyButtons(container) {
  if (!container) return;
  const pres = container.querySelectorAll('pre');
  pres.forEach(pre => {
    if (pre.querySelector('.pre-copy-btn')) return;
    const btn = document.createElement('button');
    btn.type = 'button';
    btn.className = 'pre-copy-btn';
    btn.title = 'Copy code snippet';
    btn.innerHTML = `
      <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
        <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
        <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
      </svg>
      <span>Copy Code</span>`;
    btn.onclick = (e) => {
      e.stopPropagation();
      const codeEl = pre.querySelector('code');
      const textToCopy = codeEl ? codeEl.innerText : pre.innerText;
      copyTextToClipboard(textToCopy, btn, 'Code snippet copied!');
    };
    pre.appendChild(btn);
  });
}
window.attachCodeCopyButtons = attachCodeCopyButtons;

function appendMessage(role, content, cellId = null, imageSrc = null) {
  if (!messagesEl) return;
  const isAi = role === 'ai';
  const row = document.createElement('div');
  row.className = `msg-row ${isAi ? '' : 'user-row-msg'}`;
  if (cellId) row.dataset.cell = cellId;
  row.dataset.rawContent = content || '';

  let imageHtml = '';
  if (imageSrc) {
    const fullSrc = (imageSrc.startsWith('http') || imageSrc.startsWith('data:'))
      ? imageSrc
      : `${API_BASE}${imageSrc}`;
    imageHtml = `
      <div class="msg-image-wrap">
        <img class="msg-image" src="${fullSrc}" alt="Screenshot / Image" onclick="openImageModal('${fullSrc}')" />
        <span class="msg-image-badge">Vision Active</span>
      </div>`;
  }

  const bubbleBody = renderBubbleContent(content, isAi);
  const copyBtnTitle = isAi ? 'Copy AI response' : 'Copy prompt';

  row.innerHTML = `
    <div class="msg-avatar ${isAi ? 'ai-av' : 'user-av'}">${isAi ? 'HB' : window.userId[0].toUpperCase()}</div>
    <div class="msg-body">
      <div class="msg-header">
        <div class="msg-name">${isAi ? 'HEARTBEAT' : 'You'}</div>
        ${content ? `
        <button type="button" class="msg-copy-btn" onclick="copyMessageText(this)" title="${copyBtnTitle}">
          <svg width="12" height="12" viewBox="0 0 24 24" fill="none" stroke="currentColor" stroke-width="2" stroke-linecap="round" stroke-linejoin="round">
            <rect x="9" y="9" width="13" height="13" rx="2" ry="2"></rect>
            <path d="M5 15H4a2 2 0 0 1-2-2V4a2 2 0 0 1 2-2h9a2 2 0 0 1 2 2v1"></path>
          </svg>
          <span>Copy</span>
        </button>` : ''}
      </div>
      ${imageHtml}
      ${content ? `<div class="msg-bubble ${isAi ? 'ai-bubble' : 'user-bubble'}">${bubbleBody}</div>` : ''}
      ${isAi && cellId ? `
      <div class="depth-row">
        <button class="depth-btn" onclick="requestDepth('${cellId}', 1, this)">Summary</button>
        <button class="depth-btn" onclick="requestDepth('${cellId}', 2, this)">Detail</button>
        <button class="depth-btn" onclick="requestDepth('${cellId}', 3, this)">Original</button>
      </div>` : ''}
    </div>
  `;
  messagesEl.appendChild(row);
  if (isAi) {
    attachCodeCopyButtons(row);
  }
  scrollToBottom();
  return row;
}

async function requestDepth(cellId, level, btnEl) {
  const thinkingEl = appendThinking();
  try {
    const res = await fetch(`${API_BASE}/api/answer`, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ user_id: window.userId, cell_id: cellId, depth_level: level })
    });
    const data = await res.json();
    if (thinkingEl) thinkingEl.remove();
    appendMessage('ai', data.response || 'Depth data unavailable.');
  } catch (e) {
    if (thinkingEl) thinkingEl.remove();
  }
}
window.requestDepth = requestDepth;

function appendThinking() {
  const row = document.createElement('div');
  row.className = 'msg-row thinking';
  row.innerHTML = `
    <div class="msg-avatar ai-av">HB</div>
    <div class="msg-body"><div class="msg-name">HEARTBEAT</div><div class="msg-bubble ai-bubble">...</div></div>
  `;
  messagesEl.appendChild(row);
  scrollToBottom();
  return row;
}

function showWelcome() { if (welcomeEl) welcomeEl.style.display = 'flex'; }
function hideWelcome() { if (welcomeEl) welcomeEl.style.display = 'none'; }
function showClarify(q) { if (clarifyText) clarifyText.textContent = q; clarifyBanner.classList.remove('hidden'); }
function hideClarify() { clarifyBanner.classList.add('hidden'); }
function scrollToBottom() { if (messagesEl) messagesEl.scrollTop = messagesEl.scrollHeight; }
function setSendLoading(l) { isLoading = l; updateSendBtn(); sendBtnEl.classList.toggle('loading', l); }
function updateSendBtn() {
  if (!sendBtnEl) return;
  const hasContent = userInputEl && userInputEl.value.trim().length > 0;
  const hasImage = pendingImageBase64 !== null;
  sendBtnEl.disabled = (!hasContent && !hasImage) || isLoading;
}
function updateCharCount() { charCountEl.textContent = `${userInputEl.value.length} / 4000`; }

// Auto-expand textarea dynamically up to 3cm max-height
function autoResizeTextarea() {
  if (!userInputEl) return;
  userInputEl.style.height = 'auto';
  // 3cm = ~113.4px
  const maxHeight = 3 * 37.795;
  const scrollH = userInputEl.scrollHeight;
  if (scrollH > maxHeight) {
    userInputEl.style.height = `${maxHeight}px`;
    userInputEl.style.overflowY = 'auto';
  } else {
    userInputEl.style.height = `${Math.max(24, scrollH)}px`;
    userInputEl.style.overflowY = 'hidden';
  }
}
window.autoResizeTextarea = autoResizeTextarea;

function escHtml(s) { return String(s || '').replace(/&/g, '&amp;').replace(/</g, '&lt;').replace(/>/g, '&gt;'); }
function formatTime(ts) {
  if (!ts) return '';
  const date = new Date(ts);
  return date.toLocaleTimeString([], { hour: '2-digit', minute: '2-digit' });
}

// ── CELLS REFRESH & LIVING METABOLISM ─────────────────────────────────────────
let currentTierFilter = 'all';
let cachedCells = [];

async function refreshCells() {
  try {
    const [cellsRes, telemetryRes] = await Promise.all([
      fetch(`${API_BASE}/api/cells/${window.userId}`),
      fetch(`${API_BASE}/api/metabolism/telemetry/${window.userId}`).catch(() => null)
    ]);
    
    if (cellsRes.ok) {
      const data = await cellsRes.json();
      cachedCells = data.cells || [];
      renderCells(cachedCells);
    }
    
    if (telemetryRes && telemetryRes.ok) {
      const tData = await telemetryRes.json();
      updateTelemetryUI(tData);
    }
  } catch (e) {
    console.debug('Cell refresh skipped:', e);
  }
}

function updateTelemetryUI(tData) {
  const bpmEl = document.getElementById('telemetry-bpm');
  const flowEl = document.getElementById('telemetry-flow');
  if (bpmEl && tData.heart_rate_bpm) bpmEl.textContent = tData.heart_rate_bpm;
  if (flowEl && tData.circulating_active != null) flowEl.textContent = tData.circulating_active;
}

function renderCells(cells) {
  if (!cellsListEl) return;
  
  let filtered = cells;
  if (currentTierFilter === 'core_genome') {
    filtered = cells.filter(c => c.memory_tier === 'core_genome');
  } else if (currentTierFilter === 'active') {
    filtered = cells.filter(c => c.status === 'active' && c.memory_tier !== 'core_genome');
  } else if (currentTierFilter === 'dormant') {
    filtered = cells.filter(c => c.status === 'dormant');
  } else {
    // 'all' shows non-expired cells
    filtered = cells.filter(c => c.status !== 'expired');
  }

  if (filtered.length === 0) {
    cellsListEl.innerHTML = `<div class="cells-empty"><p>No cells in ${currentTierFilter} tier</p></div>`;
    return;
  }

  cellsListEl.innerHTML = filtered.map(c => {
    const tier = c.memory_tier || (c.importance_score >= 8 ? 'core_genome' : 'episodic');
    const tierLabel = tier === 'core_genome' ? '🧬 Core' : (tier === 'bloodstream' ? '🩸 Flow' : '⚡ Context');
    return `
      <div class="cell-card" id="cell-card-${c.cell_id}">
          <div class="cell-card-top">
              <span class="cell-topic topic-${c.topic_id || 'general'}">${c.topic_id || 'general'}</span>
              <span class="cell-tier-badge tier-${tier}">${tierLabel}</span>
              <span class="cell-score">${c.importance_score != null ? c.importance_score + '/10' : '—'}</span>
          </div>
          <div class="cell-summary">${escHtml(c.summary || c.user_content || 'Cell memory')}</div>
          <div class="cell-card-footer">
              <span class="cell-status-tag" style="font-size:10px;color:var(--muted-foreground)">${c.status}</span>
              <button type="button" class="cell-prune-btn" onclick="pruneCell('${c.cell_id}')" title="Dissolve cell from memory">
                  🗑️ Dissolve
              </button>
          </div>
      </div>
    `;
  }).join('');
}

window.pruneCell = async function(cellId) {
  if (!confirm('Dissolve this memory cell permanently from HEARTBEAT subconscious?')) return;
  try {
    const res = await fetch(`${API_BASE}/api/cells/${cellId}`, { method: 'DELETE' });
    if (res.ok) {
      const el = document.getElementById(`cell-card-${cellId}`);
      if (el) el.remove();
      refreshCells();
    }
  } catch (err) {
    console.error('Failed to prune cell:', err);
  }
};

window.triggerMetabolicPulse = async function() {
  const btn = document.getElementById('pulse-trigger-btn');
  if (btn) {
    btn.textContent = '⏳ Pulsing...';
    btn.disabled = true;
  }
  try {
    const res = await fetch(`${API_BASE}/api/metabolism/pulse`, { method: 'POST' });
    if (res.ok) {
      const data = await res.json();
      if (data.telemetry) updateTelemetryUI(data.telemetry);
      refreshCells();
    }
  } catch (err) {
    console.error('Pulse failed:', err);
  } finally {
    if (btn) {
      btn.textContent = '⚡ Pulse';
      btn.disabled = false;
    }
  }
};

// ── EVENTS ────────────────────────────────────────────────────────────────────
const layoutEl = document.getElementById('layout') || document.querySelector('.layout');
const cellsPanel = document.getElementById('cells-panel');
const cellsToggleBtn = document.getElementById('cells-toggle-btn');
const cellsCloseBtn = document.getElementById('cells-close-btn');

function toggleSidebar() {
  if (layoutEl) layoutEl.classList.toggle('sidebar-collapsed');
  if (sidebar) sidebar.classList.toggle('collapsed');
}
window.toggleSidebar = toggleSidebar;

if (sidebarToggle) {
  sidebarToggle.onclick = toggleSidebar;
}

function toggleCellsPanel() {
  if (layoutEl) layoutEl.classList.toggle('cells-collapsed');
  if (cellsPanel) cellsPanel.classList.toggle('collapsed');
}
window.toggleCellsPanel = toggleCellsPanel;

if (cellsToggleBtn) {
  cellsToggleBtn.onclick = toggleCellsPanel;
}
if (cellsCloseBtn) {
  cellsCloseBtn.onclick = toggleCellsPanel;
}

const pulseTriggerBtn = document.getElementById('pulse-trigger-btn');
if (pulseTriggerBtn) {
  pulseTriggerBtn.onclick = window.triggerMetabolicPulse;
}

const tierTabs = document.querySelectorAll('.tier-tab-btn');
tierTabs.forEach(tab => {
  tab.onclick = () => {
    tierTabs.forEach(t => t.classList.remove('active'));
    tab.classList.add('active');
    currentTierFilter = tab.dataset.tier || 'all';
    renderCells(cachedCells);
  };
});

if (userInputEl) {
  userInputEl.oninput = () => {
    updateCharCount();
    autoResizeTextarea();
  };
  userInputEl.onkeydown = e => { if (e.key === 'Enter' && !e.shiftKey) { e.preventDefault(); sendMessage(); } };
}
if (sendBtnEl) sendBtnEl.onclick = sendMessage;
if (clarifyDismiss) clarifyDismiss.onclick = hideClarify;

// ── IMAGE & SCREENSHOT HANDLING (NVIDIA VISION) ──────────────────────────────
const previewLabel = document.getElementById('image-preview-label');
const pasteToast = document.getElementById('paste-toast');
let pasteToastTimer = null;

function showPasteToast(text = '📸 Screenshot attached from clipboard') {
  if (!pasteToast) return;
  pasteToast.textContent = text;
  pasteToast.classList.add('show');
  if (pasteToastTimer) clearTimeout(pasteToastTimer);
  pasteToastTimer = setTimeout(() => {
    pasteToast.classList.remove('show');
  }, 2500);
}

function handleImageFile(file, isPasted = false) {
  if (!file) return;

  const validTypes = ['image/png', 'image/jpeg', 'image/jpg', 'image/gif', 'image/webp', 'image/bmp'];
  if (!validTypes.includes(file.type.toLowerCase())) {
    alert('Please attach a valid image format (PNG, JPEG, WebP, GIF).');
    return;
  }

  if (file.size > 15 * 1024 * 1024) {
    alert('Image file is too large (max 15MB).');
    return;
  }

  const reader = new FileReader();
  reader.onload = (ev) => {
    pendingImageBase64 = ev.target.result;
    if (isPasted) {
      const now = new Date();
      const timeStr = now.toTimeString().split(' ')[0].replace(/:/g, '');
      pendingImageName = `Screenshot_${timeStr}.png`;
      if (previewLabel) previewLabel.textContent = '📸 Screenshot attached • NVIDIA Vision ready';
      showPasteToast('📸 Screenshot attached from clipboard');
    } else {
      pendingImageName = file.name || 'image.png';
      if (previewLabel) previewLabel.textContent = `🖼️ ${pendingImageName} • NVIDIA Vision ready`;
    }

    if (previewImg) previewImg.src = pendingImageBase64;
    if (previewContainer) previewContainer.classList.remove('hidden');
    if (attachBtn) attachBtn.classList.add('active');
    updateSendBtn();
    if (userInputEl) userInputEl.focus();
  };
  reader.readAsDataURL(file);
}

if (attachBtn) {
  attachBtn.addEventListener('click', () => {
    if (imageInput) imageInput.click();
  });
}

if (imageInput) {
  imageInput.addEventListener('change', (e) => {
    const file = e.target.files[0];
    if (file) handleImageFile(file, false);
    imageInput.value = '';
  });
}

if (previewRemove) {
  previewRemove.addEventListener('click', clearPendingImage);
}

function clearPendingImage() {
  pendingImageBase64 = null;
  pendingImageName = null;
  if (previewContainer) previewContainer.classList.add('hidden');
  if (previewImg) previewImg.src = '';
  if (attachBtn) attachBtn.classList.remove('active');
  updateSendBtn();
}

// 📋 Clipboard Paste Screenshot Handler (Ctrl+V)
document.addEventListener('paste', (e) => {
  const items = e.clipboardData?.items;
  if (!items) return;

  for (const item of items) {
    if (item.type.startsWith('image/')) {
      e.preventDefault();
      const file = item.getAsFile();
      if (file) {
        handleImageFile(file, true);
        break;
      }
    }
  }
});

// 📂 Drag and Drop image files onto input box
const inputBoxEl = document.getElementById('input-box');
if (inputBoxEl) {
  ['dragenter', 'dragover'].forEach(eventName => {
    inputBoxEl.addEventListener(eventName, (e) => {
      e.preventDefault();
      e.stopPropagation();
      inputBoxEl.classList.add('drag-over');
    });
  });

  ['dragleave', 'dragend'].forEach(eventName => {
    inputBoxEl.addEventListener(eventName, (e) => {
      e.preventDefault();
      e.stopPropagation();
      inputBoxEl.classList.remove('drag-over');
    });
  });

  inputBoxEl.addEventListener('drop', (e) => {
    e.preventDefault();
    e.stopPropagation();
    inputBoxEl.classList.remove('drag-over');
    const files = e.dataTransfer?.files;
    if (files && files.length > 0) {
      const file = files[0];
      if (file.type.startsWith('image/')) {
        handleImageFile(file, false);
      }
    }
  });
}

// 🔍 Lightbox Image Modal
function openImageModal(src) {
  let modal = document.getElementById('image-modal');
  if (!modal) {
    modal = document.createElement('div');
    modal.id = 'image-modal';
    modal.className = 'image-modal';
    modal.onclick = (e) => {
      if (e.target.tagName !== 'BUTTON') modal.classList.add('hidden');
    };
    document.body.appendChild(modal);
  }
  modal.innerHTML = `
    <div style="position:relative; max-width:90vw; max-height:90vh;">
      <img src="${src}" alt="Full size screenshot" style="max-width:90vw; max-height:85vh; border-radius:10px; display:block;" />
      <button type="button" style="position:absolute; top:10px; right:10px; background:rgba(0,0,0,0.7); color:#fff; border:none; border-radius:50%; width:32px; height:32px; cursor:pointer; font-size:16px;" onclick="document.getElementById('image-modal').classList.add('hidden')">✕</button>
    </div>
  `;
  modal.classList.remove('hidden');
}
