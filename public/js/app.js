/* ============================================================
   Wumpus World — Frontend Application Logic
   ============================================================ */

const API = '';  // Same origin

// ---- State ----
let gameId = null;
let currentState = null;
let revealMode = false;
let autoPlaying = false;

// ---- DOM Refs ----
const $ = (sel) => document.querySelector(sel);
const btnNew     = $('#btn-new-game');
const btnStep    = $('#btn-step');
const btnAuto    = $('#btn-auto');
const btnReveal  = $('#btn-reveal');
const inputRows  = $('#input-rows');
const inputCols  = $('#input-cols');
const gridBox    = $('#grid-container');
const gridPlace  = $('#grid-placeholder');
const perceptBar = $('#percepts-bar');
const perceptLst = $('#percepts-list');
const logBox     = $('#log-container');
const statusText = $('#status-text');

// Metric values
const valSteps      = $('#val-steps');
const valExplored   = $('#val-explored');
const valInferences = $('#val-inferences');
const valKb         = $('#val-kb');

// Modal
const modalOverlay = $('#modal-overlay');
const modalIcon    = $('#modal-icon');
const modalTitle   = $('#modal-title');
const modalMsg     = $('#modal-message');
const modalStats   = $('#modal-stats');
const btnModalClose = $('#btn-modal-close');

// ---- API Helpers ----
async function apiPost(url, body = {}) {
    const res = await fetch(API + url, {
        method: 'POST',
        headers: { 'Content-Type': 'application/json' },
        body: JSON.stringify(body),
    });
    if (!res.ok) throw new Error(`API error: ${res.status}`);
    return res.json();
}

// ---- New Game ----
async function newGame() {
    const rows = parseInt(inputRows.value) || 4;
    const cols = parseInt(inputCols.value) || 4;

    btnNew.disabled = true;
    statusText.textContent = 'Generating...';

    try {
        const state = await apiPost('/api/new-game', { rows, cols });
        gameId = state.game_id;
        currentState = state;
        revealMode = false;
        autoPlaying = false;

        btnStep.disabled = false;
        btnAuto.disabled = false;
        btnReveal.disabled = false;

        gridPlace.style.display = 'none';
        gridBox.style.display = 'grid';
        perceptBar.style.display = 'flex';

        renderGrid(state);
        renderMetrics(state);
        renderPercepts(state);
        renderLog(state);
        statusText.textContent = 'Agent Active';
    } catch (e) {
        console.error(e);
        statusText.textContent = 'Error';
    } finally {
        btnNew.disabled = false;
    }
}

// ---- Step ----
async function doStep() {
    if (!gameId || autoPlaying) return;
    btnStep.disabled = true;
    statusText.textContent = 'Thinking...';

    try {
        const state = await apiPost('/api/step', { game_id: gameId });
        currentState = state;
        renderGrid(state);
        renderMetrics(state);
        renderPercepts(state);
        renderLog(state);

        if (state.game_over) {
            handleGameOver(state);
        } else {
            btnStep.disabled = false;
            statusText.textContent = 'Agent Active';
        }
    } catch (e) {
        console.error(e);
        btnStep.disabled = false;
        statusText.textContent = 'Error';
    }
}

// ---- Auto-Play ----
async function doAutoPlay() {
    if (!gameId) return;
    autoPlaying = true;
    btnStep.disabled = true;
    btnAuto.disabled = true;
    statusText.textContent = 'Auto-Playing...';

    try {
        const state = await apiPost('/api/auto-play', { game_id: gameId });
        currentState = state;

        // Animate through history
        if (state.history && state.history.length > 0) {
            for (let i = 0; i < state.history.length; i++) {
                await sleep(350);
                const s = state.history[i];
                renderGrid(s);
                renderMetrics(s);
                renderPercepts(s);
                renderLog(s);
            }
        } else {
            renderGrid(state);
            renderMetrics(state);
            renderPercepts(state);
            renderLog(state);
        }

        if (state.game_over) {
            handleGameOver(state);
        }
    } catch (e) {
        console.error(e);
        statusText.textContent = 'Error';
    } finally {
        autoPlaying = false;
    }
}

// ---- Reveal ----
function toggleReveal() {
    revealMode = !revealMode;
    btnReveal.textContent = revealMode ? '🙈 Hide Map' : '👁️ Reveal Map';
    if (currentState) renderGrid(currentState);
}

