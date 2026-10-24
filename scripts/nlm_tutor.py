#!/usr/bin/env python3
# -*- coding: utf-8 -*-
"""
===============================================================================
       NLM-TUTOR: Sistema Autónomo de Aprendizaje Acelerado & Tutoría Socrática
                 para Google NotebookLM Pro (Google One 5TB)
===============================================================================
Gobernanza: Supreme Directive v8.5 & CoHaLo Engineering
Versión: 6.0.0 (SOTA Gemini Notebook / NotebookLM Octubre 2026)
Cero Subprocesos Shell: Operaciones 100% nativas mediante SDK en Python
                        de notebooklm_tools.services (jacob-bd/gemini-notebook-mcp-cli).
Integración: Minimal Viable Learning Stack (MVLS), Neurociencia del Active Recall
             (Make It Stick, Harvard 5 Rs, Roediger Testing Effect, Ebbinghaus),
             Dinámica de Sistemas MIT 1972 y Regla de 20 Horas de Josh Kaufman.
===============================================================================
"""

import os
import sys
import shutil
import subprocess

sys.dont_write_bytecode = True

# Proactive self-hygiene: purge local __pycache__ and SSoT scripts cache on launch
try:
    for _c_dir in [
        os.path.join(os.path.dirname(os.path.abspath(__file__)), "__pycache__"),
        "/var/www/baiosfera/CURSOS/MCV/__pycache__",
        "/var/www/baiosfera/0ZEROPS-AGY/0zcp-123/scripts/__pycache__"
    ]:
        if os.path.isdir(_c_dir):
            shutil.rmtree(_c_dir, ignore_errors=True)
except Exception:
    pass

import json
import time
import glob
import re
import argparse
from datetime import datetime, timedelta
from typing import Dict, List, Optional, Tuple, Any

# Descubrimiento dinámico del entorno UV de notebooklm-mcp-cli
uv_patterns = [
    os.path.expanduser("~/.local/share/uv/tools/notebooklm-mcp-cli/lib/python*/site-packages"),
    "/home/zerops/.local/share/uv/tools/notebooklm-mcp-cli/lib/python*/site-packages",
]
for pat in uv_patterns:
    for pkg_dir in sorted(glob.glob(pat), reverse=True):
        if os.path.isdir(pkg_dir) and pkg_dir not in sys.path:
            sys.path.insert(0, pkg_dir)

try:
    from notebooklm_tools.cli.utils import get_client
    from notebooklm_tools.services import (
        notebooks, studio, chat, notes, collections, cross_notebook, usage
    )
except ImportError as e_imp:
    sys.stderr.write(f"Error importando servicios nativos de NotebookLM ({e_imp}). Ejecuta 'nlm login' primero.\n")

VERSION = "6.0.0"

# Códigos de color ANSI para interfaz amigable en terminal
CYAN = "\033[1;36m"
GREEN = "\033[1;32m"
YELLOW = "\033[1;33m"
BLUE = "\033[1;34m"
MAGENTA = "\033[1;35m"
RED = "\033[1;31m"
BOLD = "\033[1m"
RESET = "\033[0m"

# Directiva afirmativa de locución y producción vocal (CoHaLo Context Engineering)
VOCAL_PERSONA_ES419 = (
    "DIRECTIVA DE PRODUCCIÓN VOCAL Y LOCUCIÓN: "
    "Conduce toda la locución y el diálogo en español neutro latinoamericano profesional (es-419). "
    "Adopta el perfil acústico de comunicadores y divulgadores científicos contemporáneos de Ciudad de México y Bogotá: "
    "tono cálido, entusiasta, ritmo televisivo ágil, articulación clara, pronunciación seseante natural y vocabulario "
    "académico accesible común a toda Hispanoamérica."
)
ANTI_PENINSULAR_CLAUSE = VOCAL_PERSONA_ES419  # Alias de compatibilidad CoHaLo

# Regla universal de evaluación para cuestionarios (CoHaLo Afirmativo & Harness Engineering)
QUIZ_STRUCTURAL_RULE = (
    "DIRECTIVA ESTRUCTURAL DEL CUESTIONARIO (COHALO AFIRMATIVO): "
    "1. FORMATO DE SELECCIÓN MÚLTIPLE DE TRES OPCIONES: Cada pregunta consta de exactamente tres alternativas concisas (A, B, C), donde una sola opción es la correcta y dos actúan como distractores analíticos plausibles. "
    "2. PREGUNTAS DINÁMICAS Y ESTIMULANTES: Diseña preguntas de razonamiento causal aplicadas a los mecanismos del material que inviten a iniciar el estudio con fluidez mental y cero fricción. "
    "3. JUSTIFICACIÓN ANALÍTICA: Acompaña cada opción con su correspondiente justificación analítica basada en las fuentes del cuaderno."
)

# ---------------------------------------------------------------------------
# Biblioteca de Prompts Maestros (Aprendizaje Acelerado & Dinámica de Sistemas)
# ---------------------------------------------------------------------------
MASTER_PROMPTS = {
    1: {
        "title": "Resumen de Máximo Detalle (Construcción del Mapa Base)",
        "desc": "Crea una base estructurada numerada tras la primera lectura.",
        "prompt": "Crea un resumen en donde expliques con el máximo detalle y claridad las ideas y conceptos más importantes de este material. Numera todas las ideas principales y secundarias para construir el mapa base del tema."
    },
    2: {
        "title": "Explicación Didáctica de Primeros Principios (Enseñanza desde Cero)",
        "desc": "Rompe la ilusión de fluidez explicando con lenguaje cotidiano.",
        "prompt": "¿Qué tendría que entender de verdad de este material para poder enseñárselo a una persona que no sabe absolutamente nada sobre este tema? Desglosa los fundamentos con analogías sencillas y lenguaje claro, sin términos vacíos ni explicaciones superficiales."
    },
    3: {
        "title": "Testing de 10 Preguntas de Razonamiento Causal (No Memoria)",
        "desc": "Somete a estrés cognitivo tu entendimiento con casos prácticos.",
        "prompt": "Genera 10 preguntas que expongan si alguien entiende profundamente este tema o si solo ha memorizado definiciones sueltas. Las preguntas deben requerir razonamiento no memoria, conectar conceptos entre sí, incluir situaciones de la vida real, mostrar casos donde un consejo típico falle, y estar ordenadas de menor a mayor dificultad."
    },
    4: {
        "title": "Plan de Sesión de Alto Enfoque (Bloque de 90 Minutos)",
        "desc": "Estructura un bloque ultradiano de alto impacto para hoy.",
        "prompt": "Con todo lo que hemos trabajado y las fuentes de este cuaderno, créame una sesión de estudio de 90 minutos para dominar este tema. Divide la sesión por bloques de tiempo e incluye: 1) qué estudiar primero, 2) qué pregunta central responder, 3) qué fuente revisar si me atasco, 4) qué resultado tangible tener al final, y 5) qué hacer en los últimos 10 minutos para detectar lagunas."
    },
    5: {
        "title": "Kit de Consolidación Final & Hoja de Errores Típicos",
        "desc": "Consolidación en un One-Pager con tabla de trampas comunes.",
        "prompt": "Con todo lo trabajado en este cuaderno, crea un kit de repaso para consolidar este tema. Incluye: 1) una hoja de estudio de una página con las ideas clave, 2) una tabla con los errores típicos y cómo corregirlos, 3) 10 preguntas de repaso ordenadas por dificultad, 4) un plan de repaso de 7 días, y 5) fuentes a revisar si me atasco."
    },
    6: {
        "title": "Debates, Matices Críticos y Vías de Consenso",
        "desc": "Explora el estado del arte y puntos de desacuerdo en las fuentes.",
        "prompt": "Extrae los 3 puntos fundamentales de desacuerdo, debate o tensión conceptual en este material. Indica para cada uno si el desacuerdo se mantiene entre autores o si existe una vía de consenso práctica."
    },
    7: {
        "title": "Mapa Mental como Syllabus Estructural",
        "desc": "Conecta causas, efectos y jerarquías entre todos los módulos.",
        "prompt": "Crea un mapa conceptual detallado que sea el equivalente a un syllabus completo conectando todos los subtemas, conceptos fundamentales y derivaciones prácticas de este cuaderno."
    },
    8: {
        "title": "Deconstrucción 80/20 en Micro-habilidades Críticas",
        "desc": "Aísla las 3 o 4 piezas críticas que dan el 80% de competencia.",
        "prompt": "Actúa como un experto en este tema. Aplicando el principio 80/20, desglosa todo este material en las 3 o 4 micro-habilidades más críticas que debo dominar para ser funcional en la práctica. Ignora la teoría periférica y dime exactamente por cuál empezar hoy."
    },
    9: {
        "title": "Autocorrección Temprana: Los 3 Errores Más Comunes",
        "desc": "Aprende a reconocer tus propios fallos sin caer en parálisis.",
        "prompt": "Resume los conceptos clave de este material en viñetas. Luego, crea una 'Lista de Verificación de Autocorrección' con los 3 errores más comunes que comete un principiante al aplicar esto, para que yo sepa inmediatamente cuándo me estoy equivocando durante mi práctica independiente."
    },
    10: {
        "title": "Anti-Bloqueo Conceptual: Analogía Inmediata de Núcleo",
        "desc": "Analogía cotidiana inmediata para destrabarte ante la confusión.",
        "prompt": "Explícame el concepto central de este tema asumiendo que tengo cero experiencia previa y usando una analogía de la vida cotidiana, porque me siento bloqueado y necesito visualizarlo con extrema sencillez antes de avanzar."
    },
    11: {
        "title": "Dinámica de Sistemas: El Iceberg Estructural de 4 Capas",
        "desc": "Hechos superficiales -> Patrones -> Estructuras -> Modelos mentales.",
        "prompt": "Analiza una afirmación central de estas fuentes en cuatro niveles: 1) El hecho visible, 2) Los patrones que se repiten en el tiempo, 3) Las estructuras, reglas e incentivos que producen esos patrones, y 4) Los modelos mentales subyacentes. Cita las fuentes exactas de cada nivel y separa lo expresado en las fuentes de lo inferido."
    },
    12: {
        "title": "Dinámica de Sistemas: Bucles de Causalidad y Palancas de Alto Impacto",
        "desc": "Identifica bucles de refuerzo, equilibrio y puntos de apalancamiento.",
        "prompt": "Identifica los bucles de retroalimentación en estas fuentes: los de refuerzo (espirales aceleradoras) y los de equilibrio (mecanismos estabilizadores). Luego, indica 3 puntos de apalancamiento donde un cambio pequeño produce un gran impacto en el sistema, citando las fuentes."
    }
}

# Prompt de Sistema Socrático del Tutor NotebookLM (Carga Dinámica desde /var/www/rol.txt con Fallback Embebido)
FALLBACK_SOCRATIC_PROMPT = (
    "<role>\n"
    "Eres el Tutor Socrático y Mentor Cognitivo de NotebookLM, anclado EXCLUSIVAMENTE en las fuentes y documentos de este cuaderno. "
    "Tu misión no es complacerme, darme resúmenes pasivos ni validar respuestas superficiales, sino forjar en mí una comprensión profunda, "
    "causal e inquebrantable de cada principio y mecanismo del material. Operas como un sparring intelectual riguroso que quiebra la ilusión de competencia "
    "y me estimula a pensar por mí mismo desde los primeros principios.\n"
    "</role>\n\n"
    "<language_and_tone>\n"
    "1. Conduce toda la interacción, retroalimentación, preguntas, explicaciones y análisis en español neutro latinoamericano profesional y cercano.\n"
    "2. Emplea un léxico y modismos profesionales propios de la divulgación académica e hispanoamericana estándar (es-419), con pronunciación seseante natural y vocabulario formal accesible compartido en toda América Latina.\n"
    "3. El tono debe ser directo, sobrio, intelectualmente estimulante y profundamente comprometido con mi crecimiento cognitivo. Cero adulación vacía ('¡excelente!', '¡increíble respuesta!'). "
    "Si un argumento es débil, señálalo con precisión causal; si es sólido, desafíalo con un caso de borde más complejo.\n"
    "4. Respuestas concisas, limpias y de alta densidad informativa, eliminando saludos ceremoniales o rodeos introductorios. Ve directo al núcleo conceptual en cada intervención.\n"
    "</language_and_tone>\n\n"
    "<epistemic_grounding>\n"
    "1. Verdad Anclada al Cuaderno: Todo tu conocimiento, preguntas, validaciones y contra-ejemplos derivan estrictamente de las fuentes de este cuaderno. Jamás inventes ni extrapoles hechos no comprobables.\n"
    "2. Frontera del Conocimiento: Si una pregunta mía no está cubierta en las fuentes, indícalo de inmediato con transparencia.\n"
    "3. Citas Rigurosas: Siempre que contrastes una idea o corrijas un razonamiento, cita el documento o sección del cuaderno donde se fundamenta.\n"
    "</epistemic_grounding>\n\n"
    "<pedagogical_architecture>\n"
    "1. Ruptura de la Ilusión de Fluidez: Reconocer un concepto no equivale a dominarlo. Primero esfuerzo de recuperación del alumno; solo después análisis y refinamiento.\n"
    "2. Indagación Causal: No formules preguntas de memoria. Formula preguntas de arquitectura causal ('¿por qué mecanismo X produce Y?', '¿qué ocurriría si falla la condición W?').\n"
    "3. Analogías Intuitivas: Descompón las ideas complejas e invítame a explicarlas mediante analogías intuitivas del mundo real sin escudarme en jerga técnica.\n"
    "4. Economía de Memoria de Trabajo: Formula exactamente UNA sola pregunta directriz principal a la vez.\n"
    "5. Cartografía de Matices: Ilumina activamente los puntos de tensión, contradicción o trade-offs entre fuentes y autores.\n"
    "</pedagogical_architecture>\n\n"
    "<interaction_and_feedback>\n"
    "Cuando entregue una respuesta, hipótesis o argumento:\n"
    "1. Validación y Fricción: Destaca en 1-2 frases qué parte del razonamiento es sólida y señala exactamente dónde está la grieta lógica o el supuesto incompleto.\n"
    "2. Desafío Socrático: Plantea una contra-pregunta o un escenario hipotético que me obligue a conectar causas con efectos y a corregir el error por mí mismo.\n"
    "3. Registro de Brechas: Si detectas una laguna conceptual o error fundamental, cierra obligatoriamente tu mensaje con esta línea final:\n"
    "BRECHA DETECTADA: [Nombre específico del concepto a reforzar] | Cita recomendada: [Nombre del documento o fuente del cuaderno]\n"
    "</interaction_and_feedback>\n\n"
    "<operating_guardrails>\n"
    "1. REGLA DE PREGUNTA ÚNICA: Termina cada intervención con exactamente UNA sola pregunta de razonamiento causal y espera mi respuesta.\n"
    "2. APLICAR SIN DISERTAR: Aplica las ciencias del aprendizaje en tu conducta y exigencia, sin dar sermones sobre teorías pedagógicas o psicólogos.\n"
    "3. ERRADICACIÓN DEL RESUMEN PASIVO: Reorienta socráticamente las solicitudes de resumen pasivo.\n"
    "4. INTERROGACIÓN HASTA LA RAÍZ: No cambies de tema hasta consolidar el modelo mental actual.\n"
    "</operating_guardrails>"
)

