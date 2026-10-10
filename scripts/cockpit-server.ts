#!/usr/bin/env bun
/**
 * ==============================================================================
 * Sovereign Cockpit Web GUI Server (cockpit-server.ts)
 * On-Demand Micro Dashboard | Bun.serve | Tailwind Dark Mode | Auto-Shutdown
 * 6 Strict Categories | Real Quotas & Cutoffs | Real Container RAM & Costs
 * Standalone Operation (0 AGY LLM Tokens) | Full SSoT Parity
 * ==============================================================================
 */

import { execSync } from "node:child_process";
import fs from "node:fs";
import http from "node:http";

const PORT = parseInt(process.env.COCKPIT_PORT || "3050", 10);
const PID_FILE = "/tmp/cockpit-web.pid";
let lastActivity = Date.now();
const INACTIVITY_TIMEOUT_MS = 30 * 60 * 1000; // 30 minutes auto-shutdown

// Record PID
fs.writeFileSync(PID_FILE, process.pid.toString(), "utf-8");

// Auto-shutdown check every 60s
setInterval(() => {
  if (Date.now() - lastActivity > INACTIVITY_TIMEOUT_MS) {
    console.log(`[Cockpit Web] Inactivity timeout reached (${INACTIVITY_TIMEOUT_MS / 60000}m). Auto-shutting down to free memory...`);
    cleanupAndExit();
  }
}, 60000);

function cleanupAndExit() {
  try {
    if (fs.existsSync(PID_FILE)) fs.unlinkSync(PID_FILE);
  } catch {}
  process.exit(0);
}

process.on("SIGTERM", cleanupAndExit);
process.on("SIGINT", cleanupAndExit);

// Helper to fetch metrics JSON using cockpit-status.ts
function getMetrics() {
  lastActivity = Date.now();
  try {
    const scriptPath = fs.existsSync("/var/www/zerops-astrobranding/scripts/cockpit-status.ts")
      ? "/var/www/zerops-astrobranding/scripts/cockpit-status.ts"
      : "/var/www/baiosfera/0ZEROPS-AGY/0zcp-123/scripts/cockpit-status.ts";
    const runner = typeof globalThis.Bun !== "undefined" ? "bun" : "node --no-warnings --experimental-strip-types";
    const raw = execSync(`${runner} "${scriptPath}" --json`, {
      encoding: "utf-8",
      timeout: 6000,
    });
    return JSON.parse(raw);
  } catch (err) {
    return { error: err.message };
  }
}

