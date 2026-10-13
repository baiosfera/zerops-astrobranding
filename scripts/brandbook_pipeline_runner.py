#!/usr/bin/env python3
"""
brandbook_pipeline_runner.py — High-Performance Brandbook Fast-Track & Studio Pipeline.
Dual-Track Architecture | W3C DTCG 2025.10 Tokens | Tailwind v4 @theme | Bifrost Gateway.

Orchestrates:
1. Ingestion of Silver Shards (client_dumps_15_shards.json, ~22 KB) + Gold Feeds (never 50 MB raw cache).
2. LLM Reasoning via Bifrost Gateway (http://bifrost:8080) with x-tier: production and json_object.
3. Dual-track generation:
   - brandbook_superfull_[MARCA].json (SSoT W3C DTCG tokens, brand architecture, voice/tone)
   - brandbook-theme.css (Tailwind v4 @theme block + :root CSS variables)
   - system_prompt.md (Conversational projection for WhatsAppBot / Agents)
4. SSoT synchronization: localstorage/[MARCA]/dev/ and baiosfera/PROYECTOS/[MARCA]/dev/
"""

from __future__ import annotations

import argparse
from datetime import datetime, timezone
import json
import logging
import os
from pathlib import Path
import re
import sys
import urllib.error
import urllib.request
from typing import Any, Dict, List, Optional, Tuple

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(levelname)s] %(name)s: %(message)s")
logger = logging.getLogger("brandbook.pipeline_runner")


def sanitize_brand(brand_raw: str) -> Tuple[str, str]:
    """Returns (canonical_upper, canonical_lower) slug for a brand."""
    cleaned = re.sub(r"[^a-zA-Z0-9]+", "", brand_raw).strip()
    if not cleaned:
        cleaned = "MARCA"
    return cleaned.upper(), cleaned.lower()


class IngestionEngine:
    """Discovers and digests astrological Silver shards and Gold feeds within strict token budgets."""

    def __init__(self, brand_upper: str, diag_root: Optional[Path] = None):
        self.brand_upper = brand_upper
        self.diag_root = diag_root or Path("/var/www/baiosfera/ASTROLOGÍA/DIAG") / brand_upper

    def load_context(self, enhance_baseline: Optional[Dict[str, Any]] = None) -> Dict[str, Any]:
        """Loads Silver shards and Gold feeds. Rejects raw cache traversal."""
        context: Dict[str, Any] = {
            "brand": self.brand_upper,
            "silver_shards": {},
            "gold_feeds": {},
            "astrobranding_brief": "",
            "author_psychology": "",
            "baseline": enhance_baseline or {},
        }

        if not self.diag_root.exists():
            logger.warning(f"Astrological directory not found for {self.brand_upper} at {self.diag_root}. Running in brand-only mode.")
            return context

        # 1. Silver Shards (Priority 1: client_dumps_15_shards.json)
        dumps_dir = self.diag_root / "raw" / "json" / "dumps"
        silver_file = dumps_dir / "client_dumps_15_shards.json"
        if silver_file.exists():
            try:
                with open(silver_file, "r", encoding="utf-8") as f:
                    context["silver_shards"] = json.load(f)
                logger.info(f"Loaded 15 Silver relational shards from {silver_file} ({silver_file.stat().st_size} bytes)")
            except Exception as e:
                logger.warning(f"Failed to read silver shards: {e}")

        # Fallback to individual shards if consolidated file is missing
        if not context["silver_shards"] and dumps_dir.exists():
            individual_shards: Dict[str, Any] = {}
            for i in range(1, 13):
                s_path = dumps_dir / f"shard_{i:02d}.json"
                if s_path.exists():
                    try:
                        with open(s_path, "r", encoding="utf-8") as f:
                            individual_shards[f"shard_{i:02d}"] = json.load(f)
                    except Exception:
                        pass
            if individual_shards:
                context["silver_shards"] = individual_shards
                logger.info(f"Loaded {len(individual_shards)} individual Bronze/Silver shards from {dumps_dir}")

        # 2. Gold Feeds (raw/feeds/*.md)
        feeds_dir = self.diag_root / "raw" / "feeds"
        if feeds_dir.exists():
            for f_path in feeds_dir.glob("*.md"):
                try:
                    context["gold_feeds"][f_path.stem] = f_path.read_text(encoding="utf-8")
                except Exception:
                    pass

        # 3. LLM Deliverables (raw/llm/*.md)
        llm_dir = self.diag_root / "raw" / "llm"
        if llm_dir.exists():
            for f_path in llm_dir.glob("*.md"):
                f_name = f_path.name.lower()
                if "astrobranding" in f_name:
                    context["astrobranding_brief"] = f_path.read_text(encoding="utf-8")
                elif "author_psychology" in f_name:
                    context["author_psychology"] = f_path.read_text(encoding="utf-8")

        return context


