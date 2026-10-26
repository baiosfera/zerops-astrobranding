"""
Hermes-Agent Execution Tools
Sovereign Integration Mesh: Connects Hermes-Agent to PostgreSQL 18, NATS JetStream, and the AstroBranding Central Engine.
"""
import os
import re
import sys
import time
import signal
import subprocess
import json
import uuid
import httpx
from typing import Dict, Any, Optional

API_BASE = os.getenv("API_BASE_URL", "http://astrobranding:3000")
DATABASE_URL = os.getenv("DATABASE_URL", "")
NATS_URL = os.getenv("NATS_URL") or os.getenv("ZCP_NATS_URL", "nats://nats:4222")

async def get_system_health() -> dict:
    """Check health across mesh components"""
    async with httpx.AsyncClient(timeout=5.0) as client:
        try:
            res = await client.get(f"{API_BASE}/health")
            return res.json()
        except Exception as e:
            return {"service": "hermes-agent", "status": "autonomous", "upstream_error": str(e)}

async def calculate_natal_chart(client_id: str, ayanamsha: str = "tropical") -> dict:
    """Calculate chart or trigger computation via internal engine"""
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            res = await client.post(
                f"{API_BASE}/api/astrology/chart",
                json={"clientId": client_id, "ayanamsha": ayanamsha, "houseSystem": "placidus"}
            )
            return res.json()
        except Exception as e:
            return {"error": str(e)}

async def get_client_gold_feeds(client_id: str) -> dict:
    """Fetch XML Gold Feeds directly from PostgreSQL 18 or API fallback"""
    if DATABASE_URL:
        try:
            import asyncpg
            conn = await asyncpg.connect(DATABASE_URL)
            rows = await conn.fetch(
                "SELECT feed_name, feed_xml FROM client_feeds WHERE client_id = $1",
                uuid.UUID(client_id)
            )
            await conn.close()
            feeds = {row["feed_name"]: row["feed_xml"] for row in rows}
            return {"status": "ok", "client_id": client_id, "source": "postgres_direct", "feeds": feeds}
        except Exception as err:
            pass

    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            res = await client.get(f"{API_BASE}/api/v1/feeds/{client_id}")
            return res.json()
        except Exception as e:
            return {"error": str(e)}

async def query_client_dumps(client_id: str, shard_name: Optional[str] = None) -> dict:
    """Query 15-shard JSONB client dumps directly from PostgreSQL 18"""
    if not DATABASE_URL:
        return {"status": "error", "message": "DATABASE_URL not configured"}
    try:
        import asyncpg
        conn = await asyncpg.connect(DATABASE_URL)
        if shard_name:
            query = f"SELECT {shard_name} FROM client_dumps WHERE client_id = $1"
            row = await conn.fetchrow(query, uuid.UUID(client_id))
            await conn.close()
            return {
                "status": "ok",
                "client_id": client_id,
                "shard": shard_name,
                "data": json.loads(row[0]) if row and row[0] else None
            }
        else:
            row = await conn.fetchrow("SELECT * FROM client_dumps WHERE client_id = $1", uuid.UUID(client_id))
            await conn.close()
            return {"status": "ok", "client_id": client_id, "data": dict(row) if row else None}
    except Exception as err:
        return {"status": "error", "message": f"PostgreSQL query failed: {str(err)}"}

async def trigger_universal_extraction(birth_data: dict, dry_run: bool = False) -> dict:
    """Trigger or dispatch the 15-Shard Universal Extraction across federated astrology engines"""
    task_id = str(uuid.uuid4())
    payload = {
        "task_id": task_id,
        "action": "astrology.calculate.v1",
        "client": birth_data,
        "dry_run": dry_run
    }
    try:
        from nats.aio.client import Client as NATS
        nc = NATS()
        await nc.connect(NATS_URL)
        js = nc.jetstream()
        await js.publish(
            "astrology.requests",
            json.dumps(payload).encode("utf-8"),
            headers={"Nats-Msg-Id": task_id}
        )
        await nc.close()
        return {"status": "dispatched", "task_id": task_id, "message": "Astrological calculation queued on NATS."}
    except Exception:
        # Fallback to direct HTTP if NATS connection is unavailable
        async with httpx.AsyncClient(timeout=30.0) as client:
            try:
                res = await client.post(
                    f"{API_BASE}/api/v1/extract?dryRun={'true' if dry_run else 'false'}",
                    json=birth_data
                )
                return res.json()
            except Exception as e:
                return {"status": "error", "error": str(e)}

async def send_whatsapp_otp(phone: str, client_name: str) -> dict:
    """Send OTP via Evolution API or internal broker"""
    async with httpx.AsyncClient(timeout=10.0) as client:
        try:
            res = await client.post(
                f"{API_BASE}/api/whatsapp/otp",
                json={"phoneNumber": phone, "clientName": client_name, "template": "otp_verification"}
            )
            return res.json()
        except Exception as e:
            return {"error": str(e)}

