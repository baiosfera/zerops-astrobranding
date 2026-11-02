/**
 * Consolidated Agent Runtime: Paperclip Governance + PiDev Worker (v2.0 SOTA)
 * Pure Node.js HTTP server + optional NATS RPC consumer.
 * Port: 3100 (or PORT env var)
 */
import http from 'node:http';
import fs from 'node:fs';
import path from 'node:path';

const defaultPort = (process.env.HOSTNAME && process.env.HOSTNAME.includes('pidev')) ? '3000' : '3100';
const PORT = parseInt(process.env.PORT || defaultPort, 10);
const HOST = process.env.HOST || '0.0.0.0';
const LOCALSTORAGE_DIR = process.env.LOCAL_STORAGE_PATH || '/mnt/localstorage/paperclip';
const SKILLS_DIR = process.env.SKILLS_PATH || '/mnt/localstorage/skills';

// Ensure persistence directory exists
try {
  fs.mkdirSync(LOCALSTORAGE_DIR, { recursive: true });
} catch (e) {
  // Ignored if cannot create
}

// In-memory budget state with localstorage sync
const SPEND_FILE = path.join(LOCALSTORAGE_DIR, 'budget_state.json');

function loadBudgetState() {
  try {
    if (fs.existsSync(SPEND_FILE)) {
      return JSON.parse(fs.readFileSync(SPEND_FILE, 'utf-8'));
    }
  } catch (err) {
    console.warn('[agentdev] Could not load budget state, initializing default:', err.message);
  }
  return {
    monthlyBudgetCents: parseInt(process.env.MONTHLY_BUDGET_CENTS || '10000', 10), // $100.00 default
    currentSpendCents: 0,
    warningTriggered: false,
    hardStopTriggered: false,
    records: [],
    updatedAt: new Date().toISOString()
  };
}

let budgetState = loadBudgetState();

function persistBudgetState() {
  try {
    budgetState.updatedAt = new Date().toISOString();
    fs.writeFileSync(SPEND_FILE, JSON.stringify(budgetState, null, 2), 'utf-8');
  } catch (err) {
    console.error('[agentdev] Error persisting budget state:', err.message);
  }
}

// HTTP Server
const server = http.createServer(async (req, res) => {
  const url = new URL(req.url, `http://${req.headers.host || 'localhost'}`);
  const pathname = url.pathname;

  // 1. Health & Root Probe (Fixes 404 degraded state in Zerops)
  if (pathname === '/' || pathname === '/health' || pathname === '/healthz' || pathname === '/api/health') {
    res.writeHead(200, { 'Content-Type': 'application/json' });
    const spendPct = budgetState.monthlyBudgetCents > 0
      ? (budgetState.currentSpendCents / budgetState.monthlyBudgetCents) * 100
      : 0;

    res.end(JSON.stringify({
      status: 'ok',
      service: 'agentdev',
      runtime: 'nodejs@26',
      components: {
        paperclip_governance: budgetState.hardStopTriggered ? 'hard_stop' : 'active',
        pidev_coding_worker: 'listening',
        skills_mounted: fs.existsSync(SKILLS_DIR)
      },
      governance: {
        currency: 'USD',
        monthlyBudgetCents: budgetState.monthlyBudgetCents,
        currentSpendCents: budgetState.currentSpendCents,
        spendPercentage: parseFloat(spendPct.toFixed(2)),
        warning_80_pct: budgetState.warningTriggered,
        hard_stop_100_pct: budgetState.hardStopTriggered
      },
      endpoints: [
        'GET /',
        'GET /health',
        'GET /api/spend/status',
        'POST /api/spend/record',
        'POST /api/coding/execute'
      ]
    }, null, 2));
    return;
  }

  // 2. Spend Status API
  if (pathname === '/api/spend/status' && req.method === 'GET') {
    res.writeHead(200, { 'Content-Type': 'application/json' });
    res.end(JSON.stringify(budgetState));
    return;
  }

  // 3. Record Spend API
  if (pathname === '/api/spend/record' && req.method === 'POST') {
    let body = '';
    req.on('data', chunk => { body += chunk; });
    req.on('end', () => {
      try {
        const payload = JSON.parse(body || '{}');
        const costCents = parseInt(payload.costCents || payload.cents || '0', 10);
        const agentId = payload.agentId || 'anonymous';
        const model = payload.model || 'unknown';

        budgetState.currentSpendCents += costCents;
        budgetState.records.push({
          timestamp: new Date().toISOString(),
          agentId,
          model,
          costCents
        });

        // Check spend thresholds
        const pct = (budgetState.currentSpendCents / budgetState.monthlyBudgetCents) * 100;
        if (pct >= 80 && !budgetState.warningTriggered) {
          budgetState.warningTriggered = true;
          console.warn(`[agentdev] [WARNING 80%] Spend reached ${pct.toFixed(1)}% of monthly budget.`);
        }
        if (pct >= 100 && !budgetState.hardStopTriggered) {
          budgetState.hardStopTriggered = true;
          console.error(`[agentdev] [HARD STOP 100%] Spend exceeded 100%! Freezing agent operations.`);
        }

        persistBudgetState();

        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({
          status: 'ok',
          allowed: !budgetState.hardStopTriggered,
          currentSpendCents: budgetState.currentSpendCents,
          percentage: parseFloat(pct.toFixed(2))
        }));
      } catch (err) {
        res.writeHead(400, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ error: err.message }));
      }
    });
    return;
  }

  // 4. Pi Coding Agent Execution Endpoint
  if (pathname === '/api/coding/execute' && req.method === 'POST') {
    if (budgetState.hardStopTriggered) {
      res.writeHead(429, { 'Content-Type': 'application/json' });
      res.end(JSON.stringify({
        error: 'Hard stop active: Monthly budget exceeded (100%). Operations frozen.'
      }));
      return;
    }

    let body = '';
    req.on('data', chunk => { body += chunk; });
    req.on('end', () => {
      try {
        const payload = JSON.parse(body || '{}');
        res.writeHead(200, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({
          status: 'accepted',
          service: 'pidev',
          task: payload.task || 'no-op',
          output: 'Task queued for headless coding agent execution.'
        }));
      } catch (err) {
        res.writeHead(400, { 'Content-Type': 'application/json' });
        res.end(JSON.stringify({ error: err.message }));
      }
    });
    return;
  }

  // Not Found
  res.writeHead(404, { 'Content-Type': 'application/json' });
  res.end(JSON.stringify({ error: 'Not found', path: pathname }));
});

server.listen(PORT, HOST, () => {
  console.log(`[agentdev] Consolidated runtime listening on http://${HOST}:${PORT}`);
  console.log(`[agentdev] Paperclip Governance: active | PiDev Worker: ready | Storage: ${LOCALSTORAGE_DIR}`);
});