class BifrostGatewayClient:
    """Communicates with Bifrost AI Gateway enforcing production headers and structured JSON."""

    def __init__(self, base_url: str = "http://bifrost:8080", primary_model: str = "deepseek/deepseek-chat",
                 fallback_model: str = "freellmapi/deepseek-v4-flash", timeout_sec: int = 180):
        self.base_url = base_url.rstrip("/")
        self.primary_model = primary_model
        self.fallback_model = fallback_model
        self.timeout_sec = timeout_sec

    def call_chat_completion(self, messages: List[Dict[str, str]], temperature: float = 0.2) -> Dict[str, Any]:
        """Calls /v1/chat/completions with automatic fallback."""
        models_to_try = [self.primary_model]
        if self.fallback_model and self.fallback_model != self.primary_model:
            models_to_try.append(self.fallback_model)

        last_error = None
        for model in models_to_try:
            try:
                logger.info(f"Invoking Bifrost Gateway with model: {model} (x-tier: production, json_object)")
                res = self._send_request(model, messages, temperature)
                return res
            except Exception as e:
                logger.warning(f"Call with model {model} failed: {e}. Trying next fallback...")
                last_error = e

        raise RuntimeError(f"All Bifrost models failed. Last error: {last_error}")

    def _send_request(self, model: str, messages: List[Dict[str, str]], temperature: float) -> Dict[str, Any]:
        url = f"{self.base_url}/v1/chat/completions"
        payload = {
            "model": model,
            "messages": messages,
            "temperature": temperature,
            "response_format": {"type": "json_object"},
            "max_tokens": 8192,
        }
        data = json.dumps(payload).encode("utf-8")
        req = urllib.request.Request(url, data=data, method="POST")
        req.add_header("Content-Type", "application/json")
        req.add_header("x-tier", "production")
        req.add_header("x-routing-tier", "production")

        try:
            with urllib.request.urlopen(req, timeout=self.timeout_sec) as resp:
                body = resp.read().decode("utf-8")
                result = json.loads(body)
        except urllib.error.HTTPError as e:
            err_body = e.read().decode("utf-8") if e.fp else ""
            raise RuntimeError(f"HTTP {e.code}: {e.reason} - {err_body}") from e

        choices = result.get("choices", [])
        if not choices:
            raise ValueError(f"Empty choices in Bifrost response: {result}")

        content_raw = choices[0].get("message", {}).get("content", "")
        if not content_raw:
            raise ValueError(f"Empty content in message: {choices[0]}")

        # Clean markdown wrappers if present (e.g. ```json ... ```)
        cleaned_json = content_raw.strip()
        if cleaned_json.startswith("```"):
            cleaned_json = re.sub(r"^```[a-zA-Z]*\n?", "", cleaned_json)
            cleaned_json = re.sub(r"\n?```$", "", cleaned_json).strip()

        try:
            return json.loads(cleaned_json)
        except json.JSONDecodeError as err:
            logger.warning(f"Initial JSON decode failed ({err}). Attempting truncation repair...")
            repaired = self._repair_json_truncation(cleaned_json)
            if repaired is not None:
                logger.info("Successfully repaired truncated JSON!")
                return repaired
            raise

    @staticmethod
    def _repair_json_truncation(raw_str: str) -> Optional[Dict[str, Any]]:
        """Repairs incomplete JSON strings caused by token limit cutoffs."""
        s = raw_str.strip()
        for _ in range(50):
            quotes = re.findall(r'(?<!\\)"', s)
            test_s = s
            if len(quotes) % 2 != 0:
                test_s = s + '"'

            open_braces = test_s.count("{") - test_s.count("}")
            open_brackets = test_s.count("[") - test_s.count("]")

            closed_s = test_s + ("]" * max(0, open_brackets)) + ("}" * max(0, open_braces))
            try:
                return json.loads(closed_s)
            except Exception:
                last_comma = max(s.rfind(","), s.rfind("\n"))
                if last_comma > 0:
                    s = s[:last_comma].rstrip(", \t\n")
                else:
                    break
        return None


