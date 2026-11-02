import { spawn } from "node:child_process";
import fs from "node:fs";

const configPath = "/home/zerops/.paperclip/instances/default/config.json";

// Dynamic subdomain resolution for zero hardcoding across any Zerops project
if (fs.existsSync(configPath)) {
  try {
    const raw = fs.readFileSync(configPath, "utf8");
    const cfg = JSON.parse(raw);
    if (!cfg.server) cfg.server = {};
    if (!Array.isArray(cfg.server.allowedHostnames)) {
      cfg.server.allowedHostnames = [];
    }

    const subdomains = ["paperclip", "localhost", "127.0.0.1"];

    if (process.env.zeropsSubdomainString) {
      try {
        const rawUrl = process.env.zeropsSubdomainString.replace("${port}", "3100");
        const parsed = new URL(rawUrl);
        if (parsed.hostname && !subdomains.includes(parsed.hostname)) {
          subdomains.push(parsed.hostname);
        }
      } catch (e) {
        console.warn("Could not parse zeropsSubdomainString:", e.message);
      }
    }

    for (const host of subdomains) {
      if (!cfg.server.allowedHostnames.includes(host)) {
        cfg.server.allowedHostnames.push(host);
      }
    }

    cfg.server.port = 3100;
    cfg.server.host = "0.0.0.0";
    cfg.server.bind = "lan";
    fs.writeFileSync(configPath, JSON.stringify(cfg, null, 2), "utf8");
  } catch (err) {
    console.error("Config patch warning:", err.message);
  }
}

console.log("🚀 Starting Paperclip AI Native Platform on port 3100...");
const child = spawn("paperclipai", ["run", "--bind", "lan", "--force"], {
  stdio: "inherit",
  env: {
    ...process.env,
    PORT: "3100",
    HOST: "0.0.0.0"
  }
});

child.on("exit", (code) => {
  console.log(`Paperclip exited with code ${code}`);
  process.exit(code || 0);
});

process.on("SIGTERM", () => child.kill("SIGTERM"));
process.on("SIGINT", () => child.kill("SIGINT"));
