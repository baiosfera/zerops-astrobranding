#!/usr/bin/env bun
// ==============================================================================
// Architecture Guardian: Deterministic Static Boundary Sensor
// Zero LLM Tokens | Bounded Execution < 100ms | 100% Deterministic
// ==============================================================================
import { existsSync } from "node:fs";
import { readdir, readFile } from "node:fs/promises";
import path from "node:path";

const targetRoot = path.resolve(process.argv[2] || ".");
let violations = 0;

function report(rule, file, message) {
  console.error(`❌ [${rule}] in ${file}:`);
  console.error(`   ${message}`);
  violations++;
}

async function getFiles(dir) {
  const dirents = await readdir(dir, { withFileTypes: true });
  const files = await Promise.all(
    dirents.map((dirent) => {
      const res = path.resolve(dir, dirent.name);
      if (dirent.isDirectory()) {
        if (dirent.name === "node_modules" || dirent.name === "dist" || dirent.name === ".astro") {
          return [];
        }
        return getFiles(res);
      }
      return res;
    })
  );
  return files.flat();
}

async function checkContractsPurity(contractsDir) {
  if (!existsSync(contractsDir)) return false;
  const contractFiles = await getFiles(contractsDir);
  const forbiddenFrameworks = ["hono", "drizzle-orm", "postgres", "react", "react-dom", "@astrojs", "bullmq"];

  for (const file of contractFiles) {
    if (!file.endsWith(".ts")) continue;
    const content = await readFile(file, "utf-8");
    for (const fw of forbiddenFrameworks) {
      if (content.includes(`from "${fw}`) || content.includes(`from '${fw}`)) {
        report(
          "contracts-framework-purity",
          path.relative(targetRoot, file),
          `@astrobranding/contracts must be 100% pure TypeScript/Zod. Found forbidden dependency '${fw}'.`
        );
      }
    }
  }
  return true;
}

async function checkDatabaseBoundaries(databaseDir) {
  if (!existsSync(databaseDir)) return false;
  const dbFiles = await getFiles(databaseDir);
  for (const file of dbFiles) {
    if (!file.endsWith(".ts")) continue;
    const content = await readFile(file, "utf-8");
    if (content.includes("from 'react'") || content.includes('from "react"')) {
      report(
        "database-no-ui",
        path.relative(targetRoot, file),
        "Database package must never import UI libraries."
      );
    }
  }
  return true;
}

async function run() {
  console.log("============================================================");
  console.log(`  🔍 Running Architecture Guardian (${targetRoot})`);
  console.log("============================================================");

  const checkedContracts = await checkContractsPurity(path.join(targetRoot, "packages/contracts/src"));
  const checkedDatabase = await checkDatabaseBoundaries(path.join(targetRoot, "packages/database/src"));

  if (!checkedContracts && !checkedDatabase) {
    console.log("ℹ️  Catalog repository (no packages/contracts/src or packages/database/src). Skipping monorepo package boundary check.");
    process.exit(0);
  }

  if (violations === 0) {
    console.log("✅ Architecture Guardian: All layer boundaries verified (exit code 0).");
    process.exit(0);
  } else {
    console.error(`❌ Architecture Guardian: Rejected with ${violations} boundary violation(s).`);
    process.exit(1);
  }
}

run().catch((err) => {
  console.error("Fatal error during architecture check:", err);
  process.exit(1);
});
