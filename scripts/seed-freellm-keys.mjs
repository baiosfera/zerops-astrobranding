#!/usr/bin/env node

/**
 * Universal FreeLLMAPI Multi-Account Seeder CLI
 * Usage:
 *   node scripts/seed-freellm-keys.mjs [file1.md file2.md ... | /path/to/keys-dir] [freellmapi_url]
 *
 * Agnostic quota-stacking seeder:
 * - Scans markdown credential files (.md) and env files (.env, KEY=VALUE)
 * - Ingests provider keys per account into FreeLLMAPI REST /admin/seed
 * - Writes offline fallback seed.json for cold boots without erasing existing seeds
 */

import fs from "node:fs";
import path from "node:path";

const args = process.argv.slice(2);
let targetUrl = process.env.FREELLMAPI_URL || "http://localhost:3001";
const fileCandidates = [];

// Parse CLI arguments (files, directories, or URL)
for (const arg of args) {
  if (arg.startsWith("http://") || arg.startsWith("https://")) {
    targetUrl = arg;
    continue;
  }
  if (fs.existsSync(arg)) {
    const stat = fs.statSync(arg);
    if (stat.isDirectory()) {
      const files = fs.readdirSync(arg);
      for (const f of files) {
        fileCandidates.push(path.resolve(arg, f));
      }
    } else if (stat.isFile()) {
      fileCandidates.push(path.resolve(arg));
    }
  }
}

// Fallback search locations if no files passed
if (fileCandidates.length === 0) {
  const envFiles = [process.env.KEYS_FILE, process.env.KEYS_DIR].filter(Boolean);
  for (const ef of envFiles) {
    if (fs.existsSync(ef)) {
      const stat = fs.statSync(ef);
      if (stat.isDirectory()) {
        for (const f of fs.readdirSync(ef)) {
          fileCandidates.push(path.resolve(ef, f));
        }
      } else if (stat.isFile()) {
        fileCandidates.push(path.resolve(ef));
      }
    }
  }

  const defaultLocations = [
    "/var/www/keys",
    "/var/www/keys.md",
    "/var/www/.env",
    process.env.KEYS_PATH,
    process.env.BRAND_KEYS_PATH,
    "/var/www/baiosfera/0ZEROPS-AGY/users-apis/api_keys_global",
  ].filter(Boolean);
  for (const loc of defaultLocations) {
    if (fs.existsSync(loc)) {
      const stat = fs.statSync(loc);
      if (stat.isDirectory()) {
        for (const f of fs.readdirSync(loc)) {
          fileCandidates.push(path.resolve(loc, f));
        }
      } else if (stat.isFile()) {
        fileCandidates.push(path.resolve(loc));
      }
    }
  }
}

if (fileCandidates.length === 0) {
  console.log(`[Info] No credentials files found. FreeLLMAPI will run with environment variables or existing seed.`);
  process.exit(0);
}

// Deduplicate candidate paths
const uniqueFiles = [...new Set(fileCandidates)];
console.log(`\n==> [FreeLLMAPI Seeder] Discovered ${uniqueFiles.length} credentials candidate file(s):`);
uniqueFiles.forEach((f) => console.log(`    - ${f}`));

const seedPayloadFiles = [];
const fallbackFlattenedKeys = [];