def load_socratic_prompt() -> str:
    """Carga el prompt soberano del Tutor Socrático desde /var/www/rol.txt si existe y es válido, con fallback."""
    rol_file = "/var/www/rol.txt"
    if os.path.isfile(rol_file):
        try:
            with open(rol_file, "r", encoding="utf-8") as f:
                content = f.read().strip()
                if len(content) > 500:
                    return content
        except Exception:
            pass
    return FALLBACK_SOCRATIC_PROMPT

SOCRATIC_SYSTEM_PROMPT = load_socratic_prompt()

# Prompt de Sistema Especializado para el Cuaderno Índice [00] (Director Académico / Decano Curricular)
DEAN_CURRICULAR_PROMPT = (
    "<role>\n"
    "Eres el Director Académico y Decano Curricular de esta colección y ruta de aprendizaje basada EXCLUSIVAMENTE en las fuentes de este cuaderno maestro.\n"
    "</role>\n\n"
    "<language_contract>\n"
    "Conduce toda la interacción, preguntas, diagnósticos y asesorías en español neutro latinoamericano profesional.\n"
    "</language_contract>\n\n"
    "<methodology>\n"
    "1. Tu misión NO es enseñar los detalles técnicos de cada lección, sino orientar al estudiante en el orden óptimo de consumo formativo.\n"
    "2. Diagnostica activamente el nivel previo del alumno mediante preguntas de razonamiento antes de sugerir por qué curso arrancar.\n"
    "3. Recomienda con precisión quirúrgica cuál cuaderno específico de la serie (P01, P02, P03... Pn) debe abrir y estudiar primero, justificando la correlatividad pedagógica y prerrequisitos.\n"
    "4. Explica qué habilidades se adquieren en cada fase del currículum y desaconseja saltarse los fundamentos antes de abordar niveles avanzados.\n"
    "5. Conecta las dudas transversales del estudiante con el mapa general de la obra del autor.\n"
    "</methodology>\n\n"
    "<rubric>\n"
    "Tras cada consulta del estudiante, orienta estructurando en:\n"
    "1) NIVEL ESTIMADO: Evaluación del estado de conocimientos o prerrequisitos expresados.\n"
    "2) CUADERNO RECOMENDADO: Nombre exacto del cuaderno (ej: [P01] o [P04]) al que debe dirigirse.\n"
    "3) JUSTIFICACIÓN PEDAGÓGICA: Por qué ese curso y no otro en esta etapa.\n"
    "4) PREGUNTA DE ENFOQUE: Pregunta clave que el estudiante debe tener en mente al entrar a ese cuaderno.\n"
    "</rubric>"
)


# ---------------------------------------------------------------------------
# Funciones Utilitarias Nativas de Resolución
# ---------------------------------------------------------------------------

def get_all_notebooks(client=None, max_results=500):
    """Obtiene la lista de cuadernos en formato nativo mediante el SDK."""
    if not client:
        try:
            client = get_client()
        except Exception:
            return []
    try:
        data = notebooks.list_notebooks(client, max_results=max_results)
        if isinstance(data, dict):
            return data.get("notebooks", [])
        elif isinstance(data, list):
            return data
        return []
    except Exception as e:
        sys.stderr.write(f"{RED}[ERROR SDK list_notebooks]{RESET} {e}\n")
        return []


def resolve_notebook(query, client=None):
    """Resuelve un cuaderno por UUID, URL directa, prefijo o coincidencia de título."""
    if not client:
        try:
            client = get_client()
        except Exception as e_cl:
            sys.stderr.write(f"{RED}[ERROR]{RESET} No se pudo inicializar cliente de NotebookLM: {e_cl}\n")
            sys.exit(1)

    q = query.strip()

    # 1. Extracción determinista de UUID canónico (36 chars) de query o URL
    uuid_match = re.search(r'[0-9a-f]{8}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{4}-[0-9a-f]{12}', q, re.I)
    if uuid_match:
        target_uuid = uuid_match.group(0).lower()
        try:
            nb_direct = notebooks.get_notebook(client, target_uuid)
            if nb_direct:
                return {
                    "id": nb_direct.get("notebook_id") or target_uuid,
                    "notebook_id": nb_direct.get("notebook_id") or target_uuid,
                    "title": nb_direct.get("title", "Cuaderno"),
                    "source_count": nb_direct.get("source_count", 0),
                    "sources": nb_direct.get("sources", []),
                    "url": nb_direct.get("url", f"https://notebooklm.google.com/notebook/{target_uuid}"),
                    "emoji": nb_direct.get("emoji")
                }
        except Exception:
            pass

    # 2. Búsqueda en catálogo completo
    all_nbs = get_all_notebooks(client, max_results=500)
    if not all_nbs:
        sys.stderr.write(f"{RED}[ERROR]{RESET} No se encontraron cuadernos en tu cuenta de NotebookLM.\n")
        sys.exit(1)

    q_lower = q.lower()

    # Coincidencia exacta de ID
    for nb in all_nbs:
        nid = (nb.get("id") or nb.get("notebook_id") or "").lower()
        if nid == q_lower:
            return nb

    # Coincidencia por prefijo de ID
    matches_id = [
        nb for nb in all_nbs
        if (nb.get("id") or nb.get("notebook_id") or "").lower().startswith(q_lower)
    ]
    if len(matches_id) == 1:
        return matches_id[0]

    # Coincidencia por texto en título
    matches_title = [nb for nb in all_nbs if q_lower in (nb.get("title") or "").lower()]
    if len(matches_title) == 1:
        return matches_title[0]
    elif len(matches_title) > 1:
        print(f"\n{YELLOW}Se encontraron múltiples cuadernos que coinciden con '{query}':{RESET}")
        for idx, nb in enumerate(matches_title, 1):
            nid = nb.get("id") or nb.get("notebook_id")
            print(f"  {BOLD}{idx}.{RESET} {nb.get('title')} ({CYAN}{nid}{RESET})")
        print(f"\nPor favor especifica el ID completo o sé más específico.")
        sys.exit(1)

    sys.stderr.write(f"{RED}[ERROR]{RESET} No se encontró ningún cuaderno que coincida con '{query}'.\n")
    sys.exit(1)


# ---------------------------------------------------------------------------
# Función de Auto-Registro Silencioso de Lagunas Cognitivas
# ---------------------------------------------------------------------------

def log_cognitive_gap(client, nb_id, gap_text):
    """Registra de forma silenciosa y atómica una laguna cognitiva en la nota 00_CUADERNO_DE_LAGUNAS."""
    try:
        notes_data = notes.list_notes(client, nb_id)
        notes_list = notes_data.get("notes", []) if isinstance(notes_data, dict) else []
        laguna_note = None
        for n in notes_list:
            t = (n.get("title") or "").upper()
            if "00_CUADERNO_DE_LAGUNAS" in t or "LAGUNAS" in t:
                laguna_note = n
                break

        timestamp = datetime.now().strftime("%Y-%m-%d %H:%M")
        new_entry = f"\n- [{timestamp}] {gap_text.strip()}"

        if laguna_note:
            note_id = laguna_note.get("id")
            current_content = laguna_note.get("content", "") or ""
            updated_content = current_content + new_entry
            notes.update_note(client, nb_id, note_id, content=updated_content)
        else:
            initial_content = (
                f"# 📓 Cuaderno de Lagunas Cognitivas y Puntos Ciegos\n"
                f"*Registro automático del Tutor Socrático para repetición espaciada*\n"
                f"{new_entry}"
            )
            notes.create_note(client, nb_id, content=initial_content, title="00_CUADERNO_DE_LAGUNAS")
        return True
    except Exception:
        return False


# ---------------------------------------------------------------------------
# Arnés Determinista de Renombramiento & Vigilancia Autónoma en Studio
# ---------------------------------------------------------------------------

def launch_background_watcher(nb_id: str):
    """Lanza el daemon de vigilancia autónoma en segundo plano desacoplado (0 CPU, 0 tokens)."""
    script_path = os.path.abspath(__file__)
    uv_python = os.path.expanduser("~/.local/share/uv/tools/notebooklm-mcp-cli/bin/python")
    py_exec = uv_python if os.path.isfile(uv_python) and os.access(uv_python, os.X_OK) else sys.executable
    env = os.environ.copy()
    uv_pkg_dirs = [p for p in sys.path if "site-packages" in p]
    if uv_pkg_dirs:
        env["PYTHONPATH"] = os.pathsep.join(uv_pkg_dirs + ([env["PYTHONPATH"]] if "PYTHONPATH" in env else []))
    try:
        subprocess.Popen(
            [py_exec, script_path, "_watch", nb_id],
            start_new_session=True,
            stdout=subprocess.DEVNULL,
            stderr=subprocess.DEVNULL,
            close_fds=True,
            env=env
        )
    except Exception:
        pass


def reconcile_notebook_artifacts(client, nb_id: str, verbose: bool = True) -> int:
    """
    Reconcilia y renombra todos los artefactos completados en Studio aplicando títulos canónicos numerados.
    Erradica de raíz términos deprecados (como Cebador-Inicial) y aplica mapeos de manifiesto o ruta.
    Retorna la cantidad de artefactos renombrados con éxito.
    """
    try:
        status_data = studio.get_studio_status(client, nb_id)
        arts = status_data.get("artifacts", []) if isinstance(status_data, dict) else status_data
        if not arts:
            return 0

        manifest_map = extract_cloud_manifest(client, nb_id)
        route_titles = []

        # Inspeccionar nota de ruta para títulos previstos
        try:
            res_notes = notes.list_notes(client, nb_id)
            raw_notes = res_notes.get("notes", []) if isinstance(res_notes, dict) else res_notes
            for n in raw_notes:
                t = n.get("title", "")
                if "00_RUTA_DE_ESTUDIO" in t or "RUTA" in t:
                    c = n.get("content", "")
                    found = re.findall(r'(\d{2}_[A-Za-z0-9_\-]+)', c)
                    if found:
                        route_titles = [x.replace("Cebador-Inicial", "Activacion-Conceptual") for x in found]
        except Exception:
            pass

        canonical_fallback = [
            "01_DIAGNOSTICO_Activacion-Conceptual",
            "02_MAPA_Syllabus-Estructural",
            "03_AUDIO_Inmersion-General-Podcast",
            "04_TABLA_Matriz-Deconstruccion-80-20",
            "05_INFORME_Plan-de-Accion-y-Errores",
            "06_TABLE_Comparativa-Conceptos-y-Matices",
            "07_SLIDES_Autoensenanza-Feynman",
            "08_FLASHCARDS_Recuperacion-Activa",
            "09_QUIZ_Nivel-3-Razonamiento-Intermedio",
            "10_QUIZ_Nivel-5-Casos-Criticos-Simulacro",
            "11_REPORT_Guia-de-Estudio-Fundamentos"
        ]
        target_pool = list(route_titles) if route_titles else list(canonical_fallback)

        existing_numbered = {
            a.get("title"): a for a in arts
            if a.get("title") and re.match(r'^\d{2}_', a.get("title", "")) and "Cebador-Inicial" not in a.get("title", "")
        }
        missing_pool = [t for t in target_pool if t not in existing_numbered]

        renamed_count = 0
        type_keywords = {
            "video": ["VIDEO"],
            "slide_deck": ["SLIDES"],
            "infographic": ["INFOGRAFIA", "INFOGRAPHIC"],
            "data_table": ["TABLA", "TABLE"],
            "mind_map": ["MAPA", "MINDMAP"],
            "flashcards": ["FLASHCARDS"],
            "audio": ["AUDIO"],
            "quiz": ["DIAGNOSTICO", "SIMULACRO", "QUIZ"],
            "report": ["INFORME", "REPORT", "SINTESIS", "BRIEFING", "FAQ"]
        }

        for a in reversed(arts):
            art_id = a.get("artifact_id")
            current_title = a.get("title", "")
            astatus = a.get("status")
            atype = a.get("type", "artifact")

            if not art_id or astatus != "completed":
                continue

            target_title = None

            # Prioridad 0: Si contiene término deprecado 'Cebador-Inicial'
            if "Cebador-Inicial" in current_title:
                target_title = current_title.replace("Cebador-Inicial", "Activacion-Conceptual")

            # Prioridad 1: Mapeo exacto por ID desde manifiesto
            elif art_id in manifest_map:
                target_title = manifest_map[art_id]

            # Prioridad 2: Si ya tiene título numerado canónico limpio
            elif re.match(r'^\d{2}_', current_title):
                if verbose:
                    print(f"  • {current_title} ({GREEN}Al día{RESET})")
                continue

            # Prioridad 3: Inferencia inteligente por tipo sobre missing_pool
            else:
                kws = type_keywords.get(atype, [atype.upper()])
                matched_cand = None
                for cand in missing_pool:
                    if any(kw in cand.upper() for kw in kws):
                        matched_cand = cand
                        break
                if matched_cand:
                    target_title = matched_cand
                    missing_pool.remove(matched_cand)

            if target_title and current_title != target_title:
                try:
                    studio.rename_artifact(client, art_id, target_title)
                    renamed_count += 1
                    if verbose:
                        print(f"  {GREEN}✓ Renombrado:{RESET} {current_title} ➔ {BOLD}{CYAN}{target_title}{RESET}")
                except Exception as e_ren:
                    if verbose:
                        print(f"  {YELLOW}Aviso renombrando {art_id}: {e_ren}{RESET}")
            elif verbose:
                if not target_title:
                    print(f"  • {current_title} ({YELLOW}Sin mapeo aplicable{RESET})")
                else:
                    print(f"  • {current_title} ({GREEN}Al día{RESET})")

        return renamed_count
    except Exception as e_rec:
        if verbose:
            print(f"{YELLOW}Aviso en reconciliación: {e_rec}{RESET}")
        return 0


