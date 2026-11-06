"""
Hermes-Agent Execution Loop
"""
import os
import re
import json
import uuid
import logging
import httpx

logger = logging.getLogger("hermes.agent")
try:
    from prompts import HERMES_SYSTEM_PROMPT, format_chatml_prompt, get_hermes_system_prompt
    from tools import (
        get_system_health, calculate_natal_chart, send_whatsapp_otp,
        list_zerops_services, start_zerops_service, stop_zerops_service, delete_zerops_service, get_zerops_service_status,
        read_web_file, edit_web_file, git_web_status, git_web_diff,
        deploy_webdev_preview, promote_to_production_webprod,
        git_web_log, git_web_diff_branches,
        read_file, write_file, edit_file, list_directory, run_command,
        search_web, fetch_web_page, download_file,
        describe_store_schema, execute_store_query,
        create_store_product, set_site_image,
        get_store_products, update_product_price,
        get_store_services, get_makeup_services,
        update_service_price, get_recent_orders,
        get_store_bookings, get_makeup_bookings,
        run_crew_ai, extract_structured_data,
        list_available_crews, get_paperclip_status,
        mem_context, mem_search, mem_save
    )
except (ImportError, ValueError):
    from .prompts import HERMES_SYSTEM_PROMPT, format_chatml_prompt, get_hermes_system_prompt
    from .tools import (
        get_system_health, calculate_natal_chart, send_whatsapp_otp,
        list_zerops_services, start_zerops_service, stop_zerops_service, delete_zerops_service, get_zerops_service_status,
        read_web_file, edit_web_file, git_web_status, git_web_diff,
        deploy_webdev_preview, promote_to_production_webprod,
        git_web_log, git_web_diff_branches,
        read_file, write_file, edit_file, list_directory, run_command,
        search_web, fetch_web_page, download_file,
        describe_store_schema, execute_store_query,
        create_store_product, set_site_image,
        get_store_products, update_product_price,
        get_store_services, get_makeup_services,
        update_service_price, get_recent_orders,
        get_store_bookings, get_makeup_bookings,
        run_crew_ai, extract_structured_data,
        list_available_crews, get_paperclip_status,
        mem_context, mem_search, mem_save
    )

