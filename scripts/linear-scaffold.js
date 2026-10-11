#!/usr/bin/env node
/**
 * Linear Scaffold Sovereign Automation (Project-as-Code)
 * Reads templates/linear_template.json and provisions an agnostic grouped project in Linear.
 *
 * Usage:
 *   node scripts/linear-scaffold.ts <APP_IDENTITY> "<PROJECT_NAME>" [--dry-run] [--profile <minimal|content|ecommerce|full-mesh>]
 */

const fs = require("fs");
const path = require("path");
const { execSync } = require("child_process");

const args = process.argv.slice(2);
if (args.length < 2) {
  console.log("Usage: node scripts/linear-scaffold.ts <APP_IDENTITY> \"<PROJECT_NAME>\" [--dry-run] [--profile <minimal|content|ecommerce|full-mesh>]");
  process.exit(1);
}

const appIdentity = args[0];
const projectName = args[1];
const isDryRun = args.includes("--dry-run");

let profile = "full-mesh";
const profIdx = args.indexOf("--profile");
if (profIdx !== -1 && args[profIdx + 1]) {
  profile = args[profIdx + 1].toLowerCase();
}

const templateCandidates = [
  path.join(process.cwd(), "templates/linear_template.json"),
  path.join(process.cwd(), "artifacts/templates/linear_template.json"),
  "/var/www/artifacts/templates/linear_template.json",
  "/var/www/zerops-astrobranding/templates/linear_template.json",
  "/var/www/baiosfera/0ZEROPS-AGY/0zcp-123/templates/linear_template.json"
];

let templatePath = templateCandidates.find((p) => fs.existsSync(p));
if (!templatePath) {
  console.error("❌ Error: linear_template.json not found in candidate paths.");
  process.exit(1);
}

const templateData = JSON.parse(fs.readFileSync(templatePath, "utf-8"));
const allIssues = templateData.issues || [];

const profileMap = {
  minimal: ["BAI-0", "BAI-1", "BAI-3", "BAI-6"],
  content: ["BAI-0", "BAI-1", "BAI-2", "BAI-3", "BAI-6"],
  ecommerce: ["BAI-0", "BAI-1", "BAI-2", "BAI-3", "BAI-4", "BAI-6"],
  "full-mesh": ["BAI-0", "BAI-1", "BAI-2", "BAI-3", "BAI-4", "BAI-5", "BAI-6"]
};

const allowedKeys = new Set(profileMap[profile] || profileMap["full-mesh"]);
const filteredIssues = allIssues.filter((iss) => allowedKeys.has(iss.key));

console.log(`\n🚀 [Linear Scaffold] App Identity: ${appIdentity}`);
console.log(`📋 [Linear Scaffold] Project Name: \"${projectName}\"`);
console.log(`🎯 [Linear Scaffold] Profile: ${profile} (${filteredIssues.length} issues selected)`);
console.log(`⚙️ [Linear Scaffold] Mode: ${isDryRun ? "DRY-RUN (Simulación)" : "LIVE PROVISIONING"}\n`);

if (isDryRun) {
  console.log("--- SIMULATED ISSUES ---");
  for (const iss of filteredIssues) {
    const title = iss.title.replace("[Brand]", `[${appIdentity}]`);
    console.log(`• [${iss.key}] ${title}`);
    console.log(`  Milestone: ${iss.milestone}`);
    console.log(`  DoD: ${iss.definitionOfDone ? iss.definitionOfDone.length : 0} checks`);
  }
  console.log("\n✅ Dry-run completed successfully without mutating Linear.");
  process.exit(0);
}

console.log(`📦 Creando proyecto padre en Linear: \"${projectName}\"...`);
try {
  const createProjCmd = `linear-cli create-project \"${projectName}\" \"Linear Blueprint for ${appIdentity} (${profile} profile)\"`;
  execSync(createProjCmd, { stdio: "inherit" });
} catch (e) {
  console.error("❌ Error creando el proyecto padre:", e.message);
  process.exit(1);
}

try {
  execSync(`linear-cli set-project \"${projectName}\"`, { stdio: "inherit" });
} catch (e) {
  console.error("❌ Error fijando proyecto activo:", e.message);
  process.exit(1);
}

console.log("\n📝 Creando tareas agrupadas bajo el proyecto...");
for (const iss of filteredIssues) {
  const title = iss.title.replace("[Brand]", `[${appIdentity}]`);
  const dodText = (iss.definitionOfDone || []).map((d) => `- [ ] ${d}`).join("\n");
  const desc = `${iss.description}\n\n### Definition of Done:\n${dodText}`;
  try {
    const createCmd = `linear-cli create \"${title}\" \"${desc}\"`;
    execSync(createCmd, { stdio: "inherit" });
  } catch (err) {
    console.error(`⚠️ Error creando issue ${title}:`, err.message);
  }
}

console.log(`\n🎉 [Linear Scaffold] Proyecto \"${projectName}\" aprovisionado con éxito con ${filteredIssues.length} tareas agrupadas sin huérfanos!`);
