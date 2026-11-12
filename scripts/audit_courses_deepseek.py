#!/usr/bin/env python3
"""
audit_courses_deepseek.py — Clasificador y Auditor Epistemológico Universal vía DeepSeek.

Analiza semánticamente unidades de curso en /var/www/baiosfera (CURSOS, PLATZI, DIGITALMARKETER):
- Extrae estructura didáctica y muestras de contenido.
- Clasifica con DeepSeek Chat (v3/flash) bajo la Directiva de Abstracción Soberana Zerops.
- Aplica Criterios de Exclusión (MLM, Autoayuda pura, Empleabilidad tradicional, Gambling/Fuera de foco).
- Mapea a Taxonomía de Macro-Colecciones evitando cuadernos anémicos.
- Poda mentalidad 'click-ops' de SaaS propietarios (WordPress, Shopify, n8n, ManyChat).
"""

import os
import sys
import json
import time
import argparse
import subprocess
import urllib.request
import urllib.error
from typing import Dict, List, Any

DEEPSEEK_API_KEY = os.environ.get("bifrost_DEEPSEEK_API_KEY", "")
DEEPSEEK_API_URL = "https://api.deepseek.com/chat/completions"
MODEL_NAME = "deepseek-chat"

RCLONE_BIN = "/var/www/.rclone/bin/rclone"
RCLONE_CONF = "/var/www/.rclone/config/rclone/rclone.conf"
BASE_STORAGE = "/var/www/localstorage/knowledge_cache"

SYSTEM_PROMPT = """Eres el Auditor Epistemológico en Jefe y Arquitecto de Contenidos de Baiosfera.
Tu misión es clasificar y depurar cursos para construir compendios y playbooks de Marketing Digital, Ventas, Copywriting y Estrategia de Crecimiento para el stack soberano de Zerops (Astro 5 SSR, Bun, Directus 11+, PostgreSQL 18, NATS JetStream, BullMQ/Valkey, Evolution Go WhatsApp, Bifrost y CrewAI).

CRITERIOS INVIOLABLES DE EXCLUSIÓN (action = "DISCARD"):
1. MLM_NETWORK_MARKETING: Redes de mercadeo, multinivel, prospección piramidal, network marketing.
2. SELF_HELP_SPIRITUAL: Autoayuda genérica, ley de atracción, coaching místico, mentalidad sin aplicación táctica a negocios.
3. EMPLOYABILITY_CV: Preparación de currículum, entrevistas laborales tradicionales para ser empleado (cursos de empleabilidad Platzi).
4. OUT_OF_SCOPE: Temas ajenos a negocios o marketing (apuestas, arbitraje deportivo, seducción, cocina, etc.).

DIRECTIVA DE ABSTRACCIÓN SOBERANA ZEROPS (ZERO CLICK-OPS):
- Baiosfera NO utiliza WordPress, WooCommerce, Shopify, n8n, Zapier ni interfaces web de ChatGPT/Claude.
- Si un curso enseña landing pages usando WordPress/Elementor, clasifícalo bajo "landing_pages_cro" (analizando su estructura de persuasión, Above-The-Fold y copy para implementarlo en astro-web).
- Si un curso enseña automatización en n8n/Zapier, clasifícalo en "automations_workflows" o "ai_marketing_automation" abstrayendo la lógica de triggers y eventos para NATS/BullMQ.
- Si un curso enseña flotas de vendedores externos, revendedores o embajadores (ej. Yugula PRO), clasifícalo bajo "affiliates_ambassadors_sales_force".

POLÍTICA ANTI-CUADERNOS ANÉMICOS:
- Prioriza mapear a las colecciones macro y micro-clusters existentes:
  * 00_category_of_one (SOLO Velocity Media - no asignar a externos)
  * 01_velocity_sales_doctrine (SOLO Velocity Media - no asignar a externos)
  * branding_authority
  * personal_branding_social
  * copywriting_persuasion
  * vsl_scripting
  * funnels_cro
  * landing_pages_cro
  * offers_pricing
  * paid_ads_strategy (meta, google, tiktok)
  * seo_aeo
  * social_content_distribution
  * email_retention
  * chatbots_messaging_conversational
  * data_analytics
  * automations_workflows
  * ai_marketing_automation
  * affiliates_ambassadors_sales_force
  * sales_closing
  * ecommerce_scaling
- Si descubres un área de negocio de alto valor que NO encaja en lo anterior, proponla marcando "is_new_cluster": true.

RESPONDE EXCLUSIVAMENTE CON ESTE JSON:
{
  "action": "KEEP" | "DISCARD",
  "cluster": "nombre_del_cluster_en_snake_case",
  "is_new_cluster": false,
  "macro_collection": "NOMBRE_DE_COLECCION",
  "confidence": 0.95,
  "reason": "Explicación concisa y técnica del motivo de retención o descarte",
  "discard_category": null | "MLM_NETWORK_MARKETING" | "SELF_HELP_SPIRITUAL" | "EMPLOYABILITY_CV" | "OUT_OF_SCOPE",
  "target_audience": "Público objetivo",
  "key_topics": ["Tema 1", "Tema 2"]
}"""

def get_remote_files(remote_path: str) -> List[str]:
    cmd = [RCLONE_BIN, "--config", RCLONE_CONF, "lsf", f"baiosfera:{remote_path}", "--recursive", "--files-only"]
    res = subprocess.run(cmd, stdout=subprocess.PIPE, stderr=subprocess.PIPE, text=True, check=True)
    return [l.strip() for l in res.stdout.splitlines() if l.strip()]