def passive_reconcile_artifacts(client, nb_id: str):
    """Chequeo pasivo no bloqueante (<0.3s) para garantizar títulos al día al entrar a sesión o schedule."""
    try:
        reconcile_notebook_artifacts(client, nb_id, verbose=False)
    except Exception:
        pass


def reconcile_and_rename_artifacts(client, nb_id, expected_artifacts, max_wait=60, poll_interval=10):
    """
    Sondea el estado inicial de los artefactos en Studio y renombra de inmediato los rápidos.
    Para artefactos pesados (audio/video/slides) que sigan in_progress, delega a un watcher autónomo
    en segundo plano, garantizando cero intervención manual del usuario.
    """
    if not expected_artifacts:
        return

    print(f"\n{BOLD}[Verificación & Renombrado en Studio]{RESET} Verificando artefactos concluidos para aplicar títulos canónicos...")
    start_time = time.time()
    pending = list(expected_artifacts)

    while pending and (time.time() - start_time) < max_wait:
        try:
            status_data = studio.get_studio_status(client, nb_id)
            current_arts = status_data.get("artifacts", [])
            completed_map = {a.get("artifact_id"): a for a in current_arts if a.get("status") == "completed"}

            still_pending = []
            for item in pending:
                target_title, art_id, atype = item
                if not art_id:
                    continue
                if art_id in completed_map:
                    current_title = completed_map[art_id].get("title", "")
                    if current_title != target_title:
                        try:
                            studio.rename_artifact(client, art_id, target_title)
                            print(f"  {GREEN}✓ Renombrado:{RESET} {CYAN}{target_title}{RESET}")
                        except Exception as e_ren:
                            print(f"  {YELLOW}Aviso renombrando {target_title}: {e_ren}{RESET}")
                else:
                    still_pending.append(item)

            pending = still_pending
            if not pending:
                break
        except Exception as e_poll:
            print(f"  {YELLOW}Aviso sondeo Studio: {e_poll}{RESET}")

        time.sleep(poll_interval)

    if pending:
        print(f"  {YELLOW}ℹ️ {len(pending)} artefactos pesados (audio/video/slides) continúan renderizándose en segundo plano en Google Cloud.{RESET}")
        print(f"  {GREEN}🚀 Vigilante autónomo activado en segundo plano.{RESET} Los títulos canónicos se aplicarán de forma automática al completarse.")
        launch_background_watcher(nb_id)
    else:
        print(f"  {GREEN}✓ Todos los artefactos fueron verificados y renombrados exitosamente en Studio.{RESET}")


# ---------------------------------------------------------------------------
# UTILIDAD: clean_notebook
# Purga Higiénica Controlada (Studio + Notas 00 + Chat) sin tocar Fuentes
# ---------------------------------------------------------------------------

def clean_notebook(client, nb_id, clean_studio=True, clean_notes=True, clean_chat=True, all_notes=False):
    """
    Elimina de forma segura y controlada los artefactos generados en Studio,
    las notas creadas por el tutor y el historial de chat de un cuaderno.
    REGLA DE ORO DE GOBERNANZA: NUNCA toca ni elimina las fuentes ('sources').
    """
    print(f"\n{YELLOW}============================================================{RESET}")
    print(f"  🧹 LIMPIEZA HIGIÉNICA DE CUADERNO (Cero eliminación de fuentes)")
    print(f"  UUID: {CYAN}{nb_id}{RESET}")
    print(f"{YELLOW}============================================================{RESET}\n")

    # 1. Limpiar artefactos de Studio
    if clean_studio:
        print(f"{BOLD}[1/3]{RESET} Limpiando artefactos de Studio...")
        try:
            status_data = studio.get_studio_status(client, nb_id)
            artifacts = status_data.get("artifacts", []) if isinstance(status_data, dict) else status_data
            if not artifacts:
                print(f"  {GREEN}✓ Studio ya estaba limpio (0 artefactos).{RESET}")
            else:
                print(f"  Detectados {len(artifacts)} artefactos en Studio. Eliminando...")
                deleted_cnt = 0
                for a in artifacts:
                    art_id = a.get("id") or a.get("artifact_id")
                    title = a.get("title") or a.get("type", "artefacto")
                    if not art_id:
                        continue
                    try:
                        studio.delete_artifact(client, art_id, nb_id)
                        deleted_cnt += 1
                        print(f"  {GREEN}✓ Eliminado de Studio:{RESET} {title} ({art_id[:8]}...)")
                    except Exception as e_del:
                        print(f"  {YELLOW}Aviso borrando {title}: {e_del}{RESET}")
                print(f"  {GREEN}✓ {deleted_cnt}/{len(artifacts)} artefactos eliminados de Studio.{RESET}")
        except Exception as e_st:
            print(f"  {RED}⚠️ Error al consultar Studio: {e_st}{RESET}")

    # 2. Limpiar Notas del Tutor
    if clean_notes:
        print(f"\n{BOLD}[2/3]{RESET} Limpiando notas...")
        try:
            res = notes.list_notes(client, nb_id)
            raw_notes = res.get("notes", []) if isinstance(res, dict) else res
            tutor_notes = []
            for n in raw_notes:
                title = n.get("title", "")
                nid = n.get("id") or n.get("note_id")
                if not nid:
                    continue
                if all_notes or "00_" in title or "RUTA" in title or "LAGUNA" in title or "MANIFEST" in title.upper():
                    tutor_notes.append((nid, title))

            if not tutor_notes:
                print(f"  {GREEN}✓ No se encontraron notas del tutor para eliminar.{RESET}")
            else:
                print(f"  Detectadas {len(tutor_notes)} notas para eliminar. Procesando...")
                del_notes_cnt = 0
                for nid, title in tutor_notes:
                    try:
                        notes.delete_note(client, nb_id, nid)
                        del_notes_cnt += 1
                        print(f"  {GREEN}✓ Eliminada nota:{RESET} {title}")
                    except Exception as e_dn:
                        print(f"  {YELLOW}Aviso borrando nota {title}: {e_dn}{RESET}")
                print(f"  {GREEN}✓ {del_notes_cnt}/{len(tutor_notes)} notas eliminadas.{RESET}")
        except Exception as e_nt:
            print(f"  {RED}⚠️ Error al procesar notas: {e_nt}{RESET}")

    # 3. Limpiar Historial de Chat (DeleteChatTurns en el servidor de Google)
    if clean_chat:
        print(f"\n{BOLD}[3/3]{RESET} Limpiando historial de conversación del Chat...")
        conv_id = None
        try:
            conv_id = client.get_conversation_id(nb_id)
        except Exception:
            pass

        if not conv_id:
            print(f"  {GREEN}✓ Chat ya estaba limpio (sin conversación previa).{RESET}")
        else:
            turns = None
            try:
                turns = client.get_conversation_turns(nb_id, conv_id)
            except Exception:
                pass

            if not turns:
                print(f"  {GREEN}✓ Chat ya estaba limpio (sin turnos de conversación).{RESET}")
            else:
                try:
                    rpc_name = getattr(client, "RPC_DELETE_CHAT_HISTORY", None)
                    if rpc_name and hasattr(client, "_call_rpc"):
                        client._call_rpc(rpc_name, [None, conv_id, None, True], path=f"/notebook/{nb_id}")
                        if hasattr(client, "_state_lock") and hasattr(client, "_conversation_cache"):
                            with client._state_lock:
                                client._conversation_cache.pop(conv_id, None)
                        print(f"  {GREEN}✓ Historial de chat reseteado a cero ({len(turns)} turno(s) eliminado(s)).{RESET}")
                    else:
                        print(f"  {YELLOW}Aviso: Limpieza interna de chat no disponible directamente en esta versión del SDK.{RESET}")
                except Exception as e_ch:
                    print(f"  {YELLOW}Aviso al limpiar chat: {e_ch}{RESET}")

    print(f"\n{GREEN}✨ Limpieza completada. Fuentes originales 100% conservadas e intactas.{RESET}\n")


def resolve_collection(target: str, client) -> Tuple[str, str, List[str]]:
    """Resuelve una colección nativa por nombre o UUID, retornando (id, nombre, lista_notebook_ids)."""
    data = collections.list_collections(client)
    cols = data.get("collections", []) if isinstance(data, dict) else []
    target_clean = target.strip().lower()
    for col in cols:
        cid = col.get("id") or col.get("collection_id") or ""
        name = col.get("name") or ""
        if cid.lower() == target_clean or name.lower() == target_clean or target_clean in name.lower():
            return (cid, name, list(col.get("notebook_ids", [])))
    raise ValueError(f"No se encontró ninguna colección que coincida con '{target}'")


# ---------------------------------------------------------------------------
# Gestión de Manifiestos SSoT en la Nube (Cero Footprint Local en Disco)
# ---------------------------------------------------------------------------

def extract_cloud_manifest(client, nb_id: str) -> Dict[str, str]:
    """
    Extrae el mapeo canónico de artefactos directamente de la nota '00_RUTA_DE_ESTUDIO' en NotebookLM.
    Garantiza 0 bytes en disco local (~/.config/), portabilidad 100% cloud-native y sincronización SSoT.
    Retorna un diccionario {artifact_id: target_title}.
    """
    manifest_map = {}
    try:
        res_notes = notes.list_notes(client, nb_id)
        raw_notes = res_notes.get("notes", []) if isinstance(res_notes, dict) else res_notes
        for n in raw_notes:
            t = n.get("title", "")
            if "00_RUTA_DE_ESTUDIO" in t or "RUTA" in t:
                content = n.get("content", "")
                m_json = re.search(r'<!--\s*NLM_TUTOR_MANIFEST:\s*(\[.*?\])\s*-->', content, re.DOTALL)
                if m_json:
                    try:
                        items = json.loads(m_json.group(1))
                        for it in items:
                            aid = it.get("artifact_id") or it.get("id")
                            target_title = it.get("target_title") or it.get("title")
                            if aid and target_title:
                                manifest_map[aid] = target_title.replace("Cebador-Inicial", "Activacion-Conceptual")
                        if manifest_map:
                            return manifest_map
                    except Exception:
                        pass
    except Exception:
        pass
    return manifest_map

def purge_cloud_manifest_notes(client, nb_id: str):
    """Elimina notas residuales __STUDIO_MANIFEST__ para mantener el espacio de estudio del usuario 100% limpio."""
    try:
        res_notes = notes.list_notes(client, nb_id)
        raw_notes = res_notes.get("notes", []) if isinstance(res_notes, dict) else res_notes
        for n in raw_notes:
            t = n.get("title", "")
            if t == "__STUDIO_MANIFEST__":
                nid = n.get("id") or n.get("note_id")
                if nid:
                    notes.delete_note(client, nb_id, nid)
                    print(f"  {GREEN}✓ Purgada nota interna residual '__STUDIO_MANIFEST__' de las notas del cuaderno.{RESET}")
    except Exception:
        pass

def analyze_notebook_density(client, nb_id: str) -> Tuple[int, str, Dict[str, Any]]:
    """
    Analiza semánticamente la amplitud conceptual, diversidad temática y volumen documental
    del cuaderno para calibrar la suite pedagógica de forma inteligente y adaptativa.
    
    No cae en la trampa simplista de contar fuentes (donde 10 videos de la misma charla de 20 min
    parecían 'ricos' y 3 conferencias de 3 horas parecían 'ligeras').
    
    Evalúa:
    1. Fuentes y diversidad léxica en títulos de fuentes (ratio de tokens únicos).
    2. Clusters de palabras clave y solapamiento temático (monotemático vs multidominio).
    3. Presencia de macro-formatos en títulos (conferencias, cursos completos, tratados, masterclasses).
    4. Resumen y tópicos oficiales de NotebookLM (describe_notebook).
    
    Retorna: (total_fuentes, tier: 'focused' | 'standard' | 'multi_domain' | 'macro_curriculum', metrics)
    """
    metrics = {
        "sources_count": 0,
        "lexical_diversity": 1.0,
        "top_keyword_concentration": 0.0,
        "is_macro_format": False,
        "dominant_keyword": "",
        "summary_topics_count": 0,
    }
    try:
        nb_data = notebooks.get_notebook(client, nb_id)
        raw_sources = nb_data.get("sources", []) if isinstance(nb_data, dict) else []
        src_count = len(raw_sources)
        metrics["sources_count"] = src_count
        titles = [s.get("title", "") for s in raw_sources if isinstance(s, dict)]
    except Exception:
        src_count = 10
        titles = []

    # 1. Extracción y normalización de tokens léxicos
    stop_words = {
        "como", "en", "de", "la", "el", "los", "las", "para", "por", "con", "un", "una",
        "y", "o", "a", "del", "al", "que", "se", "es", "su", "sus", "how", "to", "in",
        "by", "the", "and", "of", "an", "is", "ted", "talks", "resumen", "libro", "animated",
        "solo", "sólo", "aprender", "aprenda", "cualquier", "cosa"
    }
    all_words = []
    macro_kws = ["curso completo", "conferencia", "masterclass", "tratado", "diplomado", "seminario", "carrera", "guia completa"]
    has_macro_format = False

    for t in titles:
        t_low = t.lower()
        if any(mk in t_low for mk in macro_kws):
            has_macro_format = True
        cleaned = re.sub(r"[^\w\s]", " ", t_low)
        tokens = [w for w in cleaned.split() if len(w) > 2 and w not in stop_words]
        all_words.extend(tokens)

    metrics["is_macro_format"] = has_macro_format

    if all_words:
        unique_words = set(all_words)
        lexical_ratio = len(unique_words) / max(1, len(all_words))
        metrics["lexical_diversity"] = round(lexical_ratio, 2)

        # Concentración de palabra clave más frecuente
        from collections import Counter
        counts = Counter(all_words)
        most_common = counts.most_common(1)
        if most_common and src_count > 0:
            top_freq = most_common[0][1]
            top_ratio = top_freq / max(1, src_count)
            metrics["top_keyword_concentration"] = round(top_ratio, 2)
            metrics["dominant_keyword"] = most_common[0][0]

    # 2. Análisis del resumen oficial de NotebookLM
    try:
        desc = notebooks.describe_notebook(client, nb_id)
        suggested_topics = desc.get("suggested_topics", []) if isinstance(desc, dict) else []
        metrics["summary_topics_count"] = len(suggested_topics)
    except Exception:
        pass

    # 3. Clasificación inteligente de dominio
    # Si >= 50% de las fuentes repiten el mismo término dominante (ej: Josh Kaufman en 10 videos)
    if metrics["top_keyword_concentration"] >= 0.50 and not has_macro_format:
        tier = "focused"
    elif src_count <= 2 and not has_macro_format:
        tier = "focused"
    elif has_macro_format or src_count >= 20 or (metrics["lexical_diversity"] >= 0.65 and src_count >= 10):
        tier = "multi_domain"
    elif src_count > 30:
        tier = "macro_curriculum"
    else:
        tier = "standard"

    metrics["tier"] = tier
    return (src_count, tier, metrics)


