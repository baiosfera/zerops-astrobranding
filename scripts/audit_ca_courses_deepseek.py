#!/usr/bin/env python3
"""
audit_ca_courses_deepseek.py — Clasificador y Auditor Epistemológico Piloto para CURSOS/CA vía DeepSeek.

Analiza semánticamente las unidades de curso dentro de /var/www/baiosfera/CURSOS/CA:
- Extrae estructura de lecciones y muestras de texto.
- Evalúa con DeepSeek Chat (API directa v3/flash).
- Detecta exclusiones (MLM, Autoayuda pura, CVs, Fuera de tema).
- Asigna o expande micro-clusters dinámicos de marketing/negocios.
- Computa tokens consumidos y costos reales.
"""

import os
import sys
import json
import time
import subprocess
import urllib.request
import urllib.error
from typing import Dict, List, Any, Optional

# Configuración y Credenciales
DEEPSEEK_API_KEY = os.environ.get("bifrost_DEEPSEEK_API_KEY", "")
DEEPSEEK_API_URL = "https://api.deepseek.com/chat/completions"
MODEL_NAME = "deepseek-chat"

RCLONE_BIN = "/var/www/.rclone/bin/rclone"
RCLONE_CONF = "/var/www/.rclone/config/rclone/rclone.conf"
BASE_REMOTE = "baiosfera:CURSOS/CA"
LOCAL_MOUNT = "/var/www/baiosfera/CURSOS/CA"

OUTPUT_JSON = "/var/www/localstorage/knowledge_cache/ca_pilot_audit.json"
OUTPUT_MD = "/var/www/artifacts/reports/ca_pilot_audit.md"

SYSTEM_PROMPT = """Eres el Auditor Epistemológico en Jefe y Arquitecto de Contenidos de Baiosfera.
Tu misión es clasificar y depurar unidades de cursos para construir compendios y playbooks de Marketing Digital, Ventas, Copywriting, Estrategia de Marca y Crecimiento de Negocios en Internet.

CRITERIOS INVIOLABLES DE EXCLUSIÓN (action = "DISCARD"):
1. MLM_NETWORK_MARKETING: Redes de mercadeo, multinivel, prospección para pirámides/redes, network marketing.
2. SELF_HELP_SPIRITUAL: Autoayuda genérica, mentalidad sin aplicación táctica a negocios, ley de atracción, espiritualidad, coaching místico.
3. EMPLOYABILITY_CV: Preparación de CV, entrevistas de trabajo para ser empleado, empleabilidad tradicional.
4. OUT_OF_SCOPE: Temas totalmente ajenos a marketing digital, comercio o negocios (ej. seducción, cocina, salud esotérica).

CRITERIOS DE RETENCIÓN (action = "KEEP"):
- Cursos aplicados de Marketing, Funnels, Tráfico/Pauta (Meta, Google, TikTok), SEO/AEO, Copywriting, VSLs, Creación de Ofertas, Pricing, Marca Personal orientada a Negocios, Landing Pages/WordPress, Automatizaciones, Chatbots/WhatsApp, y Estrategia de Crecimiento.
- Si el curso encaja en la taxonomía base (ej: funnels_cro, personal_branding_social, offers_pricing, seo_aeo, paid_ads_strategy, copywriting_persuasion, branding_authority, ai_marketing_automation, etc.), asigna ese cluster.
- TAXONOMÍA DINÁMICA: Si el curso trata un tema específico de alto valor que NO encaja limpiamente en los clusters convencionales o merece una rama propia (ejemplos: "chatbots_messaging_conversational", "vsl_scripting", "wordpress_landing_pages", "high_ticket_consulting"), PROPÓN EL NUEVO CLUSTER y marca "is_new_cluster": true.

DEBES RESPONDER EXCLUSIVAMENTE CON UN OBJETO JSON VÁLIDO CON ESTA ESTRUCTURA EXACTA:
{
  "action": "KEEP" | "DISCARD",
  "cluster": "nombre_del_cluster_en_snake_case",
  "is_new_cluster": false,
  "macro_collection": "NOMBRE_DE_COLECCION_SUGERIDA",
  "confidence": 0.95,
  "reason": "Explicación concisa y técnica del motivo de retención o descarte",
  "discard_category": null | "MLM_NETWORK_MARKETING" | "SELF_HELP_SPIRITUAL" | "EMPLOYABILITY_CV" | "OUT_OF_SCOPE",
  "target_audience": "Breve descripción del público objetivo",
  "key_topics": ["Tema 1", "Tema 2", "Tema 3"]
}"""