for (const fpath of uniqueFiles) {
  try {
    const raw = fs.readFileSync(fpath, "utf-8");
    const baseName = path.basename(fpath, path.extname(fpath));
    const headerMatch = raw.match(/#\s+API\s+Keys\s+[-—]\s+([^\n\r]+)/i);
    const accountLabel = headerMatch ? headerMatch[1].trim() : baseName;

    seedPayloadFiles.push({
      content: raw,
      label: accountLabel,
    });

    // Pattern 1: Parse markdown sections with ### and **Plataforma:** / **API Key:**
    const sections = raw.split(/###\s+\d+\.\s+/);
    for (const sec of sections) {
      if (!sec.trim()) continue;
      const platformMatch = sec.match(/\*\*Plataforma:\*\*\s*`([^`]+)`/i);
      const keyMatch = sec.match(/\*\*API Key:\*\*\s*`([^`]+)`/i);
      const labelMatch = sec.match(/\*\*Etiqueta:\*\*\s*`([^`]+)`/i);

      if (platformMatch && keyMatch && keyMatch[1] && !keyMatch[1].includes("YOUR_")) {
        fallbackFlattenedKeys.push({
          provider: platformMatch[1].trim().toLowerCase(),
          account: accountLabel,
          label: labelMatch ? labelMatch[1].trim() : accountLabel,
          apiKey: keyMatch[1].trim(),
        });
      }
    }

    // Pattern 2: Parse KEY=VALUE lines
    const lines = raw.split(/\r?\n/);
    for (const line of lines) {
      const trimmed = line.trim();
      if (!trimmed || trimmed.startsWith("#")) continue;
      const eqIdx = trimmed.indexOf("=");
      if (eqIdx <= 0) continue;
      const rawKey = trimmed.substring(0, eqIdx).trim();
      let rawVal = trimmed.substring(eqIdx + 1).trim();
      if ((rawVal.startsWith('"') && rawVal.endsWith('"')) || (rawVal.startsWith("'") && rawVal.endsWith("'"))) {
        rawVal = rawVal.slice(1, -1);
      }
      if (!rawVal || rawVal.includes("YOUR_") || rawVal.includes("your_")) continue;

      let provider = null;
      if (/OPENAI.*KEY/i.test(rawKey)) provider = "openai";
      else if (/ANTHROPIC.*KEY|CLAUDE.*KEY/i.test(rawKey)) provider = "anthropic";
      else if (/GEMINI.*KEY|GOOGLE.*AI.*KEY/i.test(rawKey)) provider = "gemini";
      else if (/GROQ.*KEY/i.test(rawKey)) provider = "groq";
      else if (/MISTRAL.*KEY/i.test(rawKey)) provider = "mistral";
      else if (/DEEPSEEK.*KEY/i.test(rawKey)) provider = "deepseek";
      else if (/COHERE.*KEY/i.test(rawKey)) provider = "cohere";
      else if (/PERPLEXITY.*KEY/i.test(rawKey)) provider = "perplexity";
      else if (/OPENROUTER.*KEY/i.test(rawKey)) provider = "openrouter";
      else if (/TOGETHER.*KEY/i.test(rawKey)) provider = "together";
      else if (/CEREBRAS.*KEY/i.test(rawKey)) provider = "cerebras";

      if (provider) {
        fallbackFlattenedKeys.push({
          provider,
          account: accountLabel,
          label: rawKey,
          apiKey: rawVal,
        });
      }
    }
  } catch (err) {
    console.warn(`[Warning] Failed reading ${fpath}: ${err.message}`);
  }
}

console.log(`==> Total extracted provider keys for pooling: ${fallbackFlattenedKeys.length}`);

async function seedViaRest() {
  try {
    const endpoint = `${targetUrl.replace(/\/$/, "")}/admin/seed`;
    const res = await fetch(endpoint, {
      method: "POST",
      headers: { "Content-Type": "application/json" },
      body: JSON.stringify({ files: seedPayloadFiles }),
    });

    if (res.ok) {
      const data = await res.json();
      console.log(`\n==> [Success] Seeded ${data.keysIngested || fallbackFlattenedKeys.length} keys into live FreeLLMAPI at ${endpoint}!`);
      return true;
    }
    console.warn(`[Warning] HTTP ${res.status} from FreeLLMAPI REST API at ${endpoint}.`);
  } catch (err) {
    console.warn(`[Info] Live service not reached at ${targetUrl} (${err.message}). Storing offline seed...`);
  }
  return false;
}

async function main() {
  await seedViaRest();

  // Write offline fallback seed.json
  const seedTargets = [
    "/mnt/localstorage/freellmapi/seed.json",
    path.join(process.cwd(), "apps", "freellmapi", "data", "seed.json"),
  ];

  for (const st of seedTargets) {
    try {
      const dir = path.dirname(st);
      if (!fs.existsSync(dir)) fs.mkdirSync(dir, { recursive: true });

      // If no new keys discovered and file already exists with content, do NOT overwrite with empty
      if (fallbackFlattenedKeys.length === 0 && fs.existsSync(st)) {
        try {
          const existing = JSON.parse(fs.readFileSync(st, "utf-8"));
          if (Array.isArray(existing) && existing.length > 0) {
            console.log(`==> [Offline Seed] Preserving existing ${existing.length} keys in ${st}`);
            continue;
          }
        } catch {}
      }

      fs.writeFileSync(st, JSON.stringify(fallbackFlattenedKeys, null, 2), "utf-8");
      console.log(`==> [Offline Seed] Wrote ${fallbackFlattenedKeys.length} keys to ${st}`);
    } catch {
      // Ignore write errors if path not writable in current environment
    }
  }

  console.log(`\n==> [FreeLLMAPI Seeder] Multi-account quota stacking ready.\n`);
}

main();