def build_adaptive_suite(
    nb_id: str,
    nb_title: str,
    is_master_guide: bool,
    tier: str = "standard",
    with_video: bool = False,
    all_media: bool = False,
    no_media: bool = False,
    max_count: Optional[int] = None
) -> List[Tuple[str, str, Dict[str, Any]]]:
    """
    Construye dinámicamente la suite adaptativa de entregables según la densidad documental y temática real.
    Protección Activa de Cuota Google One:
    - Por defecto despacha 1 solo audio principal y CERO videos pesados.
    - Los artefactos de texto, mapas y visuales (cuota 0%) se potencian al máximo.
    - Videos y audios secundarios (crítica, debate) solo se activan con --with-video o --all-media.
    """
    if is_master_guide:
        suite = [
            ("01_INFORME_Decano-Curricular-y-Ruta", "report", {
                "report_format": "Create Your Own",
                "language": "es-419",
                "custom_prompt": (
                    "Documento Maestro y Guía Curricular de la Colección. Basado estrictamente en las fuentes del cuaderno índice: "
                    "1) Arquitectura global del mapa de aprendizaje y objetivos formativos, 2) Mapa secuencial de cuadernos recomendados (P01..Pn), "
                    "3) Prerrequisitos cognitivos y correlatividades pedagógicas, 4) Matriz de competencias adquiridas por cada nivel."
                )
            }),
            ("02_MAPA_Syllabus-Integral-Coleccion", "mind_map", {
                "title": "02_MAPA_Syllabus-Integral-Coleccion"
            })
        ]
        if not no_media:
            suite.append(
                ("03_AUDIO_Orientacion-Ruta", "audio", {
                    "audio_format": "brief",
                    "language": "es-419",
                    "focus_prompt": (
                        f"{VOCAL_PERSONA_ES419}\n\n"
                        "Monólogo ejecutivo breve (<2 minutos) en español neutro latinoamericano profesional. "
                        "Da la bienvenida al estudiante, explica la visión panorámica de la ruta de cursos, justifica el orden de correlatividades "
                        "y recomienda por cuál cuaderno arrancar según el nivel de conocimientos."
                    )
                })
            )
        suite.extend([
            ("04_TABLA_Matriz-Correlatividades-y-Prerrequisitos", "data_table", {
                "language": "es-419",
                "description": (
                    "Matriz curricular estructurada. Columnas: Código de Cuaderno, Título del Curso, Prerrequisitos Obligatorios, "
                    "Nivel de Complejidad (1-5), Competencia Central y Resultado Tangible."
                )
            }),
            ("05_SLIDES_Presentacion-Arquitectura-Coleccion", "slide_deck", {
                "slide_format": "detailed_deck",
                "language": "es-419",
                "focus_prompt": (
                    "Presentación ejecutiva del currículum completo en español latinoamericano neutro: "
                    "1) Visión general y promesa de la ruta, 2) Mapa visual de módulos, "
                    "3) Casos de aplicación práctica por nivel formativo."
                )
            }),
            ("06_INFORME_FAQ-Ruta-de-Estudio", "report", {
                "report_format": "Create Your Own",
                "language": "es-419",
                "custom_prompt": (
                    "Documento de Preguntas Frecuentes (FAQ) de navegación curricular. Estructura: 1) ¿Por qué curso arranco si ya tengo experiencia?, "
                    "2) ¿Cuánto tiempo dedicar a cada aula?, 3) ¿Cómo sincronizar con el Tutor Socrático en terminal?, 4) Cómo validar avances."
                )
            })
        ])
        if max_count and max_count > 0:
            return suite[:max_count]
        return suite

    # AULA DE ESTUDIO TEMÁTICA
    raw_suite = []

    # 1. Activación Conceptual (Quiz ágil pre-test: rompe la ilusión de familiaridad)
    raw_suite.append((
        "01_DIAGNOSTICO_Activacion-Conceptual", "quiz", {
            "question_count": 1,
            "difficulty": "easy",
            "language": "es-419",
            "focus_prompt": (
                f"{QUIZ_STRUCTURAL_RULE}\n\n"
                "OBJETIVO FORMATIVO: Micro-evaluación ágil, estimulante y minimalista de preguntas de razonamiento "
                "para despertar la curiosidad y activar el mapa conceptual antes de la primera lectura a fondo. "
                "Crea preguntas concisas y directas para motivar el estudio con fluidez mental y cero fricción."
            )
        }
    ))

    # 2. Mapa Estructural (Mind Map: modelos mentales del MIT y visión panorámica)
    raw_suite.append((
        "02_MAPA_Syllabus-Estructural", "mind_map", {
            "title": "02_MAPA_Syllabus-Estructural"
        }
    ))

    # 3. Audio Principal de Inmersión (1 solo audio por defecto para proteger la cuota Google One)
    if not no_media:
        raw_suite.append((
            "AUDIO_Inmersion-General-Podcast", "audio", {
                "audio_format": "deep_dive",
                "language": "es-419",
                "focus_prompt": (
                    f"{VOCAL_PERSONA_ES419}\n\n"
                    "Conversación fluida estilo podcast entre dos interlocutores expertos en español neutro latinoamericano. "
                    "Presenta de forma amena, rigurosa y conectada el panorama global del tema, explicando las relaciones causales esenciales "
                    "y los principios rectores extraídos de las fuentes del cuaderno."
                )
            }
        ))

    # 4. Matriz de Deconstrucción 80/20 (Data Table: densidad informativa pura, 0% cuota)
    raw_suite.append((
        "TABLA_Matriz-Deconstruccion-80-20", "data_table", {
            "language": "es-419",
            "description": (
                "Matriz estructurada de deconstrucción del tema en micro-habilidades prácticas (Principio 80/20 de Kaufman). "
                "Columnas: Micro-habilidad Crítica, Principio Causal en las Fuentes, Ejercicio Práctico Inmediato, "
                "Trampa Común de Principiante, Criterio de Dominio Suficiente."
            )
        }
    ))

    # 5. Plan de Acción y Catálogo de Errores (Reporte 'Create Your Own': autocorrección temprana)
    raw_suite.append((
        "INFORME_Plan-de-Accion-y-Errores", "report", {
            "report_format": "Create Your Own",
            "language": "es-419",
            "custom_prompt": (
                "Plan de acción de una página y catálogo de trampas frecuentes. "
                "Estructura: 1) Hoja de ruta para implementación inmediata en 5 pasos lógicos, 2) Matriz de errores comunes (el error típico vs lo que demuestran las fuentes), "
                "3) Lista de verificación de autodiagnóstico, 4) Cronograma de repasos periódicos para afianzar el conocimiento a largo plazo."
            )
        }
    ))

    # SUITE EXTENDIDA 'STANDARD' (11 Artefactos Canónicos del Manual para Cursos Troncales)
    if tier in ("standard", "exhaustive", "macro_curriculum"):
        raw_suite.extend([
            ("TABLE_Comparativa-Conceptos-y-Matices", "data_table", {
                "language": "es-419",
                "description": (
                    "Matriz analítica comparativa que exponga los puntos de contraste, divergencia, trade-offs o escuelas de pensamiento "
                    "presentes en las fuentes del cuaderno. Columnas: Eje de Comparación / Tema, Enfoque A y Fundamento (con citas), "
                    "Enfoque B y Fundamento (con citas), Implicaciones Prácticas, y Síntesis de Aplicación."
                )
            }),
            ("SLIDES_Autoensenanza-Feynman", "slide_deck", {
                "slide_format": "detailed_deck",
                "language": "es-419",
                "focus_prompt": (
                    "Presentación de diapositivas conceptuales para auto-enseñanza Feynman en voz alta en español latinoamericano neutro. "
                    "Cada diapositiva aísla un principio rector con explicaciones claras, diagramas lógicos intuitivos y preguntas de control."
                )
            }),
            ("FLASHCARDS_Recuperacion-Activa", "flashcards", {
                "difficulty": "medium",
                "language": "es-419",
                "focus_prompt": (
                    "Tarjetas de estudio para consolidación a libro cerrado de distinciones operativas, fórmulas o principios clave. "
                    "Frente: Escenario de aplicación o pregunta de razonamiento causal. "
                    "Reverso: Explicación precisa con fundamento directo en las fuentes del cuaderno y advertencia de trampas comunes."
                )
            }),
            ("QUIZ_Nivel-3-Razonamiento-Intermedio", "quiz", {
                "question_count": 1,
                "difficulty": "medium",
                "language": "es-419",
                "focus_prompt": (
                    f"{QUIZ_STRUCTURAL_RULE}\n\n"
                    "OBJETIVO FORMATIVO: Evaluación intermedia de razonamiento causal. "
                    "Evalúa conexiones entre conceptos de diferentes módulos y requiere aplicar principios teóricos a casos prácticos."
                )
            }),
            ("QUIZ_Nivel-5-Casos-Criticos-Simulacro", "quiz", {
                "question_count": 1,
                "difficulty": "hard",
                "language": "es-419",
                "focus_prompt": (
                    f"{QUIZ_STRUCTURAL_RULE}\n\n"
                    "OBJETIVO FORMATIVO: Simulacro integral con preguntas aplicadas a casos reales y dilemas complejos del material. "
                    "Exige evaluar escenarios hipotéticos, resolver disyuntivas prácticas y demostrar dominio causal completo."
                )
            }),
            ("REPORT_Guia-de-Estudio-Fundamentos", "report", {
                "report_format": "Create Your Own",
                "language": "es-419",
                "custom_prompt": (
                    "Informe maestro de fundamentos, modelos mentales y relaciones causales basado estrictamente en las fuentes del cuaderno. "
                    "Estructura obligatoria: 1) Modelos mentales rectores y mecanismos fundamentales, 2) Mapa causal de causas, efectos y trade-offs prácticos, "
                    "3) Glosario de términos y distinciones operativas clave citando textualmente las fuentes."
                )
            })
        ])

    # Entregables Multimedia Pesados (SOLO SI SE SOLICITAN EXPLÍCITAMENTE)
    if (with_video or all_media) and not no_media:
        raw_suite.append((
            "VIDEO_Resumen-Audiovisual", "video", {
                "video_format": "explainer",
                "visual_style": "auto_select",
                "language": "es-419",
                "focus_prompt": (
                    f"{VOCAL_PERSONA_ES419}\n\n"
                    "Video explicativo dinámico y profesional que resuma visualmente los engranajes esenciales del tema. "
                    "Tono directo y didáctico, conectando conceptos abstractos con ejemplos concretos según las fuentes."
                )
            }
        ))

    if all_media and not no_media:
        raw_suite.extend([
            ("AUDIO_The-Brief-Resumen-Ejecutivo", "audio", {
                "audio_format": "brief",
                "language": "es-419",
                "focus_prompt": (
                    f"{VOCAL_PERSONA_ES419}\n\n"
                    "Monólogo ejecutivo ultraconcentrado (<2 minutos) en español neutro latinoamericano. "
                    "Un solo presentador sintetiza con máxima elocuencia, rigor y precisión los principios causales rectores."
                )
            }),
            ("AUDIO_Analisis-Critico-y-Matices", "audio", {
                "audio_format": "critique",
                "language": "es-419",
                "focus_prompt": (
                    f"{VOCAL_PERSONA_ES419}\n\n"
                    "Debate analítico y crítico riguroso entre dos expertos en español neutro latinoamericano. "
                    "Analizan a fondo los límites del tema, objeciones y escenarios donde las reglas estándar fallan."
                )
            }),
            ("AUDIO_Debate-Dialectico", "audio", {
                "audio_format": "debate",
                "language": "es-419",
                "focus_prompt": (
                    f"{VOCAL_PERSONA_ES419}\n\n"
                    "Debate dialéctico polarizado entre dos expertos en español neutro latinoamericano confrontando tesis y contra-argumentos."
                )
            })
        ])

    # Renumeración secuencial contigua y limpia (01, 02, 03... N)
    final_suite = []
    for idx, (orig_title, atype, kwargs) in enumerate(raw_suite, 1):
        clean_name = re.sub(r'^\d{2}_', '', orig_title)
        num_title = f"{idx:02d}_{clean_name}"
        final_suite.append((num_title, atype, kwargs))

    if max_count and max_count > 0:
        return final_suite[:max_count]
    return final_suite


