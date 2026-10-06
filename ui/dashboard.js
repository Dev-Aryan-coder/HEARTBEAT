/**
 * HEARTBEAT DEVELOPER DASHBOARD ENGINE
 * Dual-Frontend Architecture - Real-time Monitoring
 */

// Global Configuration
const API_BASE = 'http://127.0.0.1:8000';
const WS_BASE  = 'ws://127.0.0.1:8000';
// ISSUE 4 FIX: Use same localStorage key as index.html so both frontends share the same userId
let userId = localStorage.getItem('hb_user_id');
if (!userId || userId.toUpperCase() === 'MASTER_USER') {
    userId = 'MASTER_USER';
    localStorage.setItem('hb_user_id', userId);
}

// Chart.js Global Defaults
Chart.defaults.color = '#888888';
Chart.defaults.borderColor = '#1e1e1e';
Chart.defaults.font.family = "'DM Sans', sans-serif";

// State Management
let currentPage = localStorage.getItem('hb_dash_page') || 'health';
let appIntervals = [];
let wsFeed = null;
let wsActivity = null;
let isFeedPaused = false;
let pendingFeedEvents = 0;
const MAX_FEED_EVENTS = 50;

// Reusable Components Functions
const skeleton = (w, h) => `<div class="skeleton" style="width: ${w}; height: ${h}; border-radius: 6px;"></div>`;

const metricCard = (title, val, sub, color) => `
<div class="card metric-card" style="border-left: 3px solid ${color}">
    <span class="metric-title">${title}</span>
    <span class="metric-value monospace">${val}</span>
    <span class="metric-subtitle">${sub}</span>
</div>`;

const statusBadge = (s) => {
    const colors = {
        active: 'green', dormant: 'blue', expired: 'red',
        pending_clarification: 'amber', raw: 'text-3', purified: 'accent'
    };
    const c = colors[s] || 'text-3';
    return `<span class="badge bg-${c}-s text-${c} border-${c}"><span class="dot bg-${c}"></span> ${s.replace('_',' ')}</span>`;
};

const importanceBar = (score) => {
    let html = '<div class="importance-bar" style="display:flex; gap:2px; align-items:center;">';
    for(let i=1; i<=10; i++) {
        let bg = '#1a1a1a';
        if (i <= score) {
            if (score <= 3) bg = 'var(--red)';
            else if (score <= 6) bg = 'var(--amber)';
            else bg = 'var(--green)';
        }
        html += `<div style="width:8px; height:12px; border-radius:1px; background:${bg}"></div>`;
    }
    html += `<span style="font-size:11px; margin-left:8px; color:#888;">${score}/10</span></div>`;
    return html;
};

const jsonBlock = (data) => {
    const str = JSON.stringify(data, null, 2);
    // Rough colorization
    return `<pre class="json-block monospace">${str.replace(/"(\w+)"\s*:/g, '<span class="jk-key">"$1"</span>:')
        .replace(/: "(.*)"/g, ': <span class="jk-str">"$1"</span>')
        .replace(/: (\d+)/g, ': <span class="jk-num">$1</span>')
        .replace(/: (true|false|null)/g, ': <span class="jk-bool">$1</span>')}</pre>`;
};

const formatTime = (iso) => {
    if (!iso) return '—';
    const d = new Date(iso);
    const now = new Date();
    const diff = Math.floor((now - d) / 1000);
    if (diff < 60) return `${diff}s ago`;
    if (diff < 3600) return `${Math.floor(diff/60)}m ago`;
    if (diff < 86400) return `${Math.floor(diff/3600)}h ago`;
    return d.toLocaleDateString();
};

const formatDate = (iso) => iso ? new Date(iso).toLocaleString([], {month:'short', day:'numeric', hour:'2-digit', minute:'2-digit'}) : '—';

// Core Navigation Logic
function initNavigation() {
    const navItems = document.querySelectorAll('.nav-item');
    navItems.forEach(item => {
        item.addEventListener('click', () => {
            const page = item.getAttribute('data-page');
            switchPage(page);
        });
    });

    // Auto-select initial page
    switchPage(currentPage);
}