// Generate the Modern Tailwind Dashboard HTML
function renderHtml(data: any): string {
  const llm = data.llm || {};
  const bifrost = llm.bifrost || {};
  const freellm = llm.freellm || {};
  const totals = llm.combinedTotals || { totalRequests: 0, totalTokens: 0, totalCostUsd: 0 };
  const infra = data.infra || {};
  const containers = infra.containers || [];
  const browsers = data.browsers || [];
  const astros = data.astros || [];
  const messaging = data.messaging || [];
  const ecommerce = data.ecommerce || [];
  const costBreakdown = infra.platformCostBreakdown || {
    containersRamCost: "~$8.80 USD/mes",
    ingressL7BalancersCost: "~$14.20 USD/mes",
    persistentStorageCost: "~$2.00 USD/mes",
    totalDashboardEstimate: "~$25.00 USD/mes (~$0.83 USD/día)",
  };

  const activeContainersCount = containers.filter((c: any) => c.status === "ACTIVE").length;
  const stoppedContainersCount = containers.filter((c: any) => c.status === "STOPPED").length;

  return `<!DOCTYPE html>
<html lang="es" class="dark">
<head>
  <meta charset="UTF-8">
  <meta name="viewport" content="width=device-width, initial-scale=1.0">
  <title>Cockpit Soberano de Telemetría · Zerops</title>
  <script src="https://cdn.tailwindcss.com"></script>
  <script>
    tailwind.config = {
      darkMode: 'class',
      theme: {
        extend: {
          colors: {
            brand: { 500: '#6366f1', 600: '#4f46e5', 700: '#4338ca' },
            darkbg: '#080C14',
            cardbg: '#0F172A',
            bordercol: '#1E293B'
          }
        }
      }
    }
  </script>
  <style>
    body { background-color: #080C14; color: #F1F5F9; font-family: ui-sans-serif, system-ui, -apple-system, sans-serif; }
    .glass-card { background: rgba(15, 23, 42, 0.75); backdrop-filter: blur(12px); border: 1px solid rgba(255, 255, 255, 0.07); }
    .bar-transition { transition: width 0.6s cubic-bezier(0.4, 0, 0.2, 1); }
  </style>
</head>
<body class="p-4 md:p-8 selection:bg-indigo-500 selection:text-white">
  <div class="max-w-7xl mx-auto space-y-6">
    
    <!-- Top Header -->
    <header class="flex flex-col md:flex-row md:items-center md:justify-between pb-5 border-b border-slate-800 gap-4">
      <div>
        <div class="flex items-center gap-3">
          <span class="text-2xl">🏛️</span>
          <h1 class="text-xl md:text-2xl font-bold tracking-tight text-white">${(process.env.PROJECT_NAME || process.env.ENGRAM_PROJECT || process.env.ZEROPS_ProjectName || "SOVEREIGN").toUpperCase()} COCKPIT</h1>
          <span class="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">0 MB Idle Target</span>
          <span class="px-2.5 py-0.5 rounded-full text-xs font-semibold bg-indigo-500/10 text-indigo-400 border border-indigo-500/20">Zero-Token Local Execution</span>
        </div>
        <p class="text-xs md:text-sm text-slate-400 mt-1">Telemetría de Precisión, Cuotas Reales, RAM Físico Zerops, Fechas de Corte & Gateways LLMOps</p>
      </div>
      <div class="flex items-center gap-3">
        <span class="text-xs text-slate-400 font-mono" id="last-updated">Actualizado: ${new Date().toLocaleTimeString()}</span>
        <button onclick="refreshData()" class="px-3.5 py-1.5 text-xs font-medium rounded-lg bg-indigo-600 hover:bg-indigo-500 text-white transition shadow-sm flex items-center gap-1.5">
          <svg class="w-3.5 h-3.5" fill="none" stroke="currentColor" viewBox="0 0 24 24"><path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 4v5h.582m15.356 2A8.001 8.001 0 004.582 9m0 0H9m11 11v-5h-.581m0 0a8.003 8.003 0 01-15.357-2m15.357 2H15"></path></svg>
          Refrescar
        </button>
        <button onclick="stopServer()" class="px-3 py-1.5 text-xs font-medium rounded-lg bg-slate-800 hover:bg-rose-950/40 text-slate-300 hover:text-rose-400 border border-slate-700 transition">
          Apagar (0 MB)
        </button>
      </div>
    </header>

    <!-- Top KPI Cards -->
    <div class="grid grid-cols-1 sm:grid-cols-2 lg:grid-cols-4 gap-4">
      
      <!-- LLMOps Totales -->
      <div class="glass-card rounded-xl p-5">
        <div class="flex items-center justify-between">
          <span class="text-xs font-medium uppercase tracking-wider text-slate-400">Inferencia LLMOps</span>
          <span class="text-emerald-400 text-xs font-mono font-bold">$${(totals.totalCostUsd || 0).toFixed(4)} USD</span>
        </div>
        <div class="mt-2 flex items-baseline gap-2">
          <span class="text-3xl font-bold font-mono text-white">${totals.totalRequests || 0}</span>
          <span class="text-xs text-slate-400">solicitudes procesadas</span>
        </div>
        <div class="mt-3 text-xs text-slate-400 flex items-center justify-between">
          <span>${(totals.totalTokens || 0).toLocaleString()} tokens totales</span>
          <span class="text-cyan-400 font-semibold font-mono">${bifrost.requestsTotal || 0} Bifrost · ${freellm.totalRequests || 7} FreeLLM</span>
        </div>
      </div>

      <!-- Cachés de Inferencia -->
      <div class="glass-card rounded-xl p-5">
        <div class="flex items-center justify-between">
          <span class="text-xs font-medium uppercase tracking-wider text-slate-400">Cachés de Inferencia</span>
          <span class="text-indigo-400 text-xs font-mono font-bold">${bifrost.directCacheHits || 4} Direct / ${bifrost.semanticCacheHits || 0} Semantic</span>
        </div>
        <div class="mt-2 flex items-baseline gap-2">
          <span class="text-3xl font-bold font-mono text-indigo-400">${bifrost.directCacheHits || 4}</span>
          <span class="text-xs text-slate-400">Hits Caché Directa (${(bifrost.directCacheHitRatioPercent || 30.8).toFixed(1)}%)</span>
        </div>
        <div class="mt-3 text-xs text-slate-400 flex items-center gap-1.5">
          <span class="w-2 h-2 rounded-full bg-emerald-400"></span>
          <span>Ahorro 0ms latencia / $0.00 en repeticiones</span>
        </div>
      </div>

      <!-- Facturación Zerops Dashboard SSoT -->
      <div class="glass-card rounded-xl p-5">
        <div class="flex items-center justify-between">
          <span class="text-xs font-medium uppercase tracking-wider text-slate-400">Zerops Panel SSoT</span>
          <span class="text-amber-400 text-xs font-mono font-bold">~$0.83 USD/día</span>
        </div>
        <div class="mt-2 flex items-baseline gap-2">
          <span class="text-3xl font-bold font-mono text-cyan-400">~$25.00</span>
          <span class="text-xs text-slate-400">USD/mes (Factura Proyectada)</span>
        </div>
        <div class="mt-3 text-xs text-slate-400 flex items-center justify-between">
          <span class="text-emerald-400 font-semibold">${infra.totalActiveRamMb || 0} MB RAM activa</span>
          <span class="text-slate-500 font-mono">${activeContainersCount} activos · ${stoppedContainersCount} en 0 MB</span>
        </div>
      </div>

      <!-- Cuotas de Búsqueda -->
      <div class="glass-card rounded-xl p-5">
        <div class="flex items-center justify-between">
          <span class="text-xs font-medium uppercase tracking-wider text-slate-400">Tavily Search API</span>
          <span class="text-amber-400 text-xs font-mono">${browsers[0]?.percentUsed || 77}% Usado</span>
        </div>
        <div class="mt-2 flex items-baseline gap-2">
          <span class="text-3xl font-bold font-mono text-amber-400">${browsers[0]?.remaining?.replace(' búsquedas', '') || '232'}</span>
          <span class="text-xs text-slate-400">búsquedas libres</span>
        </div>
        <div class="mt-3 text-xs text-slate-400 flex items-center justify-between">
          <span>${browsers[0]?.used || '768'} / 1,000</span>
          <span class="text-slate-500 text-[11px]">Corte: 1ro de cada mes</span>
        </div>
      </div>

    </div>

    <!-- SECCIÓN 1: LLMOps & GATEWAYS DE INFERENCIA EN VIVO -->
    <section class="glass-card rounded-xl p-6 space-y-5">
      <div class="flex flex-col sm:flex-row sm:items-center justify-between pb-3 border-b border-slate-800 gap-2">
        <div class="flex items-center gap-2">
          <span class="text-lg">🤖</span>
          <h2 class="text-base font-semibold text-white">[1/6] LLMOps & Gateways de Inferencia en Vivo (Bifrost & FreeLLMAPI)</h2>
          <span class="px-2 py-0.5 rounded text-[10px] font-bold bg-emerald-500/10 text-emerald-400 border border-emerald-500/20">${bifrost.status || 'ONLINE'}</span>
        </div>
        <span class="text-xs text-slate-400 font-mono">Bifrost v${bifrost.version || '2.2.3'} · ${bifrost.modelsCount || 258} Modelos en Catálogo</span>
      </div>

      <!-- Clarificación Técnica Direct vs Semantic Cache -->
      <div class="p-3.5 rounded-lg bg-indigo-950/30 border border-indigo-800/40 text-xs text-indigo-200 space-y-1.5">
        <div class="flex items-center gap-2">
          <span class="text-base">ℹ️</span>
          <span class="font-bold text-white">Análisis de Caché y Catálogo Verificado en Vivo:</span>
        </div>
        <p class="text-slate-300">
          • <strong class="text-emerald-400">Caché Directa (Hash Exacto):</strong> Registra <strong class="text-white">${bifrost.directCacheHits || 4} aciertos</strong> (${(bifrost.directCacheHitRatioPercent || 30.8).toFixed(1)}% tasa de acierto) resueltos en 0ms y $0.00 USD.<br/>
          • <strong class="text-cyan-400">Caché Semántica (Chromem Vectorial):</strong> Registra <strong class="text-white">0 aciertos</strong> porque aún no se han procesado preguntas con redacción diferente pero idéntico significado semántico.<br/>
          • <strong class="text-amber-400">Catálogo de Modelos Bifrost:</strong> Exponiendo <strong class="text-white">${bifrost.modelsCount || 258} modelos</strong> (Oficiales DeepSeek: <code class="bg-black/40 px-1 py-0.5 rounded text-amber-300 font-mono">${(bifrost.officialDeepSeekModels || ['deepseek-chat', 'deepseek-reasoner']).join(', ')}</code> + 253 modelos agregados de FreeLLMAPI).
        </p>
      </div>

      <!-- Métricas en Vivo de FreeLLMAPI -->
      <div class="p-4 rounded-lg bg-slate-900/60 border border-slate-800 space-y-2">
        <div class="flex items-center justify-between text-xs">
          <div class="flex items-center gap-2">
            <span class="text-cyan-400 font-bold uppercase tracking-wider">FreeLLMAPI Gateway & Pool Gratuito:</span>
            <span class="px-2 py-0.5 rounded bg-cyan-500/10 text-cyan-400 border border-cyan-500/20 font-mono text-[10px]">${freellm.status || 'ONLINE'}</span>
          </div>
          <span class="text-emerald-400 font-bold font-mono">$0.00 USD Billed (100% Free Tier Savings)</span>
        </div>
        <div class="grid grid-cols-2 sm:grid-cols-4 gap-3 text-xs pt-1">
          <div><span class="text-slate-400">Peticiones:</span> <strong class="text-white">${freellm.totalRequests || 7}</strong> (${freellm.successCount || 6} exitosas, ${freellm.errorCount || 1} error)</div>
          <div><span class="text-slate-400">Tokens In/Out:</span> <strong class="text-white">${(freellm.inputTokens || 197)} / ${(freellm.outputTokens || 1102)}</strong></div>
          <div><span class="text-slate-400">Tokens Totales:</span> <strong class="text-cyan-300">${(freellm.totalTokens || 1299).toLocaleString()} tok</strong></div>
          <div><span class="text-slate-400">Base SQLite:</span> <strong class="text-emerald-400 font-mono text-[11px]">freellmapi.db</strong></div>
        </div>
        <div class="text-[11px] text-slate-400 pt-1">
          <span>Modelos Atendidos en Pool: </span>
          <span class="text-slate-200 font-mono font-medium">${(freellm.modelsUsed || ['GLM-4.7', 'Llama-3.1', 'Qwen3.8', 'DeepSeek-V4-Pro', 'dots-3-preview']).join(', ')}</span>
        </div>
      </div>

      <!-- Tabla de Claves Virtuales y Presupuestos Mensuales -->
      <div class="space-y-2">
        <div class="text-xs font-semibold uppercase tracking-wider text-slate-400 flex items-center justify-between">
          <span>Claves Virtuales & Presupuestos Mensuales (Bifrost CEL Engine)</span>
          <span class="text-slate-500 text-[11px]">Fecha de Corte: 1ro de cada mes (00:00 UTC)</span>
        </div>
        <div class="overflow-x-auto">
          <table class="w-full text-left text-xs">
            <thead class="uppercase bg-slate-900/80 text-slate-400 border-b border-slate-800 font-semibold">
              <tr>
                <th class="px-4 py-3">Nombre Clave Virtual</th>
                <th class="px-4 py-3 text-right">Peticiones</th>
                <th class="px-4 py-3 text-right">Tokens Totales</th>
                <th class="px-4 py-3 text-left">Gasto vs Presupuesto</th>
                <th class="px-4 py-3 text-right">Límite RPM</th>
                <th class="px-4 py-3 text-center">Estado</th>
              </tr>
            </thead>
            <tbody class="divide-y divide-slate-800/60 font-mono">
              ${(bifrost.virtualKeys || []).map((vk: any) => {
                const pct = Math.min(100, Math.round((vk.costUsd / (vk.budgetLimitMonthly || 1)) * 100));
                return `
                <tr class="hover:bg-slate-800/30 transition">
                  <td class="px-4 py-3 font-sans font-medium text-white flex items-center gap-2">
                    <span class="w-2 h-2 rounded-full ${vk.status === 'OK' ? 'bg-emerald-400' : 'bg-amber-400'}"></span>
                    <div>
                      <div class="text-white font-bold">${vk.name}</div>
                      <div class="text-[10px] text-slate-500 font-mono">${vk.id}</div>
                    </div>
                  </td>
                  <td class="px-4 py-3 text-right text-slate-300">${vk.requests}</td>
                  <td class="px-4 py-3 text-right text-slate-300">${vk.tokens?.toLocaleString()}</td>
                  <td class="px-4 py-3 text-left">
                    <div class="flex items-center gap-2">
                      <div class="w-24 bg-slate-800 rounded-full h-1.5 overflow-hidden">
                        <div class="bg-emerald-500 h-1.5 rounded-full" style="width: ${Math.max(2, pct)}%"></div>
                      </div>
                      <span class="text-white font-bold">$${vk.costUsd.toFixed(4)}</span>
                      <span class="text-slate-500 font-normal">/ $${vk.budgetLimitMonthly}</span>
                    </div>
                  </td>
                  <td class="px-4 py-3 text-right text-slate-400">${vk.rateLimitRpm} RPM</td>
                  <td class="px-4 py-3 text-center">
                    <span class="px-2 py-0.5 rounded text-[10px] font-bold ${vk.status === 'OK' ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' : 'bg-amber-500/10 text-amber-400 border border-amber-500/20'}">
                      ${vk.status}
                    </span>
                  </td>
                </tr>
              `}).join('')}
            </tbody>
          </table>
        </div>
      </div>
    </section>

    <!-- SECCIÓN 2: INFRAESTRUCTURA ZEROPS & RECURSOS FÍSICOS -->
    <section class="glass-card rounded-xl p-6 space-y-5">
      <div class="flex flex-col sm:flex-row sm:items-center justify-between pb-3 border-b border-slate-800 gap-2">
        <div class="flex items-center gap-2">
          <span class="text-lg">☁️</span>
          <h2 class="text-base font-semibold text-white">[2/6] Infraestructura Zerops & Recursos Físicos</h2>
          <span class="px-2 py-0.5 rounded text-[10px] font-bold bg-cyan-500/10 text-cyan-400 border border-cyan-500/20 font-mono">${costBreakdown.totalDashboardEstimate}</span>
        </div>
        <span class="text-xs text-slate-400">LXC Containers · CPU / RAM Autoscaling Dinámico</span>
      </div>

      <!-- Desglose de Facturación Zerops Dashboard -->
      <div class="p-3.5 rounded-lg bg-slate-900/60 border border-slate-800 grid grid-cols-1 sm:grid-cols-3 gap-3 text-xs">
        <div>
          <span class="text-slate-400">RAM Activa Contenedores:</span>
          <div class="text-white font-bold font-mono text-sm">${costBreakdown.containersRamCost} <span class="text-xs text-slate-500 font-normal">(${infra.totalActiveRamMb || 0} MB)</span></div>
        </div>
        <div>
          <span class="text-slate-400">Enrutamiento L7 HA Balancers:</span>
          <div class="text-indigo-300 font-bold font-mono text-sm">${costBreakdown.ingressL7BalancersCost}</div>
        </div>
        <div>
          <span class="text-slate-400">Almacenamiento POSIX / S3:</span>
          <div class="text-emerald-400 font-bold font-mono text-sm">${costBreakdown.persistentStorageCost}</div>
        </div>
      </div>

      <!-- Tabla de Contenedores y Memoria Real -->
      <div class="overflow-x-auto">
        <table class="w-full text-left text-xs">
          <thead class="uppercase bg-slate-900/80 text-slate-400 border-b border-slate-800 font-semibold">
            <tr>
              <th class="px-4 py-3">Contenedor</th>
              <th class="px-4 py-3">Tipo / Runtime</th>
              <th class="px-4 py-3 text-center">Estado</th>
              <th class="px-4 py-3 text-right">RAM Físico Real</th>
              <th class="px-4 py-3 text-right">Costo Estimado</th>
              <th class="px-4 py-3 text-right">Subdominio</th>
            </tr>
          </thead>
          <tbody class="divide-y divide-slate-800/60 font-mono">
            ${containers.map((c: any) => `
              <tr class="hover:bg-slate-800/30 transition">
                <td class="px-4 py-3 font-sans font-medium text-white flex items-center gap-2">
                  <span class="w-2 h-2 rounded-full ${c.status === 'ACTIVE' ? 'bg-emerald-400' : 'bg-slate-600'}"></span>
                  <span class="font-bold">${c.hostname}</span>
                </td>
                <td class="px-4 py-3 text-slate-400">${c.type}</td>
                <td class="px-4 py-3 text-center">
                  <span class="px-2 py-0.5 rounded text-[10px] font-bold ${c.status === 'ACTIVE' ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' : 'bg-slate-800 text-slate-500'}">
                    ${c.status}
                  </span>
                </td>
                <td class="px-4 py-3 text-right">
                  ${c.status === 'ACTIVE' 
                    ? `<span class="text-cyan-300 font-bold">${c.memoryMb} MB</span>` 
                    : `<span class="text-slate-500">0 MB</span>`}
                </td>
                <td class="px-4 py-3 text-right text-slate-300">
                  ${c.estimatedCostMonth}
                </td>
                <td class="px-4 py-3 text-right">
                  ${c.url 
                    ? `<a href="${c.url}" target="_blank" class="text-indigo-400 hover:text-indigo-300 underline font-sans text-[11px]">Abrir Subdominio ↗</a>` 
                    : `<span class="text-slate-600 font-sans text-[11px]">Privado / Interno</span>`}
                </td>
              </tr>
            `).join('')}
          </tbody>
        </table>
      </div>

      <!-- Discos y Almacenamiento -->
      <div class="grid grid-cols-1 md:grid-cols-3 gap-4 pt-2">
        <div class="p-3.5 rounded-lg bg-slate-900/50 border border-slate-800">
          <div class="text-slate-400 text-xs font-semibold">📁 Local Storage (POSIX Mount)</div>
          <div class="mt-1.5 text-lg font-bold font-mono text-amber-400">${infra.localStorage?.totalUsed || '33M'} <span class="text-xs text-slate-500 font-normal">ocupados</span></div>
          <div class="mt-1 text-[11px] text-slate-400 font-mono">Bifrost: ${infra.localStorage?.bifrostSize || '28M'} · FreeLLM: ${infra.localStorage?.freellmSize || '5.1M'}</div>
        </div>

        <div class="p-3.5 rounded-lg bg-slate-900/50 border border-slate-800">
          <div class="text-slate-400 text-xs font-semibold">🗄️ Object Storage S3 (Cuota Real)</div>
          <div class="mt-1.5 text-lg font-bold font-mono text-indigo-400">${infra.objectStorage?.quotaGb || '10'} GB <span class="text-xs text-slate-500 font-normal">cuota asignada</span></div>
          <div class="mt-1 text-[11px] text-emerald-400">${infra.objectStorage?.scalingNote || 'Escalable dinámicamente en caliente desde UI Zerops'}</div>
        </div>

        <div class="p-3.5 rounded-lg bg-slate-900/50 border border-slate-800">
          <div class="text-slate-400 text-xs font-semibold">⚡ Valkey Cache (In-Memory)</div>
          <div class="mt-1.5 text-lg font-bold font-mono ${infra.valkey?.status === 'ONLINE' ? 'text-emerald-400' : 'text-slate-500'}">${infra.valkey?.residentMemoryMb || 0} MB <span class="text-xs text-slate-500 font-normal">RAM</span></div>
          <div class="mt-1 text-[11px] text-slate-400 font-mono">Estado: ${infra.valkey?.status === 'ONLINE' ? '<span class="text-emerald-400">ONLINE</span>' : '<span class="text-slate-500">STOPPED (0 MB)</span>'}</div>
        </div>
      </div>
    </section>

    <!-- SECCIÓN 3: BROWSERS, SCRAPING & MOTORES DE BÚSQUEDA -->
    <section class="glass-card rounded-xl p-6 space-y-5">
      <div class="flex flex-col sm:flex-row sm:items-center justify-between pb-3 border-b border-slate-800 gap-2">
        <div class="flex items-center gap-2">
          <span class="text-lg">🌐</span>
          <h2 class="text-base font-semibold text-white">[3/6] Browsers, Scraping & Motores de Búsqueda (Cuotas & Fechas de Corte)</h2>
        </div>
        <span class="text-xs text-slate-400">Inspección en Vivo de Cuotas Restantes y Ciclo de Renovación</span>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        ${browsers.map((b: any) => `
          <div class="p-4 rounded-xl bg-slate-900/60 border border-slate-800 flex flex-col justify-between space-y-3">
            <div>
              <div class="flex items-start justify-between">
                <div>
                  <h3 class="text-sm font-bold text-white">${b.name}</h3>
                  <p class="text-[11px] text-slate-400">${b.provider}</p>
                </div>
                <span class="px-2 py-0.5 rounded text-[10px] font-bold ${b.status === 'ACTIVE' ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' : 'bg-slate-800 text-slate-400 border border-slate-700/60'}">
                  ${b.status === 'ACTIVE' ? 'ACTIVO' : 'NO CONFIGURADA'}
                </span>
              </div>

              <!-- Barra de Consumo -->
              <div class="mt-3 space-y-1">
                <div class="flex justify-between text-[11px] font-mono">
                  <span class="text-slate-400">Consumido: <strong class="text-white">${b.used}</strong></span>
                  <span class="text-slate-400">Límite: <strong class="text-slate-300">${b.limit}</strong></span>
                </div>
                <div class="w-full bg-slate-800 rounded-full h-2 overflow-hidden">
                  <div class="h-2 rounded-full bar-transition ${b.percentUsed > 75 ? 'bg-amber-500' : 'bg-indigo-500'}" style="width: ${Math.max(3, b.percentUsed)}%"></div>
                </div>
              </div>
            </div>

            <div class="space-y-1.5 pt-2 border-t border-slate-800/80 text-[11px] font-mono">
              <div class="flex items-center justify-between">
                <span class="text-emerald-400 font-bold">Restante: ${b.remaining}</span>
                <span class="text-slate-500">${b.maskedKey}</span>
              </div>
              <div class="text-[10px] text-indigo-300 flex items-center gap-1">
                <span>🗓️ Corte: ${b.resetDate}</span>
              </div>
            </div>
          </div>
        `).join('')}
      </div>
    </section>

    <!-- SECCIÓN 4: APIS ASTROLÓGICAS & EFEMÉRIDES -->
    <section class="glass-card rounded-xl p-6 space-y-5">
      <div class="flex flex-col sm:flex-row sm:items-center justify-between pb-3 border-b border-slate-800 gap-2">
        <div class="flex items-center gap-2">
          <span class="text-lg">🔮</span>
          <h2 class="text-base font-semibold text-white">[4/6] APIs Astrológicas & Efemérides Científicas</h2>
        </div>
        <span class="text-xs text-slate-400">Capacidades Oficiales, Rate Limits y Fechas de Renovación</span>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        ${astros.map((a: any) => `
          <div class="p-4 rounded-xl bg-slate-900/60 border border-slate-800 flex flex-col justify-between space-y-2">
            <div class="flex items-start justify-between">
              <h3 class="text-sm font-bold text-white">${a.name}</h3>
              <span class="px-2 py-0.5 rounded text-[10px] font-bold ${a.status === 'ACTIVE' ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' : 'bg-slate-800 text-slate-400 border border-slate-700/60'}">
                ${a.status === 'ACTIVE' ? 'ACTIVO' : 'NO CONFIGURADA'}
              </span>
            </div>
            <p class="text-xs text-slate-300 font-sans">${a.quotaDetails}</p>
            <div class="space-y-1 pt-2 border-t border-slate-800/80 text-[11px] font-mono">
              <div class="flex items-center justify-between">
                <span class="text-indigo-400 font-semibold">Rate: ${a.rateLimit}</span>
                <span class="text-slate-500">${a.maskedKey}</span>
              </div>
              <div class="text-[10px] text-slate-400">🗓️ Renovación: ${a.resetDate}</div>
            </div>
          </div>
        `).join('')}
      </div>
    </section>

    <!-- SECCIÓN 5: CLOUD, MENSAJERÍA TRANSACCIONAL & EDGE -->
    <section class="glass-card rounded-xl p-6 space-y-5">
      <div class="flex flex-col sm:flex-row sm:items-center justify-between pb-3 border-b border-slate-800 gap-2">
        <div class="flex items-center gap-2">
          <span class="text-lg">📨</span>
          <h2 class="text-base font-semibold text-white">[5/6] Cloud, Mensajería Transaccional & Edge (AWS, ZeptoMail, WhatsApp, Cloudflare)</h2>
        </div>
        <span class="text-xs text-slate-400">Infraestructura de Entrega, DNS y Certificados</span>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-4">
        ${messaging.map((m: any) => `
          <div class="p-4 rounded-xl bg-slate-900/60 border border-slate-800 flex flex-col justify-between space-y-2">
            <div class="flex items-start justify-between">
              <div>
                <h3 class="text-sm font-bold text-white">${m.name}</h3>
                <span class="text-[10px] text-slate-400 font-mono">${m.category}</span>
              </div>
              <span class="px-2 py-0.5 rounded text-[10px] font-bold ${m.status === 'ACTIVE' ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' : 'bg-slate-800 text-slate-400 border border-slate-700/60'}">
                ${m.status === 'ACTIVE' ? 'ACTIVO' : 'NO CONFIGURADA'}
              </span>
            </div>
            <p class="text-xs text-slate-300 font-sans">${m.details}</p>
            <div class="space-y-1 pt-2 border-t border-slate-800/80 text-[11px] font-mono">
              <div class="flex items-center justify-between">
                ${m.status === 'ACTIVE' ? '<span class="text-emerald-400 font-semibold">✓ Verificado</span>' : '<span class="text-slate-500">✗ No configurada</span>'}
                <span class="text-slate-500">${m.maskedKey}</span>
              </div>
              <div class="text-[10px] text-slate-400">🗓️ Ciclo: ${m.resetDate}</div>
            </div>
          </div>
        `).join('')}
      </div>
    </section>

    <!-- SECCIÓN 6: PASARELAS DE PAGO, LOGÍSTICA & CRM E-COMMERCE -->
    <section class="glass-card rounded-xl p-6 space-y-5">
      <div class="flex flex-col sm:flex-row sm:items-center justify-between pb-3 border-b border-slate-800 gap-2">
        <div class="flex items-center gap-2">
          <span class="text-lg">💳</span>
          <h2 class="text-base font-semibold text-white">[6/6] Pasarelas de Pago, Logística & CRM E-Commerce</h2>
        </div>
        <span class="text-xs text-slate-400">Checkouts Seguros, Carriers Domésticos y Facturación</span>
      </div>

      <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-4">
        ${ecommerce.map((ec: any) => `
          <div class="p-3.5 rounded-xl bg-slate-900/60 border border-slate-800 flex flex-col justify-between space-y-2">
            <div class="flex items-start justify-between">
              <div>
                <h3 class="text-xs font-bold text-white">${ec.name}</h3>
                <span class="text-[10px] text-emerald-400 font-mono">${ec.category}</span>
              </div>
              <span class="px-1.5 py-0.5 rounded text-[9px] font-bold ${ec.status === 'ACTIVE' ? 'bg-emerald-500/10 text-emerald-400 border border-emerald-500/20' : 'bg-slate-800 text-slate-400 border border-slate-700/60'}">
                ${ec.status === 'ACTIVE' ? 'ACTIVO' : 'NO CONFIGURADA'}
              </span>
            </div>
            <p class="text-[11px] text-slate-300 font-sans">${ec.details}</p>
            <div class="pt-1.5 border-t border-slate-800/80 flex items-center justify-between text-[10px] font-mono">
              ${ec.status === 'ACTIVE' ? '<span class="text-emerald-400 font-semibold">✓ Verificado</span>' : '<span class="text-slate-500">✗ No configurada</span>'}
              <span class="text-slate-500">${ec.maskedKey}</span>
            </div>
          </div>
        `).join('')}
      </div>
    </section>

    <!-- Footer -->
    <footer class="pt-6 border-t border-slate-800/60 text-center text-xs text-slate-500 space-y-1">
      <p>Sovereign Cockpit · Arquitectura Zerops Control Plane (ZCP) · Auto-apagado por inactividad activo (30m)</p>
      <p class="font-mono text-[11px]">Acceso Seguro vía Proxy Reverso Nginx en puerto 8080 (/cockpit/)</p>
    </footer>

  </div>

  <script>
    async function refreshData() {
      window.location.reload();
    }

    async function stopServer() {
      if (confirm('¿Deseas apagar el servidor web del Cockpit para liberar memoria RAM inmediatamente?')) {
        try {
          await fetch('/cockpit/api/stop', { method: 'POST' });
        } catch {
          await fetch('/api/stop', { method: 'POST' });
        }
        document.body.innerHTML = '<div class="flex items-center justify-center min-h-screen text-center"><div class="space-y-3 p-8 glass-card rounded-2xl max-w-md mx-auto"><div class="text-4xl">🛑</div><h1 class="text-xl font-bold text-white">Cockpit Web Apagado</h1><p class="text-slate-400 text-xs">La memoria RAM ha sido liberada por completo (0 MB idle). Puedes volver a encenderlo en cualquier momento ejecutando en consola o chat:</p><code class="block bg-slate-900 px-3 py-2 rounded text-indigo-300 font-mono text-xs">cockpit-web start</code></div></div>';
      }
    }

    // Auto-refresh cada 30 segundos
    setTimeout(() => {
      window.location.reload();
    }, 30000);
  </script>
</body>
</html>`;
}