// ---- Render Grid ----
function renderGrid(state) {
    const { rows, cols } = state.grid;
    const agentPos = state.agent.position;
    const alive = state.agent.alive;

    // Build lookup sets
    const visited   = new Set(state.cells.visited.map(c => `${c[0]},${c[1]}`));
    const safe      = new Set(state.cells.safe.map(c => `${c[0]},${c[1]}`));
    const dangerous = new Set(state.cells.dangerous.map(c => `${c[0]},${c[1]}`));
    const frontier  = new Set(state.cells.frontier.map(c => `${c[0]},${c[1]}`));

    const pits   = new Set((state.hazards.pits || []).map(c => `${c[0]},${c[1]}`));
    const wumpus = state.hazards.wumpus ? `${state.hazards.wumpus[0]},${state.hazards.wumpus[1]}` : null;
    const gold   = state.hazards.gold ? `${state.hazards.gold[0]},${state.hazards.gold[1]}` : null;

    const perceptMap = state.percepts.map || {};

    gridBox.style.gridTemplateColumns = `repeat(${cols}, 1fr)`;
    gridBox.style.gridTemplateRows = `repeat(${rows}, 1fr)`;
    gridBox.innerHTML = '';

    for (let r = 0; r < rows; r++) {
        for (let c = 0; c < cols; c++) {
            const key = `${r},${c}`;
            const cell = document.createElement('div');
            cell.className = 'grid-cell';
            cell.id = `cell-${r}-${c}`;

            // Coordinate label
            const coord = document.createElement('span');
            coord.className = 'cell-coord';
            coord.textContent = `${r},${c}`;
            cell.appendChild(coord);

            // Determine cell state class
            const isAgent = (r === agentPos[0] && c === agentPos[1]);

            if (isAgent && !alive) {
                cell.classList.add('cell-dead');
            } else if (isAgent) {
                cell.classList.add('cell-agent');
            } else if (dangerous.has(key)) {
                cell.classList.add('cell-danger');
            } else if (visited.has(key)) {
                cell.classList.add('cell-visited');
            } else if (safe.has(key)) {
                cell.classList.add('cell-safe');
            } else if (frontier.has(key)) {
                cell.classList.add('cell-frontier');
            } else {
                cell.classList.add('cell-unknown');
            }

            // Icon
            const icon = document.createElement('span');
            icon.className = 'cell-icon';

            if (isAgent) {
                icon.textContent = alive ? '🤖' : '💀';
            } else if (revealMode || state.game_over) {
                // Show hazards
                if (pits.has(key)) {
                    icon.textContent = '🕳️';
                    if (!dangerous.has(key)) cell.classList.add('cell-reveal-pit');
                } else if (key === wumpus) {
                    icon.textContent = '👹';
                    if (!dangerous.has(key)) cell.classList.add('cell-reveal-wumpus');
                } else if (key === gold) {
                    icon.textContent = '💎';
                    cell.classList.add('cell-reveal-gold');
                } else if (visited.has(key)) {
                    icon.textContent = '✓';
                }
            } else if (dangerous.has(key)) {
                icon.textContent = '⚠️';
            } else if (visited.has(key)) {
                icon.textContent = '✓';
            }

            cell.appendChild(icon);

            // Show percepts in visited cells
            if (visited.has(key) && perceptMap[key]) {
                const pDiv = document.createElement('div');
                pDiv.className = 'cell-percepts';
                const percepts = perceptMap[key];
                if (percepts.includes('breeze'))  pDiv.innerHTML += '<span title="Breeze">💨</span>';
                if (percepts.includes('stench'))  pDiv.innerHTML += '<span title="Stench">😷</span>';
                if (percepts.includes('glitter')) pDiv.innerHTML += '<span title="Glitter">✨</span>';
                cell.appendChild(pDiv);
            }

            gridBox.appendChild(cell);
        }
    }
}

// ---- Render Metrics ----
function renderMetrics(state) {
    const m = state.metrics;
    animateValue(valSteps, m.steps_taken);
    animateValue(valExplored, m.cells_explored);
    animateValue(valInferences, m.total_inference_steps);
    animateValue(valKb, m.kb_clauses);
}

