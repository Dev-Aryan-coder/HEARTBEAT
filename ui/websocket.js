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
      
      // 1. Skip system handshakes
      if (data.type === 'WELCOME' || data.type === 'PONG') {
        return;
      }

      // 2. Metabolic Pulse: Update vital signs telemetry silently without touching DOM cards
      if (data.type === 'METABOLIC_PULSE') {
        if (data.telemetry && typeof updateTelemetryUI === 'function') {
          updateTelemetryUI(data.telemetry);
        }
        return;
      }

      // 3. Cell Pruned: Remove specifically targetted card with smooth fade
      if (data.type === 'CELL_PRUNED' && data.cell_id) {
        const el = document.getElementById(`cell-card-${data.cell_id}`);
        if (el) {
          el.style.transition = 'opacity 0.3s ease, transform 0.3s ease';
          el.style.opacity = '0';
          el.style.transform = 'scale(0.95)';
          setTimeout(() => el.remove(), 300);
        }
        return;
      }

      // 4. Cell Purified: Silently sync memory cells in background without resetting UI
      if (data.type === 'CELL_PURIFIED' || data.cell_id) {
        if (typeof refreshCells === 'function') {
          refreshCells();
        }
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
  // Graceful no-op fallback
  if (typeof refreshCells === 'function') {
    refreshCells();
  }
}

function escHtml(str) {
  return String(str || '').replace(/&/g,'&amp;').replace(/</g,'&lt;').replace(/>/g,'&gt;').replace(/"/g,'&quot;');
}

// Connect once window is ready
document.addEventListener('DOMContentLoaded', () => {
  // Wait slightly for app.js to initialize window.userId
  setTimeout(connectWebSocket, 100);
});