def setup_single_notebook(client, nb_id: str, nb_title: str, args):
    """Ejecuta la configuración del entorno socrático y suite dinámica de artefactos sobre un cuaderno específico."""
    print(f"\n{CYAN}============================================================{RESET}")
    print(f"  🎓 NLM-TUTOR SETUP (COHALO FRACTAL v{VERSION}): {BOLD}{nb_title}{RESET}")
    print(f"  UUID: {CYAN}{nb_id}{RESET}")
    print(f"{CYAN}============================================================{RESET}\n")

    # 0. Limpieza previa si se especificó la bandera --clean
    if getattr(args, "clean", False):
        print(f"{YELLOW}🧹 Bandera --clean detectada: ejecutando purga previa de Studio, notas 00 y chat...{RESET}")
        clean_notebook(client, nb_id, clean_studio=True, clean_notes=True, clean_chat=True)

    # 0.1. Purgar cualquier nota residual interna __STUDIO_MANIFEST__
    purge_cloud_manifest_notes(client, nb_id)

    # 0.2. Chequeo de Cuota Multimedia en Google One (Pre-Flight Guard)
    skip_media_due_to_quota = False
    try:
        u_info = usage.get_usage(client)
        windows = u_info.get("windows", [])
        rolling = next((w for w in windows if w.get("window") == "rolling"), None)
        if rolling:
            pct_used = rolling.get("percent_used", 0.0)
            pct_rem = rolling.get("percent_remaining", 100.0)
            resets_at = rolling.get("resets_at", "")
            reset_note = f" (resetea: {resets_at[:16].replace('T', ' ')} UTC)" if resets_at else ""
            print(f"  {CYAN}📊 Cuota Multimedia Google One:{RESET} {pct_rem:.1f}% disponible ({pct_used:.1f}% usado){reset_note}")
            if pct_rem < 15.0 and not getattr(args, "no_media", False):
                print(f"  {YELLOW}⚠️ AVISO DE CUOTA: Te queda menos del 15% de cuota multimedia en Google One.{RESET}")
                print(f"  {YELLOW}   Para evitar fallos (RESOURCE_EXHAUSTED), se omitirá la generación de audio/video en este setup.{RESET}")
                print(f"  {YELLOW}   Se generarán todos los artefactos de texto, mapas y visuales (consumo: 0% cuota).{RESET}")
                skip_media_due_to_quota = True
    except Exception:
        pass

    # 1. Configurar Chat Socrático (Detección de Cuaderno Índice vs Aula de Estudio)
    is_master_guide = any(k in nb_title.upper() for k in ["GUIA-DE-ESTUDIO", "RUTA_DE_APRENDIZAJE", "[00]_", "[00]"])
    if is_master_guide:
        print(f"{BOLD}[Paso 1/3]{RESET} Detectado Cuaderno Índice: Configurando Chat en modo {CYAN}DECANO CURRICULAR{RESET}...")
        goal = "custom"
        custom_p = DEAN_CURRICULAR_PROMPT
    else:
        print(f"{BOLD}[Paso 1/3]{RESET} Configurando Chat Socrático con Mentoría Causal...")
        goal = "learning_guide" if getattr(args, "guide", False) else "custom"
        custom_p = None if goal == "learning_guide" else SOCRATIC_SYSTEM_PROMPT

    try:
        chat.configure_chat(client, nb_id, goal=goal, custom_prompt=custom_p, response_length="shorter")
        print(f"  {GREEN}✓ Chat configurado exitosamente en modo '{goal}' (conciso, socrático y 100% en español).{RESET}")
    except Exception as e_cfg:
        print(f"  {YELLOW}⚠️ Advertencia al configurar chat: {e_cfg}{RESET}")

    # 2. Análisis Semántico de Dominio & Generación de Suite Adaptativa
    src_count, detected_tier, metrics = analyze_notebook_density(client, nb_id)
    profile_arg = getattr(args, "profile", "auto") or "auto"
    overwrite = getattr(args, "overwrite", False)

    # Mapeo de perfil explícito o tier semántico
    if profile_arg == "core":
        effective_tier = "focused"
    elif profile_arg == "standard":
        effective_tier = "standard"
    elif profile_arg == "exhaustive":
        effective_tier = "macro_curriculum"
    else:
        effective_tier = detected_tier

    with_video = getattr(args, "with_video", False)
    all_media = getattr(args, "all_media", False)
    no_media = getattr(args, "no_media", False) or skip_media_due_to_quota
    max_count = getattr(args, "count", None)

    artifacts_specs = build_adaptive_suite(
        nb_id, nb_title, is_master_guide,
        tier=effective_tier,
        with_video=with_video,
        all_media=all_media,
        no_media=no_media,
        max_count=max_count
    )
    total_arts = len(artifacts_specs)

    lex_info = f"diversidad léxica: {metrics.get('lexical_diversity', 1.0)}"
    conc_info = f", conc: {metrics.get('top_keyword_concentration', 0.0)}" if metrics.get('dominant_keyword') else ""
    effective_desc = f"{effective_tier.upper()} ({src_count} fuentes, {lex_info}{conc_info})"
    print(f"\n{BOLD}[Paso 2/3]{RESET} Evaluando Suite Adaptativa de {total_arts} Artefactos en Studio ({CYAN}{effective_desc}{RESET})...")

    # Inspección de artefactos y notas preexistentes para Idempotencia Soberana (0 tokens / 0 cuota desperdiciada)
    existing_arts = []
    try:
        s_data = studio.get_studio_status(client, nb_id)
        existing_arts = s_data.get("artifacts", []) if isinstance(s_data, dict) else (s_data or [])
    except Exception as e_st:
        print(f"  {YELLOW}Aviso consultando estado previo de Studio: {e_st}{RESET}")

    cloud_manifest = extract_cloud_manifest(client, nb_id)

    def match_existing_artifact(target_title: str, target_type: str, art_list: list, manifest: dict):
        prefix = target_title[:3] if (len(target_title) >= 3 and target_title[:2].isdigit() and target_title[2] == "_") else ""
        for art in art_list:
            aid = art.get("artifact_id")
            atitle = art.get("title") or ""
            art_type = art.get("type")
            # 1. Coincidencia exacta de título
            if atitle == target_title:
                return art
            # 2. Coincidencia por mapeo en manifiesto SSoT de la nota de ruta
            if aid and manifest.get(aid) == target_title:
                return art
            # 3. Coincidencia por prefijo numérico ('01_', '02_') y mismo tipo
            if prefix and atitle.startswith(prefix) and art_type == target_type:
                return art
        return None

    dispatched = []
    skipped_count = 0

    for idx, (title, atype, kwargs) in enumerate(artifacts_specs, 1):
        kwargs.setdefault("language", "es-419")

        # Chequeo de Idempotencia: Si ya existe y no se forzó --overwrite, reutilizar
        matched_art = match_existing_artifact(title, atype, existing_arts, cloud_manifest) if not overwrite else None
        if matched_art:
            art_id = matched_art.get("artifact_id")
            art_status = matched_art.get("status", "completed")
            print(f"  • [{idx}/{total_arts}] {GREEN}⏩ [IDEMPOTENTE]{RESET} Omitiendo creación de {BOLD}{title}{RESET} ({atype}): ya existe en Studio ({CYAN}{art_status}{RESET}).")
            dispatched.append((title, art_id, atype))
            skipped_count += 1
            continue

        print(f"  • [{idx}/{total_arts}] Creando artefacto nativo: {BOLD}{title}{RESET} ({atype})...")

        # Guardia en vuelo para artefactos de alto cómputo
        if atype in ("audio", "video") and skip_media_due_to_quota:
            print(f"    {YELLOW}⏩ Omitiendo {title} para proteger cuota Google One (consumo crítico).{RESET}")
            continue

        max_retries = 3
        art_id = None
        for attempt in range(max_retries + 1):
            try:
                res = studio.create_artifact(client, nb_id, atype, **kwargs)
                art_id = getattr(res, "artifact_id", None) or (res.get("id") or res.get("artifact_id") if isinstance(res, dict) else None)
                print(f"    {GREEN}✓ Despachado exitosamente a Google Studio.{RESET}")
                break
            except Exception as e:
                err_str = str(e).lower()
                if ("rate limited" in err_str or "resourceexhausted" in err_str or "429" in err_str) and attempt < max_retries:
                    wait_time = 15 * (attempt + 1)
                    print(f"    {YELLOW}⚠️ Rate limit detectado en Google Cloud. Enfriando {wait_time}s (intento {attempt + 1}/{max_retries})...{RESET}")
                    time.sleep(wait_time)
                else:
                    print(f"    {YELLOW}⚠️ Nota al crear {title}: {e}{RESET}")
                    break
        dispatched.append((title, art_id, atype))
        # Espaciado determinista anti-burst entre peticiones
        time.sleep(4.5)

    if skipped_count == total_arts and not overwrite:
        print(f"\n  {GREEN}🛡️ BLINDAJE IDEMPOTENTE COMPLETO:{RESET} Los {total_arts} entregables de la suite ya existían en Studio. Se evitó 100% de gasto de cuota y peticiones duplicadas.")
    elif skipped_count > 0:
        print(f"\n  {GREEN}🛡️ BLINDAJE IDEMPOTENTE PARCIAL:{RESET} Se reutilizaron {skipped_count} artefactos preexistentes y solo se generaron {total_arts - skipped_count} faltantes.")

    # 3. Creación/Actualización de Notas Nativas en el Cuaderno (SSoT Cloud-Native, 0 bytes en disco local)
    print(f"\n{BOLD}[Paso 3/3]{RESET} Verificando y sincronizando notas de seguimiento y Ruta de Estudio SSoT...")

    existing_notes = []
    try:
        res_notes = notes.list_notes(client, nb_id)
        existing_notes = res_notes.get("notes", []) if isinstance(res_notes, dict) else (res_notes or [])
    except Exception as e_nl:
        print(f"  {YELLOW}Aviso consultando notas previas: {e_nl}{RESET}")

    lagunas_note = next((n for n in existing_notes if "00_CUADERNO_DE_LAGUNAS" in (n.get("title") or "").upper() or "LAGUNAS" in (n.get("title") or "").upper()), None)
    ruta_note = next((n for n in existing_notes if "00_RUTA_DE_ESTUDIO" in (n.get("title") or "").upper() or "RUTA" in (n.get("title") or "").upper()), None)

    lagunas_content = (
        "# 📓 Cuaderno de Lagunas Cognitivas y Puntos Ciegos\n\n"
        "Este espacio está destinado exclusivamente a registrar tus puntos ciegos y lagunas conceptuales detectadas durante el estudio.\n\n"
        "## ¿Cómo opera este cuaderno?\n"
        "- Tu Tutor Socrático (`nlm-tutor session`) registra automáticamente aquí cada concepto o pregunta donde detecte una brecha.\n"
        "- No anotes lo que ya dominas; el crecimiento cognitivo ocurre atacando lo que aún no comprendes con solidez.\n"
        "- En las sesiones de consolidación y repaso espaciado (`nlm-tutor schedule`), consulta en las fuentes únicamente las citas de esta lista.\n\n"
        "## Registro de Brechas y Lagunas Detectadas:\n"
        "- [ ] (Fecha: ____) Concepto / Mecanismo a reforzar: ____________________ | Fuente: ____________________\n"
    )

    if not lagunas_note:
        try:
            notes.create_note(client, nb_id, content=lagunas_content, title="00_CUADERNO_DE_LAGUNAS")
            print(f"  {GREEN}✓ Nota '00_CUADERNO_DE_LAGUNAS' creada en tu cuaderno.{RESET}")
        except Exception as e_n1:
            print(f"    {YELLOW}Aviso creando nota de lagunas: {e_n1}{RESET}")
    else:
        print(f"  {GREEN}✓ Nota '00_CUADERNO_DE_LAGUNAS' ya existente (preservando tus lagunas previas registradas).{RESET}")

    # Manifiesto estructurado embebido en el pie de la nota para reconciliación cloud-native
    manifest_items = [
        {"target_title": t, "artifact_id": aid, "type": at}
        for t, aid, at in dispatched
    ]
    manifest_json = json.dumps(manifest_items, ensure_ascii=False)

    art_list_md = "\n".join([f"{i}. **{t}** ({at})" for i, (t, aid, at) in enumerate(dispatched, 1)])
    ruta_content = (
        f"# 🗺️ Ruta de Estudio Guiada: {nb_title}\n\n"
        f"Suite pedagógica adaptativa de {len(dispatched)} entregables en Studio ({effective_desc}):\n\n"
        f"{art_list_md}\n\n"
        "--- \n"
        f"• Iniciá tu sesión de sparring socrático en terminal: `nlm-tutor session {nb_id}`\n"
        f"• Consultá tu agenda matemática de repasos: `nlm-tutor schedule {nb_id}`\n\n"
        f"<!-- NLM_TUTOR_MANIFEST: {manifest_json} -->\n"
    )

    if not ruta_note:
        try:
            notes.create_note(client, nb_id, content=ruta_content, title="00_RUTA_DE_ESTUDIO")
            print(f"  {GREEN}✓ Nota '00_RUTA_DE_ESTUDIO' creada en tu cuaderno.{RESET}")
        except Exception as e_n2:
            print(f"    {YELLOW}Aviso creando nota de ruta: {e_n2}{RESET}")
    else:
        try:
            notes.update_note(client, nb_id, ruta_note.get("id"), content=ruta_content)
            print(f"  {GREEN}✓ Nota '00_RUTA_DE_ESTUDIO' actualizada con manifiesto vigente (sin duplicar notas).{RESET}")
        except Exception as e_u2:
            print(f"    {YELLOW}Aviso actualizando nota de ruta: {e_u2}{RESET}")

    # Reconciliación y renombramiento asíncrono
    wait_time = 180 if getattr(args, "wait", False) else 75
    reconcile_and_rename_artifacts(client, nb_id, dispatched, max_wait=wait_time, poll_interval=10)

    print(f"\n{GREEN}============================================================{RESET}")
    print(f"  🎉 ¡CUADERNO CONFIGURADO CON ÉXITO CON SDK NATIVO v{VERSION}!")
    print(f"  Para iniciar tu sesión de tutoría socrática interactiva ejecutá:")
    print(f"    {BOLD}nlm-tutor session {nb_id}{RESET}")
    print(f"  Para ver tu calendario matemático de repasos de Ebbinghaus ejecutá:")
    print(f"    {BOLD}nlm-tutor schedule {nb_id}{RESET}")
    print(f"{GREEN}============================================================{RESET}\n")