# --- Zerops Control Plane & Platform Tools ---

import subprocess

def _clean_service_name(name: str) -> str:
    name = name.strip().lower()
    name = name.replace("/var/www/", "").strip("/")
    return name.split(".")[0]

def list_zerops_services() -> str:
    """Lists all services in the Zerops project and their current status (ACTIVE/STOPPED)."""
    project_id = os.getenv("projectId", "I6YfEvtmRgivAAYYXm537A")
    res = subprocess.run(
        ["/opt/zerops/bin/zcli", "service", "list", f"--projectId={project_id}"],
        capture_output=True, text=True, timeout=15
    )
    if res.returncode == 0:
        return res.stdout.strip()
    return f"Error listing services: {res.stderr.strip()}"

def start_zerops_service(service_name: str) -> str:
    """Starts/turns on a Zerops service stack by name (e.g. 'webdev', 'brand', 'videoworker')."""
    service_name = _clean_service_name(service_name)
    project_id = os.getenv("projectId", "I6YfEvtmRgivAAYYXm537A")
    res = subprocess.run(
        ["/opt/zerops/bin/zcli", "service", "start", service_name, f"--projectId={project_id}"],
        capture_output=True, text=True, timeout=20
    )
    if res.returncode == 0:
        return f"✅ El servicio '{service_name}' está siendo iniciado en Zerops (comando enviado con éxito)."
    return f"❌ Error iniciando '{service_name}': {res.stderr.strip()}"

def stop_zerops_service(service_name: str) -> str:
    """Stops/turns off a Zerops service stack by name (e.g. 'webdev', 'brand')."""
    service_name = _clean_service_name(service_name)
    project_id = os.getenv("projectId", "I6YfEvtmRgivAAYYXm537A")
    res = subprocess.run(
        ["/opt/zerops/bin/zcli", "service", "stop", service_name, f"--projectId={project_id}"],
        capture_output=True, text=True, timeout=20
    )
    if res.returncode == 0:
        return f"🛑 El servicio '{service_name}' está siendo detenido en Zerops (comando enviado con éxito)."
    return f"❌ Error deteniendo '{service_name}': {res.stderr.strip()}"

def get_zerops_service_status(service_name: str) -> str:
    """Checks current status of a specific Zerops service."""
    service_name = _clean_service_name(service_name)
    output = list_zerops_services()
    for line in output.splitlines():
        if service_name in line.lower():
            return f"Estado de '{service_name}': {line.strip()}"
    return f"No se encontró el servicio '{service_name}' en el proyecto."

# --- GitOps & Webdev Code Mutation Tools ---

WEB_REPO_DIR = os.getenv("WEB_REPO_DIR", "/mnt/localstorage/web")

def read_web_file(relative_path: str) -> str:
    """Reads the contents of a file in the webdev repository (e.g., 'brandbook.json', 'package.json', 'apps/web/src/pages/index.astro')."""
    target = os.path.normpath(os.path.join(WEB_REPO_DIR, relative_path.lstrip("/")))
    if not target.startswith(WEB_REPO_DIR):
        return "❌ Error: Ruta fuera del repositorio permitida."
    if not os.path.exists(target):
        return f"❌ El archivo '{relative_path}' no existe en el repositorio."
    try:
        with open(target, "r", encoding="utf-8") as f:
            content = f.read()
        if len(content) > 4000:
            return content[:4000] + "\n... [Truncado: archivo mayor a 4000 caracteres]"
        return content
    except Exception as e:
        return f"❌ Error leyendo archivo: {str(e)}"

def edit_web_file(relative_path: str, new_content: str) -> str:
    """Writes or updates a file in the webdev repository."""
    target = os.path.normpath(os.path.join(WEB_REPO_DIR, relative_path.lstrip("/")))
    if not target.startswith(WEB_REPO_DIR):
        return "❌ Error: Ruta fuera del repositorio permitida."
    try:
        os.makedirs(os.path.dirname(target), exist_ok=True)
        with open(target, "w", encoding="utf-8") as f:
            f.write(new_content)
        return f"✅ Archivo '{relative_path}' actualizado con éxito en el repositorio."
    except Exception as e:
        return f"❌ Error escribiendo archivo: {str(e)}"

def git_web_status() -> str:
    """Shows git status and modified files in the webdev repository."""
    if not os.path.exists(WEB_REPO_DIR):
        return "❌ Repositorio web no encontrado en /mnt/localstorage/web."
    res = subprocess.run(["git", "status", "-s"], cwd=WEB_REPO_DIR, capture_output=True, text=True)
    if res.returncode == 0:
        output = res.stdout.strip()
        return output if output else "Working tree limpio (sin cambios pendientes)."
    return f"❌ Error en git status: {res.stderr.strip()}"