function switchPage(pageId) {
    currentPage = pageId;
    localStorage.setItem('hb_dash_page', pageId);
    
    // UI update
    document.querySelectorAll('.page-container').forEach(p => p.classList.remove('active'));
    document.querySelectorAll('.nav-item').forEach(n => n.classList.remove('active'));
    
    const target = document.getElementById(`page-${pageId}`);
    const nav = document.querySelector(`.nav-item[data-page="${pageId}"]`);
    if (target) target.classList.add('active');
    if (nav) nav.classList.add('active');

    // Clear old intervals
    appIntervals.forEach(clearInterval);
    appIntervals = [];

    // Trigger page load function
    const loaderName = `load${pageId.charAt(0).toUpperCase() + pageId.slice(1)}`;
    if (typeof window[loaderName] === 'function') window[loaderName]();
    else if (typeof window[`init${pageId.charAt(0).toUpperCase() + pageId.slice(1)}`] === 'function') window[`init${pageId.charAt(0).toUpperCase() + pageId.slice(1)}`]();
}

// 🏥 PAGE 1 - SYSTEM HEALTH
window.loadHealth = async () => {
    updateHealthUI();
    appIntervals.push(setInterval(updateHealthUI, 10000));
};

async function updateHealthUI() {
    const statsContainer = document.querySelector('#page-health .metrics-grid');
    statsContainer.innerHTML = Array(6).fill(skeleton('100%', '110px')).join('');

    try {
        const statsRes = await fetch(`${API_BASE}/api/stats/${userId}`);
        const stats = await statsRes.json();
        const pingRes = await fetch(`${API_BASE}/api/ping`);
        const isOnline = pingRes.status === 200;

        document.getElementById('health-last-updated').innerText = `Last updated: ${new Date().toLocaleTimeString()}`;

        statsContainer.innerHTML = `
            ${metricCard('Total Cells', stats.total_cells || 0, 'across all statuses', 'var(--blue)')}
            ${metricCard('Active Cells', stats.active_cells || 0, 'circulating now', 'var(--green)')}
            ${metricCard('Pending Clarification', stats.pending_cells || 0, 'awaiting user answer', 'var(--amber)')}
            ${metricCard('Total Messages', stats.total_messages || 0, `across ${stats.total_chats || 0} chats`, 'var(--purple)')}
            ${metricCard('Avg Importance', (stats.avg_importance || 0).toFixed(1) + '/10', 'for purified cells', 'var(--accent)')}
            ${metricCard('API Status', isOnline ? 'Online' : 'Offline', isOnline ? 'HEARTBEAT active' : 'Check server', isOnline ? 'var(--green)' : 'var(--accent)')}
        `;

        renderHealthCharts(stats);
        updateDashboardMiniStats(stats);
    } catch (e) {
        statsContainer.innerHTML = `<div class="alert-red w-100">Failed to fetch system stats. Verify backend connection.</div>`;
    }
}

function renderHealthCharts(stats) {
    // Status Doughnut
    const ctxStatus = document.getElementById('health-status-chart');
    if (window.statusChart) window.statusChart.destroy();
    window.statusChart = new Chart(ctxStatus, {
        type: 'doughnut',
        data: {
            labels: ['Active', 'Dormant', 'Expired', 'Pending'],
            datasets: [{
                data: [stats.active_cells || 0, stats.dormant_cells || 0, stats.expired_cells || 0, stats.pending_cells || 0],
                backgroundColor: ['#22c55e', '#3b82f6', '#dc2626', '#f59e0b'],
                borderWidth: 0, cutout: '75%'
            }]
        },
        options: { plugins: { legend: { position: 'bottom', labels: { boxWidth: 10, padding: 20 } } } }
    });

    // Topic Bar
    const ctxTopic = document.getElementById('health-topic-chart');
    if (window.topicChart) window.topicChart.destroy();
    const topics = Object.entries(stats.topic_distribution || {}).sort((a,b) => b[1] - a[1]).slice(0, 8);
    window.topicChart = new Chart(ctxTopic, {
        type: 'bar',
        data: {
            labels: topics.map(t => t[0]),
            datasets: [{ label: 'Cells', data: topics.map(t => t[1]), backgroundColor: '#E94560', borderRadius: 4 }]
        },
        options: { indexAxis: 'y', plugins: { legend: { display: false } }, scales: { x: { grid: { display: false } }, y: { grid: { display: false } } } }
    });
}