BIFROST_URL = os.getenv("HERMES_MODEL_ENDPOINT", "http://bifrost:8080/v1")
MODEL_NAME = os.getenv("HERMES_MODEL_OVERRIDE") or os.getenv("HERMES_MODEL_NAME") or "deepseek-chat"
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
    },
    {
        "type": "function",
        "function": {
            "name": "create_store_product",
            "description": "Crea o actualiza un producto en el catálogo de la tienda en PostgreSQL 18. Recibe el nombre comercial, precio en COP, stock y la foto adjunta. Normaliza automáticamente la URL en Astro.",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "description": "Nombre comercial elegante del producto (ej: 'Enterizo Escultor Zafiro')"},
                    "base_price": {"type": "integer", "description": "Precio numérico en COP (ej: 120000)"},
                    "stock": {"type": "integer", "description": "Cantidad de unidades en inventario (ej: 2)"},
                    "image_filename_or_url": {"type": "string", "description": "Nombre de archivo de la foto guardada en localstorage (ej: 'telegram_116_AQADaw1rG5KL-UZ-.jpg') o ruta relativa '/images/products/...'"},
                    "category": {"type": "string", "description": "Categoría (por defecto 'activewear')"},
                    "description": {"type": "string", "description": "Descripción del producto"}
                },
                "required": ["name", "base_price", "stock", "image_filename_or_url"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "set_site_image",
            "description": "Actualiza la imagen principal o secundaria del sitio web en PostgreSQL 18 (tabla site_settings, clave 'hero_image' para la portada principal). Se refleja en vivo vía SSR.",
            "parameters": {
                "type": "object",
                "properties": {
                    "key": {"type": "string", "enum": ["hero_image", "hero_secondary_image"], "description": "Clave visual a actualizar ('hero_image' para la portada principal)"},
                    "image_filename_or_url": {"type": "string", "description": "Nombre de archivo de la foto (ej: 'telegram_108_AQADaw1rG5KL-UZ-.jpg')"},
                    "alt": {"type": "string", "description": "Texto alternativo descriptivo de la imagen"},
                    "title": {"type": "string", "description": "Título opcional en el card visual"},
                    "badge": {"type": "string", "description": "Etiqueta opcional (ej: 'Estructura Seamless')"},
                    "price": {"type": "string", "description": "Precio opcional mostrado en el hero"}
                },
                "required": ["key", "image_filename_or_url"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "mem_context",
            "description": "Recupera las observaciones más recientes de la memoria persistente compartida Engram (SSoT) para el proyecto activo. Usar al inicio de una tarea o sesión para no repetir análisis ni gastar tokens.",
            "parameters": {
                "type": "object",
                "properties": {
                    "limit": {"type": "integer", "description": "Cantidad de observaciones recientes a retornar (por defecto 5)"}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "mem_search",
            "description": "Busca en la memoria persistente Engram por palabras clave en títulos, temas y contenido. Usar cuando el usuario mencione decisiones, arquitecturas o tareas pasadas.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Término o palabra clave a buscar en Engram"},
                    "limit": {"type": "integer", "description": "Máximo de resultados a retornar (por defecto 5)"}
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "mem_save",
            "description": "Guarda de forma persistente e indestructible una nueva observación, decisión o descubrimiento en Engram (SSoT compartido en localstorage).",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "Título conciso (Verbo + objeto)"},
                    "content": {"type": "string", "description": "Contenido detallado (What, Why, Where, Learned)"},
                    "type": {"type": "string", "enum": ["discovery", "architecture", "decision", "bugfix", "pattern", "config", "preference"], "description": "Tipo de memoria"},
                    "topic_key": {"type": "string", "description": "Clave estable de tema (ej: 'hermes/ops', 'seo/strategy')"}
                },
                "required": ["title", "content"]
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
            "name": "delete_zerops_service",
            "description": "Delete or permanently remove a Zerops service stack by name (e.g. 'videoworker', 'brand'). Use this when the user explicitly asks to delete or remove a service.",
            "parameters": {
                "type": "object",
                "properties": {
                    "service_name": {
                        "type": "string",
                        "description": "The exact service name, e.g. 'videoworker'"
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
    },
    {
        "type": "function",
        "function": {
            "name": "list_available_crews",
            "description": "Lista todas las cuadrillas autónomas de CrewAI pre-registradas (seo_aeo_geo, general_research, astrology_timing, google_seo) y la capacidad de orquestar las 141 skills de CoHaLo.",
            "parameters": {
                "type": "object",
                "properties": {}
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_paperclip_status",
            "description": "Consulta el estado en vivo de la plataforma Paperclip AI (http://paperclip:3100), incluyendo los agentes registrados (Hermes y CrewAI), tareas y salud del board.",
            "parameters": {
                "type": "object",
                "properties": {}
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
    if not content:
        return []

    # 1. ChatML format: <|tool_call|><|tool_name|>NAME<|tool_name|><|parameters|>JSON<|parameters|>
    chatml_matches = re.findall(
        r"<[\||\s]*tool_call[\||\s]*>\s*<[\||\s]*tool_name[\||\s]*>([^<]+)<[\||\s]*/tool_name[\||\s]*>\s*<[\||\s]*parameters[\||\s]*>(.*?)<[\||\s]*/parameters[\||\s]*>",
        content,
        re.DOTALL | re.IGNORECASE
    )
    for name, body in chatml_matches:
        params = {}
        try:
            params = json.loads(body.strip())
        except Exception:
            raw_params = re.findall(r"\"([^\"]+)\"\s*:\s*\"([^\"]+)\"", body)
            params = dict(raw_params)
        tool_calls.append({
            "id": str(uuid.uuid4()),
            "name": name.strip(),
            "args": params if isinstance(params, dict) else {}
        })

    # 2. XML invoke format: <invoke name="NAME">...</invoke> (including <dots_function_call>)
    if "<invoke" in content or "invoke name=" in content or "dots_function_call" in content:
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

    # 3. Standard XML <tool_call><name>...</name><arguments>...</arguments></tool_call>
    if "<tool_call>" in content and not chatml_matches and not tool_calls:
        xml_matches = re.findall(r"<tool_call>\s*<(?:name|tool_name)>([^<]+)</(?:name|tool_name)>\s*<(?:arguments|parameters)>(.*?)</(?:arguments|parameters)>\s*</tool_call>", content, re.DOTALL | re.IGNORECASE)
        for name, body in xml_matches:
            try:
                params = json.loads(body.strip())
            except Exception:
                params = {}
            tool_calls.append({
                "id": str(uuid.uuid4()),
                "name": name.strip(),
                "args": params if isinstance(params, dict) else {}
            })

    return tool_calls

TOOL_DISPATCH = {
    "describe_store_schema": lambda a: describe_store_schema(),
    "create_store_product": lambda a: create_store_product(
        a.get("name", ""), int(a.get("base_price", 0)), int(a.get("stock", 1)),
        a.get("image_filename_or_url", ""), a.get("category", "activewear"), a.get("description", "")
    ),
    "set_site_image": lambda a: set_site_image(
        a.get("key", "hero_image"), a.get("image_filename_or_url", ""),
        a.get("alt", ""), a.get("title", ""), a.get("badge", ""), a.get("price", "")
    ),
    "execute_store_query": lambda a: execute_store_query(a.get("query", ""), a.get("explanation", "")),
    "get_store_products": lambda a: get_store_products(a.get("category", "")),
    "update_product_price": lambda a: update_product_price(a.get("product_name", ""), int(a.get("new_price", 0))),
    "get_store_services": lambda a: get_store_services(),
    "get_makeup_services": lambda a: get_store_services(),
    "update_service_price": lambda a: update_service_price(a.get("service_name", ""), int(a.get("new_price", 0))),
    "get_recent_orders": lambda a: get_recent_orders(int(a.get("limit", 5))),
    "get_store_bookings": lambda a: get_store_bookings(int(a.get("limit", 5))),
    "get_makeup_bookings": lambda a: get_store_bookings(int(a.get("limit", 5))),
    "start_zerops_service": lambda a: start_zerops_service(a.get("service_name", "")),
    "stop_zerops_service": lambda a: stop_zerops_service(a.get("service_name", "")),
    "delete_zerops_service": lambda a: delete_zerops_service(a.get("service_name", "")),
    "list_zerops_services": lambda a: list_zerops_services(),
    "get_zerops_service_status": lambda a: get_zerops_service_status(a.get("service_name", "")),
    "read_web_file": lambda a: read_web_file(a.get("relative_path", "")),
    "edit_web_file": lambda a: edit_web_file(a.get("relative_path", ""), a.get("new_content", "")),
    "git_web_status": lambda a: git_web_status(),
    "git_web_diff": lambda a: git_web_diff(),
    "deploy_webdev_preview": lambda a: deploy_webdev_preview(a.get("commit_message", "chore: preview update from telegram")),
    "promote_to_production_webprod": lambda a: promote_to_production_webprod(a.get("commit_message", "release: promote to production from telegram")),
    "git_web_log": lambda a: git_web_log(a.get("branch_or_range", "main..dev")),
    "git_web_diff_branches": lambda a: git_web_diff_branches(a.get("base_branch", "main"), a.get("target_branch", "dev")),
    "read_file": lambda a: read_file(a.get("path", "")),
    "write_file": lambda a: write_file(a.get("path", ""), a.get("content", "")),
    "edit_file": lambda a: edit_file(a.get("path", ""), a.get("target", ""), a.get("replacement", "")),
    "list_directory": lambda a: list_directory(a.get("path", "/mnt/localstorage")),
    "run_command": lambda a: run_command(a.get("command", "")),
    "search_web": lambda a: search_web(a.get("query", ""), a.get("max_results", 5)),
    "fetch_web_page": lambda a: fetch_web_page(a.get("url", "")),
    "download_file": lambda a: download_file(a.get("url", ""), a.get("destination_path", "")),
    "run_crew_ai": lambda a: run_crew_ai(a.get("mission", ""), a.get("roles", []), a.get("tier", "free")),
    "extract_structured_data": lambda a: extract_structured_data(a.get("fields_spec", {}), a.get("user_input", ""), a.get("tier", "free")),
    "list_available_crews": lambda a: list_available_crews(),
    "get_paperclip_status": lambda a: get_paperclip_status(),
    "mem_context": lambda a: mem_context(int(a.get("limit", 5))),
    "mem_search": lambda a: mem_search(a.get("query", ""), int(a.get("limit", 5))),
    "mem_save": lambda a: mem_save(a.get("title", ""), a.get("content", ""), a.get("type", "discovery"), a.get("topic_key", "")),
}

async def execute_tool(fn_name: str, fn_args: dict) -> str:
    try:
        handler = TOOL_DISPATCH.get(fn_name)
        if not handler:
            return f"Herramienta desconocida: {fn_name}"
        res = handler(fn_args)
        if asyncio.iscoroutine(res):
            raw_res = await res
        else:
            raw_res = res
        
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
                        logger.warning(f"[Hermes] Primary gateway status {res.status_code}. Retrying with pro failover...")
                        res = await client.post(
                            f"{BIFROST_URL}/chat/completions",
                            headers={
                                "Authorization": f"Bearer {self.bifrost_key}",
                                "x-force-deepseek": "true",
                                "x-routing-tier": "pro"
                            },
                            json={
                                "model": MODEL_NAME,
                                "messages": messages,
                                "tools": self.tools,
                                "temperature": 0.3,
                            },
                            timeout=120.0
                        )
                        if res.status_code != 200:
                            logger.error(f"[Hermes] Gateway fallback failed: {res.status_code} - {res.text}")
                            return "⚠️ El gateway de inferencia está experimentando alta demanda temporal. Por favor intentá nuevamente en unos momentos."
                    
                    data = res.json()
                    msg = data["choices"][0]["message"]
                    parsed_tool_calls = extract_tool_calls(msg)
                    
                    if not parsed_tool_calls:
                        raw_content = msg.get("content") or ""
                        cleaned = re.sub(r"<[^>]*function_call.*?</[^>]*function_call>", "", raw_content, flags=re.DOTALL | re.IGNORECASE)
                        cleaned = re.sub(r"<[^>]*tool_call.*?</[^>]*tool_call>", "", cleaned, flags=re.DOTALL | re.IGNORECASE)
                        cleaned = re.sub(r"<[\||\s]*tool_calls?[\||\s]*>.*?</[\||\s]*tool_calls?[\||\s]*>", "", cleaned, flags=re.DOTALL | re.IGNORECASE)
                        cleaned = re.sub(r"<dots_function_call>.*?</dots_function_call>", "", cleaned, flags=re.DOTALL | re.IGNORECASE)
                        cleaned = re.sub(r"<[^>]*invoke.*?</[^>]*invoke>", "", cleaned, flags=re.DOTALL | re.IGNORECASE)
                        cleaned = re.sub(r"<[｜|\s]*DSML.*?</[｜|\s]*DSML[｜|\s]*tool_calls>", "", cleaned, flags=re.DOTALL | re.IGNORECASE)
                        cleaned = re.sub(r"<[\||\s]*(?:tool_calls?|tool_name|parameters)[\||\s]*>", "", cleaned, flags=re.IGNORECASE)
                        cleaned = re.sub(r"</[\||\s]*(?:tool_calls?|tool_name|parameters)[\||\s]*>", "", cleaned, flags=re.IGNORECASE)
                        cleaned = re.sub(r"</?dots_function_call>", "", cleaned, flags=re.IGNORECASE).strip()
                        final_content = cleaned if cleaned else raw_content
                        if not final_content.strip() or ("<|" in final_content and "|>" in final_content):
                            logger.warning("[Hermes] Model output contained corrupted or unparsed tool syntax. Retrying with pro failover...")
                            res_pro = await client.post(
                                f"{BIFROST_URL}/chat/completions",
                                headers={
                                    "Authorization": f"Bearer {self.bifrost_key}",
                                    "x-force-deepseek": "true",
                                    "x-routing-tier": "pro"
                                },
                                json={
                                    "model": MODEL_NAME,
                                    "messages": messages,
                                    "tools": self.tools,
                                    "temperature": 0.3,
                                },
                                timeout=120.0
                            )
                            if res_pro.status_code == 200:
                                data_pro = res_pro.json()
                                msg_pro = data_pro["choices"][0]["message"]
                                parsed_pro = extract_tool_calls(msg_pro)
                                if parsed_pro:
                                    parsed_tool_calls = parsed_pro
                                    msg = msg_pro
                                else:
                                    final_content = (msg_pro.get("content") or "").strip()
                                    break
                            else:
                                break
                        else:
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