def group_courses(files: List[str], prefix: str) -> Dict[str, List[str]]:
    courses: Dict[str, List[str]] = {}
    for f in files:
        parts = f.split('/')
        if len(parts) == 1:
            key = f"{prefix}/{parts[0]}"
        else:
            key = f"{prefix}/{parts[0]}/{parts[1]}"
        if key not in courses:
            courses[key] = []
        courses[key].append(f)
    return courses

def call_deepseek(prompt_payload: str) -> Dict[str, Any]:
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
                return {
                    "success": True,
                    "data": parsed,
                    "usage": data.get("usage", {}),
                    "latency_sec": round(elapsed, 2)
                }
        except Exception as e:
            time.sleep(1.5 * (attempt + 1))
            if attempt == 2:
                return {"success": False, "error": str(e)}
    return {"success": False, "error": "Max retries exceeded"}

def main():
    parser = argparse.ArgumentParser(description="Auditor Epistemológico DeepSeek Universal")
    parser.add_argument("--source", type=str, default="CURSOS/CA", help="Subruta en baiosfera (ej: CURSOS/CA, CURSOS/MCV, PLATZI, DIGITALMARKETER)")
    args = parser.parse_args()

    if not DEEPSEEK_API_KEY:
        print("ERROR: bifrost_DEEPSEEK_API_KEY no presente en entorno.")
        sys.exit(1)

    print(f"🚀 INICIANDO AUDITORÍA DE: baiosfera:{args.source}")
    files = get_remote_files(args.source)
    courses = group_courses(files, args.source)
    print(f"• Archivos: {len(files)} | Unidades de curso detectadas: {len(courses)}")

    active_courses = {k: v for k, v in courses.items() if not k.endswith(('.zip', '.txt')) or len(v) > 2}
    print(f"• Unidades activas a auditar: {len(active_courses)}")

    out_slug = args.source.replace('/', '_').lower()
    out_json = f"{BASE_STORAGE}/audit_{out_slug}.json"
    out_md = f"/var/www/artifacts/reports/audit_{out_slug}.md"

    results = []
    tot_p_tok, tot_c_tok = 0, 0

    for idx, (c_key, c_files) in enumerate(sorted(active_courses.items()), 1):
        sample_files = [os.path.basename(f) for f in c_files if not f.endswith(('.jpg', '.png', '.rar', '.zip'))][:15]
        prompt = f"""CURSO ({idx}/{len(active_courses)}):
Ruta/Identificador: {c_key}
Archivos ({len(c_files)}):
{json.dumps(sample_files, ensure_ascii=False, indent=2)}

Clasifica según las reglas de Abstracción Soberana Zerops y exclusiones en JSON."""

        res = call_deepseek(prompt)
        if res.get("success"):
            data = res["data"]
            u = res.get("usage", {})
            tot_p_tok += u.get("prompt_tokens", 0)
            tot_c_tok += u.get("completion_tokens", 0)
            action = data.get("action", "UNKNOWN")
            cluster = data.get("cluster", "unclassified")
            icon = "✅" if action == "KEEP" else "❌"
            print(f"[{idx:02d}/{len(active_courses):02d}] {icon} {action} | {c_key} -> {cluster} ({res['latency_sec']}s)")
            results.append({"course_key": c_key, "files_count": len(c_files), "classification": data})
        else:
            print(f"[{idx:02d}/{len(active_courses):02d}] ⚠️ ERROR en {c_key}: {res.get('error')}")

    cost_usd = ((tot_p_tok / 1e6) * 0.27) + ((tot_c_tok / 1e6) * 0.28)
    summary = {
        "source": args.source,
        "total_courses": len(results),
        "kept": sum(1 for r in results if r.get("classification", {}).get("action") == "KEEP"),
        "discarded": sum(1 for r in results if r.get("classification", {}).get("action") == "DISCARD"),
        "tokens": {"prompt": tot_p_tok, "completion": tot_c_tok, "total": tot_p_tok + tot_c_tok},
        "cost_usd": round(cost_usd, 5),
        "results": results
    }

    os.makedirs(os.path.dirname(out_json), exist_ok=True)
    with open(out_json, "w", encoding="utf-8") as fp:
        json.dump(summary, fp, indent=2, ensure_ascii=False)

    os.makedirs(os.path.dirname(out_md), exist_ok=True)
    with open(out_md, "w", encoding="utf-8") as fp:
        fp.write(f"# Auditoría Semántica: {args.source}\n\n")
        fp.write(f"- Cursos: {summary['total_courses']} | Retenidos: {summary['kept']} | Descartados: {summary['discarded']}\n")
        fp.write(f"- Tokens: {summary['tokens']['total']} | Costo: ${summary['cost_usd']} USD\n\n")
        fp.write("## Clasificación de Cursos\n\n| Curso | Acción | Cluster | Motivo |\n|---|---|---|---|\n")
        for r in results:
            c = r.get("classification", {})
            fp.write(f"| `{r['course_key']}` | `{c.get('action')}` | `{c.get('cluster')}` | {c.get('reason')} |\n")

    print(f"\n💾 Guardado: {out_json} y {out_md}")
    print(f"📊 Retenidos: {summary['kept']} | Descartados: {summary['discarded']} | Costo: ${summary['cost_usd']} USD")

if __name__ == "__main__":
    main()
