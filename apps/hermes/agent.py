"""
Hermes-Agent Execution Loop
Sovereign Master Agent for Apotelos Multi-Agent Mesh & MentorIA
"""
import os
import re
import json
import uuid
import logging
import asyncio
import httpx

logger = logging.getLogger("hermes.agent")
try:
    from prompts import HERMES_SYSTEM_PROMPT, format_chatml_prompt, get_hermes_system_prompt
    from tools import (
        get_system_health, calculate_natal_chart, send_whatsapp_otp,
        list_zerops_services, start_zerops_service, stop_zerops_service, delete_zerops_service, get_zerops_service_status,
        zerops_get_service_logs, zerops_deploy_service,
        pidev_get_status, pidev_dispatch_task,
        read_file, write_file, edit_file, list_directory, run_command,
        search_web, fetch_web_page, download_file,
        execute_store_query,
        run_crew_ai, extract_structured_data,
        list_available_crews, get_paperclip_status,
        paperclip_list_tasks, paperclip_create_task, paperclip_register_agent,
        mem_context, mem_search, mem_save,
        linear_create_issue, linear_update_status, linear_get_issue, linear_comment_issue
    )
except (ImportError, ValueError):
    from .prompts import HERMES_SYSTEM_PROMPT, format_chatml_prompt, get_hermes_system_prompt
    from .tools import (
        get_system_health, calculate_natal_chart, send_whatsapp_otp,
        list_zerops_services, start_zerops_service, stop_zerops_service, delete_zerops_service, get_zerops_service_status,
        zerops_get_service_logs, zerops_deploy_service,
        pidev_get_status, pidev_dispatch_task,
        read_file, write_file, edit_file, list_directory, run_command,
        search_web, fetch_web_page, download_file,
        execute_store_query,
        run_crew_ai, extract_structured_data,
        list_available_crews, get_paperclip_status,
        paperclip_list_tasks, paperclip_create_task, paperclip_register_agent,
        mem_context, mem_search, mem_save,
        linear_create_issue, linear_update_status, linear_get_issue, linear_comment_issue
    )

BIFROST_URL = os.getenv("HERMES_MODEL_ENDPOINT", "http://bifrost:8080/v1")
MODEL_NAME = os.getenv("HERMES_MODEL_OVERRIDE") or os.getenv("HERMES_MODEL_NAME") or "auto"
BIFROST_KEY = os.getenv("BIFROST_VIRTUAL_KEY", "vk-hermes-agent")

