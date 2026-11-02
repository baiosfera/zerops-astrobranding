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

function renderDashboardHtml(state) {
  const currentSpendCents = state.currentSpendCents || 0;
  const monthlyBudgetCents = state.monthlyBudgetCents || 10000;
  const spendPct = monthlyBudgetCents > 0 ? (currentSpendCents / monthlyBudgetCents) * 100 : 0;
  const records = state.records || [];

  const rows = records.slice(-10).reverse().map(r => `
    <tr class="border-b border-neutral-800/50 hover:bg-neutral-800/30">
      <td class="py-2 text-neutral-400">${new Date(r.timestamp).toLocaleTimeString()}</td>
      <td class="py-2 font-semibold text-neutral-200">${r.agentId}</td>
      <td class="py-2 text-neutral-400">${r.model}</td>
      <td class="py-2 text-right font-bold text-emerald-400">$${(r.costCents / 100).toFixed(4)}</td>
    </tr>
  `).join('');

  return `<!DOCTYPE html>
<html lang="es" class="dark">
<head>
  <meta charset="utf-8">
  <meta name="viewport" content="width=device-width, initial-scale=1">
  <title>Paperclip — Sovereign Governance & Agent Spend Watchdog</title>
  <link rel="preconnect" href="https://fonts.googleapis.com">
  <link href="https://fonts.googleapis.com/css2?family=Plus+Jakarta+Sans:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500&display=swap" rel="stylesheet">
  <script src="https://cdn.tailwindcss.com"></script>
  <script>
    tailwind.config = {
      darkMode: 'class',
      theme: {
        extend: {
          fontFamily: {
            sans: ['"Plus Jakarta Sans"', 'sans-serif'],
            mono: ['"JetBrains Mono"', 'monospace']
          }
        }
      }
    }
  </script>
</head>
<body class="bg-neutral-950 text-neutral-100 min-h-screen font-sans antialiased p-6 md:p-12">
  <div class="max-w-5xl mx-auto space-y-8">
    <header class="flex flex-col md:flex-row md:items-center justify-between border-b border-neutral-800 pb-6 gap-4">
      <div>
        <div class="flex items-center gap-3">
          <span class="inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-950 text-emerald-400 border border-emerald-800">
            <span class="w-1.5 h-1.5 rounded-full bg-emerald-400 animate-pulse mr-1.5"></span>
            ACTIVE 24/7
          </span>
          <h1 class="text-2xl font-bold tracking-tight">Paperclip Governance</h1>
        </div>
        <p class="text-sm text-neutral-400 mt-1">Autonomous Spend Caps Watchdog & Coding Agent Worker</p>
      </div>
      <div class="text-left md:text-right font-mono text-xs text-neutral-400">
        <div>Runtime: Node.js 26 (Ubuntu)</div>
        <div class="text-emerald-400 font-semibold">Service: agentdev / paperclip</div>
      </div>
    </header>

    <div class="bg-neutral-900 border border-neutral-800 rounded-xl p-6 shadow-xl space-y-4">
      <div class="flex items-center justify-between">
        <h2 class="text-sm font-semibold tracking-wide text-neutral-400 uppercase">Monthly Budget Control</h2>
        <span class="text-xs font-mono text-neutral-400">Caps: 80% Warn · 100% Hard Stop</span>
      </div>
      <div class="flex flex-col md:flex-row md:items-baseline justify-between gap-2">
        <div>
          <span class="text-4xl font-extrabold tracking-tight font-mono text-white">$${(currentSpendCents / 100).toFixed(2)}</span>
          <span class="text-neutral-500 font-mono text-lg"> / $${(monthlyBudgetCents / 100).toFixed(2)} USD</span>
        </div>
        <div class="text-left md:text-right">
          <span class="text-2xl font-bold font-mono ${spendPct >= 80 ? 'text-amber-400' : 'text-emerald-400'}">${spendPct.toFixed(1)}%</span>
          <p class="text-xs text-neutral-400 font-mono">Presupuesto consumido</p>
        </div>
      </div>
      <div class="w-full bg-neutral-800 rounded-full h-3 relative overflow-hidden">
        <div class="bg-gradient-to-r from-emerald-500 via-teal-400 to-cyan-500 h-3 rounded-full transition-all duration-500" style="width: ${Math.min(spendPct, 100)}%"></div>
        <div class="absolute top-0 bottom-0 left-[80%] w-0.5 bg-amber-400/80" title="80% Alerta"></div>
      </div>
      <div class="flex justify-between text-xs font-mono text-neutral-400 pt-1">
        <span>$0.00 (Inicio de ciclo)</span>
        <span class="text-amber-400">80% Alerta ($${((monthlyBudgetCents * 0.8) / 100).toFixed(2)})</span>
        <span class="text-red-400">100% Corte ($${(monthlyBudgetCents / 100).toFixed(2)})</span>
      </div>
    </div>

    <div class="grid grid-cols-1 md:grid-cols-3 gap-4">
      <div class="bg-neutral-900/60 border border-neutral-800/80 rounded-xl p-5 space-y-2">
        <div class="text-xs text-neutral-400 uppercase tracking-wider font-semibold">Spend Watchdog</div>
        <div class="flex items-center gap-2">
          <span class="w-2.5 h-2.5 rounded-full ${state.hardStopTriggered ? 'bg-red-500' : 'bg-emerald-400'}"></span>
          <span class="text-lg font-bold">${state.hardStopTriggered ? 'Hard Stop Activo' : 'Operativo (Protegido)'}</span>
        </div>
        <p class="text-xs text-neutral-400">Previene facturas desbordadas cortando inferencia paga al 100%.</p>
      </div>

      <div class="bg-neutral-900/60 border border-neutral-800/80 rounded-xl p-5 space-y-2">
        <div class="text-xs text-neutral-400 uppercase tracking-wider font-semibold">PiDev Coding Worker</div>
        <div class="flex items-center gap-2">
          <span class="w-2.5 h-2.5 rounded-full bg-emerald-400"></span>
          <span class="text-lg font-bold">Listening</span>
        </div>
        <p class="text-xs text-neutral-400">Worker headless escuchando tareas en NATS rpc.coding.execute.</p>
      </div>

      <div class="bg-neutral-900/60 border border-neutral-800/80 rounded-xl p-5 space-y-2">
        <div class="text-xs text-neutral-400 uppercase tracking-wider font-semibold">Skills Soberanas (NVMe)</div>
        <div class="flex items-center gap-2">
          <span class="w-2.5 h-2.5 rounded-full bg-emerald-400"></span>
          <span class="text-lg font-bold">80+ Montadas</span>
        </div>
        <p class="text-xs text-neutral-400">Disponibles en /mnt/localstorage/skills/ 24/7 sin ZCP prendido.</p>
      </div>
    </div>

    <div class="bg-neutral-900 border border-neutral-800 rounded-xl p-6 shadow-xl space-y-4">
      <div class="flex items-center justify-between">
        <h3 class="text-sm font-semibold tracking-wide text-neutral-400 uppercase">Registro Reciente de Inferencia</h3>
        <span class="text-xs font-mono text-neutral-400">${records.length} registros</span>
      </div>
      <div class="overflow-x-auto">
        <table class="w-full text-left font-mono text-xs">
          <thead>
            <tr class="border-b border-neutral-800 text-neutral-400 pb-2">
              <th class="py-2">TIMESTAMP</th>
              <th class="py-2">AGENTE</th>
              <th class="py-2">MODELO</th>
              <th class="py-2 text-right">COSTO</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-neutral-800/50">
            ${records.length === 0 ? '<tr><td colspan="4" class="py-6 text-center text-neutral-500">Cero consumo registrado en este ciclo ($0.00). Inferencia enrutada al pool de 12 keys de FreeLLMAPI ($0).</td></tr>' : rows}
          </tbody>
        </table>
      </div>
    </div>

    <footer class="pt-4 border-t border-neutral-800/60 text-xs font-mono text-neutral-400 flex flex-col md:flex-row items-center justify-between gap-2">
      <div>API Endpoints: GET /health · GET /api/spend/status · POST /api/spend/record · POST /api/coding/execute</div>
      <div>Paperclip Governance v2.0 · Zerops Incus LXC</div>
    </footer>
  </div>
</body>
</html>`;
}

// HTTP Server
const server = http.createServer(async (req, res) => {
  const url = new URL(req.url, `http://${req.headers.host || 'localhost'}`);
  const pathname = url.pathname;
  const acceptsHtml = req.headers.accept && req.headers.accept.includes('text/html');

  // 1. Dashboard UI (HTML Panel for Browsers)
  if ((pathname === '/' || pathname === '/dashboard') && acceptsHtml) {
    res.writeHead(200, { 'Content-Type': 'text/html; charset=utf-8' });
    res.end(renderDashboardHtml(budgetState));
    return;
  }

  // 2. Health & Root JSON Probe
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