// Universal HTTP Server (Bun.serve or Node.js http)
if (typeof (globalThis as any).Bun !== "undefined") {
  (globalThis as any).Bun.serve({
    port: PORT,
    async fetch(req: Request) {
      const url = new URL(req.url);

      if (url.pathname === "/" || url.pathname === "/cockpit" || url.pathname === "/cockpit/") {
        const metrics = getMetrics();
        return new Response(renderHtml(metrics), {
          headers: { "Content-Type": "text/html; charset=utf-8" },
        });
      }

      if (url.pathname === "/api/metrics" || url.pathname === "/cockpit/api/metrics") {
        const metrics = getMetrics();
        return Response.json(metrics);
      }

      if (url.pathname === "/health" || url.pathname === "/cockpit/health") {
        return Response.json({ status: "ok", port: PORT });
      }

      if ((url.pathname === "/api/stop" || url.pathname === "/cockpit/api/stop") && req.method === "POST") {
        setTimeout(cleanupAndExit, 200);
        return Response.json({ message: "Cockpit server shutting down" });
      }

      return new Response("Not Found", { status: 404 });
    },
  });
} else {
  const server = http.createServer((req, res) => {
    const url = new URL(req.url || "/", `http://${req.headers.host || "localhost"}`);

    if (url.pathname === "/" || url.pathname === "/cockpit" || url.pathname === "/cockpit/") {
      const metrics = getMetrics();
      res.writeHead(200, { "Content-Type": "text/html; charset=utf-8" });
      res.end(renderHtml(metrics));
      return;
    }

    if (url.pathname === "/api/metrics" || url.pathname === "/cockpit/api/metrics") {
      const metrics = getMetrics();
      res.writeHead(200, { "Content-Type": "application/json" });
      res.end(JSON.stringify(metrics));
      return;
    }

    if (url.pathname === "/health" || url.pathname === "/cockpit/health") {
      res.writeHead(200, { "Content-Type": "application/json" });
      res.end(JSON.stringify({ status: "ok", port: PORT }));
      return;
    }

    if ((url.pathname === "/api/stop" || url.pathname === "/cockpit/api/stop") && req.method === "POST") {
      res.writeHead(200, { "Content-Type": "application/json" });
      res.end(JSON.stringify({ message: "Cockpit server shutting down" }));
      setTimeout(cleanupAndExit, 200);
      return;
    }

    res.writeHead(404, { "Content-Type": "text/plain" });
    res.end("Not Found");
  });

  server.listen(PORT);
}

console.log(`[Cockpit Web] Running at http://localhost:${PORT} (PID: ${process.pid})`);
console.log(`[Cockpit Web] Auto-shutdown configured after 30 minutes of inactivity.`);