HERMES_TOOLS = [
    {
        "type": "function",
        "function": {
            "name": "get_system_health",
            "description": "Verifica el estado de salud en tiempo real de todos los componentes del cluster (Paperclip, NATS, PostgreSQL, Zerops).",
            "parameters": {"type": "object", "properties": {}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_zerops_services",
            "description": "Lista todos los servicios desplegados en el proyecto de Zerops y su estado actual (ACTIVE / STOPPED).",
            "parameters": {"type": "object", "properties": {}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_zerops_service_status",
            "description": "Consulta el estado y salud detallada de un servicio específico de Zerops.",
            "parameters": {
                "type": "object",
                "properties": {
                    "service_name": {"type": "string", "description": "Nombre exacto del servicio (ej: 'paperclip', 'bifrost', 'hermes', 'pidev')"}
                },
                "required": ["service_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "start_zerops_service",
            "description": "Inicia o enciende un servicio de Zerops por nombre.",
            "parameters": {
                "type": "object",
                "properties": {
                    "service_name": {"type": "string", "description": "Nombre del servicio"}
                },
                "required": ["service_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "stop_zerops_service",
            "description": "Detiene o apaga un servicio de Zerops por nombre.",
            "parameters": {
                "type": "object",
                "properties": {
                    "service_name": {"type": "string", "description": "Nombre del servicio"}
                },
                "required": ["service_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "delete_zerops_service",
            "description": "Elimina de forma segura un servicio de Zerops cuando es requerido.",
            "parameters": {
                "type": "object",
                "properties": {
                    "service_name": {"type": "string", "description": "Nombre del servicio"}
                },
                "required": ["service_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "zerops_get_service_logs",
            "description": "Obtiene los logs recientes de runtime o build de cualquier contenedor en Zerops.",
            "parameters": {
                "type": "object",
                "properties": {
                    "service_name": {"type": "string", "description": "Nombre del servicio (ej: 'paperclip', 'bifrost', 'hermes', 'pidev')"},
                    "limit": {"type": "integer", "description": "Cantidad de líneas a recuperar", "default": 50}
                },
                "required": ["service_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "zerops_deploy_service",
            "description": "Dispara el despliegue o push de código a cualquier servicio de Zerops.",
            "parameters": {
                "type": "object",
                "properties": {
                    "service_name": {"type": "string", "description": "Nombre del servicio a desplegar"},
                    "working_dir": {"type": "string", "description": "Directorio local de origen (opcional)", "default": ""}
                },
                "required": ["service_name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "pidev_get_status",
            "description": "Consulta la salud en tiempo real, versión de Gentle-Pi y disponibilidad del servicio PiDev.",
            "parameters": {"type": "object", "properties": {}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "pidev_dispatch_task",
            "description": "Despacha una misión de programación o desarrollo frontend (Astro, TypeScript) al agente soberano PiDev (gentle-pi).",
            "parameters": {
                "type": "object",
                "properties": {
                    "prompt": {"type": "string", "description": "Instrucción clara de desarrollo o edición de código para Gentle-Pi"},
                    "working_dir": {"type": "string", "description": "Directorio de trabajo dentro de pidev (default: '/var/www')", "default": "/var/www"}
                },
                "required": ["prompt"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "linear_create_issue",
            "description": "Crea una nueva tarea o issue en Linear vinculado al proyecto activo.",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "Título claro de la tarea"},
                    "description": {"type": "string", "description": "Descripción y criterios de aceptación"},
                    "priority": {"type": "integer", "description": "Prioridad (0=None, 1=Urgent, 2=High, 3=Normal, 4=Low)", "default": 2}
                },
                "required": ["title"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "linear_update_status",
            "description": "Actualiza el estado de una tarea en Linear (Done requiere evidencia comprobable).",
            "parameters": {
                "type": "object",
                "properties": {
                    "issue_id": {"type": "string", "description": "ID del issue (ej: 'BAI-449')"},
                    "status": {"type": "string", "enum": ["Todo", "In Progress", "Done", "Canceled"], "description": "Nuevo estado"},
                    "evidence": {"type": "string", "description": "Evidencia técnica física que valida el cambio de estado"}
                },
                "required": ["issue_id", "status"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "linear_get_issue",
            "description": "Obtiene los detalles, descripción y estado actual de una tarea en Linear.",
            "parameters": {
                "type": "object",
                "properties": {
                    "issue_id": {"type": "string", "description": "ID del issue (ej: 'BAI-449')"}
                },
                "required": ["issue_id"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "linear_comment_issue",
            "description": "Añade un comentario u observación técnica a una tarea en Linear.",
            "parameters": {
                "type": "object",
                "properties": {
                    "issue_id": {"type": "string", "description": "ID del issue"},
                    "comment": {"type": "string", "description": "Texto del comentario"}
                },
                "required": ["issue_id", "comment"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "get_paperclip_status",
            "description": "Consulta el estado en vivo de Paperclip AI (http://paperclip:3100), incluyendo agentes registrados, tareas y spend caps.",
            "parameters": {"type": "object", "properties": {}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "paperclip_list_tasks",
            "description": "Lista tareas e issues activos registrados en el tablero Kanban de Paperclip Control Plane.",
            "parameters": {
                "type": "object",
                "properties": {
                    "status": {
                        "type": "string",
                        "description": "Filtro opcional por estado (todo, in_progress, in_review, done, backlog)"
                    }
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "paperclip_create_task",
            "description": "Crea una nueva tarea o issue en el tablero Kanban de Paperclip Control Plane.",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {
                        "type": "string",
                        "description": "Título claro y conciso de la tarea"
                    },
                    "description": {
                        "type": "string",
                        "description": "Detalles o criterios de aceptación de la tarea"
                    },
                    "priority": {
                        "type": "string",
                        "description": "Prioridad de la tarea (low, medium, high, urgent)",
                        "enum": ["low", "medium", "high", "urgent"]
                    }
                },
                "required": ["title"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "paperclip_register_agent",
            "description": "Registra un nuevo agente permanente en el organigrama y control plane de Paperclip bajo la supervisión de Hermes.",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {
                        "type": "string",
                        "description": "Nombre del agente (ej. Closer de Ventas, Especialista DIAN, Analista de Mercado)"
                    },
                    "title": {
                        "type": "string",
                        "description": "Cargo formal del agente en el organigrama"
                    },
                    "role": {
                        "type": "string",
                        "description": "Nivel jerárquico (lead, worker)",
                        "enum": ["lead", "worker"]
                    },
                    "adapter_type": {
                        "type": "string",
                        "description": "Tipo de adaptador de ejecución (hermes_gateway, pi_local, process)",
                        "enum": ["hermes_gateway", "pi_local", "process"]
                    },
                    "capabilities": {
                        "type": "string",
                        "description": "Descripción concisa de las capacidades y responsabilidades del agente"
                    },
                    "budget_monthly_cents": {
                        "type": "integer",
                        "description": "Techo de gasto mensual en centavos de dólar (default: 50000 = $500 USD)"
                    }
                },
                "required": ["name"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "run_crew_ai",
            "description": "Despacha una cuadrilla autónoma multi-agente en memoria (CrewAI) para misiones complejas. Puede componer agentes por roles ad-hoc o conectar skills de CoHaLo, con validación Pydantic opcional.",
            "parameters": {
                "type": "object",
                "properties": {
                    "mission": {"type": "string", "description": "Objetivo o consigna general para la cuadrilla"},
                    "roles": {
                        "type": "array",
                        "description": "Lista opcional de agentes con rol, meta y backstory",
                        "items": {"type": "object"}
                    },
                    "skills": {
                        "type": "array",
                        "description": "Lista opcional de nombres de skills CoHaLo a invocar (ej: ['seo-aeo-geo', 'automation-engine'])",
                        "items": {"type": "string"}
                    },
                    "output_schema": {
                        "type": "object",
                        "description": "Diccionario opcional de validación Pydantic (ej: {'estrategia': 'str', 'precio_sugerido_usd': 'int', 'acciones': 'list[str]'})",
                        "additionalProperties": {"type": "string"}
                    },
                    "tier": {"type": "string", "enum": ["free", "pro"], "default": "free"}
                },
                "required": ["mission"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_available_crews",
            "description": "Lista todas las cuadrillas autónomas de CrewAI pre-registradas (general_research, astrology_timing, seo_aeo_geo, google_seo).",
            "parameters": {"type": "object", "properties": {}}
        }
    },
    {
        "type": "function",
        "function": {
            "name": "extract_structured_data",
            "description": "Extrae y valida datos estructurados con tipado estricto (PydanticAI) en tiempo de ejecución a partir de texto desordenado.",
            "parameters": {
                "type": "object",
                "properties": {
                    "fields_spec": {
                        "type": "object",
                        "description": "Diccionario campo:tipo (ej: {'nombre': 'str', 'score': 'float', 'tags': 'list[str]'})"
                    },
                    "user_input": {"type": "string", "description": "Texto sin estructurar del cual extraer la información"},
                    "tier": {"type": "string", "enum": ["free", "pro"], "default": "free"}
                },
                "required": ["fields_spec", "user_input"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "mem_context",
            "description": "Recupera las observaciones más recientes de la memoria persistente Engram (SSoT) para el proyecto activo.",
            "parameters": {
                "type": "object",
                "properties": {
                    "limit": {"type": "integer", "default": 5}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "mem_search",
            "description": "Busca en la memoria persistente Engram por palabras clave en títulos, temas y contenido.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Término o palabra clave a buscar"},
                    "limit": {"type": "integer", "default": 5}
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "mem_save",
            "description": "Guarda de forma persistente una nueva observación, decisión o descubrimiento en Engram.",
            "parameters": {
                "type": "object",
                "properties": {
                    "title": {"type": "string", "description": "Título conciso (Verbo + objeto)"},
                    "content": {"type": "string", "description": "Contenido detallado"},
                    "type": {"type": "string", "enum": ["discovery", "architecture", "decision", "bugfix", "pattern", "config", "preference"]},
                    "topic_key": {"type": "string", "description": "Clave estable de tema"}
                },
                "required": ["title", "content"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "read_file",
            "description": "Lee cualquier archivo del filesystem por ruta absoluta (ej: '/mnt/localstorage/...', '/var/www/...').",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Ruta absoluta del archivo"}
                },
                "required": ["path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "write_file",
            "description": "Crea o sobreescribe un archivo con contenido completo.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Ruta del archivo"},
                    "content": {"type": "string", "description": "Contenido a escribir"}
                },
                "required": ["path", "content"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "edit_file",
            "description": "Realiza reemplazo quirúrgico exacto de cadenas de texto en un archivo.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Ruta del archivo"},
                    "target": {"type": "string", "description": "Texto exacto a reemplazar"},
                    "replacement": {"type": "string", "description": "Texto nuevo de reemplazo"}
                },
                "required": ["path", "target", "replacement"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "list_directory",
            "description": "Lista archivos y subdirectorios de una ruta en disco.",
            "parameters": {
                "type": "object",
                "properties": {
                    "path": {"type": "string", "description": "Ruta del directorio (ej: '/mnt/localstorage')"}
                }
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "run_command",
            "description": "Ejecuta comandos de shell en el contenedor de Hermes (git, python, curl, scripts).",
            "parameters": {
                "type": "object",
                "properties": {
                    "command": {"type": "string", "description": "Comando a ejecutar"}
                },
                "required": ["command"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "search_web",
            "description": "Búsqueda en vivo en la web mediante Tavily API con Brave fallback.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Consulta de búsqueda"},
                    "max_results": {"type": "integer", "default": 5}
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "fetch_web_page",
            "description": "Extrae el contenido limpio en Markdown de cualquier página web mediante Jina Reader.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "URL HTTP/HTTPS a extraer"}
                },
                "required": ["url"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "download_file",
            "description": "Descarga activos o binarios directamente desde una URL hacia una ruta local.",
            "parameters": {
                "type": "object",
                "properties": {
                    "url": {"type": "string", "description": "URL directa de descarga"},
                    "destination_path": {"type": "string", "description": "Ruta de destino en disco"}
                },
                "required": ["url", "destination_path"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "execute_query",
            "description": "Ejecuta consultas SQL arbitrarias sobre la base de datos PostgreSQL 18 activa. Operaciones destructivas (DROP/TRUNCATE) están prohibidas.",
            "parameters": {
                "type": "object",
                "properties": {
                    "query": {"type": "string", "description": "Consulta SQL válida para PostgreSQL"},
                    "explanation": {"type": "string", "description": "Propósito de la consulta"}
                },
                "required": ["query"]
            }
        }
    },
    {
        "type": "function",
        "function": {
            "name": "calculate_natal_chart",
            "description": "Calcula efemérides y carta natal astronómica precisa (Oraculo Astrological Worker).",
            "parameters": {
                "type": "object",
                "properties": {
                    "name": {"type": "string", "default": "Client"},
                    "year": {"type": "integer", "default": 1990},
                    "month": {"type": "integer", "default": 1},
                    "day": {"type": "integer", "default": 1},
                    "hour": {"type": "integer", "default": 12},
                    "minute": {"type": "integer", "default": 0},
                    "lat": {"type": "number", "default": 4.7110},
                    "lon": {"type": "number", "default": -74.0721},
                    "city": {"type": "string", "default": "Bogota"},
                    "nation": {"type": "string", "default": "Colombia"}
                }
            }
        }
    }
]

TOOL_DISPATCH = {
    "get_system_health": lambda a: get_system_health(),
    "list_zerops_services": lambda a: list_zerops_services(),
    "get_zerops_service_status": lambda a: get_zerops_service_status(a.get("service_name", "")),
    "start_zerops_service": lambda a: start_zerops_service(a.get("service_name", "")),
    "stop_zerops_service": lambda a: stop_zerops_service(a.get("service_name", "")),
    "delete_zerops_service": lambda a: delete_zerops_service(a.get("service_name", "")),
    "zerops_get_service_logs": lambda a: zerops_get_service_logs(a.get("service_name", ""), int(a.get("limit", 50))),
    "zerops_deploy_service": lambda a: zerops_deploy_service(a.get("service_name", ""), a.get("working_dir", "")),
    "pidev_get_status": lambda a: pidev_get_status(),
    "pidev_dispatch_task": lambda a: pidev_dispatch_task(a.get("prompt", ""), a.get("working_dir", "/var/www")),
    "linear_create_issue": lambda a: linear_create_issue(a.get("title", ""), a.get("description", ""), int(a.get("priority", 2))),
    "linear_update_status": lambda a: linear_update_status(a.get("issue_id", ""), a.get("status", ""), a.get("evidence", "")),
    "linear_get_issue": lambda a: linear_get_issue(a.get("issue_id", "")),
    "linear_comment_issue": lambda a: linear_comment_issue(a.get("issue_id", ""), a.get("comment", "")),
    "get_paperclip_status": lambda a: get_paperclip_status(),
    "paperclip_list_tasks": lambda a: paperclip_list_tasks(a.get("status", "")),
    "paperclip_create_task": lambda a: paperclip_create_task(a.get("title", ""), a.get("description", ""), a.get("priority", "medium")),
    "paperclip_register_agent": lambda a: paperclip_register_agent(
        a.get("name", ""),
        a.get("title", ""),
        a.get("role", "worker"),
        a.get("adapter_type", "hermes_gateway"),
        a.get("capabilities", ""),
        int(a.get("budget_monthly_cents", 50000))
    ),
    "run_crew_ai": lambda a: run_crew_ai(
        a.get("mission", ""),
        a.get("roles", []),
        a.get("tier", "free"),
        a.get("output_schema"),
        a.get("skills")
    ),
    "list_available_crews": lambda a: list_available_crews(),
    "extract_structured_data": lambda a: extract_structured_data(a.get("fields_spec", {}), a.get("user_input", ""), a.get("tier", "free")),
    "mem_context": lambda a: mem_context(int(a.get("limit", 5))),
    "mem_search": lambda a: mem_search(a.get("query", ""), int(a.get("limit", 5))),
    "mem_save": lambda a: mem_save(a.get("title", ""), a.get("content", ""), a.get("type", "discovery"), a.get("topic_key", "")),
    "read_file": lambda a: read_file(a.get("path", "")),
    "write_file": lambda a: write_file(a.get("path", ""), a.get("content", "")),
    "edit_file": lambda a: edit_file(a.get("path", ""), a.get("target", ""), a.get("replacement", "")),
    "list_directory": lambda a: list_directory(a.get("path", "/mnt/localstorage")),
    "run_command": lambda a: run_command(a.get("command", "")),
    "search_web": lambda a: search_web(a.get("query", ""), a.get("max_results", 5)),
    "fetch_web_page": lambda a: fetch_web_page(a.get("url", "")),
    "download_file": lambda a: download_file(a.get("url", ""), a.get("destination_path", "")),
    "execute_query": lambda a: execute_store_query(a.get("query", ""), a.get("explanation", "")),
    "calculate_natal_chart": lambda a: calculate_natal_chart(
        a.get("name", "Client"), a.get("year", 1990), a.get("month", 1), a.get("day", 1),
        a.get("hour", 12), a.get("minute", 0), float(a.get("lat", 4.7110)), float(a.get("lon", -74.0721)),
        a.get("city", "Bogota"), a.get("nation", "Colombia")
    ),
    "send_whatsapp_otp": lambda a: send_whatsapp_otp(a.get("phone", ""), a.get("otp", "")),
}

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

    # 1. Parse <dots_function_call> or <invoke name="..."> blocks (Qwen 2.5 / DeepSeek / OSS)
    if "<invoke" in content or "<dots_function_call>" in content:
        invokes = re.findall(r'<invoke\s+name=["\']([^"\']+)["\']\s*>(.*?)</invoke>', content, re.DOTALL | re.IGNORECASE)
        for name, body in invokes:
            params = {}
            param_matches = re.findall(r'<parameter\s+name=["\']([^"\']+)["\']\s*>(.*?)</parameter>', body, re.DOTALL | re.IGNORECASE)
            if param_matches:
                for p_name, p_val in param_matches:
                    p_val_clean = p_val.strip()
                    try:
                        params[p_name] = json.loads(p_val_clean)
                    except Exception:
                        params[p_name] = p_val_clean
            else:
                body_clean = body.strip()
                if body_clean.startswith("{") and body_clean.endswith("}"):
                    try:
                        params = json.loads(body_clean)
                    except Exception:
                        params = {}
            tool_calls.append({
                "id": str(uuid.uuid4()),
                "name": name.strip(),
                "args": params
            })
        if tool_calls:
            return tool_calls

    # 2. Parse XML <tool_call> or function_call blocks if model emitted raw text
    if "<tool_call>" in content:
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
        if tool_calls:
            return tool_calls

    return tool_calls

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
        self.bifrost_key = bifrost_key or os.getenv("BIFROST_VIRTUAL_KEY", "vk-hermes-agent")
        self.tools = tools if tools is not None else HERMES_TOOLS
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
        total_prompt_tokens = 0
        total_completion_tokens = 0
        total_cost_cents = 0.0
        active_provider = "freellmapi"
        active_model = MODEL_NAME
        
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
                    
                    # Accumulate tokens & calculate model costs (FreeLLMAPI = $0, DeepSeek = paid)
                    usage = data.get("usage", {})
                    p_tok = int(usage.get("prompt_tokens", 0))
                    c_tok = int(usage.get("completion_tokens", 0))
                    total_prompt_tokens += p_tok
                    total_completion_tokens += c_tok
                    
                    extra = data.get("extra_fields", {})
                    call_provider = extra.get("provider", "freellmapi")
                    active_model = extra.get("resolved_model_used", data.get("model", MODEL_NAME))
                    if call_provider == "deepseek":
                        active_provider = "deepseek"
                        # DeepSeek V3/V4: $0.14/1M prompt, $0.28/1M completion (rates in cents: 0.000014 / 0.000028)
                        total_cost_cents += (p_tok * 0.000014) + (c_tok * 0.000028)

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
                        break
                    
                    # Tool call execution step
                    assistant_msg = {"role": "assistant"}
                    if msg.get("tool_calls"):
                        assistant_msg["tool_calls"] = msg["tool_calls"]
                    else:
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
                
                if not final_content or not final_content.strip():
                    # If tools were executed but no text content was emitted, force synthesis turn without tools
                    messages.append({
                        "role": "user",
                        "content": "Con base en los resultados observados de las herramientas ejecutadas, redactá el informe técnico con tu veredicto estructurado para el usuario."
                    })
                    try:
                        res_synth = await client.post(
                            f"{BIFROST_URL}/chat/completions",
                            headers={"Authorization": f"Bearer {self.bifrost_key}"},
                            json={
                                "model": MODEL_NAME,
                                "messages": messages,
                                "temperature": 0.3,
                            },
                            timeout=30.0
                        )
                        if res_synth.status_code == 200:
                            s_data = res_synth.json()
                            s_usage = s_data.get("usage", {})
                            s_p = int(s_usage.get("prompt_tokens", 0))
                            s_c = int(s_usage.get("completion_tokens", 0))
                            total_prompt_tokens += s_p
                            total_completion_tokens += s_c
                            s_extra = s_data.get("extra_fields", {})
                            if s_extra.get("provider") == "deepseek":
                                active_provider = "deepseek"
                                total_cost_cents += (s_p * 0.000014) + (s_c * 0.000028)
                            synth_msg = s_data["choices"][0]["message"].get("content") or ""
                            cleaned = re.sub(r"<[^>]*function_call.*?</[^>]*function_call>", "", synth_msg, flags=re.DOTALL | re.IGNORECASE)
                            cleaned = re.sub(r"<[^>]*tool_call.*?</[^>]*tool_call>", "", cleaned, flags=re.DOTALL | re.IGNORECASE)
                            cleaned = re.sub(r"<dots_function_call>.*?</dots_function_call>", "", cleaned, flags=re.DOTALL | re.IGNORECASE)
                            final_content = cleaned.strip() if cleaned.strip() else synth_msg.strip()
                    except Exception as se:
                        logger.warning(f"Synthesis turn failed: {se}")

                if not final_content or not final_content.strip():
                    final_content = "Operación técnica completada. Los comandos y herramientas del sistema fueron ejecutados con éxito."

                # Store turn cost and usage telemetry for Paperclip Control Plane
                self.last_turn_telemetry = {
                    "provider": active_provider,
                    "model": active_model,
                    "prompt_tokens": total_prompt_tokens,
                    "completion_tokens": total_completion_tokens,
                    "cost_cents": round(total_cost_cents, 4),
                }
                
                # Persist turn
                if chat_id:
                    await save_chat_turn(chat_id, user_query, final_content)
                else:
                    self.history.append({"role": "user", "content": user_query})
                    self.history.append({"role": "assistant", "content": final_content})
                    if len(self.history) > 6:
                        self.history = self.history[-6:]
                
                return final_content
            except Exception as e:
                logger.error(f"[Hermes] Error in run_turn: {e}")
                return f"⚠️ Error en la ejecución del turno de Hermes: {str(e)}"