class BrandbookPipelineRunner:
    """Coordinates digestion, synthesis, CSS extraction, and SSoT disk distribution."""

    def __init__(self, brand_raw: str, mode: str = "fast-track", enhance: bool = False,
                 bifrost_url: str = "http://bifrost:8080", model: str = "deepseek/deepseek-chat",
                 output_dir: Optional[str] = None):
        self.brand_upper, self.brand_lower = sanitize_brand(brand_raw)
        self.mode = mode
        self.enhance = enhance
        self.bifrost_url = bifrost_url
        self.model = model
        self.custom_output_dir = Path(output_dir) if output_dir else None

        # SSoT target directories
        self.localstorage_dev = Path("/var/www/localstorage") / self.brand_upper / "dev"
        self.drive_dev = Path("/var/www/baiosfera/PROYECTOS") / self.brand_upper / "dev"

    def run(self, dry_run: bool = False) -> int:
        """Executes the pipeline end-to-end."""
        logger.info(f"=== Starting Brandbook Pipeline Runner for '{self.brand_upper}' [mode: {self.mode}] ===")

        # 1. Load Baseline if --enhance
        baseline_data = None
        if self.enhance:
            baseline_data = self._find_existing_brandbook()
            if baseline_data:
                logger.info(f"Enhance mode active: loaded existing brandbook baseline with {len(baseline_data.keys())} sections")

        # 2. Ingestion
        ingestor = IngestionEngine(self.brand_upper)
        context = ingestor.load_context(enhance_baseline=baseline_data)

        if dry_run:
            logger.info("Dry-run requested: summary of ingested context:")
            logger.info(f"  • Silver shards keys: {list(context['silver_shards'].keys())}")
            logger.info(f"  • Gold feeds count: {len(context['gold_feeds'])}")
            logger.info(f"  • Astrobranding brief present: {bool(context['astrobranding_brief'])}")
            return 0

        # 3. Build Bifrost Prompt
        messages = self._build_prompt_messages(context)

        # 4. Invoke LLM via Bifrost
        client = BifrostGatewayClient(base_url=self.bifrost_url, primary_model=self.model)
        generated_brandbook = client.call_chat_completion(messages)

        # 5. Enrich & Normalize W3C DTCG Format
        final_brandbook = self._normalize_brandbook_dtcg(generated_brandbook)

        # 6. Derive Tailwind v4 Theme CSS & System Prompt
        theme_css = self._derive_tailwind_theme_css(final_brandbook)
        system_prompt_md = self._derive_system_prompt_md(final_brandbook)

        # 7. Write to LocalStorage Dev (Primary Runtime SSoT)
        out_dir = self.custom_output_dir or self.localstorage_dev
        out_dir.mkdir(parents=True, exist_ok=True)

        f_superfull = out_dir / f"brandbook_superfull_{self.brand_lower}.json"
        f_brandbook = out_dir / "brandbook.json"
        f_theme_css = out_dir / "brandbook-theme.css"
        f_prompt_md = out_dir / "system_prompt.md"

        f_superfull.write_text(json.dumps(final_brandbook, indent=2, ensure_ascii=False), encoding="utf-8")
        f_brandbook.write_text(json.dumps(final_brandbook, indent=2, ensure_ascii=False), encoding="utf-8")
        f_theme_css.write_text(theme_css, encoding="utf-8")
        f_prompt_md.write_text(system_prompt_md, encoding="utf-8")

        logger.info(f"Emitted artifacts to runtime directory: {out_dir}")
        logger.info(f"  • {f_superfull.name} ({f_superfull.stat().st_size} bytes)")
        logger.info(f"  • {f_brandbook.name} ({f_brandbook.stat().st_size} bytes)")
        logger.info(f"  • {f_theme_css.name} ({f_theme_css.stat().st_size} bytes)")
        logger.info(f"  • {f_prompt_md.name} ({f_prompt_md.stat().st_size} bytes)")

        # 8. Mirror to Google Drive SSoT if available
        if self.drive_dev.parent.exists():
            try:
                self.drive_dev.mkdir(parents=True, exist_ok=True)
                (self.drive_dev / f"brandbook_superfull_{self.brand_lower}.json").write_text(
                    json.dumps(final_brandbook, indent=2, ensure_ascii=False), encoding="utf-8"
                )
                (self.drive_dev / "brandbook.json").write_text(
                    json.dumps(final_brandbook, indent=2, ensure_ascii=False), encoding="utf-8"
                )
                (self.drive_dev / "brandbook-theme.css").write_text(theme_css, encoding="utf-8")
                (self.drive_dev / "system_prompt.md").write_text(system_prompt_md, encoding="utf-8")
                logger.info(f"Mirrored SSoT files successfully to Drive: {self.drive_dev}")
            except Exception as e:
                logger.warning(f"Could not mirror to Drive SSoT (non-fatal): {e}")

        # 9. Physical Sensors Validation (Exit Code 0 Verification)
        self._verify_artifacts(out_dir)

        print("=" * 70)
        print(f"✅ BRANDBOOK DUAL-TRACK PIPELINE COMPLETADO EXITOSAMENTE PARA: {self.brand_upper}")
        print(f"  • Archivo Maestro JSON: {f_superfull}")
        print(f"  • Estilos Tailwind v4 CSS: {f_theme_css}")
        print(f"  • Proyección System Prompt: {f_prompt_md}")
        print("=" * 70)
        return 0

    def _find_existing_brandbook(self) -> Optional[Dict[str, Any]]:
        """Searches for existing brandbook files across standard candidate paths."""
        candidates = [
            self.localstorage_dev / f"brandbook_superfull_{self.brand_lower}.json",
            self.localstorage_dev / f"brandbook-{self.brand_lower}-potenciado.json",
            self.localstorage_dev / "brandbook.json",
            self.drive_dev / f"brandbook_superfull_{self.brand_lower}.json",
            self.drive_dev / f"brandbook-{self.brand_lower}-potenciado.json",
            self.drive_dev / "brandbook.json",
        ]
        for c in candidates:
            if c.exists():
                try:
                    with open(c, "r", encoding="utf-8") as f:
                        return json.load(f)
                except Exception:
                    pass
        return None

    def _build_prompt_messages(self, context: Dict[str, Any]) -> List[Dict[str, str]]:
        system_prompt = (
            "You are an Elite Brand Architect, Creative Director, and Design Systems Engineer.\n"
            "Your mission is to generate a comprehensive, authoritative Brandbook JSON complying with the "
            "W3C Design Tokens Community Group (DTCG) specification (2025.10).\n"
            "CRITICAL INVARIANTS:\n"
            "1. Output MUST be valid, parseable JSON only. Do not include markdown preamble or conversational prose.\n"
            "2. Be concise, punchy, and architectural. Use high-density statements and clear bullet items. Do NOT write verbose essays or rambling filler.\n"
            "3. Design Tokens MUST use strictly formatted W3C DTCG nodes: every token must have '$type', '$value', "
            "and optional '$description'. Extra metadata like HEX must reside in '$extensions.hex', NEVER at token root.\n"
            "4. Colors MUST be specified primarily in OKLCH (e.g. 'oklch(0.62 0.22 35)'), with hex values in '$extensions.hex'.\n"
            "5. Include complete Brand Architecture, Ethical Pillars, Design System (color, typography, motion), "
            "Voice & Tone, Target Audience, and LLM System Prompt Engine.\n"
            "6. Ground the colors, fonts, voice, and positioning directly in the astrological shards (Air dominant, Gemini Sun/MC, Libra Moon, Yang Wood, etc.)."
        )

        # Build compact user payload from silver shards & briefs
        shards_summary: Dict[str, Any] = {}
        if context["silver_shards"]:
            # Extract key components to remain well within context budget (< 8k tokens)
            s = context["silver_shards"]
            shards_summary = {
                "western_tripod": s.get("shard_01", {}).get("data", {}).get("tripod_of_iron", {}),
                "arroyo_elements": s.get("shard_01", {}).get("data", {}).get("arroyo_elements", {}),
                "client_triad": s.get("shard_01", {}).get("data", {}).get("client_triad", {}),
                "bazi_day_master": s.get("shard_04", {}).get("data", {}).get("day_master", {}),
                "yong_shen": s.get("shard_04", {}).get("data", {}).get("yong_shen", {}),
                "human_design": s.get("shard_05", {}).get("data", {}),
                "wealth_houses": s.get("shard_07", {}).get("data", {}),
                "numerology": s.get("shard_09", {}).get("data", {}).get("core_numerology", {}),
            }

        user_content = {
            "brand_name": self.brand_upper,
            "mode": self.mode,
            "astrological_shards_summary": shards_summary,
            "astrobranding_brief_snippet": context["astrobranding_brief"][:3000] if context["astrobranding_brief"] else "",
            "author_psychology_snippet": context["author_psychology"][:2000] if context["author_psychology"] else "",
            "baseline_to_enhance": context["baseline"] if self.enhance else None,
            "required_sections": [
                "$schema", "metadata", "brand_architecture", "ethical_pillars_and_anti_bias",
                "design_system", "voice_tone_and_messaging", "target_audience", "llm_system_prompt_engine"
            ]
        }

        return [
            {"role": "system", "content": system_prompt},
            {"role": "user", "content": f"Generate the comprehensive Brandbook JSON for brand '{self.brand_upper}':\n{json.dumps(user_content, indent=2, ensure_ascii=False)}"}
        ]

    def _normalize_brandbook_dtcg(self, raw_data: Dict[str, Any]) -> Dict[str, Any]:
        """Ensures top-level schema conformance, timestamp injection, and DTCG structural integrity."""
        raw_data["$schema"] = "https://design-tokens.github.io/community-group/format/"
        if "metadata" not in raw_data:
            raw_data["metadata"] = {}

        raw_data["metadata"]["title"] = f"Brandbook Superfull — {self.brand_upper}"
        raw_data["metadata"]["brand_name"] = self.brand_upper
        raw_data["metadata"]["version"] = raw_data["metadata"].get("version", "1.0.0")
        raw_data["metadata"]["generated_at"] = datetime.now(timezone.utc).isoformat()
        raw_data["metadata"]["generator"] = f"brandbook_pipeline_runner ({self.mode})"

        # Ensure design_system exists with minimum required color tokens
        ds = raw_data.setdefault("design_system", {})
        color = ds.setdefault("color", {})
        brand_colors = color.setdefault("brand", {})

        # Default fallback palette if missing
        if "primary" not in brand_colors:
            brand_colors["primary"] = {
                "$type": "color",
                "$value": "oklch(0.62 0.22 35)",
                "$description": "Primary brand essence color",
                "$extensions": {"hex": "#e0533c"}
            }
        if "accent" not in brand_colors:
            brand_colors["accent"] = {
                "$type": "color",
                "$value": "oklch(0.72 0.18 55)",
                "$description": "Accent high-conversion color",
                "$extensions": {"hex": "#f59e0b"}
            }
        if "balance" not in brand_colors:
            brand_colors["balance"] = {
                "$type": "color",
                "$value": "oklch(0.55 0.12 75)",
                "$description": "Balancing grounding element color",
                "$extensions": {"hex": "#8c6b3e"}
            }

        neutrals = color.setdefault("neutral", {})
        if "bg" not in neutrals:
            neutrals["bg"] = {"$type": "color", "$value": "oklch(0.14 0.02 260)", "$description": "Background dark canvas", "$extensions": {"hex": "#0f172a"}}
        if "surface" not in neutrals:
            neutrals["surface"] = {"$type": "color", "$value": "oklch(0.20 0.03 260)", "$description": "Card surface canvas", "$extensions": {"hex": "#1e293b"}}
        if "text" not in neutrals:
            neutrals["text"] = {"$type": "color", "$value": "oklch(0.96 0.01 260)", "$description": "Primary crisp text", "$extensions": {"hex": "#f8fafc"}}
        if "muted" not in neutrals:
            neutrals["muted"] = {"$type": "color", "$value": "oklch(0.70 0.04 260)", "$description": "Muted secondary text", "$extensions": {"hex": "#94a3b8"}}

        # Typography defaults
        typo = ds.setdefault("typography", {})
        ff = typo.setdefault("fontFamily", {})
        if "display" not in ff:
            ff["display"] = {"$type": "fontFamily", "$value": ["Cinzel", "Playfair Display", "serif"], "$description": "Headline display typography"}
        if "body" not in ff:
            ff["body"] = {"$type": "fontFamily", "$value": ["Inter", "Plus Jakarta Sans", "sans-serif"], "$description": "Readable body typography"}

        return raw_data

    def _derive_tailwind_theme_css(self, brandbook: Dict[str, Any]) -> str:
        """Derives a production-ready Tailwind CSS v4 @theme file with :root custom properties."""
        colors = brandbook.get("design_system", {}).get("color", {})
        brand_colors = colors.get("brand", {})
        neutrals = colors.get("neutral", {})
        typo = brandbook.get("design_system", {}).get("typography", {}).get("fontFamily", {})

        def extract_color(token: Any, default_val: str) -> str:
            if isinstance(token, dict):
                return token.get("$value") or default_val
            return str(token) if token else default_val

        p_oklch = extract_color(brand_colors.get("primary"), "oklch(0.62 0.22 35)")
        a_oklch = extract_color(brand_colors.get("accent"), "oklch(0.72 0.18 55)")
        b_oklch = extract_color(brand_colors.get("balance"), "oklch(0.55 0.12 75)")
        bg_oklch = extract_color(neutrals.get("bg"), "oklch(0.14 0.02 260)")
        surf_oklch = extract_color(neutrals.get("surface"), "oklch(0.20 0.03 260)")
        text_oklch = extract_color(neutrals.get("text"), "oklch(0.96 0.01 260)")
        muted_oklch = extract_color(neutrals.get("muted"), "oklch(0.70 0.04 260)")

        def format_font(token: Any, default_str: str) -> str:
            if isinstance(token, dict):
                val = token.get("$value")
                if isinstance(val, list):
                    return ", ".join(f"'{v}'" if " " in v else v for v in val)
                elif isinstance(val, str):
                    return val
            return default_str

        font_disp = format_font(typo.get("display"), "'Cinzel', serif")
        font_body = format_font(typo.get("body"), "'Inter', sans-serif")

        css_lines = [
            f"/* ==========================================================================",
            f"   Tailwind CSS v4 Brand Theme Tokens — {self.brand_upper}",
            f"   Generated automatically by brandbook_pipeline_runner.py",
            f"   Standard: W3C DTCG 2025.10 | Zero Slop Invariant",
            f"   ========================================================================== */",
            "",
            '@import "tailwindcss";',
            "",
            "@theme {",
            f"  --color-brand-primary: {p_oklch};",
            f"  --color-brand-accent: {a_oklch};",
            f"  --color-brand-balance: {b_oklch};",
            f"  --color-brand-bg: {bg_oklch};",
            f"  --color-brand-surface: {surf_oklch};",
            f"  --color-brand-text: {text_oklch};",
            f"  --color-brand-muted: {muted_oklch};",
            "",
            f"  --font-display: {font_disp};",
            f"  --font-body: {font_body};",
            "}",
            "",
            ":root {",
            f"  --color-brand-primary: {p_oklch};",
            f"  --color-brand-accent: {a_oklch};",
            f"  --color-brand-balance: {b_oklch};",
            f"  --color-brand-bg: {bg_oklch};",
            f"  --color-brand-surface: {surf_oklch};",
            f"  --color-brand-text: {text_oklch};",
            f"  --color-brand-muted: {muted_oklch};",
            f"  --font-display: {font_disp};",
            f"  --font-body: {font_body};",
            "}",
            "",
        ]
        return "\n".join(css_lines)

    def _derive_system_prompt_md(self, brandbook: Dict[str, Any]) -> str:
        """Projects the Brandbook into a structured System Prompt for downstream conversational agents."""
        engine = brandbook.get("llm_system_prompt_engine", {})
        arch = brandbook.get("brand_architecture", {})
        voice = brandbook.get("voice_tone_and_messaging", {})
        audience = brandbook.get("target_audience", {})

        role = engine.get("role", f"Sovereign Brand Ambassador for {self.brand_upper}")
        identity = engine.get("core_identity", arch.get("essence_statement", f"Official digital touchpoint for {self.brand_upper}."))
        style = engine.get("communication_style", "Warm, authoritative, empathetic, and direct.")
        guardrails = engine.get("guardrails", [
            "Never hallucinate services or products outside verified brand assets.",
            "Respect the brand's tone and forbidden vocabulary at all times.",
            "Prioritize genuine connection and value before conversion."
        ])

        pref_terms = voice.get("vocabulary", {}).get("preferred_terms", [])
        forb_terms = voice.get("vocabulary", {}).get("forbidden_terms", [])

        lines = [
            f"# System Prompt: {self.brand_upper}",
            "",
            "> **Identidad Conversacional & Directrices de Marca SSoT**",
            "> Este archivo es la proyección viva del Brandbook consumida por WhatsAppBot y Agentes Downstream.",
            "",
            "## 1. Identidad y Rol Soberano",
            f"- **Rol Asignado:** {role}",
            f"- **Esencia de Marca:** {identity}",
            f"- **Estilo de Comunicación:** {style}",
            "",
            "## 2. Pautas de Voz y Tono",
            f"- **Tono Principal:** {voice.get('primary_tone', 'Autoridad serena y calidez profesional')}",
        ]

        if voice.get("voice_traits"):
            lines.append("- **Rasgos de Voz:**")
            for vt in voice["voice_traits"]:
                lines.append(f"  * {vt}")

        lines.extend([
            "",
            "## 3. Diccionario Terminológico",
            f"- **Términos Preferidos:** {', '.join(pref_terms) if pref_terms else 'Lenguaje claro, conciso y respetuoso'}",
            f"- **Términos Prohibidos:** {', '.join(forb_terms) if forb_terms else 'Clichés baratos, urgencia falsa, modismos vulgares'}",
            "",
            "## 4. Perfil del Consultante / Cliente Ideal (ICP)",
            f"- **Descripción:** {audience.get('ideal_customer_profile', 'Personas que buscan excelencia, transformación y rigor.')}",
            "",
            "## 5. Salvaguardas y Reglas Innegociables",
        ])

        for g in guardrails:
            lines.append(f"- {g}")

        lines.append("")
        return "\n".join(lines)

    def _verify_artifacts(self, out_dir: Path) -> None:
        """Physical sensor check verifying file existence, non-zero size, and parseable JSON/CSS."""
        f_json = out_dir / f"brandbook_superfull_{self.brand_lower}.json"
        f_css = out_dir / "brandbook-theme.css"
        f_prompt = out_dir / "system_prompt.md"

        assert f_json.exists() and f_json.stat().st_size > 100, f"Verification failed: {f_json} is missing or empty"
        assert f_css.exists() and f_css.stat().st_size > 50, f"Verification failed: {f_css} is missing or empty"
        assert f_prompt.exists() and f_prompt.stat().st_size > 50, f"Verification failed: {f_prompt} is missing or empty"

        # Check JSON parseability
        with open(f_json, "r", encoding="utf-8") as f:
            data = json.load(f)
        assert "$schema" in data and "design_system" in data, "Verification failed: required DTCG keys missing"
        logger.info("Physical sensor verification passed (Exit code 0).")


def main() -> int:
    parser = argparse.ArgumentParser(description="Brandbook Fast-Track & Studio Pipeline Runner")
    parser.add_argument("--brand", required=True, help="Brand name or slug (e.g. CATALINAGLAMUR, ELPLACERDC)")
    parser.add_argument("--mode", choices=["fast-track", "studio"], default="fast-track", help="Execution mode")
    parser.add_argument("--enhance", action="store_true", help="Enhance/enrich existing brandbook baseline")
    parser.add_argument("--bifrost-url", default="http://bifrost:8080", help="Bifrost AI Gateway URL")
    parser.add_argument("--model", default="deepseek/deepseek-chat", help="Primary LLM model via Bifrost")
    parser.add_argument("--output-dir", help="Custom output directory")
    parser.add_argument("--dry-run", action="store_true", help="Inspect context without calling LLM")

    args = parser.parse_args()
    runner = BrandbookPipelineRunner(
        brand_raw=args.brand,
        mode=args.mode,
        enhance=args.enhance,
        bifrost_url=args.bifrost_url,
        model=args.model,
        output_dir=args.output_dir
    )
    return runner.run(dry_run=args.dry_run)


if __name__ == "__main__":
    sys.exit(main())