def git_web_diff() -> str:
    """Shows git diff of unstaged or staged changes in the webdev repository."""
    if not os.path.exists(WEB_REPO_DIR):
        return "❌ Repositorio web no encontrado en /mnt/localstorage/web."
    res = subprocess.run(["git", "diff"], cwd=WEB_REPO_DIR, capture_output=True, text=True)
    if res.returncode == 0:
        output = res.stdout.strip()
        if len(output) > 3000:
            return output[:3000] + "\n... [Diff truncado]"
        return output if output else "No hay diferencias locales."
    return f"❌ Error en git diff: {res.stderr.strip()}"

def deploy_webdev_preview(commit_message: str) -> str:
    """Commits local changes on 'dev' branch, pushes to GitHub and deploys to Zerops webdev preview."""
    if not os.path.exists(WEB_REPO_DIR):
        return "❌ Repositorio web no encontrado."
    project_id = os.getenv("projectId", "I6YfEvtmRgivAAYYXm537A")
    try:
        subprocess.run(["git", "add", "."], cwd=WEB_REPO_DIR, check=True)
        commit_res = subprocess.run(["git", "commit", "-m", commit_message], cwd=WEB_REPO_DIR, capture_output=True, text=True)
        push_res = subprocess.run(["git", "push", "origin", "dev"], cwd=WEB_REPO_DIR, capture_output=True, text=True)
        zcli_res = subprocess.run(
            ["/opt/zerops/bin/zcli", "push", "webdev", f"--working-dir={WEB_REPO_DIR}", f"--project-id={project_id}", "--no-wait"],
            capture_output=True, text=True, timeout=30
        )
        return f"🚀 Cambios subidos a GitHub (dev) y despliegue disparado en webdev:\nCommit: {commit_res.stdout.strip()}\nZerops Push: {zcli_res.stdout.strip()}"
    except Exception as e:
        return f"❌ Error en deploy_webdev_preview: {str(e)}"

def promote_to_production_webprod(commit_message: str) -> str:
    """Merges 'dev' into 'main' and pushes to GitHub, triggering the GitHub Actions CI/CD to deploy to webprod."""
    if not os.path.exists(WEB_REPO_DIR):
        return "❌ Repositorio web no encontrado."
    try:
        subprocess.run(["git", "checkout", "main"], cwd=WEB_REPO_DIR, check=True)
        subprocess.run(["git", "pull", "origin", "main"], cwd=WEB_REPO_DIR, check=True)
        merge_res = subprocess.run(["git", "merge", "dev", "-m", commit_message], cwd=WEB_REPO_DIR, capture_output=True, text=True)
        push_res = subprocess.run(["git", "push", "origin", "main"], cwd=WEB_REPO_DIR, capture_output=True, text=True)
        subprocess.run(["git", "checkout", "dev"], cwd=WEB_REPO_DIR, check=True)
        return f"🌟 ¡Promoción a PRODUCCIÓN disparada!\nMerge: {merge_res.stdout.strip()}\nGitHub Push: {push_res.stdout.strip()}\nGitHub Actions está desplegando ahora en producción."
    except Exception as e:
        subprocess.run(["git", "checkout", "dev"], cwd=WEB_REPO_DIR)
        return f"❌ Error en promote_to_production_webprod: {str(e)}"

def git_web_log(branch_or_range: str = "main..dev") -> str:
    """Shows commit history for a branch or range (e.g. 'main..dev' shows all commits on dev waiting to be pushed/merged to main/production)."""
    if not os.path.exists(WEB_REPO_DIR):
        return "❌ Repositorio web no encontrado en /mnt/localstorage/web."
    try:
        subprocess.run(["git", "fetch", "origin"], cwd=WEB_REPO_DIR, capture_output=True, timeout=10)
    except Exception:
        pass
    res = subprocess.run(["git", "log", branch_or_range, "--oneline", "-n", "15"], cwd=WEB_REPO_DIR, capture_output=True, text=True)
    if res.returncode == 0:
        output = res.stdout.strip()
        return output if output else f"No hay commits pendientes en el rango '{branch_or_range}' (ramas sincronizadas)."
    return f"❌ Error en git log: {res.stderr.strip()}"