function animateValue(el, target) {
    const current = parseInt(el.textContent) || 0;
    if (current === target) return;
    el.textContent = target;
    el.style.transform = 'scale(1.2)';
    el.style.transition = 'transform 0.3s ease';
    setTimeout(() => { el.style.transform = 'scale(1)'; }, 300);
}

// ---- Render Percepts ----
function renderPercepts(state) {
    const percepts = state.percepts.current;
    perceptLst.innerHTML = '';

    if (!percepts || percepts.length === 0) {
        const tag = document.createElement('span');
        tag.className = 'percept-tag percept-none';
        tag.textContent = 'None';
        perceptLst.appendChild(tag);
        return;
    }

    percepts.forEach(p => {
        const tag = document.createElement('span');
        tag.className = `percept-tag percept-${p}`;
        const icons = { breeze: '💨 Breeze', stench: '😷 Stench', glitter: '✨ Glitter' };
        tag.textContent = icons[p] || p;
        perceptLst.appendChild(tag);
    });
}

// ---- Render Log ----
function renderLog(state) {
    const logs = state.log || [];
    logBox.innerHTML = '';

    if (logs.length === 0) {
        logBox.innerHTML = '<div class="log-empty">No activity yet.</div>';
        return;
    }

    logs.forEach(entry => {
        const div = document.createElement('div');
        div.className = 'log-entry';

        // Color-code by prefix
        const lower = entry.toLowerCase();
        if (lower.includes('visit'))  div.classList.add('log-visit');
        if (lower.includes('safe'))   div.classList.add('log-safe');
        if (lower.includes('danger')) div.classList.add('log-danger');
        if (lower.includes('move'))   div.classList.add('log-move');
        if (lower.includes('risk'))   div.classList.add('log-risk');
        if (lower.includes('gold'))   div.classList.add('log-gold');
        if (lower.includes('death'))  div.classList.add('log-death');
        if (lower.includes('stuck'))  div.classList.add('log-stuck');
        if (lower.includes('done'))   div.classList.add('log-done');

        div.textContent = entry;
        logBox.appendChild(div);
    });

    // Auto-scroll to bottom
    logBox.scrollTop = logBox.scrollHeight;
}

// ---- Game Over Modal ----
function handleGameOver(state) {
    btnStep.disabled = true;
    btnAuto.disabled = true;
    revealMode = true;
    renderGrid(state);

    const alive = state.agent.alive;
    const hasGold = state.agent.has_gold;

    if (hasGold) {
        modalIcon.textContent = '🏆';
        modalTitle.textContent = 'Gold Found!';
        modalMsg.textContent = 'The agent successfully found the gold using logical deduction!';
        statusText.textContent = 'Victory!';
    } else if (!alive) {
        modalIcon.textContent = '💀';
        modalTitle.textContent = 'Agent Died';
        modalMsg.textContent = 'The agent encountered a hazard it could not deduce.';
        statusText.textContent = 'Game Over';
    } else {
        modalIcon.textContent = '🗺️';
        modalTitle.textContent = 'Exploration Complete';
        modalMsg.textContent = 'The agent has explored all safely reachable cells.';
        statusText.textContent = 'Complete';
    }

    const m = state.metrics;
    modalStats.innerHTML = `
        <div class="modal-stat"><div class="stat-val">${m.steps_taken}</div><div class="stat-lbl">Steps</div></div>
        <div class="modal-stat"><div class="stat-val">${m.cells_explored}</div><div class="stat-lbl">Explored</div></div>
        <div class="modal-stat"><div class="stat-val">${m.total_inference_steps}</div><div class="stat-lbl">Inferences</div></div>
        <div class="modal-stat"><div class="stat-val">${m.kb_clauses}</div><div class="stat-lbl">KB Clauses</div></div>
    `;

    modalOverlay.style.display = 'flex';
}

// ---- Utilities ----
function sleep(ms) {
    return new Promise(resolve => setTimeout(resolve, ms));
}

// ---- Event Listeners ----
btnNew.addEventListener('click', newGame);
btnStep.addEventListener('click', doStep);
btnAuto.addEventListener('click', doAutoPlay);
btnReveal.addEventListener('click', toggleReveal);
btnModalClose.addEventListener('click', () => {
    modalOverlay.style.display = 'none';
});
