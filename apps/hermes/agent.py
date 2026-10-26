"""
Hermes-Agent Execution Loop
"""
import os
import re
import json
import uuid
import httpx
try:
    from prompts import HERMES_SYSTEM_PROMPT, format_chatml_prompt, get_hermes_system_prompt
    from tools import (
        get_system_health, calculate_natal_chart, send_whatsapp_otp,
        list_zerops_services, start_zerops_service, stop_zerops_service, get_zerops_service_status,
        read_web_file, edit_web_file, git_web_status, git_web_diff,
        deploy_webdev_preview, promote_to_production_webprod,
        git_web_log, git_web_diff_branches,
        read_file, write_file, edit_file, list_directory, run_command,
        search_web, fetch_web_page, download_file,
        describe_store_schema, execute_store_query,
        get_store_products, update_product_price, get_makeup_services,
        update_service_price, get_recent_orders, get_makeup_bookings,
        run_crew_ai, extract_structured_data
    )
except (ImportError, ValueError):
    from .prompts import HERMES_SYSTEM_PROMPT, format_chatml_prompt, get_hermes_system_prompt
    from .tools import (
        get_system_health, calculate_natal_chart, send_whatsapp_otp,
        list_zerops_services, start_zerops_service, stop_zerops_service, get_zerops_service_status,
        read_web_file, edit_web_file, git_web_status, git_web_diff,
        deploy_webdev_preview, promote_to_production_webprod,
        git_web_log, git_web_diff_branches,
        read_file, write_file, edit_file, list_directory, run_command,
        search_web, fetch_web_page, download_file,
        describe_store_schema, execute_store_query,
        get_store_products, update_product_price, get_makeup_services,
        update_service_price, get_recent_orders, get_makeup_bookings,
        run_crew_ai, extract_structured_data
    )

BIFROST_URL = os.getenv("HERMES_MODEL_ENDPOINT", "http://bifrost:8080/v1")
MODEL_NAME = os.getenv("HERMES_MODEL_OVERRIDE") or ("auto" if os.getenv("HERMES_MODEL_NAME") in (None, "", "deepseek-chat") else os.getenv("HERMES_MODEL_NAME"))
BIFROST_KEY = os.getenv("BIFROST_VIRTUAL_KEY", "vk-hermes-agent")

ECOMMERCE_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "describe_store_schema",
            "description": "Descubre la estructura, tablas y columnas de la base de datos de la tienda en PostgreSQL 18. Usar para conocer qué tablas (productos, pedidos, citas, clientes) existen en el proyecto activo.",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "execute_store_query",
            "description": "Ejecuta cualquier consulta o actualización SQL sobre la base de datos de la tienda en PostgreSQL 18. Permite consultar o actualizar cualquier dato (productos, precios, stock, pedidos, citas, ventas) en tiempo real con libertad agéntica total. Operaciones destructivas (DROP/TRUNCATE) están prohibidas.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {
                        "type": "string",
                        "description": "Consulta SQL estándar válida para PostgreSQL (ej: 'SELECT * FROM products WHERE is_active = 1', 'UPDATE products SET base_price = 98000 WHERE name ILIKE \'%obsidiana%\'')"
                    },
                    "explanation": {
                        "type": "string",
                        "description": "Breve explicación en lenguaje natural del propósito comercial de la consulta."
                    }
                },
                "required": ["query"]
            }
        }
    }
]