def git_web_diff_branches(base_branch: str = "main", target_branch: str = "dev") -> str:
    """Compares two branches (e.g. 'main' and 'dev') and lists changed files and statistics."""
    if not os.path.exists(WEB_REPO_DIR):
        return "❌ Repositorio web no encontrado en /mnt/localstorage/web."
    try:
        subprocess.run(["git", "fetch", "origin"], cwd=WEB_REPO_DIR, capture_output=True, timeout=10)
    except Exception:
        pass
    res = subprocess.run(["git", "diff", f"{base_branch}..{target_branch}", "--stat"], cwd=WEB_REPO_DIR, capture_output=True, text=True)
    if res.returncode == 0:
        output = res.stdout.strip()
        return output if output else f"Las ramas '{base_branch}' y '{target_branch}' están idénticas (sin diferencias)."
    return f"❌ Error en git diff: {res.stderr.strip()}"

# --- Universal AGY-Twin Engineering & File Tools ---

def read_file(path: str) -> str:
    """Reads any file in the workspace or localstorage (e.g. '/mnt/localstorage/${PROJECT_NAME}/dev/...', '/mnt/localstorage/products/...', or '/var/www/...')."""
    path = os.path.normpath(path)
    if not os.path.exists(path):
        return f"❌ El archivo '{path}' no existe."
    if os.path.isdir(path):
        return f"❌ '{path}' es un directorio, usa list_directory."
    try:
        with open(path, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
        if len(content) > 4000:
            return content[:4000] + f"\n... [Truncado: total {len(content)} caracteres]"
        return content
    except Exception as e:
        return f"❌ Error leyendo archivo: {str(e)}"

PROTECTED_PATH_PATTERNS = [
    re.compile(r'(\.git/|\.env\b|00-SUPREME-DIRECTIVE\.md|_handover)', re.IGNORECASE),
    re.compile(r'(/etc/|/var/run/|/usr/|/bin/)', re.IGNORECASE)
]

def validate_code_safety(path: str, new_content: str, allow_shrink: bool = False) -> Optional[str]:
    """Validates syntax and security invariants before modifying files on disk."""
    norm = os.path.normpath(path)
    for pat in PROTECTED_PATH_PATTERNS:
        if pat.search(norm):
            return f"❌ Violación de seguridad: Ruta protegida contra escritura: '{norm}'."

    # 1. AST syntax check for Python
    if norm.endswith(".py"):
        import ast
        try:
            ast.parse(new_content)
        except SyntaxError as e:
            return f"❌ Error de sintaxis Python bloqueado: {e.msg} en línea {e.lineno}."

    # 2. Syntax check for Shell
    elif norm.endswith((".sh", ".bash")):
        res = subprocess.run(["bash", "-n"], input=new_content, text=True, capture_output=True)
        if res.returncode != 0:
            return f"❌ Error de sintaxis Bash bloqueado: {res.stderr.strip()}."

    # 3. Anti-Wiping monotonicity check
    if os.path.exists(norm) and not allow_shrink:
        try:
            with open(norm, "r", encoding="utf-8", errors="ignore") as f:
                old_lines = f.readlines()
            new_lines = new_content.splitlines()
            if len(old_lines) > 50 and len(new_lines) < (len(old_lines) * 0.5):
                return (
                    f"❌ Bloqueado por Anti-Wiping: Intento de reducir '{norm}' de {len(old_lines)} a "
                    f"{len(new_lines)} líneas sin flag explícito de refactorización."
                )
        except Exception:
            pass

    return None

def write_file(path: str, content: str, allow_shrink: bool = False) -> str:
    """Creates or overwrites a file with syntax validation and anti-wiping safety."""
    path = os.path.normpath(path)
    safety_err = validate_code_safety(path, content, allow_shrink)
    if safety_err:
        return safety_err

    try:
        target_dir = os.path.dirname(path)
        os.makedirs(target_dir, exist_ok=True)
        temp_file = os.path.join(target_dir, f".tmp_{uuid.uuid4().hex[:8]}_{os.path.basename(path)}")
        with open(temp_file, "w", encoding="utf-8") as f:
            f.write(content)
        os.replace(temp_file, path)
        return f"✅ Archivo '{path}' guardado con éxito ({len(content)} bytes, sintaxis validada)."
    except Exception as e:
        return f"❌ Error escribiendo archivo: {str(e)}"

def edit_file(path: str, target: str, replacement: str, allow_shrink: bool = False) -> str:
    """Replaces exact target text with replacement text after AST validation."""
    path = os.path.normpath(path)
    if not os.path.exists(path):
        return f"❌ El archivo '{path}' no existe."
    try:
        with open(path, "r", encoding="utf-8") as f:
            content = f.read()
        if target not in content:
            return f"❌ No se encontró el texto objetivo en '{path}'."
        new_content = content.replace(target, replacement)
        
        safety_err = validate_code_safety(path, new_content, allow_shrink)
        if safety_err:
            return safety_err

        target_dir = os.path.dirname(path)
        temp_file = os.path.join(target_dir, f".tmp_{uuid.uuid4().hex[:8]}_{os.path.basename(path)}")
        with open(temp_file, "w", encoding="utf-8") as f:
            f.write(new_content)
        os.replace(temp_file, path)
        return f"✅ Archivo '{path}' modificado con éxito (sintaxis validada)."
    except Exception as e:
        return f"❌ Error editando archivo: {str(e)}"

def list_directory(path: str = "/mnt/localstorage") -> str:
    """Lists files and folders inside any directory."""
    path = os.path.normpath(path)
    if not os.path.exists(path):
        return f"❌ La ruta '{path}' no existe."
    try:
        items = os.listdir(path)
        formatted = []
        for item in sorted(items)[:50]:
            full = os.path.join(path, item)
            is_dir = os.path.isdir(full)
            formatted.append(f"{'[DIR] ' if is_dir else '      '}{item}")
        return "\n".join(formatted) if formatted else "Directorio vacío."
    except Exception as e:
        return f"❌ Error listando directorio: {str(e)}"

INTERACTIVE_PROMPT_REGEX = re.compile(
    r'(\[y/n\]|\(yes/no\)|password\s*:|enter passphrase|do you want to continue\?)',
    re.IGNORECASE
)

def run_command(command: str) -> str:
    """Executes a bounded shell command with process group isolation, non-interactive env, and Pointer Pattern."""
    # Block destructive Git commands
    if re.search(r'git\s+push\s+.*(--force|-f)\b', command, re.IGNORECASE):
        return "❌ Violación de seguridad: 'git push --force' está estrictamente prohibido."
    if re.search(r'git\s+reset\s+--hard\b', command, re.IGNORECASE):
        return "❌ Violación de seguridad: 'git reset --hard' está estrictamente prohibido."

    env = dict(os.environ)
    env["DEBIAN_FRONTEND"] = "noninteractive"
    env["GIT_TERMINAL_PROMPT"] = "0"
    env["CI"] = "true"
    env["TERM"] = "dumb"
    env["PYTHONUNBUFFERED"] = "1"

    try:
        proc = subprocess.Popen(
            command,
            shell=True,
            stdout=subprocess.PIPE,
            stderr=subprocess.PIPE,
            stdin=subprocess.DEVNULL,  # Prevent interactive hangs
            preexec_fn=os.setsid,       # Process group isolation
            text=True,
            env=env
        )

        try:
            stdout, stderr = proc.communicate(timeout=30)
        except subprocess.TimeoutExpired:
            # Kill entire process group
            try:
                os.killpg(proc.pid, signal.SIGTERM)
                time.sleep(0.5)
                os.killpg(proc.pid, signal.SIGKILL)
            except Exception:
                pass
            return "❌ Error: El comando excedió el tiempo límite de 30 segundos y su grupo de procesos fue terminado."

        output = stdout.strip() if stdout else ""
        err = stderr.strip() if stderr else ""

        # Check for interactive prompt traps in output
        if INTERACTIVE_PROMPT_REGEX.search(output + "\n" + err):
            return f"❌ Advertencia de proceso interactivo detectada en salida. Ejecución abortada:\n{output[:500]}"

        combined = []
        if output:
            combined.append(output)
        if err:
            combined.append(f"STDERR:\n{err}")
        full_res = "\n".join(combined) if combined else "(Comando ejecutado con éxito sin salida)"

        # Pointer Pattern: If output > 6000 chars, persist full log to localstorage and return preview
        if len(full_res) > 6000:
            artifacts_dir = "/mnt/localstorage/artifacts"
            os.makedirs(artifacts_dir, exist_ok=True)
            art_id = f"cmd_out_{uuid.uuid4().hex[:8]}.log"
            art_path = os.path.join(artifacts_dir, art_id)
            with open(art_path, "w", encoding="utf-8") as f:
                f.write(full_res)
            return (
                f"[SALIDA TRUNCADA: total {len(full_res)} caracteres. Log completo en {art_path}]\n"
                f"=== HEAD (primeros 2500 caracteres) ===\n{full_res[:2500]}\n"
                f"... [SNIP {len(full_res) - 5000} caracteres] ...\n"
                f"=== TAIL (últimos 2500 caracteres) ===\n{full_res[-2500:]}"
            )

        return full_res
    except Exception as e:
        return f"❌ Error ejecutando comando: {str(e)}"

# --- Multi-Tier Internet Research & Asset Ingestion Tools (AGY Parity) ---

def search_web(query: str, max_results: int = 5) -> str:
    """Performs deep epistemic web search using Tavily API (with Brave API fallback). Returns titles, URLs, and snippets."""
    tavily_key = os.getenv("TAVILY_API_KEY")
    if tavily_key:
        try:
            with httpx.Client(timeout=15.0) as client:
                res = client.post(
                    "https://api.tavily.com/search",
                    json={"query": query, "max_results": min(max_results, 8), "api_key": tavily_key}
                )
                if res.status_code == 200:
                    data = res.json()
                    results = data.get("results", [])
                    if not results:
                        return f"No se encontraron resultados en la web para: '{query}'."
                    formatted = [f"Resultados web para '{query}':"]
                    for i, r in enumerate(results, 1):
                        title = r.get("title", "Sin título")
                        url = r.get("url", "")
                        snippet = r.get("content", "").strip()[:300]
                        formatted.append(f"{i}. [{title}]({url})\n   {snippet}")
                    return "\n\n".join(formatted)
        except Exception:
            pass

    brave_key = os.getenv("BRAVE_API_KEY")
    if brave_key:
        try:
            with httpx.Client(timeout=15.0) as client:
                res = client.get(
                    "https://api.search.brave.com/res/v1/web/search",
                    headers={"X-Subscription-Token": brave_key, "Accept": "application/json"},
                    params={"q": query, "count": min(max_results, 8)}
                )
                if res.status_code == 200:
                    data = res.json()
                    results = data.get("web", {}).get("results", [])
                    if not results:
                        return f"No se encontraron resultados en Brave Search para: '{query}'."
                    formatted = [f"Resultados web (Brave) para '{query}':"]
                    for i, r in enumerate(results, 1):
                        title = r.get("title", "Sin título")
                        url = r.get("url", "")
                        snippet = r.get("description", "").strip()[:300]
                        formatted.append(f"{i}. [{title}]({url})\n   {snippet}")
                    return "\n\n".join(formatted)
        except Exception as e:
            return f"❌ Error en búsqueda web: {str(e)}"

    return "❌ Error: Ni TAVILY_API_KEY ni BRAVE_API_KEY están disponibles en el entorno."

def fetch_web_page(url: str) -> str:
    """Fetches and parses any web page into clean readable Markdown using Jina Reader API."""
    jina_key = os.getenv("JINA_API_KEY")
    headers = {"Authorization": f"Bearer {jina_key}"} if jina_key else {}
    target_url = f"https://r.jina.ai/{url}"
    try:
        with httpx.Client(timeout=20.0, follow_redirects=True) as client:
            res = client.get(target_url, headers=headers)
            if res.status_code == 200:
                text = res.text.strip()
                if len(text) > 6000:
                    return text[:6000] + f"\n... [Contenido truncado: total {len(text)} caracteres]"
                return text if text else "Página web vacía o sin contenido extraíble."
            return f"❌ Error al consultar la página {url}: HTTP {res.status_code} - {res.text[:200]}"
    except Exception as e:
        return f"❌ Error al extraer contenido web de {url}: {str(e)}"

def download_file(url: str, destination_path: str, max_mb: int = 50) -> str:
    """Downloads a binary or asset file (video, image, font, template) from a URL directly to the workspace."""
    dest = os.path.normpath(destination_path)
    for pat in PROTECTED_PATH_PATTERNS:
        if pat.search(dest):
            return f"❌ Violación de seguridad: No se puede descargar a '{dest}'."

    try:
        os.makedirs(os.path.dirname(dest), exist_ok=True)
        with httpx.Client(timeout=60.0, follow_redirects=True) as client:
            with client.stream("GET", url) as res:
                if res.status_code != 200:
                    return f"❌ Error HTTP {res.status_code} al descargar desde '{url}'."
                cl = res.headers.get("content-length")
                if cl and int(cl) > max_mb * 1024 * 1024:
                    return f"❌ Archivo demasiado grande ({int(cl)/(1024*1024):.1f} MB). Límite máximo: {max_mb} MB."
                
                bytes_written = 0
                with open(dest, "wb") as f:
                    for chunk in res.iter_bytes(chunk_size=65536):
                        f.write(chunk)
                        bytes_written += len(chunk)
                        if bytes_written > max_mb * 1024 * 1024:
                            return f"❌ Descarga abortada: superó el límite de {max_mb} MB."
                
        return f"✅ Archivo descargado exitosamente en '{dest}' ({bytes_written/1024:.1f} KB)."
    except Exception as e:
        return f"❌ Error durante la descarga: {str(e)}"

# --- Sovereign Agentic SQL Engine (PostgreSQL 18 Live Impact) ---

async def describe_store_schema() -> str:
    """Discovers all tables, columns, and data types in the public PostgreSQL database."""
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        return "❌ Error: DATABASE_URL no está configurada."
    try:
        import asyncpg
        conn = await asyncpg.connect(db_url, timeout=5.0)
        query = """
        SELECT table_name, column_name, data_type
        FROM information_schema.columns
        WHERE table_schema = 'public'
        ORDER BY table_name, ordinal_position;
        """
        rows = await conn.fetch(query)
        await conn.close()
        if not rows:
            return "No se encontraron tablas públicas en la base de datos."
        
        tables = {}
        for r in rows:
            t_name = r["table_name"]
            if t_name not in tables:
                tables[t_name] = []
            tables[t_name].append(f"{r['column_name']} ({r['data_type']})")
        
        out = ["📊 **Esquema de Base de Datos Soberano (PostgreSQL 18):**"]
        for t, cols in tables.items():
            out.append(f"• **{t}**: {', '.join(cols)}")
        return "\n".join(out)
    except Exception as e:
        return f"❌ Error descubriendo esquema: {str(e)}"

async def execute_store_query(query: str, explanation: str = "") -> str:
    """Executes arbitrary SQL queries or mutations on PostgreSQL 18.
    Provides complete agentic freedom for querying and updating products, categories,
    prices, orders, stock, bookings, or analytics.
    Destructive operations (DROP DATABASE, DROP TABLE, DROP SCHEMA, TRUNCATE) are forbidden.
    """
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        return "❌ Error: DATABASE_URL no está configurada."
    
    clean_q = query.strip()
    forbidden = re.compile(r'\b(DROP\s+DATABASE|DROP\s+TABLE|DROP\s+SCHEMA|TRUNCATE)\b', re.IGNORECASE)
    if forbidden.search(clean_q):
        return "❌ Violación de seguridad: Operaciones destructivas (DROP/TRUNCATE) están prohibidas."
    
    try:
        import asyncpg
        conn = await asyncpg.connect(db_url, timeout=10.0)
        is_select = clean_q.lstrip().upper().startswith(("SELECT", "WITH", "EXPLAIN", "SHOW"))
        
        if is_select:
            rows = await conn.fetch(clean_q)
            await conn.close()
            if not rows:
                return "La consulta no devolvió resultados (0 filas)."
            
            cols = list(rows[0].keys())
            if len(rows) <= 15:
                header = "| " + " | ".join(cols) + " |"
                sep = "| " + " | ".join(["---"] * len(cols)) + " |"
                lines = [header, sep]
                for r in rows:
                    row_vals = [str(r[c]) if r[c] is not None else "NULL" for c in cols]
                    lines.append("| " + " | ".join(row_vals) + " |")
                return f"✅ Resultado ({len(rows)} filas):\n" + "\n".join(lines)
            else:
                out = [f"✅ Resultado ({len(rows)} filas - mostrando primeras 15):"]
                for i, r in enumerate(rows[:15]):
                    items = [f"{c}={r[c]}" for c in cols]
                    out.append(f"{i+1}. {', '.join(items)}")
                return "\n".join(out)
        else:
            status = await conn.execute(clean_q)
            await conn.close()
            return f"✅ Consulta ejecutada exitosamente: {status}"
    except Exception as e:
        return f"❌ Error ejecutando SQL: {str(e)}"

# --- E-Commerce & Store Management Tools (SSR PostgreSQL 18 Live Impact) ---

async def get_store_products(category: str = "") -> str:
    """Lists available activewear products with prices and status from the live store database."""
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        return "❌ Error: DATABASE_URL no está configurada."
    try:
        import asyncpg
        conn = await asyncpg.connect(db_url, timeout=5.0)
        rows = await conn.fetch("SELECT name, base_price, is_active FROM products WHERE is_active = 1 ORDER BY base_price ASC")
        await conn.close()
        if not rows:
            return "No hay productos activos en el catálogo."
        out = ["🛍️ **Catálogo de Productos Activos en Producción:**"]
        for r in rows:
            out.append(f"• **{r['name']}**: ${r['base_price']:,} COP")
        return "\n".join(out)
    except Exception as e:
        return f"❌ Error consultando catálogo: {str(e)}"

async def update_product_price(product_name: str, new_price: int) -> str:
    """Updates the price of a product in the live store database."""
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        return "❌ Error: DATABASE_URL no está configurada."
    try:
        import asyncpg
        conn = await asyncpg.connect(db_url, timeout=5.0)
        await conn.execute(
            "UPDATE products SET base_price = $1, updated_at = NOW() WHERE name ILIKE $2",
            new_price, f"%{product_name.strip()}%"
        )
        row = await conn.fetchrow("SELECT name, base_price FROM products WHERE name ILIKE $1 LIMIT 1", f"%{product_name.strip()}%")
        await conn.close()
        if row:
            return f"✅ Precio actualizado con éxito en vivo:\n• **{row['name']}**: ${row['base_price']:,} COP\nEl cambio ya es visible en producción (SSR en tiempo real)."
        return f"❌ No se encontró ningún producto que coincida con '{product_name}'."
    except Exception as e:
        return f"❌ Error actualizando precio: {str(e)}"

async def get_makeup_services() -> str:
    """Lists active professional services and pricing."""
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        return "❌ Error: DATABASE_URL no está configurada."
    try:
        import asyncpg
        conn = await asyncpg.connect(db_url, timeout=5.0)
        rows = await conn.fetch("SELECT name, price, is_active FROM services WHERE is_active = 1 ORDER BY price ASC")
        await conn.close()
        if not rows:
            return "No hay servicios activos."
        out = ["💄 **Servicios Profesionales Activos en Producción:**"]
        for r in rows:
            out.append(f"• **{r['name']}**: ${r['price']:,} COP")
        return "\n".join(out)
    except Exception as e:
        return f"❌ Error consultando servicios: {str(e)}"

async def update_service_price(service_name: str, new_price: int) -> str:
    """Updates the price of a service in the live database."""
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        return "❌ Error: DATABASE_URL no está configurada."
    try:
        import asyncpg
        conn = await asyncpg.connect(db_url, timeout=5.0)
        await conn.execute(
            "UPDATE services SET price = $1, updated_at = NOW() WHERE name ILIKE $2",
            new_price, f"%{service_name.strip()}%"
        )
        row = await conn.fetchrow("SELECT name, price FROM services WHERE name ILIKE $1 LIMIT 1", f"%{service_name.strip()}%")
        await conn.close()
        if row:
            return f"✅ Servicio actualizado con éxito en vivo:\n• **{row['name']}**: ${row['price']:,} COP\nEl cambio ya es visible en producción."
        return f"❌ No se encontró ningún servicio que coincida con '{service_name}'."
    except Exception as e:
        return f"❌ Error actualizando servicio: {str(e)}"

async def get_recent_orders(limit: int = 5) -> str:
    """Lists recent customer orders from the store database."""
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        return "❌ Error: DATABASE_URL no está configurada."
    try:
        import asyncpg
        conn = await asyncpg.connect(db_url, timeout=5.0)
        rows = await conn.fetch("SELECT id, customer_name, total_amount, status, created_at FROM orders ORDER BY created_at DESC LIMIT $1", limit)
        await conn.close()
        if not rows:
            return "No hay pedidos registrados en la tienda todavía."
        out = [f"📦 **Últimos {len(rows)} Pedidos:**"]
        for r in rows:
            date_str = r['created_at'].strftime('%Y-%m-%d %H:%M') if r.get('created_at') else 'N/A'
            out.append(f"• ID #{str(r['id'])[:8]} - {r['customer_name'] or 'Cliente'}: ${r['total_amount']:,} COP [{r['status']}] ({date_str})")
        return "\n".join(out)
    except Exception as e:
        return f"❌ Error consultando pedidos: {str(e)}"

async def get_makeup_bookings(limit: int = 5) -> str:
    """Lists upcoming or recent makeup appointment bookings."""
    db_url = os.getenv("DATABASE_URL")
    if not db_url:
        return "❌ Error: DATABASE_URL no está configurada."
    try:
        import asyncpg
        conn = await asyncpg.connect(db_url, timeout=5.0)
        rows = await conn.fetch("SELECT id, customer_name, customer_phone, service_name, appointment_date, status FROM bookings ORDER BY created_at DESC LIMIT $1", limit)
        await conn.close()
        if not rows:
            return "No hay citas de maquillaje registradas todavía."
        out = [f"📅 **Citas de Maquillaje ({len(rows)}):**"]
        for r in rows:
            out.append(f"• {r['customer_name']} ({r['customer_phone'] or 'Sin tel'}): {r['service_name']} - Fecha: {r['appointment_date']} [{r['status']}]")
        return "\n".join(out)
    except Exception as e:
        return f"❌ Error consultando citas: {str(e)}"

# --- Dynamic AI Swarms (CrewAI) & Structured Validation (PydanticAI) ---

async def run_crew_ai(mission: str, roles: list, tier: str = "free") -> str:
    """Dispatches a dynamic in-memory CrewAI swarm without static scripts."""
    try:
        import asyncio
        from crews.crew_factory import CrewFactory
        return await asyncio.to_thread(CrewFactory.create_dynamic_crew, goal=mission, roles=roles, tier=tier)
    except Exception as e:
        return f"❌ Error ejecutando CrewAI: {str(e)}"

async def extract_structured_data(fields_spec: dict, user_input: str, tier: str = "free") -> str:
    """Extracts and validates structured data dynamically via PydanticAI."""
    try:
        from pydanticai_engine import extract_structured_data as _extract
        return await _extract(fields_spec=fields_spec, user_input=user_input, tier=tier)
    except Exception as e:
        return f"❌ Error extrayendo datos con PydanticAI: {str(e)}"
