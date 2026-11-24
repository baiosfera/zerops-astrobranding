#!/usr/bin/env bun
import { existsSync, copyFileSync } from "node:fs";
import { execSync } from "node:child_process";
import { resolve } from "node:path";

console.log("==================================================================");
console.log("   🌟 Zerops AstroBranding Sovereign Monorepo Bootstrapper 🌟    ");
console.log("==================================================================\n");

const ROOT_DIR = resolve(import.meta.dir, "..");

function runStep(name, cmd) {
  console.log(`==> [Step] ${name}...`);
  try {
    execSync(cmd, { cwd: ROOT_DIR, stdio: "inherit" });
    console.log(`✅ ${name} completed.\n`);
  } catch (err) {
    console.error(`❌ ${name} failed:`, err.message);
    process.exit(1);
  }
}

// 1. Environment Configuration
const envPath = resolve(ROOT_DIR, ".env");
const envExamplePath = resolve(ROOT_DIR, ".env.example");

if (!existsSync(envPath) && existsSync(envExamplePath)) {
  console.log("==> Copying .env.example -> .env");
  copyFileSync(envExamplePath, envPath);
  console.log("✅ .env file initialized.\n");
} else {
  console.log("ℹ️  .env file already exists.\n");
}

// 2. Install Workspace Dependencies
runStep("Installing Dependencies via Bun", "bun install");

// 3. Validate SSoT Parity & Architecture Guardian Check
if (existsSync("/var/www/.bin/ssot-parity-check")) {
  runStep("Validating SSoT Parity", "ssot-parity-check --allow-unpushed");
}
runStep("Enforcing Architecture Boundaries", "bun scripts/architecture-check.mjs");

// 5. Build Unified Fullstack App (Astro 5 SSR + React 19 + Hono)
runStep("Building Fullstack AstroBranding App", "bun --filter @astrobranding/astrobranding build");

console.log("==================================================================");
console.log("🎉 Bootstrap complete! All packages and apps built with exit code 0.");
console.log("");
console.log("Available commands:");
console.log("  • bun run dev           -> Start unified fullstack dev server (port 3000)");
console.log("  • bun run build         -> Build all workspaces");
console.log("  • bun run check:arch    -> Run Architecture Guardian sensor");
console.log("  • bun run start         -> Start production SSR server");
console.log("==================================================================\n");