// ⚡ PAGE 2 - LIVE ACTIVITY
async function loadActivity() {
    initActivityWS();
    initActivitySparkline();
}

function initActivityWS() {
    if (wsActivity) wsActivity.close();
    const badge = document.getElementById('activity-ws-badge');
    
    wsActivity = new WebSocket(`${WS_BASE}/ws/connect/${userId}_dashboard_activity`);
    
    wsActivity.onopen = () => {
        badge.className = 'badge bg-green-s text-green border-green';
        badge.innerHTML = '<span class="dot bg-green"></span> Connected';
        addActivityLog({ type: 'WEBSOCKET', description: 'Real-time activity link established.' });
    };

    wsActivity.onmessage = (e) => {
        if (e.data === 'ping') {
            try { wsActivity.send('pong'); } catch (err) {}
            return;
        }
        if (e.data === 'pong') return;
        try {
            const data = JSON.parse(e.data);
            if (isFeedPaused) {
                pendingFeedEvents++;
                document.getElementById('pending-events-count').innerText = pendingFeedEvents;
                document.getElementById('activity-pause-banner').classList.remove('hidden');
            } else {
                addActivityLog(data);
            }
        } catch (err) {}
    };

    wsActivity.onclose = () => {
        badge.className = 'badge bg-red-s text-red border-red';
        badge.innerHTML = '<span class="dot-pulse bg-red"></span> Disconnected';
        setTimeout(initActivityWS, 3000); // Auto-reconnect
    };
}

function addActivityLog(data) {
    const container = document.getElementById('activity-log');
    if (container.querySelector('.empty-state')) container.innerHTML = '';
    
    const row = document.createElement('div');
    row.className = 'activity-row flex-center gap-16 p-12 border-bottom hover-bg';
    const typeLabel = (data.type || 'EVENT').toUpperCase();
    const typeColor = {
        CELL_CREATED: 'green', CELL_PURIFIED: 'accent', CELL_EXPIRED: 'red',
        AMBIGUITY: 'amber', TOPIC_SHIFT: 'blue', PIPELINE_ERROR: 'red',
        WEBSOCKET: 'text-3', USER_MESSAGE: 'purple'
    }[typeLabel] || 'text-3';

    row.innerHTML = `
        <span class="f-11 text-3 monospace">${new Date().toLocaleTimeString().split(' ')[0]}</span>
        <span class="badge bg-${typeColor}-s text-${typeColor}">${typeLabel}</span>
        <span class="f-13 flex-1 overflow-hidden" style="white-space:nowrap; text-overflow:ellipsis">${data.description || data.summary || 'Pulse point detected'}</span>
        ${data.cell_id ? `<span class="f-10 text-3 monospace clickable" onclick="navigator.clipboard.writeText('${data.cell_id}')">${data.cell_id.slice(-8)}</span>` : ''}
    `;
    
    container.prepend(row);
    if (container.children.length > 200) container.lastChild.remove();
}