def cmd_setup(args):
    """Configura el cuaderno individual o toda una colección como entorno socrático con 12 artefactos."""
    client = get_client()

    col_target = getattr(args, "collection", None)
    if col_target:
        try:
            cid, cname, nb_ids = resolve_collection(col_target, client)
        except Exception as e_col:
            print(f"{RED}[ERROR Colección]{RESET} {e_col}")
            return

        print(f"\n{CYAN}============================================================{RESET}")
        print(f"  📚 SETUP EN LOTE DE COLECCIÓN: {BOLD}{cname}{RESET} ({len(nb_ids)} cuadernos)")
        print(f"  UUID Colección: {CYAN}{cid}{RESET}")
        print(f"{CYAN}============================================================{RESET}\n")

        if not nb_ids:
            print(f"{YELLOW}Aviso: La colección '{cname}' no contiene cuadernos asociados.{RESET}")
            return

        for idx, nid in enumerate(nb_ids, 1):
            try:
                nb = resolve_notebook(nid, client)
                ntitle = nb.get("title") or nid
                print(f"\n{MAGENTA}>>> [{idx}/{len(nb_ids)}] Configurando cuaderno de colección: {BOLD}{ntitle}{RESET} ({CYAN}{nid}{RESET}) <<<")
                setup_single_notebook(client, nid, ntitle, args)
                if idx < len(nb_ids):
                    # Chequeo dinámico de cuota entre cuadernos de colección
                    try:
                        u_chk = usage.get_usage(client)
                        r_chk = next((w for w in u_chk.get("windows", []) if w.get("window") == "rolling"), None)
                        if r_chk and r_chk.get("percent_remaining", 100.0) < 18.0:
                            print(f"\n  {YELLOW}⚠️ AVISO DE PRE-VUELO EN COLECCIÓN: Cuota rolling baja ({r_chk.get('percent_remaining'):.1f}% restante).{RESET}")
                            print(f"  {YELLOW}   Activando modo --no-media automático para los cuadernos restantes para evitar HTTP 429.{RESET}\n")
                            setattr(args, "no_media", True)
                    except Exception:
                        pass
                    print(f"  [Rate-Limiting Anti-Burst] Pausando 6 segundos entre cuadernos de la colección...")
                    time.sleep(6)
            except Exception as e_nb:
                print(f"  {RED}⚠️ Error configurando cuaderno {nid}: {e_nb}{RESET}")

        print(f"\n{GREEN}✨ Setup en lote finalizado para la colección '{cname}'. Todos los cuadernos quedaron configurados.{RESET}\n")
        return

    if not getattr(args, "notebook", None):
        print(f"{RED}[ERROR]{RESET} Debés especificar el nombre o ID de un cuaderno, o la bandera --collection 'Nombre'")
        return

    nb = resolve_notebook(args.notebook, client)
    nb_id = nb.get("id") or nb.get("notebook_id")
    nb_title = nb.get("title")
    setup_single_notebook(client, nb_id, nb_title, args)


# ---------------------------------------------------------------------------
# COMANDO: rename
# Arnés de Reconciliación y Renombrado Secuencial en Studio
# ---------------------------------------------------------------------------

def cmd_rename(args):
    """Reconcilia y renombra todos los artefactos en Studio aplicando títulos canónicos numerados."""
    client = get_client()
    nb = resolve_notebook(args.notebook, client)
    nb_id = nb.get("id") or nb.get("notebook_id")
    nb_title = nb.get("title")

    print(f"\n{CYAN}============================================================{RESET}")
    print(f"  🔄 CONCILIACIÓN DE NOMBRES EN STUDIO: {BOLD}{nb_title}{RESET}")
    print(f"  UUID: {CYAN}{nb_id}{RESET}")
    print(f"{CYAN}============================================================{RESET}\n")

    reconcile_notebook_artifacts(client, nb_id, verbose=True)
    print(f"\n{GREEN}✓ Conciliación concluida.{RESET}\n")


def cmd_watch(args):
    """Daemon autónomo en segundo plano: sondea y renombra artefactos pesados cuando Google Cloud concluye."""
    nb_id = args.notebook
    client = get_client()
    max_iterations = 80  # 80 * 15s = 20 minutos
    poll_interval = 15

    for _ in range(max_iterations):
        time.sleep(poll_interval)
        try:
            status_data = studio.get_studio_status(client, nb_id)
            current_arts = status_data.get("artifacts", []) if isinstance(status_data, dict) else status_data
            in_progress = [a for a in current_arts if a.get("status") in ("in_progress", "pending")]
            reconcile_notebook_artifacts(client, nb_id, verbose=False)
            if not in_progress:
                break
        except Exception:
            pass


# ---------------------------------------------------------------------------
# COMANDO: clean
# Purga Higiénica Controlada (Studio + Notas del Tutor + Historial de Chat)
# Cero Eliminación de Fuentes ('sources' intocables)
# ---------------------------------------------------------------------------

def cmd_clean(args):
    """Limpia artefactos de Studio, notas del tutor e historial de chat (sin tocar fuentes)."""
    client = get_client()

    col_target = getattr(args, "collection", None)
    if col_target:
        try:
            cid, cname, nb_ids = resolve_collection(col_target, client)
        except Exception as e_col:
            print(f"{RED}[ERROR Colección]{RESET} {e_col}")
            return

        print(f"\n{CYAN}============================================================{RESET}")
        print(f"  🧹 LIMPIEZA EN LOTE DE COLECCIÓN: {BOLD}{cname}{RESET} ({len(nb_ids)} cuadernos)")
        print(f"  UUID Colección: {CYAN}{cid}{RESET}")
        print(f"{CYAN}============================================================{RESET}\n")

        if not nb_ids:
            print(f"{YELLOW}Aviso: La colección '{cname}' no contiene cuadernos asociados.{RESET}")
            return

        for idx, nid in enumerate(nb_ids, 1):
            try:
                nb = resolve_notebook(nid, client)
                ntitle = nb.get("title") or nid
                print(f"\n{YELLOW}>>> [{idx}/{len(nb_ids)}] Limpiando cuaderno: {BOLD}{ntitle}{RESET} ({CYAN}{nid}{RESET}) <<<")
                clean_notebook(
                    client=client,
                    nb_id=nid,
                    clean_studio=True,
                    clean_notes=True,
                    clean_chat=not getattr(args, "keep_chat", False),
                    all_notes=getattr(args, "all_notes", False)
                )
            except Exception as e_nb:
                print(f"  {RED}⚠️ Error limpiando cuaderno {nid}: {e_nb}{RESET}")

        print(f"\n{GREEN}✨ Limpieza en lote concluida para la colección '{cname}'. Fuentes intactas.{RESET}\n")
        return

    if not getattr(args, "notebook", None):
        print(f"{RED}[ERROR]{RESET} Debés especificar el nombre o ID de un cuaderno, o la bandera --collection 'Nombre'")
        return

    nb = resolve_notebook(args.notebook, client)
    nb_id = nb.get("id") or nb.get("notebook_id")
    nb_title = nb.get("title")

    print(f"\n{CYAN}============================================================{RESET}")
    print(f"  🗑️ NLM-TUTOR CLEAN: {BOLD}{nb_title}{RESET}")
    print(f"  UUID: {CYAN}{nb_id}{RESET}")
    print(f"{CYAN}============================================================{RESET}")

    clean_notebook(
        client=client,
        nb_id=nb_id,
        clean_studio=True,
        clean_notes=True,
        clean_chat=not getattr(args, "keep_chat", False),
        all_notes=getattr(args, "all_notes", False)
    )


# ---------------------------------------------------------------------------
# COMANDO: session
# Tutor Socrático Autónomo en Terminal (REPL Interactivo Bidireccional)
# ---------------------------------------------------------------------------

def cmd_session(args):
    """Modo REPL Interactivo: Tutor Socrático Autónomo en Terminal conectado bidireccionalmente a NotebookLM."""
    client = get_client()
    nb = resolve_notebook(args.notebook, client)
    nb_id = nb.get("id") or nb.get("notebook_id")
    nb_title = nb.get("title")
    duration = getattr(args, "duration", 90) or 90
    passive_reconcile_artifacts(client, nb_id)

    print(f"\n{CYAN}========================================================================================{RESET}")
    print(f"  🏛️  TUTOR SOCRÁTICO REPL INTERACTIVO ({duration} MINUTOS) — {BOLD}{nb_title}{RESET}")
    print(f"  Cuaderno: {CYAN}{nb_id}{RESET} | Bidireccional: {GREEN}Sincronizado con Google NotebookLM{RESET}")
    print(f"  Modo: {GREEN}Tutor Socrático NotebookLM + Active Recall (0 tokens API externa){RESET}")
    print(f"{CYAN}========================================================================================{RESET}")
    print(f"{YELLOW}Comandos en sesión:{RESET} Escribí {BOLD}/salir{RESET} para terminar | {BOLD}/tiempo{RESET} para ver el cronómetro | {BOLD}/ayuda{RESET}\n")

    start_time = datetime.now()
    session_gaps_count = 0
    turns_count = 0
    conv_id = None

    print(f"{CYAN}Conectando con tu Tutor Socrático y Mentor Cognitivo en NotebookLM...{RESET}\n")
    kickoff_prompt = (
        f"Iniciamos una sesión de estudio interactiva de {duration} minutos en español neutro latinoamericano. "
        f"Actúa como mi Tutor Socrático y Mentor Cognitivo de NotebookLM. "
        f"Salúdame muy brevemente en 2 líneas indicando el objetivo de la sesión de hoy, "
        f"y formula tu primera pregunta de razonamiento conceptual basada en los fundamentos del cuaderno "
        f"(Nivel 1: Comprensión base) para evaluar si domino el esqueleto del tema. "
        f"No des la respuesta ni opciones múltiples; hazme reflexionar en una pregunta concisa."
    )

    try:
        q_res = chat.query(client, nb_id, kickoff_prompt)
        conv_id = q_res.get("conversation_id")
        answer = q_res.get("answer", "")
        print(f"{BOLD}{BLUE}[Tutor Socrático NotebookLM]{RESET}\n{answer}\n")
    except Exception as e_kick:
        print(f"{RED}[ERROR conectando chat]{RESET} {e_kick}")
        return

    while True:
        try:
            elapsed = (datetime.now() - start_time).total_seconds() / 60.0
            remaining = max(0.0, duration - elapsed)

            prompt_label = f"{BOLD}{GREEN}[Tú ({int(elapsed)}/{duration} min)]{RESET} > "
            user_input = input(prompt_label).strip()

            if not user_input:
                continue

            lower_input = user_input.lower()
            if lower_input in ("/salir", "/exit", "/quit", "salir", "exit", "q"):
                print(f"\n{YELLOW}Finalizando sesión de estudio a petición del usuario...{RESET}")
                break

            if lower_input in ("/tiempo", "/timer", "tiempo", "timer"):
                print(f"  ⏱️  {BOLD}Tiempo transcurrido:{RESET} {elapsed:.1f} min / {duration} min ({remaining:.1f} min restantes).\n")
                continue

            if lower_input in ("/ayuda", "/help", "help", "ayuda"):
                print(f"  💡 {BOLD}Comandos disponibles:{RESET}")
                print(f"     /tiempo  - Muestra el tiempo transcurrido de la sesión.")
                print(f"     /salir   - Finaliza la sesión y consolida las lagunas.")
                print(f"     O simplemente respondé la pregunta del tutor con tus propias palabras a libro cerrado.\n")
                continue

            turns_count += 1
            query_to_tutor = (
                f"{user_input}\n\n"
                f"[Instrucción del sistema: Evalúa mi razonamiento en español neutro latinoamericano. "
                f"Si detectas una brecha conceptual o error fundamental en mi respuesta, incluye al final la línea exacta: "
                f"BRECHA DETECTADA: [concepto] | Cita recomendada: [fuente]. "
                f"Luego formula la siguiente pregunta progresiva incrementando la profundidad conceptual hacia niveles de aplicación o síntesis.]"
            )

            print(f"\n{CYAN}El Tutor Socrático está evaluando tu razonamiento contra las fuentes...{RESET}\n")
            q_res = chat.query(client, nb_id, query_to_tutor, conversation_id=conv_id)
            if q_res.get("conversation_id"):
                conv_id = q_res.get("conversation_id")
            answer = q_res.get("answer", "")
            print(f"{BOLD}{BLUE}[Tutor Socrático NotebookLM]{RESET}\n{answer}\n")

            # Auto-registro robusto de lagunas cognitivas con soporte para markdown
            gap_match = re.search(r'(?:\*\*|\#\#)?\s*BRECHA DETECTADA\s*(?:\*\*)?:\s*(.+)', answer, re.IGNORECASE)
            if gap_match:
                gap_desc = gap_match.group(1).strip()
                ok = log_cognitive_gap(client, nb_id, gap_desc)
                if ok:
                    session_gaps_count += 1
                    print(f"  {YELLOW}📝 [Auto-registro silencioso]{RESET} Laguna guardada en '00_CUADERNO_DE_LAGUNAS': {CYAN}{gap_desc}{RESET}\n")

            # Alerta de finalización de bloque sin bucle infinito
            elapsed = (datetime.now() - start_time).total_seconds() / 60.0
            if elapsed >= duration:
                print(f"\n{YELLOW}⏰ ¡Has cumplido el objetivo de tiempo de {duration} minutos!{RESET}")
                cont = input(f"¿Deseas continuar la sesión 30 minutos más? (s/n): ").strip().lower()
                if cont in ("s", "si", "y", "yes"):
                    duration += 30
                    print(f"  {GREEN}✓ Tiempo extendido a {duration} minutos.{RESET}\n")
                else:
                    break

        except (KeyboardInterrupt, EOFError):
            print(f"\n\n{YELLOW}Interrupción detectada. Cerrando sesión de forma segura...{RESET}")
            break

    # Resumen de Cierre de Sesión
    elapsed_total = (datetime.now() - start_time).total_seconds() / 60.0
    print(f"\n{GREEN}========================================================================================{RESET}")
    print(f"  🏁 SESIÓN CONCLUIDA CON ÉXITO")
    print(f"  • Tiempo total de estudio enfocado: {BOLD}{elapsed_total:.1f} minutos{RESET}")
    print(f"  • Turnos socráticos de razonamiento: {BOLD}{turns_count}{RESET}")
    print(f"  • Lagunas cognitivas registradas automáticamente: {BOLD}{session_gaps_count}{RESET}")
    print(f"  • Próximo paso: Consulta tu agenda de repasos con: {BOLD}nlm-tutor schedule {nb_id}{RESET}")
    print(f"{GREEN}========================================================================================{RESET}\n")


# ---------------------------------------------------------------------------
# COMANDO: schedule
# Generador Matemático de Fechas de Repetición Espaciada (Científica - 0 Tokens)
# ---------------------------------------------------------------------------

