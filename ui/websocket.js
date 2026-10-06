// ── WEBSOCKET — HEARTBEAT NERVOUS SYSTEM ──────────────────────────────────────
const WS_BASE = 'ws://127.0.0.1:8000';
let socket = null;
let reconnectTimer = null;
let reconnectDelay = 1000;

function connectWebSocket() {
  const userId = window.userId || localStorage.getItem('hb_user_id');
  if (!userId) {
    console.warn('[WS] No userId found, delaying connection...');
    setTimeout(connectWebSocket, 1000);
    return;
  }
  
  const url = `${WS_BASE}/ws/connect/${userId}`;
  console.log('[WS] Connecting to Nervous System:', url);

  try {
    socket = new WebSocket(url);
  } catch (e) {
    console.warn('[WS] Could not create WebSocket:', e);
    scheduleReconnect();
    return;
  }

  socket.onopen = () => {
    console.log('[WS] Nervous System Active');
    reconnectDelay = 1000;
    updateConnectionStatus(true);
  };

  socket.onmessage = (event) => {
    if (event.data === 'ping') {
      try { socket.send('pong'); } catch (err) {}
      return;
    }
    if (event.data === 'pong') return;

    try {
      const data = JSON.parse(event.data);
      console.log('[WS] Live cell received:', data);
      // Resilience check for various data shapes
      if (data.cell_id || data.summary || data.type) {
        injectLiveCell(data);
      }
    } catch (e) {
      console.warn('[WS] Failed to parse message:', e);
    }
  };

  socket.onclose = (e) => {
    console.warn('[WS] Nervous System disconnected:', e.code);
    updateConnectionStatus(false);
    scheduleReconnect();
  };

  socket.onerror = (err) => {
    console.error('[WS] Error:', err);
    if (socket) socket.close();
  };
}

function scheduleReconnect() {
  if (reconnectTimer) clearTimeout(reconnectTimer);
  reconnectTimer = setTimeout(() => {
    console.log('[WS] Attempting reconnect...');
    connectWebSocket();
    reconnectDelay = Math.min(reconnectDelay * 2, 30000);
  }, reconnectDelay);
}

function updateConnectionStatus(online) {
  const dot  = document.getElementById('status-dot');
  const text = document.getElementById('status-text');
  if (!dot || !text) return;
  dot.className  = 'status-dot ' + (online ? 'online' : 'offline');
  text.textContent = online ? 'HEARTBEAT Active' : 'Reconnecting…';
}

function injectLiveCell(cell) {
  // Update cells panel in real time — prepend new live cell
  const listEl = document.getElementById('cells-list');
  if (!listEl) return;

  const empty = listEl.querySelector('.cells-empty');
  if (empty) empty.remove();

  const topic = (cell.topic_id || 'general').toLowerCase();
  const topicClass = ['coding','health','finance','ai'].includes(topic) ? 'topic-' + topic : 'topic-general';
  
  // Handle both raw cell objects and event broadcast objects
  const score = cell.importance_score || '—';
  const summarySource = cell.summary || cell.user_content || cell.ai_response_summary || 'Live pulse detected…';
  
  const card = document.createElement('div');
  card.className = 'cell-card';
  card.style.borderColor = '#ffd6db';
  card.innerHTML = `
    <div class="cell-card-top">
      <span class="cell-topic ${topicClass}">${escHtml(topic)}</span>
      <span class="cell-score">${score}/10</span>
    </div>
    <div class="cell-summary">${escHtml(summarySource)}</div>
  `;

  listEl.prepend(card);

  // Fade border back to normal after 2s
  setTimeout(() => { card.style.borderColor = ''; }, 2000);

  // Cap at 20 cells
  const cards = listEl.querySelectorAll('.cell-card');
  if (cards.length > 20) cards[cards.length - 1].remove();
}

function escHtml(str) {
  return String(str || '').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

// Connect once window is ready
document.addEventListener('DOMContentLoaded', () => {
  // Wait slightly for app.js to initialize window.userId
  setTimeout(connectWebSocket, 100);
});