function initActivitySparkline() {
    const ctx = document.getElementById('activity-sparkline-chart');
    if (window.sparkChart) window.sparkChart.destroy();
    
    let activityData = Array(60).fill(0);
    window.sparkChart = new Chart(ctx, {
        type: 'line',
        data: {
            labels: Array(60).fill(''),
            datasets: [{
                data: activityData, borderColor: '#E94560', borderWidth: 2, 
                fill: true, backgroundColor: 'rgba(233,69,96,0.1)', tension: 0.4, pointRadius: 0
            }]
        },
        options: {
            plugins: { legend: { display: false } },
            scales: { x: { display: false }, y: { display: false, min: 0 } },
            animation: false
        }
    });

    let currentSecEvents = 0;
    // We count events in the main feed or Right panel to simulate this
    appIntervals.push(setInterval(() => {
        activityData.shift();
        activityData.push(currentSecEvents);
        currentSecEvents = 0;
        window.sparkChart.update();
    }, 1000));
}

// 🧬 PAGE 3 - BLOOD CELLS
let cellDataStore = [];
let cellCurrentPage = 1;
const CELLS_PER_PAGE = 12;

window.loadCells = async () => {
    updateCellsUI();
    appIntervals.push(setInterval(updateCellsUI, 10000));
};

async function updateCellsUI() {
    const container = document.getElementById('cells-container');
    if (cellDataStore.length === 0) container.innerHTML = Array(6).fill(skeleton('100%', '240px')).join('');

    try {
        const res = await fetch(`${API_BASE}/api/cells/${userId}`);
        const data = await res.json();
        cellDataStore = data.cells || [];
        renderCellsGrid();
    } catch (e) {
        container.innerHTML = `<div class="alert-red">Failed to fetch memory cells.</div>`;
    }
}

function renderCellsGrid() {
    const filters = document.getElementById('cells-search-input').value.toLowerCase();
    const statusFilter = document.querySelector('#cell-status-filters .pill.active').dataset.status;
    const sort = document.getElementById('cells-sort-select').value;

    let filtered = cellDataStore.filter(c => {
        const text = (c.summary + c.topic_id + (c.keywords || '') + c.user_raw_content).toLowerCase();
        const matchesSearch = text.includes(filters);
        const matchesStatus = statusFilter === 'all' || c.status === statusFilter;
        return matchesSearch && matchesStatus;
    });

    // Sorting
    filtered.sort((a,b) => {
        if (sort === 'newest') return new Date(b.created_at) - new Date(a.created_at);
        if (sort === 'oldest') return new Date(a.created_at) - new Date(b.created_at);
        if (sort === 'importance_high') return b.importance_score - a.importance_score;
        if (sort === 'importance_low') return a.importance_score - b.importance_score;
        return 0;
    });

    document.getElementById('cells-count').innerText = filtered.length;
    const totalPages = Math.ceil(filtered.length / CELLS_PER_PAGE) || 1;
    document.getElementById('cells-pagination-info').innerText = `Page ${cellCurrentPage} of ${totalPages}`;

    const start = (cellCurrentPage - 1) * CELLS_PER_PAGE;
    const paginated = filtered.slice(start, start + CELLS_PER_PAGE);

    const container = document.getElementById('cells-container');
    if (paginated.length === 0) {
        container.innerHTML = `<div class="empty-state">No cells match these filters.</div>`;
        return;
    }

    container.innerHTML = paginated.map(c => `
        <div class="card border-sys flex-col gap-12">
            <div class="flex-between">
                <span class="badge bg-purple-s text-purple">${c.topic_id || 'general'}</span>
                ${statusBadge(c.status)}
            </div>
            <div class="flex-center gap-8 f-10 text-3 monospace">
                ID: ${c.cell_id.slice(-12)}
                <span class="clickable" onclick="navigator.clipboard.writeText('${c.cell_id}'); alert('Copied!')">📋</span>
            </div>
            <div>
                <span class="f-11 fw-700 text-3 uppercase">Importance</span>
                ${importanceBar(c.importance_score)}
            </div>
            <div class="flex-col">
                <span class="f-11 fw-700 text-3 uppercase">Summary</span>
                <p class="f-13 fw-600 truncate-3">${c.summary || 'Awaiting purification'}</p>
            </div>
            <div class="f-11 text-3">
                Created: ${formatTime(c.created_at)}<br>
                Expires: ${formatDate(c.expires_at)}
            </div>
            <div class="flex gap-8 mt-8">
                <button class="btn btn-secondary flex-1 f-11" onclick="openCellModal('${c.cell_id}')">View Detail</button>
                ${c.status === 'dormant' ? `<button class="btn btn-blue f-11" onclick="manageCell('${c.cell_id}','wake')">Wake</button>` : ''}
                ${c.status === 'active' ? `<button class="btn btn-accent f-11" onclick="manageCell('${c.cell_id}','expire')">Expire</button>` : ''}
            </div>
        </div>
    `).join('');
}