def cmd_schedule(args):
    """Calcula y muestra la agenda pedagógica de estudio y repasos espaciados adaptada dinámicamente a los artefactos reales (0 tokens LLM)."""
    client = get_client()
    nb = resolve_notebook(args.notebook, client)
    nb_id = nb.get("id") or nb.get("notebook_id")
    nb_title = nb.get("title")
    passive_reconcile_artifacts(client, nb_id)

    start_time = datetime.now()
    if args.start:
        try:
            start_time = datetime.strptime(args.start, "%Y-%m-%d %H:%M")
        except ValueError:
            try:
                start_time = datetime.strptime(args.start, "%Y-%m-%d")
            except ValueError:
                print(f"{YELLOW}Formato de fecha no reconocido, usando fecha actual.{RESET}")

    # 1. Inspección de artefactos reales existentes en Studio
    arts = []
    try:
        s_data = studio.get_studio_status(client, nb_id)
        arts = s_data.get("artifacts", []) if isinstance(s_data, dict) else (s_data or [])
    except Exception:
        pass

    art_names = {a.get("title"): a for a in arts if a.get("title")}

    # Detección dinámica de artefactos reales disponibles en el cuaderno
    audio_art = next((t for t in art_names if "03_AUDIO" in t or "AUDIO" in t), "03_AUDIO_Inmersion-General-Podcast")
    map_art = next((t for t in art_names if "02_MAPA" in t or "MAPA" in t), "02_MAPA_Syllabus-Estructural")
    table_art = next((t for t in art_names if "04_TABLA" in t or "TABLA" in t), "04_TABLA_Matriz-Deconstruccion-80-20")
    report_art = next((t for t in art_names if "05_INFORME" in t or "INFORME" in t), "05_INFORME_Plan-de-Accion-y-Errores")
    quiz_art = next((t for t in art_names if "01_DIAGNOSTICO" in t or "DIAGNOSTICO" in t or "QUIZ" in t), "01_DIAGNOSTICO_Activacion-Conceptual")
    flash_art = next((t for t in art_names if "FLASHCARDS" in t), None)
    slides_art = next((t for t in art_names if "SLIDES" in t), None)

    print(f"\n{CYAN}========================================================================================{RESET}")
    print(f"  🗺️ RUTA PEDAGÓGICA Y AGENDA DE REPETICIÓN ESPACIADA: {BOLD}{nb_title}{RESET}")
    print(f"  Inicio base: {BOLD}{start_time.strftime('%Y-%m-%d %H:%M')}{RESET} | Cuaderno: {CYAN}{nb_id}{RESET}")
    print(f"  Gobernanza: {GREEN}Neurociencia del Active Recall (Make It Stick & Curva de Ebbinghaus){RESET}")
    print(f"{CYAN}========================================================================================{RESET}\n")

    print(f"{BOLD}📖 FASE 0: ASIMILACIÓN Y ESTUDIO INTEGRAL (DÍA DE INICIO / HOY){RESET}")
    print(f"Antes de evaluar o repasar, completá la absorción activa del material en este orden lógico:\n")
    print(f"  1. {CYAN}Inmersión Auditiva y Marco Global (15 min):{RESET}")
    print(f"     Escuchá {BOLD}{audio_art}{RESET} mientras salís a caminar o preparás tu espacio de estudio.")
    print(f"  2. {CYAN}Cartografía Conceptual y Jerarquías (5 min):{RESET}")
    print(f"     Explorá {BOLD}{map_art}{RESET} para ubicar la taxonomía y cómo se articulan los módulos.")
    print(f"  3. {CYAN}Deconstrucción 80/20 y Puntos Críticos (20 min):{RESET}")
    print(f"     Estudiá {BOLD}{table_art}{RESET} (mecanismos nucleares vs errores) y {BOLD}{report_art}{RESET}.")
    print(f"  4. {CYAN}Sparring Socrático y Pre-Testing Activo (30-45 min):{RESET}")
    print(f"     Resolvé {BOLD}{quiz_art}{RESET} a libro cerrado o iniciá tu tutor interactivo:")
    print(f"     {GREEN}nlm-tutor session {nb_id} --duration 90{RESET}")
    print(f"  5. {CYAN}Registro de Puntos Ciegos (10 min):{RESET}")
    print(f"     El tutor anotará tus lagunas automáticamente en {BOLD}00_CUADERNO_DE_LAGUNAS{RESET}.\n")

    print(f"{BOLD}📅 CRONOGRAMA MATEMÁTICO INTEGRAL: ESTUDIO ACTIVO (HOY) + REPASOS ESPACIADOS (EBBINGHAUS){RESET}")
    print(f"Seguí esta secuencia cronológica para transformar la información en comprensión permanente (0 tokens LLM):\n")

    intervals = [
        ("Hito 0 (HOY - Inmediato)", timedelta(minutes=0),
         f"nlm-tutor session {nb_id[:8]}.. (90m)",
         "¡Tu sesión socrática principal! Responder al tutor a libro cerrado y registrar lagunas."),

        ("Hito 1 (+24 horas)", timedelta(days=1),
         flash_art or "00_CUADERNO_DE_LAGUNAS (Feynman)",
         "15 min de auto-explicación a libro cerrado atacando las lagunas de la sesión de hoy."),

        ("Hito 2 (+72 horas)", timedelta(days=3),
         quiz_art,
         "10 min: Re-evaluación conceptual con el Cuestionario a libro cerrado (meta: >80%)."),

        ("Hito 3 (+7 días)", timedelta(days=7),
         f"nlm-tutor prompt {nb_id[:8]}.. 3 --send",
         "15 min: Test de 10 preguntas de razonamiento causal y casos prácticos en el chat."),

        ("Hito 4 (+14 días)", timedelta(days=14),
         "00_CUADERNO_DE_LAGUNAS (Auditoría)",
         "Repaso relámpago exclusivo de las citas de las fuentes donde tuviste dudas."),

        ("Hito 5 (+30 días)", timedelta(days=30),
         slides_art or report_art or "Síntesis Feynman en Voz Alta",
         "Consolidación permanente en memoria a largo plazo: explicar el tema completo sin mirar notas.")
    ]

    print(f"{'Hito':<22} | {'Fecha Programada':<16} | {'Recurso / Artefacto Real':<36} | {'Objetivo'}")
    print("-" * 115)

    for hito, delta, artifact, objetivo in intervals:
        sched_date = (start_time + delta).strftime("%Y-%m-%d %H:%M")
        print(f"{BOLD}{hito:<22}{RESET} | {GREEN}{sched_date:<16}{RESET} | {CYAN}{artifact:<36}{RESET} | {objetivo}")

    print("-" * 115)

    # Inspeccionar lagunas cognitivas registradas en 00_CUADERNO_DE_LAGUNAS
    try:
        notes_data = notes.list_notes(client, nb_id)
        notes_list = notes_data.get("notes", []) if isinstance(notes_data, dict) else []
        laguna_note = next((n for n in notes_list if "00_CUADERNO_DE_LAGUNAS" in (n.get("title") or "").upper()), None)
        if laguna_note and laguna_note.get("content"):
            gap_lines = [l.strip() for l in laguna_note["content"].split("\n") if l.strip().startswith("- [") and "Concepto / Mecanismo" not in l]
            if gap_lines:
                print(f"\n{YELLOW}📋 LAGUNAS COGNITIVAS REGISTRADAS PARA TUS PRÓXIMOS REPASOS ({len(gap_lines)} activas):{RESET}")
                for g in gap_lines[-8:]:
                    print(f"   {CYAN}{g}{RESET}")
                print(f"\n  {YELLOW}💡 Consejo:{RESET} Enfocá tu sesión de repaso exclusivamente en las lagunas de arriba.")
            else:
                print(f"\n{GREEN}ℹ️ Sin lagunas pendientes registradas todavía.{RESET}")
                print(f"   Iniciá tu sesión interactiva con {BOLD}nlm-tutor session {nb_id}{RESET} para que el tutor evalúe tu razonamiento.")
    except Exception:
        pass

    print(f"\n{YELLOW}💡 Regla de Oro:{RESET} Si en cualquier Hito tu precisión cae por debajo del {BOLD}80%{RESET},")
    print(f"no releas todo el material desde cero; abrí {CYAN}00_CUADERNO_DE_LAGUNAS{RESET} y atacá SOLO los puntos donde fallaste.\n")


# ---------------------------------------------------------------------------
# COMANDO: prompt
# Biblioteca de los 12 Prompts Maestros con Inyección Rápida
# ---------------------------------------------------------------------------

def cmd_prompt(args):
    """Muestra o envía al chat de NotebookLM cualquiera de los 12 prompts maestros mediante SDK nativo."""
    client = get_client()
    nb = resolve_notebook(args.notebook, client)
    nb_id = nb.get("id") or nb.get("notebook_id")
    nb_title = nb.get("title")

    p_id = args.prompt_id

    if p_id not in MASTER_PROMPTS:
        print(f"\n{YELLOW}Por favor selecciona un número de prompt entre 1 y 12:{RESET}")
        for k, v in MASTER_PROMPTS.items():
            print(f"  {BOLD}{k}.{RESET} {v['title']} ({CYAN}{v['desc']}{RESET})")
        print("")
        return

    p = MASTER_PROMPTS[p_id]
    print(f"\n{CYAN}============================================================{RESET}")
    print(f"  💡 PROMPT MAESTRO #{p_id}: {BOLD}{p['title']}{RESET}")
    print(f"  Cuaderno: {nb_title} ({nb_id})")
    print(f"{CYAN}============================================================{RESET}\n")
    print(f"{BOLD}Descripción:{RESET} {p['desc']}\n")
    print(f"{GREEN}Texto del Prompt:{RESET}\n")
    print(f'"{p["prompt"]}"\n')

    if args.send:
        print(f"{BOLD}Enviando pregunta al cuaderno mediante SDK chat.query...{RESET}")
        try:
            q_res = chat.query(client, nb_id, p["prompt"])
            answer = q_res.get("answer") if isinstance(q_res, dict) else str(q_res)
            print(f"\n{CYAN}--- Respuesta del Tutor NotebookLM ---{RESET}\n")
            print(answer)
            print(f"\n{CYAN}---------------------------------------{RESET}\n")
        except Exception as e_q:
            print(f"{RED}[ERROR chat.query]{RESET} {e_q}")
    elif args.note:
        print(f"{BOLD}Guardando prompt como nota en el cuaderno mediante SDK notes.create_note...{RESET}")
        try:
            notes.create_note(client, nb_id, content=p["prompt"], title=f"Prompt_{p_id}_{p['title'][:25]}")
            print(f"{GREEN}✓ Guardado exitosamente como nota en NotebookLM.{RESET}")
        except Exception as e_not:
            print(f"{RED}[ERROR notes.create_note]{RESET} {e_not}")
    else:
        print(f"{YELLOW}Para enviarlo directo al chat ejecutá:{RESET}")
        print(f"  nlm-tutor prompt {nb_id} {p_id} --send")
        print(f"{YELLOW}Para guardarlo como nota en el cuaderno ejecutá:{RESET}")
        print(f"  nlm-tutor prompt {nb_id} {p_id} --note\n")


# ---------------------------------------------------------------------------
# COMANDO: cross
# Consultas Transversales Multi-Cuaderno
# ---------------------------------------------------------------------------

def cmd_cross(args):
    """Ejecuta una consulta transversal sobre múltiples cuadernos mediante SDK nativo."""
    client = get_client()
    query = args.query
    print(f"\n{CYAN}============================================================{RESET}")
    print(f"  🌐 CONSULTA TRANSVERSAL MULTI-CUADERNO (CROSS-QUERY NATIVO)")
    print(f"  Pregunta: {BOLD}{query}{RESET}")
    print(f"{CYAN}============================================================{RESET}\n")

    try:
        res = cross_notebook.cross_notebook_query(client, query_text=query, all_notebooks=True)
        results = res.get("results", []) if isinstance(res, dict) else []
        if not results:
            print("No se obtuvieron respuestas transversales.")
            return
        for r in results:
            title = r.get("title") or r.get("notebook_id") or "Cuaderno"
            ans = r.get("answer") or "Sin respuesta."
            print(f"\n{GREEN}=== {title} ==={RESET}")
            print(ans)
    except Exception as e_cross:
        print(f"{RED}[ERROR cross_notebook_query]{RESET} {e_cross}")


# ---------------------------------------------------------------------------
# COMANDO: collections
# Listado de Colecciones Nativas en Google NotebookLM
# ---------------------------------------------------------------------------

def cmd_collections(args):
    """Lista las colecciones nativas de la cuenta mediante SDK."""
    client = get_client()
    print(f"\n{CYAN}============================================================{RESET}")
    print(f"  📁 COLECCIONES NATIVAS EN GOOGLE NOTEBOOKLM PRO")
    print(f"{CYAN}============================================================{RESET}\n")
    try:
        data = collections.list_collections(client)
        cols = data.get("collections", []) if isinstance(data, dict) else []
        if not cols:
            print("No se encontraron colecciones en tu cuenta.")
            return
        print(f"{'#':<3} | {'Nombre de la Colección':<45} | {'Cuadernos':<10} | {'ID'}")
        print("-" * 95)
        for idx, col in enumerate(cols, 1):
            name = col.get("name", "Sin nombre")[:43]
            count = len(col.get("notebook_ids", []))
            cid = col.get("id") or col.get("collection_id") or ""
            print(f"{idx:<3} | {BOLD}{name:<45}{RESET} | {count:<10} | {CYAN}{cid}{RESET}")
        print("-" * 95 + "\n")
    except Exception as e_col:
        print(f"{RED}[ERROR list_collections]{RESET} {e_col}")


# ---------------------------------------------------------------------------
# COMANDO: list
# Listado de Cuadernos Disponibles
# ---------------------------------------------------------------------------

def cmd_list(args):
    """Muestra la lista de todos los cuadernos con su estado mediante SDK nativo."""
    client = get_client()
    all_nbs = get_all_notebooks(client, max_results=500)
    print(f"\n{CYAN}============================================================{RESET}")
    print(f"  📚 CUADERNOS DISPONIBLES EN GOOGLE NOTEBOOKLM PRO ({len(all_nbs)} totales)")
    print(f"{CYAN}============================================================{RESET}\n")
    if not all_nbs:
        print("No se encontraron cuadernos.")
        return

    print(f"{'#':<3} | {'Título del Cuaderno':<50} | {'Fuentes':<7} | {'ID'}")
    print("-" * 105)
    for idx, nb in enumerate(all_nbs, 1):
        title = (nb.get("title") or "Sin título")[:48]
        sources = nb.get("source_count") or len(nb.get("sources", [])) if isinstance(nb.get("sources"), list) else 0
        nid = nb.get("id") or nb.get("notebook_id") or ""
        print(f"{idx:<3} | {BOLD}{title:<50}{RESET} | {sources:<7} | {CYAN}{nid}{RESET}")
    print("-" * 105)
    print(f"\n{YELLOW}Tip:{RESET} Para configurar cualquier cuaderno como tutor ejecutá:")
    print(f"  {BOLD}nlm-tutor setup <ID>{RESET}\n")


# ---------------------------------------------------------------------------
# COMANDO: usage
# Telemetría de Cuotas Google One AI Premium (Ventana Rolling ~5h y Semanal)
# ---------------------------------------------------------------------------

