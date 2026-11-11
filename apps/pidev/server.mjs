import http from 'node:http';
import { exec } from 'node:child_process';

const PORT = parseInt(process.env.PORT || '3000', 10);
const HOST = '0.0.0.0';

const server = http.createServer((req, res) => {
  const url = new URL(req.url, `http://${req.headers.host || 'localhost'}`);

  res.setHeader('Content-Type', 'application/json');
  res.setHeader('Access-Control-Allow-Origin', '*');
  res.setHeader('Access-Control-Allow-Methods', 'GET, POST, OPTIONS');
  res.setHeader('Access-Control-Allow-Headers', 'Content-Type, Authorization');

  if (req.method === 'OPTIONS') {
    res.writeHead(204);
    res.end();
    return;
  }

  if (req.method === 'GET' && (url.pathname === '/health' || url.pathname === '/healthz' || url.pathname === '/')) {
    res.writeHead(200);
    res.end(JSON.stringify({
      status: 'ok',
      service: 'pidev',
      node_version: process.version,
      agent: 'gentle-pi',
      cwd: process.cwd()
    }));
    return;
  }

  if (req.method === 'GET' && url.pathname === '/status') {
    exec('gentle-shell --version', (err, stdout, stderr) => {
      res.writeHead(200);
      res.end(JSON.stringify({
        status: 'ok',
        service: 'pidev',
        version: (stdout || '').trim(),
        uptime: process.uptime(),
        memory: process.memoryUsage()
      }));
    });
    return;
  }

  if (req.method === 'POST' && url.pathname === '/execute') {
    let body = '';
    req.on('data', chunk => { body += chunk; });
    req.on('end', () => {
      try {
        const payload = JSON.parse(body || '{}');
        const rawCommand = payload.command;
        const prompt = payload.prompt;
        const cwd = payload.cwd || process.cwd();

        if (!rawCommand && !prompt) {
          res.writeHead(400);
          res.end(JSON.stringify({ status: 'error', message: 'Missing "command" or "prompt" parameter' }));
          return;
        }

        const env = {
          ...process.env,
          CI: 'true',
          NON_INTERACTIVE: 'true',
          GENTLE_SHELL_NO_AUTO_SETUP: '1',
          PATH: `/mnt/localstorage/bin:/home/zerops/.local/bin:/usr/local/bin:${process.env.PATH || ''}`
        };
        if (!env.OPENAI_BASE_URL) env.OPENAI_BASE_URL = 'http://bifrost:8080/v1';
        if (!env.OPENAI_API_KEY) env.OPENAI_API_KEY = 'vk-pidev';

        const command = rawCommand || (prompt ? (prompt.startsWith('pi ') || prompt.startsWith('gentle-shell ') ? prompt : `pi --approve --provider bifrost --model bifrost/deepseek-chat -p '${prompt.replace(/'/g, "'\\''")}' < /dev/null`) : '');

        exec(command, { cwd, env, timeout: 120000, maxBuffer: 10 * 1024 * 1024 }, (err, stdout, stderr) => {
          if (err && !stdout) {
            res.writeHead(500);
            res.end(JSON.stringify({
              status: 'error',
              message: err.message,
              stdout: (stdout || '').trim(),
              stderr: (stderr || '').trim()
            }));
            return;
          }
          res.writeHead(200);
          res.end(JSON.stringify({
            status: 'ok',
            output: (stdout || '').trim(),
            stderr: (stderr || '').trim(),
            exitCode: err ? err.code : 0
          }));
        });
      } catch (parseErr) {
        res.writeHead(400);
        res.end(JSON.stringify({ status: 'error', message: 'Invalid JSON payload' }));
      }
    });
    return;
  }

  res.writeHead(404);
  res.end(JSON.stringify({ status: 'error', message: 'Not found' }));
});

server.listen(PORT, HOST, () => {
  console.log(`[pidev] Gentle-Pi HTTP Runner listening on ${HOST}:${PORT}`);
});