// 🚜 PAGE 5 - HEART PIPELINE TOOLS
window.initTestpipeline = () => {
    document.querySelectorAll('.btn-suggestion').forEach(btn => {
        btn.onclick = () => document.getElementById('pipe-test-textarea').value = btn.dataset.val;
    });

    document.getElementById('run-pipe-test-btn').onclick = runPipelineTest;
};

async function runPipelineTest() {
    const btn = document.getElementById('run-pipe-test-btn');
    const content = document.getElementById('pipe-test-textarea').value;
    if (!content) return;

    btn.innerText = 'Processing...';
    btn.disabled = true;

    try {
        const res = await fetch(`${API_BASE}/api/test/pipeline`, {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({user_id: userId, chat_id: 'test', session_id: 'test', content})
        });
        const data = await res.json();
        renderPipelineResults(data);
    } catch (e) {
        alert('Pipeline test failed.');
    } finally {
        btn.innerText = 'Run Pipeline Test';
        btn.disabled = false;
    }
}

function renderPipelineResults(data) {
    const container = document.getElementById('pipe-test-results');
    container.classList.remove('hidden');

    const l1 = data.l1 || {};
    const l2 = data.l2 || {};
    const l3 = data.l3 || {};

    container.innerHTML = `
        <div class="p-16 card border-sys mb-12">
            <h4 class="f-11 text-3 mb-8">STEP 1: L1 SIEVE [Passing: ${l1.passed ? '✓' : '✗'}]</h4>
            <div class="f-13">${l1.passed ? `Cleaned: <b class="text-green">${l1.cleaned}</b>` : '<b class="text-red">Message Rejected: Insufficient entropy/noise.</b>'}</div>
            ${jsonBlock(l1)}
        </div>
        <div class="p-16 card border-sys mb-12 ${!l1.passed ? 'opacity-3' : ''}">
            <h4 class="f-11 text-3 mb-8">STEP 2: L2 VALVE [Intent: ${l2.intent_type || '—'}]</h4>
            <div class="flex gap-8">
                ${statusBadge(l2.intent_type || 'raw')}
                ${l2.is_ambiguous ? '<span class="badge bg-amber-s text-amber">Ambiguous Detected</span>' : ''}
            </div>
            ${l2.is_ambiguous ? `<div class="alert-amber mt-8 f-12">Question: ${l2.clarification_question}</div>` : ''}
            ${jsonBlock(l2)}
        </div>
        <div class="p-16 card border-sys mb-12 ${!l1.passed || l2.is_ambiguous ? 'opacity-3' : ''}">
            <h4 class="f-11 text-3 mb-8">STEP 3: L3 PURIFIER [Memory Formed]</h4>
            <div class="f-13 mb-8">Summary: <b>${l3.summary || '—'}</b></div>
            ${importanceBar(l3.importance_score || 0)}
            ${jsonBlock(l3)}
        </div>
    `;
}