def get_ca_files() -> List[str]:
    """Obtiene la lista completa de archivos en baiosfera:CURSOS/CA vía rclone lsf."""
    cmd = [RCLONE_BIN, "--config", RCLONE_CONF, "lsf", BASE_REMOTE, "--recursive", "--files-only"]
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
    return [l.strip() for l in res.stdout.splitlines() if l.strip()]

def group_into_courses(files: List[str]) -> Dict[str, List[str]]:
    """Agrupa los archivos en unidades de curso según la jerarquía de carpetas."""
    courses: Dict[str, List[str]] = {}
    for f in files:
        parts = f.split('/')
        if len(parts) == 1:
            key = f"[ROOT]/{parts[0]}"
        elif len(parts) == 2:
            key = f"{parts[0]}/{parts[1]}"
        else:
            key = f"{parts[0]}/{parts[1]}"
        if key not in courses:
            courses[key] = []
        courses[key].append(f)
    return courses

def extract_course_context(course_key: str, files: List[str]) -> Dict[str, Any]:
    """Extrae estructura de lecciones y una muestra de texto representativa."""
    # Descartar archivos accesorios irrelevantes para la clasificación
    meaningful_files = [f for f in files if not f.endswith(('.jpg', '.jpeg', '.png', '.url', '.rar', '.zip'))]
    sample_files = [os.path.basename(f) for f in meaningful_files[:20]]
    
    # Intentar leer muestras de texto si hay archivos .txt, .docx, o .srt accesibles
    text_sample = ""
    for rel_f in files:
        ext = os.path.splitext(rel_f)[1].lower()
        if ext in ['.txt', '.docx', '.srt', '.md']:
            local_path = os.path.join(LOCAL_MOUNT, rel_f)
            if os.path.exists(local_path):
                try:
                    if ext in ['.txt', '.srt', '.md']:
                        with open(local_path, 'r', encoding='utf-8', errors='ignore') as fp:
                            content = fp.read(1500).strip()
                            if len(content) > 100:
                                text_sample = content[:1000]
                                break
                    elif ext == '.docx':
                        import docx
                        doc = docx.Document(local_path)
                        paras = [p.text for p in doc.paragraphs if p.text.strip()]
                        content = "\n".join(paras[:10])
                        if len(content) > 100:
                            text_sample = content[:1000]
                            break
                except Exception:
                    pass

    return {
        "course_key": course_key,
        "total_files": len(files),
        "sample_filenames": sample_files,
        "text_sample": text_sample
    }

def call_deepseek(prompt_payload: str) -> Dict[str, Any]:
    """Llama a DeepSeek API y devuelve la respuesta JSON y estadísticas de tokens."""
    req_data = json.dumps({
        "model": MODEL_NAME,
        "messages": [
            {"role": "system", "content": SYSTEM_PROMPT},
            {"role": "user", "content": prompt_payload}
        ],
        "response_format": {"type": "json_object"},
        "temperature": 0.1,
        "max_tokens": 500
    }).encode("utf-8")

    req = urllib.request.Request(
        DEEPSEEK_API_URL,
        data=req_data,
        headers={
            "Authorization": f"Bearer {DEEPSEEK_API_KEY}",
            "Content-Type": "application/json"
        }
    )

    t0 = time.time()
    for attempt in range(3):
        try:
            with urllib.request.urlopen(req, timeout=30) as resp:
                data = json.loads(resp.read().decode("utf-8"))
                elapsed = time.time() - t0
                content_str = data["choices"][0]["message"]["content"]
                parsed = json.loads(content_str)
                usage = data.get("usage", {})
                return {
                    "success": True,
                    "data": parsed,
                    "usage": usage,
                    "latency_sec": round(elapsed, 2)
                }
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8", errors="ignore")
            if e.code == 429:
                time.sleep(2 * (attempt + 1))
                continue
            return {"success": False, "error": f"HTTP {e.code}: {err_body}"}
        except Exception as e:
            time.sleep(1)
            if attempt == 2:
                return {"success": False, "error": str(e)}

    return {"success": False, "error": "Max retries exceeded"}