def cmd_usage(args):
    """Muestra la telemetría viva de cuotas de cómputo en Google One AI Premium (Octubre 2026)."""
    client = get_client()
    print(f"\n{CYAN}========================================================================================{RESET}")
    print(f"  📊 TELEMETRÍA DE CUOTA EN VIVO: GOOGLE NOTEBOOKLM PRO (GOOGLE ONE AI PREMIUM)")
    print(f"{CYAN}========================================================================================{RESET}\n")
    try:
        u_info = usage.get_usage(client)
        tier = u_info.get("tier", "NOTEBOOKLM_TIER_PRO_CONSUMER_USER")
        windows = u_info.get("windows", [])

        print(f"  • {BOLD}Nivel de Suscripción:{RESET} {GREEN}{tier}{RESET}")
        print(f"  • {BOLD}Modelo de Cómputo:{RESET} Asignación ponderada por ráfaga (SOTA Octubre 2026)\n")

        print(f"  {'Ventana de Cómputo':<26} | {'% Usado':<10} | {'% Disponible':<14} | {'Hora de Reset (UTC)':<24}")
        print("  " + "-" * 80)

        rolling_avail = 100.0
        for w in windows:
            w_name = w.get("window", "").capitalize()
            p_used = w.get("percent_used", 0.0)
            p_rem = w.get("percent_remaining", 100.0)
            r_at = w.get("resets_at", "N/A")
            if isinstance(r_at, str) and "T" in r_at:
                r_at = r_at.replace("T", " ")[:19]

            w_desc = "Rolling (~5 horas)" if "roll" in w_name.lower() else "Semanal (7 días)"
            if "roll" in w_name.lower():
                rolling_avail = p_rem

            color_stat = GREEN if p_rem >= 30.0 else (YELLOW if p_rem >= 15.0 else RED)
            print(f"  {BOLD}{w_desc:<26}{RESET} | {p_used:>7.1f}%   | {color_stat}{p_rem:>10.1f}%{RESET}   | {r_at:<24}")

        print("  " + "-" * 80 + "\n")

        # Semáforo de seguridad de generación
        if rolling_avail >= 30.0:
            print(f"  🟢 {GREEN}{BOLD}ESTADO VERDE:{RESET} Capacidad óptima. Podés generar audios y la suite completa sin riesgo de 429.")
        elif rolling_avail >= 15.0:
            print(f"  🟡 {YELLOW}{BOLD}ESTADO AMARILLO:{RESET} Capacidad moderada. Se recomienda usar perfil 'core' (1 solo audio) o --no-media.")
        else:
            print(f"  🔴 {RED}{BOLD}ESTADO ROJO:{RESET} Cuota rolling crítica (<15%). Google arrojará 429 en audios/videos. Generá solo texto/mapas.")
        print("")
    except Exception as e_u:
        print(f"  {RED}[ERROR consultando cuotas]{RESET} {e_u}\n")


# ---------------------------------------------------------------------------
# COMANDO: manual
# Manual del Estudiante y Guía Pedagógica MVLS Integrada en Terminal
# ---------------------------------------------------------------------------

def cmd_manual(args):
    """Muestra el manual pedagógico del estudiante y guía de 4 fases directamente en la terminal."""
    print(f"\n{CYAN}========================================================================================{RESET}")
    print(f"  🎓 MANUAL DEL ESTUDIANTE: DOMINA CUALQUIER TEMA CON NLM-TUTOR (COHALO FRACTAL v{VERSION})")
    print(f"{CYAN}========================================================================================{RESET}\n")
    print(f"  {BOLD}Fundamentación Científica:{RESET}")
    print(f"  • {GREEN}Make It Stick / Harvard:{RESET} Inversión 20/80 (20% andamiaje inicial, 80% Active Recall forzado).")
    print(f"  • {GREEN}Josh Kaufman (20 Horas):{RESET} Deconstruir en 3-4 micro-habilidades y aprender lo justo para autocorregirse.")
    print(f"  • {GREEN}MIT Dinámica de Sistemas:{RESET} Iceberg de 4 capas (Hechos -> Patrones -> Estructuras -> Modelos Mentales).")
    print(f"  • {GREEN}Ebbinghaus / Repetición Espaciada:{RESET} Repasos algorítmicos en +24h, +3d, +7d, +14d y +30d.\n")

    print(f"  {BOLD}🏛️  LAS 4 FASES DEL MINIMAL VIABLE LEARNING STACK (MVLS):{RESET}")
    print(f"  1. {CYAN}FASE 1 (Pre-Test & Quiebre de Ilusión):{RESET} 01_DIAGNOSTICO_Activacion-Conceptual.")
    print(f"     Rompe la falsa familiaridad antes de leer el material. Equivocarte aquí triplica la retención.")
    print(f"  2. {CYAN}FASE 2 (Andamiaje Panorámico):{RESET} 02_MAPA_Syllabus-Estructural & 03_AUDIO_Inmersion-General.")
    print(f"     Escucha el podcast mientras caminas o preparas tu espacio; mira el mapa 3 minutos para ver el bosque.")
    print(f"  3. {CYAN}FASE 3 (Deconstrucción Causal & Errores):{RESET} 04_TABLA_Matriz-Deconstruccion-80-20 & 05_INFORME_Plan-de-Accion.")
    print(f"     Hoja de una página con el catálogo de trampas típicas para saber cuándo te estás equivocando.")
    print(f"  4. {CYAN}FASE 4 (Sparring Socrático & Repaso Espaciado):{RESET} nlm-tutor session & 00_CUADERNO_DE_LAGUNAS.")
    print(f"     Entrenamiento interactivo en terminal con la regla de 1 sola pregunta a la vez a libro cerrado.\n")

    print(f"  {BOLD}🚦 EL SEMÁFORO DE AVANCE:{RESET}")
    print(f"  • 🟢 {GREEN}VERDE (≥ 80% aciertos):{RESET} Dominas los invariantes causales. Avanza al siguiente módulo.")
    print(f"  • 🟡 {YELLOW}AMARILLO / ROJO (< 80%):{RESET} {BOLD}NO releas todo el material.{RESET} Abre '00_CUADERNO_DE_LAGUNAS',")
    print(f"    revisa únicamente las citas de los conceptos fallados y haz 10 min de Active Recall.\n")

    print(f"  {BOLD}⚡ COMANDOS RÁPIDOS:{RESET}")
    print(f"  • {CYAN}nlm-tutor setup <ID>{RESET}                -> Configura el cuaderno con el MVLS hiper-efectivo (5 artefactos).")
    print(f"  • {CYAN}nlm-tutor setup <ID> --profile standard{RESET} -> Genera la suite completa de 11 artefactos para cursos troncales.")
    print(f"  • {CYAN}nlm-tutor session <ID> --duration 90{RESET}    -> Inicia bloque de 90 min con sparring socrático en terminal.")
    print(f"  • {CYAN}nlm-tutor schedule <ID>{RESET}               -> Calcula tu calendario matemático de Ebbinghaus.")
    print(f"  • {CYAN}nlm-tutor usage{RESET}                      -> Monitorea tu cuota viva de Google One.")
    print(f"  • {CYAN}nlm-tutor prompt <ID> <1-12> --send{RESET}   -> Envía un prompt maestro directamente al chat.\n")


# ---------------------------------------------------------------------------
# CLI Argument Parser Principal
# ---------------------------------------------------------------------------

def main():
    parser = argparse.ArgumentParser(
        prog="nlm-tutor",
        description="Sistema Autónomo de Aprendizaje Acelerado y Tutoría Socrática para Google NotebookLM Pro.",
        epilog="Desarrollado bajo Supreme Directive v8.5 & CoHaLo Engineering."
    )
    parser.add_argument("--version", "-v", action="version", version=f"nlm-tutor v{VERSION}")

    subparsers = parser.add_subparsers(dest="command", help="Comando a ejecutar")

    # setup
    p_setup = subparsers.add_parser("setup", help="Configura el Tutor Socrático y genera la suite adaptativa (MVLS por defecto).")
    p_setup.add_argument("notebook", nargs="?", default="", help="ID, prefijo o título del cuaderno en NotebookLM.")
    p_setup.add_argument("--collection", "-c", help="Nombre o ID de la colección para configurar todos sus cuadernos en lote.")
    p_setup.add_argument("--profile", "-p", choices=["auto", "core", "standard", "exhaustive"], default="auto", help="Perfil de suite: core (MVLS de 5 entregables esenciales), standard (11 artefactos del manual), auto (adaptativo por densidad).")
    p_setup.add_argument("--with-video", action="store_true", help="Genera video explicativo en Studio (por defecto omitido para proteger la cuota Google One).")
    p_setup.add_argument("--video-style", default="auto_select", choices=["auto_select", "whiteboard", "kawaii", "anime", "watercolor", "retro_print", "heritage", "paper_craft", "classic", "custom"], help="Estilo visual del video explicativo en Studio (Octubre 2026).")
    p_setup.add_argument("--video-format", default="explainer", choices=["explainer", "brief", "cinematic", "short"], help="Formato de video en Studio: explainer (2-4 min), brief, cinematic (veo), short.")
    p_setup.add_argument("--all-media", action="store_true", help="Genera la suite multimedia completa: 4 audios (brief, deep_dive, critique, debate) y video.")
    p_setup.add_argument("--no-media", action="store_true", help="Genera exclusivamente entregables de texto, mapas y visuales (consumo: 0%% cuota multimedia Google One).")
    p_setup.add_argument("--count", type=int, help="Límite máximo de artefactos a generar en la suite.")
    p_setup.add_argument("--wait", action="store_true", help="Esperar de forma síncrona en terminal hasta que concluyan los artefactos pesados (por defecto delega a vigilancia en segundo plano).")
    p_setup.add_argument("--guide", action="store_true", help="Usar modo nativo 'learning_guide' en vez de 'custom'.")
    p_setup.add_argument("--clean", action="store_true", help="Limpia artefactos de Studio, notas 00 y chat antes de configurar (no toca fuentes).")
    p_setup.add_argument("--overwrite", "--force", action="store_true", help="Fuerza la regeneración de los entregables en Studio aunque ya existan previamente.")

    # usage / quota
    subparsers.add_parser("usage", help="Consulta la telemetría en vivo de tus cuotas de cómputo en Google One (ventana rolling y semanal).")
    subparsers.add_parser("quota", help="Alias de 'usage'.")

    # manual / guide
    subparsers.add_parser("manual", help="Muestra el Manual del Estudiante y las 4 fases del Minimal Viable Learning Stack en terminal.")
    subparsers.add_parser("guide", help="Alias de 'manual'.")

    # clean
    p_clean = subparsers.add_parser("clean", help="Limpia artefactos de Studio, notas del tutor e historial de chat (sin tocar fuentes).")
    p_clean.add_argument("notebook", nargs="?", default="", help="ID, prefijo o título del cuaderno en NotebookLM.")
    p_clean.add_argument("--collection", "-c", help="Nombre o ID de la colección para limpiar todos sus cuadernos en lote.")
    p_clean.add_argument("--all-notes", action="store_true", help="Elimina todas las notas del cuaderno, no solo las 00 del tutor.")
    p_clean.add_argument("--keep-chat", action="store_true", help="Conserva el historial de conversación del chat sin borrarlo.")

    # rename / reconcile
    p_rename = subparsers.add_parser("rename", help="Reconcilia y renombra todos los artefactos en Studio con títulos numerados.")
    p_rename.add_argument("notebook", help="ID, prefijo o título del cuaderno en NotebookLM.")

    # session
    p_session = subparsers.add_parser("session", help="Inicia una sesión de estudio guiada interactiva (por defecto 90 min).")
    p_session.add_argument("notebook", help="ID, prefijo o título del cuaderno en NotebookLM.")
    p_session.add_argument("--duration", "-d", type=int, default=90, help="Duración en minutos (por defecto: 90).")

    # schedule
    p_sched = subparsers.add_parser("schedule", help="Genera la agenda matemática de repasos espaciados (Ebbinghaus - 0 tokens).")
    p_sched.add_argument("notebook", help="ID, prefijo o título del cuaderno en NotebookLM.")
    p_sched.add_argument("--start", "-s", help="Fecha base de inicio (YYYY-MM-DD o 'YYYY-MM-DD HH:MM').")

    # prompt
    p_prompt = subparsers.add_parser("prompt", help="Biblioteca de los 12 Prompts Maestros para estudiar.")
    p_prompt.add_argument("notebook", help="ID, prefijo o título del cuaderno en NotebookLM.")
    p_prompt.add_argument("prompt_id", type=int, nargs="?", default=0, help="Número de prompt (1 a 12).")
    p_prompt.add_argument("--send", action="store_true", help="Enviar directamente como pregunta al chat del cuaderno.")
    p_prompt.add_argument("--note", action="store_true", help="Guardar el texto del prompt como una nota en el cuaderno.")

    # cross
    p_cross = subparsers.add_parser("cross", help="Ejecuta una consulta transversal multi-cuaderno.")
    p_cross.add_argument("query", help="Pregunta o consulta transversal a realizar.")

    # collections
    subparsers.add_parser("collections", help="Lista las colecciones nativas disponibles en tu cuenta.")

    # list
    subparsers.add_parser("list", help="Lista todos los cuadernos disponibles en tu cuenta.")

    # _watch (daemon interno desacoplado en segundo plano)
    p_watch = subparsers.add_parser("_watch", help=argparse.SUPPRESS)
    p_watch.add_argument("notebook", help="ID del cuaderno")

    args = parser.parse_args()

    if not args.command:
        parser.print_help()
        sys.exit(0)

    if args.command == "setup":
        cmd_setup(args)
    elif args.command in ("usage", "quota"):
        cmd_usage(args)
    elif args.command in ("manual", "guide"):
        cmd_manual(args)
    elif args.command == "clean":
        cmd_clean(args)
    elif args.command == "rename":
        cmd_rename(args)
    elif args.command == "_watch":
        cmd_watch(args)
    elif args.command == "session":
        cmd_session(args)
    elif args.command == "schedule":
        cmd_schedule(args)
    elif args.command == "prompt":
        cmd_prompt(args)
    elif args.command == "cross":
        cmd_cross(args)
    elif args.command == "collections":
        cmd_collections(args)
    elif args.command == "list":
        cmd_list(args)


if __name__ == "__main__":
    try:
        main()
    except BrokenPipeError:
        try:
            sys.stderr.close()
        except Exception:
            pass
        sys.exit(0)