// 🛠 PAGE 13 - API EXPLORER
window.initApiexplorer = () => {
    const container = document.getElementById('explorer-list');
    const endpoints = [
        {m: 'GET', p: '/api/ping', d: 'Check if HEARTBEAT server is running'},
        {m: 'POST', p: '/api/message', d: 'Send a message through the 9-step loop', b: {user_id: userId, chat_id: 'test-chat-001', session_id: 'test', content: 'Testing AI memory', content_type: 'text'}},
        {m: 'GET', p: '/api/history/{chat_id}', d: 'Get full message history', v: 'test-chat-001'},
        {m: 'GET', p: '/api/cells/{user_id}', d: 'Get all blood cells', v: userId},
        {m: 'POST', p: '/api/answer', d: 'Get progressive depth answer', b: {user_id: userId, cell_id: '', message: 'Tell me more', depth_level: 1}}
    ];

    container.innerHTML = endpoints.map((e, index) => `
        <div class="card p-0 border-sys overflow-hidden">
            <div class="p-16 flex-between bg-black-2 clickable" onclick="toggleExplorer('${index}')">
                <div class="flex-center gap-12">
                    <span class="badge bg-${e.m==='GET'?'green':'accent'}-s text-${e.m==='GET'?'green':'accent'}">${e.m}</span>
                    <span class="f-13 monospace fw-600">${e.p}</span>
                    <span class="f-11 text-3 ml-12">${e.d}</span>
                </div>
                <span id="exp-arrow-${index}">▼</span>
            </div>
            <div id="exp-body-${index}" class="hidden p-24 border-top">
                ${e.b ? `
                    <p class="f-11 text-3 uppercase mb-8">Request Body</p>
                    <textarea id="exp-input-${index}" class="input w-100 monospace h-150 mb-12">${JSON.stringify(e.b, null, 2)}</textarea>
                ` : ''}
                <button class="btn btn-accent" onclick="runExplorerTest('${index}', '${e.m}', '${e.p}', '${e.v || ''}')">Send Request</button>
                <div id="exp-res-${index}" class="mt-16 hidden"></div>
            </div>
        </div>
    `).join('');
};

window.toggleExplorer = (idx) => {
    const body = document.getElementById(`exp-body-${idx}`);
    body.classList.toggle('hidden');
    document.getElementById(`exp-arrow-${idx}`).innerText = body.classList.contains('hidden') ? '▼' : '▲';
};

window.runExplorerTest = async (idx, method, path, val) => {
    const resDiv = document.getElementById(`exp-res-${idx}`);
    resDiv.classList.remove('hidden');
    resDiv.innerHTML = skeleton('100%', '100px');

    const input = document.getElementById(`exp-input-${idx}`);
    const actualPath = path.replace('{user_id}', userId).replace('{chat_id}', val || 'test-chat-001');

    try {
        const options = { method, headers: {'Content-Type': 'application/json'} };
        if (input) options.body = input.value;

        const start = Date.now();
        const res = await fetch(`${API_BASE}${actualPath}`, options);
        const data = await res.json();
        const took = Date.now() - start;

        resDiv.innerHTML = `
            <div class="flex-between mb-8">
                <span class="badge bg-green-s text-green">Status: ${res.status}</span>
                <span class="f-11 text-3">${took}ms</span>
            </div>
            ${jsonBlock(data)}
        `;
    } catch (e) {
        resDiv.innerHTML = `<div class="alert-red">Request failed.</div>`;
    }
};