def main():
    if not DEEPSEEK_API_KEY:
        print("ERROR: bifrost_DEEPSEEK_API_KEY no encontrada en el entorno.")
        sys.exit(1)

    print("==================================================================")
    print("🚀 INICIANDO AUDITORÍA PILOTO DE CURSOS/CA CON DEEPSEEK")
    print("==================================================================")

    # 1. Obtener archivos
    print("• Listando archivos en baiosfera:CURSOS/CA...")
    files = get_ca_files()
    courses = group_into_courses(files)
    print(f"  -> {len(files)} archivos totales agrupados en {len(courses)} unidades.")

    # Filtrar unidades que son puramente archivos sueltos irrelevantes (ej. txt-mega.zip o cupones)
    active_courses = {k: v for k, v in courses.items() if not k.endswith(('.zip', '.txt')) or len(v) > 2}
    print(f"  -> {len(active_courses)} unidades de curso activas para clasificar.")

    total_prompt_tokens = 0
    total_completion_tokens = 0
    audit_results: List[Dict[str, Any]] = []

    print("\n• Ejecutando clasificación semántica con DeepSeek...")
    for idx, (course_key, c_files) in enumerate(sorted(active_courses.items()), 1):
        ctx = extract_course_context(course_key, c_files)
        
        user_prompt = f"""CURSO A AUDITAR ({idx}/{len(active_courses)}):
Identificador / Carpeta: {course_key}
Total Archivos: {ctx['total_files']}
Muestra de Lecciones / Módulos:
{json.dumps(ctx['sample_filenames'], ensure_ascii=False, indent=2)}

Muestra de Contenido de Texto (primeros 1000 caracteres):
\"\"\"{ctx['text_sample'] if ctx['text_sample'] else 'No disponible - inferir por estructura de módulos y título'}\"\"\"

Clasifica según las reglas de exclusión y retención en formato JSON."""

        res = call_deepseek(user_prompt)
        if res.get("success"):
            data = res["data"]
            usage = res["usage"]
            p_tok = usage.get("prompt_tokens", 0)
            c_tok = usage.get("completion_tokens", 0)
            total_prompt_tokens += p_tok
            total_completion_tokens += c_tok

            action = data.get("action", "UNKNOWN")
            cluster = data.get("cluster", "unclassified")
            is_new = data.get("is_new_cluster", False)
            reason = data.get("reason", "")

            icon = "✅" if action == "KEEP" else "❌"
            new_tag = " [NUEVA RAMA]" if is_new else ""
            print(f"[{idx:02d}/{len(active_courses):02d}] {icon} {action} | {course_key} -> {cluster}{new_tag} ({res['latency_sec']}s)")

            audit_results.append({
                "course_key": course_key,
                "total_files": ctx["total_files"],
                "classification": data,
                "tokens": {"prompt": p_tok, "completion": c_tok},
                "latency_sec": res["latency_sec"]
            })
        else:
            print(f"[{idx:02d}/{len(active_courses):02d}] ⚠️ ERROR: {course_key} -> {res.get('error')}")
            audit_results.append({
                "course_key": course_key,
                "error": res.get("error")
            })

    # Cálculo de Costos
    # DeepSeek precios: Input $0.27 / 1M tokens (cache miss) / $0.14 (cache hit); Output $0.28 / 1M tokens
    cost_input = (total_prompt_tokens / 1_000_000) * 0.27
    cost_output = (total_completion_tokens / 1_000_000) * 0.28
    total_cost_usd = cost_input + cost_output

    summary = {
        "timestamp": time.strftime("%Y-%m-%dT%H:%M:%SZ", time.gmtime()),
        "total_courses_audited": len(audit_results),
        "kept_count": sum(1 for r in audit_results if r.get("classification", {}).get("action") == "KEEP"),
        "discarded_count": sum(1 for r in audit_results if r.get("classification", {}).get("action") == "DISCARD"),
        "new_clusters_proposed": [
            r["classification"]["cluster"] for r in audit_results 
            if r.get("classification", {}).get("is_new_cluster") and r.get("classification", {}).get("action") == "KEEP"
        ],
        "total_tokens": {
            "prompt_tokens": total_prompt_tokens,
            "completion_tokens": total_completion_tokens,
            "total_tokens": total_prompt_tokens + total_completion_tokens
        },
        "estimated_cost_usd": round(total_cost_usd, 5),
        "results": audit_results
    }

    # Guardar JSON en localstorage
    os.makedirs(os.path.dirname(OUTPUT_JSON), exist_ok=True)
    with open(OUTPUT_JSON, "w", encoding="utf-8") as fp:
        json.dump(summary, fp, indent=2, ensure_ascii=False)
    print(f"\n💾 Manifiesto guardado en: {OUTPUT_JSON}")

    # Guardar Reporte Markdown
    os.makedirs(os.path.dirname(OUTPUT_MD), exist_ok=True)
    with open(OUTPUT_MD, "w", encoding="utf-8") as fp:
        fp.write("# Reporte de Auditoría Semántica Piloto: CURSOS/CA con DeepSeek\n\n")
        fp.write(f"- **Fecha**: {summary['timestamp']}\n")
        fp.write(f"- **Cursos Auditados**: {summary['total_courses_audited']}\n")
        fp.write(f"- **Retenidos (KEEP)**: {summary['kept_count']}\n")
        fp.write(f"- **Descartados (DISCARD)**: {summary['discarded_count']}\n")
        fp.write(f"- **Tokens Consumidos**: {summary['total_tokens']['total_tokens']} (Prompt: {total_prompt_tokens}, Completion: {total_completion_tokens})\n")
        fp.write(f"- **Costo Estimado**: ${summary['estimated_cost_usd']} USD\n\n")
        
        fp.write("## 🚫 Cursos Descartados (Exclusiones Descubiertas)\n\n")
        fp.write("| Curso / Carpeta | Categoría de Descarte | Motivo Semántico |\n")
        fp.write("|---|---|---|\n")
        for r in audit_results:
            c = r.get("classification", {})
            if c.get("action") == "DISCARD":
                fp.write(f"| `{r['course_key']}` | `{c.get('discard_category')}` | {c.get('reason')} |\n")

        fp.write("\n## ✅ Cursos Retenidos y Clasificación Temática\n\n")
        fp.write("| Curso / Carpeta | Cluster Asignado | ¿Nueva Rama? | Confianza | Motivo Semántico |\n")
        fp.write("|---|---|---|---|---|\n")
        for r in audit_results:
            c = r.get("classification", {})
            if c.get("action") == "KEEP":
                new_flag = "🌟 SÍ" if c.get("is_new_cluster") else "NO"
                fp.write(f"| `{r['course_key']}` | `{c.get('cluster')}` | {new_flag} | {c.get('confidence')} | {c.get('reason')} |\n")

    print(f"📄 Reporte Markdown guardado en: {OUTPUT_MD}")
    print(f"\n📊 RESUMEN FINAL:")
    print(f"• Cursos Retenidos: {summary['kept_count']}")
    print(f"• Cursos Descartados: {summary['discarded_count']}")
    print(f"• Nuevas Ramas Propuestas: {set(summary['new_clusters_proposed'])}")
    print(f"• Tokens Totales: {summary['total_tokens']['total_tokens']}")
    print(f"• Costo Total: ${summary['estimated_cost_usd']} USD")

if __name__ == "__main__":
    main()