ZEROPS_TOOLS = ECOMMERCE_TOOLS + [
    {
        "type": "function",
        "function": {
            "name": "start_zerops_service",
            "description": "Start or turn on a Zerops service stack by name (e.g. 'webdev', 'brand', 'videoworker', 'evolution'). Use this when the user asks to start, turn on or boot a service.",
            "parameters": {
                "type": "object",
                "properties": {
                    "service_name": {
                        "type": "string",
                        "description": "The exact service name, e.g. 'webdev'"
                    }
                },
                "required": ["service_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "stop_zerops_service",
            "description": "Stop or turn off a Zerops service stack by name (e.g. 'webdev', 'brand'). Use this when the user asks to stop, shutdown or turn off a service.",
            "parameters": {
                "type": "object",
                "properties": {
                    "service_name": {
                        "type": "string",
                        "description": "The exact service name, e.g. 'webdev'"
                    }
                },
                "required": ["service_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_zerops_services",
            "description": "List all Zerops services in the project and their current status (ACTIVE / STOPPED).",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_zerops_service_status",
            "description": "Get the current health and status of a specific Zerops service.",
            "parameters": {
                "type": "object",
                "properties": {
                    "service_name": {"type": "string", "description": "Name of the service"}
                },
                "required": ["service_name"]
            }
        }
    },

    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Read any file in the workspace or localstorage by absolute path (e.g. '/mnt/localstorage/...', '/var/www/...').",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Absolute or relative file path"}
                },
                "required": ["path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Create or overwrite a file with full content.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "File path"},
                    "content": {"type": "string", "description": "Content to write"}
                },
                "required": ["path", "content"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "edit_file",
            "description": "Perform precise string replacement in a file.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "File path"},
                    "target": {"type": "string", "description": "Exact text to be replaced"},
                    "replacement": {"type": "string", "description": "New replacement text"}
                },
                "required": ["path", "target", "replacement"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_directory",
            "description": "List files and subdirectories in a directory path.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Directory path, e.g. '/mnt/localstorage'"}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "run_command",
            "description": "Execute any shell command inside the container (git, python, bun, curl, tests).",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {"type": "string", "description": "Shell command to execute"}
                },
                "required": ["command"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_web",
            "description": "Performs deep epistemic web search using Tavily / Brave API to find stock videos, templates, documentation, or tutorials on the internet.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "The search query (e.g. 'free activewear stock videos 1080p pexels')"},
                    "max_results": {"type": "integer", "description": "Number of results to return (default 5)"}
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "fetch_web_page",
            "description": "Extracts clean readable Markdown content of any web URL using Jina Reader API.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "The full HTTP/HTTPS URL to fetch"}
                },
                "required": ["url"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "download_file",
            "description": "Downloads any asset file (video, image, font, template) from a URL directly to a workspace path (e.g. '/mnt/localstorage/web/apps/web/public/videos/hero.mp4').",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "The direct download URL of the asset"},
                    "destination_path": {"type": "string", "description": "The destination path in the workspace where the file should be saved"}
                },
                "required": ["url", "destination_path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "run_crew_ai",
            "description": "Despacha un enjambre autónomo multi-agente en memoria (CrewAI) para resolver misiones complejas de investigación, estrategia, ingeniería o análisis sin plantillas estáticas.",
            "parameters": {
                "type": "object",
                "properties": {
                    "mission": {"type": "string", "description": "Objetivo o consigna general para la cuadrilla"},
                    "roles": {
                        "type": "array",
                        "description": "Lista de agentes con rol, meta y contexto. Ej: [{'role': 'Investigador', 'goal': 'Buscar datos', 'backstory': 'Experto en...'}]",
                        "items": {"type": "object"}
                    },
                    "tier": {"type": "string", "enum": ["free", "pro"], "description": "free ($0) o pro (DeepSeek)"}
                },
                "required": ["mission", "roles"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "extract_structured_data",
            "description": "Extrae y valida datos estructurados con tipado estricto (PydanticAI) en tiempo de ejecución a partir de texto o listas desordenadas.",
            "parameters": {
                "type": "object",
                "properties": {
                    "fields_spec": {
                        "type": "object",
                        "description": "Diccionario de campos y tipos esperados (ej: {'product_name': 'str', 'price': 'int', 'stock': 'int'})"
                    },
                    "user_input": {"type": "string", "description": "Texto sin estructurar del cual extraer la información"},
                    "tier": {"type": "string", "enum": ["free", "pro"], "description": "free ($0) o pro (DeepSeek)"}
                },
                "required": ["fields_spec", "user_input"]
            }
        }
    }
]

def extract_tool_calls(msg: dict) -> list[dict]:
    tool_calls = []
    if msg.get("tool_calls"):
        for tc in msg["tool_calls"]:
            try:
                args = json.loads(tc["function"].get("arguments", "{}"))
            except Exception:
                args = {}
            tool_calls.append({
                "id": tc.get("id", str(uuid.uuid4())),
                "name": tc["function"]["name"],
                "args": args
            })
        return tool_calls

    content = msg.get("content") or ""
    if "invoke name=" in content or "DSML" in content or "function_call" in content:
        invokes = re.findall(r"<[^>]*invoke\s+name=\"([^\"]+)\"[^>]*>(.*?)</[^>]*invoke>", content, re.DOTALL | re.IGNORECASE)
        for name, body in invokes:
            raw_params = re.findall(r"<[^>]*parameter\s+name=\"([^\"]+)\"[^>]*>(.*?)</[^>]*parameter>", body, re.DOTALL | re.IGNORECASE)
            if not raw_params:
                raw_params = re.findall(r"<[^>]*param\s+name=\"([^\"]+)\"[^>]*>(.*?)</[^>]*param>", body, re.DOTALL | re.IGNORECASE)
            params = dict(raw_params)
            if not params:
                try:
                    params = json.loads(body.strip())
                except Exception:
                    params = {}
            tool_calls.append({
                "id": str(uuid.uuid4()),
                "name": name.strip(),
                "args": {k.strip(): v.strip() if isinstance(v, str) else v for k, v in params.items()}
            })
    return tool_calls

async def execute_tool(fn_name: str, fn_args: dict) -> str:
    try:
        if fn_name == "describe_store_schema":
            raw_res = await describe_store_schema()
        elif fn_name == "execute_store_query":
            raw_res = await execute_store_query(fn_args.get("query", ""), fn_args.get("explanation", ""))
        elif fn_name == "get_store_products":
            raw_res = await get_store_products(fn_args.get("category", ""))
        elif fn_name == "update_product_price":
            raw_res = await update_product_price(fn_args.get("product_name", ""), int(fn_args.get("new_price", 0)))
        elif fn_name == "get_makeup_services":
            raw_res = await get_makeup_services()
        elif fn_name == "update_service_price":
            raw_res = await update_service_price(fn_args.get("service_name", ""), int(fn_args.get("new_price", 0)))
        elif fn_name == "get_recent_orders":
            raw_res = await get_recent_orders(int(fn_args.get("limit", 5)))
        elif fn_name == "get_makeup_bookings":
            raw_res = await get_makeup_bookings(int(fn_args.get("limit", 5)))
        elif fn_name == "start_zerops_service":
            raw_res = start_zerops_service(fn_args.get("service_name", ""))
        elif fn_name == "stop_zerops_service":
            raw_res = stop_zerops_service(fn_args.get("service_name", ""))
        elif fn_name == "list_zerops_services":
            raw_res = list_zerops_services()
        elif fn_name == "get_zerops_service_status":
            raw_res = get_zerops_service_status(fn_args.get("service_name", ""))
        elif fn_name == "read_web_file":
            raw_res = read_web_file(fn_args.get("relative_path", ""))
        elif fn_name == "edit_web_file":
            raw_res = edit_web_file(fn_args.get("relative_path", ""), fn_args.get("new_content", ""))
        elif fn_name == "git_web_status":
            raw_res = git_web_status()
        elif fn_name == "git_web_diff":
            raw_res = git_web_diff()
        elif fn_name == "deploy_webdev_preview":
            raw_res = deploy_webdev_preview(fn_args.get("commit_message", "chore: preview update from telegram"))
        elif fn_name == "promote_to_production_webprod":
            raw_res = promote_to_production_webprod(fn_args.get("commit_message", "release: promote to production from telegram"))
        elif fn_name == "git_web_log":
            raw_res = git_web_log(fn_args.get("branch_or_range", "main..dev"))
        elif fn_name == "git_web_diff_branches":
            raw_res = git_web_diff_branches(fn_args.get("base_branch", "main"), fn_args.get("target_branch", "dev"))
        elif fn_name == "read_file":
            raw_res = read_file(fn_args.get("path", ""))
        elif fn_name == "write_file":
            raw_res = write_file(fn_args.get("path", ""), fn_args.get("content", ""))
        elif fn_name == "edit_file":
            raw_res = edit_file(fn_args.get("path", ""), fn_args.get("target", ""), fn_args.get("replacement", ""))
        elif fn_name == "list_directory":
            raw_res = list_directory(fn_args.get("path", "/mnt/localstorage"))
        elif fn_name == "run_command":
            raw_res = run_command(fn_args.get("command", ""))
        elif fn_name == "search_web":
            raw_res = search_web(fn_args.get("query", ""), fn_args.get("max_results", 5))
        elif fn_name == "fetch_web_page":
            raw_res = fetch_web_page(fn_args.get("url", ""))
        elif fn_name == "download_file":
            raw_res = download_file(fn_args.get("url", ""), fn_args.get("destination_path", ""))
        elif fn_name == "run_crew_ai":
            raw_res = await run_crew_ai(fn_args.get("mission", ""), fn_args.get("roles", []), fn_args.get("tier", "free"))
        elif fn_name == "extract_structured_data":
            raw_res = await extract_structured_data(fn_args.get("fields_spec", {}), fn_args.get("user_input", ""), fn_args.get("tier", "free"))
        else:
            raw_res = f"Herramienta desconocida: {fn_name}"
        
        # Pointer Pattern: If tool output exceeds 8000 characters, persist to localstorage
        res_str = str(raw_res)
        if len(res_str) > 8000:
            artifacts_dir = "/mnt/localstorage/artifacts"
            os.makedirs(artifacts_dir, exist_ok=True)
            art_id = f"tool_{fn_name}_{uuid.uuid4().hex[:8]}.log"
            art_path = os.path.join(artifacts_dir, art_id)
            try:
                with open(art_path, "w", encoding="utf-8") as f:
                    f.write(res_str)
                return (
                    f"[OBSERVACIÓN TRUNCADA: total {len(res_str)} caracteres. Log persistido en {art_path}]\n"
                    f"=== HEAD PREVIEW ===\n{res_str[:3000]}\n"
                    f"... [SNIP {len(res_str) - 6000} caracteres] ...\n"
                    f"=== TAIL PREVIEW ===\n{res_str[-3000:]}"
                )
            except Exception:
                return res_str[:8000] + f"\n... [Truncado a 8000 caracteres]"
        return res_str
    except Exception as e:
        return f"Error ejecutando {fn_name}: {str(e)}"

async def load_chat_history(chat_id: int, limit: int = 10) -> list[dict]:
    """Loads recent messages from PostgreSQL 18 with localstorage SQLite fallback."""
    if not chat_id:
        return []
    db_url = os.getenv("DATABASE_URL")
    if db_url:
        try:
            import asyncpg
            conn = await asyncpg.connect(db_url, timeout=3.0)
            rows = await conn.fetch(
                """
                SELECT role, content FROM hermes_messages 
                WHERE chat_id = $1 
                ORDER BY id DESC LIMIT $2
                """,
                chat_id, limit
            )
            await conn.close()
            return [{"role": r["role"], "content": r["content"]} for r in reversed(rows)]
        except Exception:
            pass

    # Fallback: SQLite WAL on localstorage
    try:
        import aiosqlite
        db_path = "/mnt/localstorage/hermes/sessions.db"
        if os.path.exists(db_path):
            async with aiosqlite.connect(db_path, timeout=3.0) as db:
                db.row_factory = aiosqlite.Row
                cursor = await db.execute(
                    """
                    SELECT role, content FROM hermes_messages 
                    WHERE chat_id = ? 
                    ORDER BY id DESC LIMIT ?
                    """,
                    (chat_id, limit)
                )
                rows = await cursor.fetchall()
                return [{"role": r["role"], "content": r["content"]} for r in reversed(rows)]
    except Exception:
        pass
    return []

async def save_chat_turn(chat_id: int, user_text: str, assistant_text: str) -> None:
    """Persists conversation turn to PostgreSQL 18 and localstorage SQLite WAL."""
    if not chat_id:
        return
    db_url = os.getenv("DATABASE_URL")
    if db_url:
        try:
            import asyncpg
            conn = await asyncpg.connect(db_url, timeout=3.0)
            await conn.executemany(
                """
                INSERT INTO hermes_messages (chat_id, role, content) 
                VALUES ($1, $2, $3)
                """,
                [(chat_id, "user", user_text), (chat_id, "assistant", assistant_text)]
            )
            await conn.close()
        except Exception:
            pass

    # Local replica in SQLite WAL
    try:
        import aiosqlite, time
        os.makedirs("/mnt/localstorage/hermes", exist_ok=True)
        db_path = "/mnt/localstorage/hermes/sessions.db"
        async with aiosqlite.connect(db_path, timeout=3.0) as db:
            await db.execute("PRAGMA journal_mode=WAL;")
            await db.execute("""
                CREATE TABLE IF NOT EXISTS hermes_messages (
                    id INTEGER PRIMARY KEY AUTOINCREMENT,
                    chat_id INTEGER,
                    role TEXT,
                    content TEXT,
                    created_at REAL
                );
            """)
            now = time.time()
            await db.executemany(
                """
                INSERT INTO hermes_messages (chat_id, role, content, created_at)
                VALUES (?, ?, ?, ?)
                """,
                [(chat_id, "user", user_text, now), (chat_id, "assistant", assistant_text, now + 0.01)]
            )
            await db.commit()
    except Exception:
        pass

class HermesAgent:
    def __init__(self, system_prompt: str = None, role: str = "admin", bifrost_key: str = None, tools: list = None):
        self.role = role
        self.system_prompt = system_prompt or get_hermes_system_prompt()
        if role == "client":
            self.bifrost_key = bifrost_key or os.getenv("BIFROST_CLIENT_KEY", "vk-hermes-client")
            self.tools = tools if tools is not None else ECOMMERCE_TOOLS
        else:
            self.bifrost_key = bifrost_key or os.getenv("BIFROST_VIRTUAL_KEY", "vk-hermes-agent")
            self.tools = tools if tools is not None else ZEROPS_TOOLS
        self.history: list[dict[str, str]] = []

    async def run_turn(self, user_query: str, chat_id: int = 0) -> str:
        # Load persistent history (strictly last 6 messages = 3 turns max for lean context)
        persistent_history = await load_chat_history(chat_id, limit=6)
        active_history = persistent_history if persistent_history else self.history
        
        messages = [
            {"role": "system", "content": self.system_prompt},
            *active_history,
            {"role": "user", "content": user_query}
        ]
        
        final_content = ""
        max_tool_iterations = 10
        
        async with httpx.AsyncClient(timeout=60.0) as client:
            try:
                while max_tool_iterations > 0:
                    max_tool_iterations -= 1
                    res = await client.post(
                        f"{BIFROST_URL}/chat/completions",
                        headers={"Authorization": f"Bearer {self.bifrost_key}"},
                        json={
                            "model": MODEL_NAME,
                            "messages": messages,
                            "tools": self.tools,
                            "temperature": 0.3,
                        }
                    )
                    if res.status_code != 200:
                        return f"[Hermes] Error from AI Gateway: {res.status_code}"
                    
                    data = res.json()
                    msg = data["choices"][0]["message"]
                    parsed_tool_calls = extract_tool_calls(msg)
                    
                    if not parsed_tool_calls:
                        raw_content = msg.get("content") or ""
                        cleaned = re.sub(r"<[^>]*function_call.*?</[^>]*function_call>", "", raw_content, flags=re.DOTALL | re.IGNORECASE)
                        cleaned = re.sub(r"<[^>]*tool_call.*?</[^>]*tool_call>", "", cleaned, flags=re.DOTALL | re.IGNORECASE)
                        cleaned = re.sub(r"<[^>]*invoke.*?</[^>]*invoke>", "", cleaned, flags=re.DOTALL | re.IGNORECASE)
                        cleaned = re.sub(r"<[｜|\s]*DSML.*?</[｜|\s]*DSML[｜|\s]*tool_calls>", "", cleaned, flags=re.DOTALL | re.IGNORECASE).strip()
                        final_content = cleaned if cleaned else raw_content
                        break
                    
                    assistant_msg = {"role": "assistant"}
                    if msg.get("tool_calls"):
                        assistant_msg["tool_calls"] = msg["tool_calls"]
                    elif parsed_tool_calls:
                        assistant_msg["tool_calls"] = [
                            {
                                "id": tc["id"],
                                "type": "function",
                                "function": {
                                    "name": tc["name"],
                                    "arguments": json.dumps(tc["args"])
                                }
                            }
                            for tc in parsed_tool_calls
                        ]
                    if msg.get("content"):
                        assistant_msg["content"] = msg["content"]
                    messages.append(assistant_msg)
                    
                    for tc in parsed_tool_calls:
                        fn_name = tc["name"]
                        fn_args = tc["args"]
                        tool_result = await execute_tool(fn_name, fn_args)
                        messages.append({
                            "role": "tool",
                            "tool_call_id": tc["id"],
                            "content": str(tool_result)
                        })
                
                if not final_content:
                    # Final synthesis call without tools if iterations exhausted
                    messages.append({
                        "role": "user",
                        "content": "Con base en todas las herramientas ejecutadas, responde de forma completa y profesional al usuario sintetizando los resultados y hallazgos."
                    })
                    res_final = await client.post(
                        f"{BIFROST_URL}/chat/completions",
                        headers={"Authorization": f"Bearer {self.bifrost_key}"},
                        json={
                            "model": MODEL_NAME,
                            "messages": messages,
                            "temperature": 0.3,
                        }
                    )
                    if res_final.status_code == 200:
                        data_final = res_final.json()
                        raw_final = data_final["choices"][0]["message"].get("content") or ""
                        cleaned_final = re.sub(r"<[｜|\s]*DSML.*?</[｜|\s]*DSML[｜|\s]*tool_calls>", "", raw_final, flags=re.DOTALL).strip()
                        final_content = cleaned_final if cleaned_final else raw_final
                    if not final_content:
                        final_content = "⚠️ Se alcanzó el límite de llamadas a herramientas sin que el modelo produjera una respuesta final. Verificá el resultado en la base de datos o reformulá tu solicitud."
                
                await save_chat_turn(chat_id, user_query, final_content)
                self.history.append({"role": "user", "content": user_query})
                self.history.append({"role": "assistant", "content": final_content})
                if len(self.history) > 10:
                    self.history = self.history[-10:]
                return final_content
            except Exception as e:
                return f"[Hermes] Error procesando solicitud: {str(e)}"

if __name__ == "__main__":
    import asyncio
    print("🤖 Hermes Interactive CLI (escribí 'exit' o 'salir' para terminar)")
    agent = HermesAgent()
    while True:
        try:
            query = input("\nHermes > ")
            if not query.strip():
                continue
            if query.strip().lower() in ("exit", "quit", "salir"):
                print("¡Hasta luego!")
                break
            reply = asyncio.run(agent.run_turn(query))
            print(f"\n{reply}\n")
        except (KeyboardInterrupt, EOFError):
            print("\n¡Hasta luego!")
            break