// 🛰 RIGHT FEED WEBSOCKET
function initLiveFeed() {
    if (wsFeed) wsFeed.close();
    const status = document.getElementById('feed-status');
    const container = document.getElementById('feed-stream');

    wsFeed = new WebSocket(`${WS_BASE}/ws/connect/${userId}_dashboard_feed`);
    
    wsFeed.onopen = () => {
        status.className = 'f-10 flex-center gap-4 text-green';
        status.innerHTML = '<span class="dot bg-green"></span> Connected';
        document.getElementById('feed-reconnect-btn').classList.add('hidden');
    };

    wsFeed.onmessage = (e) => {
        if (e.data === 'ping') {
            try { wsFeed.send('pong'); } catch (err) {}
            return;
        }
        if (e.data === 'pong') return;
        try {
            const data = JSON.parse(e.data);
            const item = document.createElement('div');
            item.className = 'event-item';
            const type = (data.type || 'HEARTBEAT').toUpperCase();
            const color = {CELL_PURIFIED: 'var(--accent)', CELL_CREATED: 'var(--green)', AMBIGUITY: 'var(--amber)', ERROR: 'var(--red)'}[type] || '#888';

            item.innerHTML = `
                <div class="flex-between mb-4">
                    <span class="f-10 fw-800" style="color:${color}"><span class="dot" style="background:${color}"></span> ${type}</span>
                    <span class="f-9 text-3">Just now</span>
                </div>
                <p class="f-11 text-white">${data.summary || data.description || 'Pulse detected'}</p>
            `;
            container.prepend(item);
            if (container.children.length > MAX_FEED_EVENTS) container.lastChild.remove();
            if (container.querySelector('.empty-feed')) container.querySelector('.empty-feed').remove();
        } catch (err) {}
    };

    wsFeed.onclose = () => {
        status.className = 'f-10 flex-center gap-4 text-red';
        status.innerHTML = '<span class="dot-pulse bg-red"></span> Offline';
        document.getElementById('feed-reconnect-btn').classList.remove('hidden');
    };
}

function updateDashboardMiniStats(stats) {
    document.getElementById('mini-stat-active').innerText = stats.active_cells || 0;
    document.getElementById('mini-stat-imp').innerText = (stats.avg_importance || 0).toFixed(1);
    // Rate: mock for now based on total activity
    document.getElementById('mini-stat-rate').innerText = (Math.random() * 2).toFixed(1);
}

// 🩺 OFFLINE CHECKER
async function startPingLoop() {
    appIntervals.push(setInterval(async () => {
        try {
            const res = await fetch(`${API_BASE}/api/ping`);
            document.getElementById('offline-banner').className = res.status === 200 ? 'hidden' : '';
        } catch (e) {
            document.getElementById('offline-banner').className = '';
        }
    }, 10000));
}

// Initial Launch
window.onload = () => {
    initNavigation();
    initLiveFeed();
    startPingLoop();
    document.getElementById('feed-reconnect-btn').onclick = initLiveFeed;
};

// HELPER: Modal
window.openCellModal = async (cellId) => {
    const modal = document.getElementById('modal-overlay');
    const body = document.getElementById('modal-body');
    modal.classList.remove('hidden');
    body.innerHTML = skeleton('100%', '300px');

    try {
        const res = await fetch(`${API_BASE}/api/cells/detail/${cellId}`); // You might need to add this endpoint or just find in store
        const cells = await fetch(`${API_BASE}/api/cells/${userId}`).then(r => r.json());
        const cell = cells.cells.find(c => c.cell_id === cellId);
        
        body.innerHTML = `
            <h2 class="f-18 fw-800 text-accent mb-16">Cell Insight</h2>
            <div class="grid-2 gap-16">
                <div>
                   <label class="f-10 text-3 uppercase fw-800">Topic</label>
                   <p class="f-14 fw-600">${cell.topic_id}</p>
                </div>
                <div>
                   <label class="f-10 text-3 uppercase fw-800">Status</label>
                   <p>${statusBadge(cell.status)}</p>
                </div>
            </div>
            <div class="mt-16">
                <label class="f-10 text-3 uppercase fw-800">Summary</label>
                <p class="f-13 bg-black-2 p-12 border-sys rounded-8 mt-4">${cell.summary}</p>
            </div>
            <div class="mt-16">
                <label class="f-10 text-3 uppercase fw-800">Raw Content</label>
                <p class="f-11 text-2 italic mt-4">${cell.user_raw_content}</p>
            </div>
            <div class="mt-16">
                <label class="f-10 text-3 uppercase fw-800">Metadata</label>
                ${jsonBlock(cell)}
            </div>
        `;
    } catch (e) {
        body.innerHTML = `<div class="alert-red">Failed to load cell details.</div>`;
    }
};

document.getElementById('modal-close').onclick = () => document.getElementById('modal-overlay').classList.add('hidden');
