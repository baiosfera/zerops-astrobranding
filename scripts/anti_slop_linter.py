#!/usr/bin/env python3
"""
Anti-Slop Strategic Linter & Brand Lexicon Gate (v2.1)
Validates marketing copy, landing pages, and components against:
1. Universal AI clichés (ES/EN)
2. Dynamic brandbook.json & verticals/*.json taboos (case-insensitive workspace discovery)
3. Client-facing quality gates (unless --allow-internal-jargon):
   - Unambiguous unaccented Spanish words (outside URLs/paths/code blocks)
   - Leaked internal acronyms (BANT, AEO, GEO, PWYW, Order Bump, etc.)
   - Leaked UPPER_SNAKE_CASE state enums outside code blocks / env refs
   - Obsolete AI framing clichés, forbidden narrow professions, deprecated timelines & private pricing leaks
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Dict, List, NamedTuple, Optional, Pattern, Set, Tuple


class Violation(NamedTuple):
    line_number: int
    rule_type: str
    matched_text: str
    snippet: str
    suggestion: str


class AntiSlopRule(NamedTuple):
    pattern: Pattern[str]
    rule_type: str
    label: str
    suggestion: str


UNIVERSAL_AI_CLICHES: List[Tuple[str, str, str]] = [
    (r"\blleva(?:r)?\s+tu\s+negocio\s+al\s+siguiente\s+nivel\b", "cliche_spanish", "Lleva tu negocio al siguiente nivel", "Define el resultado exacto, métrica o transformación específica."),
    (r"\ben\s+el\s+(?:competitivo\s+mundo\s+actual|mundo\s+competitivo\s+de\s+hoy)\b", "cliche_spanish", "En el competitivo mundo actual", "Entra directamente al dolor del cliente sin introducciones trilladas."),
    (r"\buna\s+experiencia\s+única\s+e\s+inolvidable\b", "cliche_spanish", "Una experiencia única e inolvidable", "Detalla los beneficios tangibles que la componen."),
    (r"\bdescubre\s+el\s+poder\s+de\b", "cliche_spanish", "Descubre el poder de", "Presenta directamente el método o solución sin hipérboles."),
    (r"\bsumérgete\s+en\b", "cliche_spanish", "Sumérgete en", "Usa verbos de acción concretos (explora, accede, revisa, prueba)."),
    (r"\bdesbloquea\s+tu\s+potencial\b", "cliche_spanish", "Desbloquea tu potencial", "Cuantifica la capacidad adquirida o el ahorro concreto."),
    (r"\bun\s+viaje\s+(?:fascinante|apasionante|de\s+transformación)\b", "cliche_spanish", "Un viaje fascinante/apasionante", "Describe el proceso real paso a paso."),
    (r"\bcomo\s+(?:inteligencia\s+artificial|modelo\s+de\s+lenguaje)\b", "ai_leak", "Fuga de identidad IA", "Elimina cualquier autorreferencia a sistemas de IA."),
    (r"\bes\s+crucial\s+recordar\s+que\b", "cliche_spanish", "Es crucial recordar que", "Presenta la regla de forma directa."),
    (r"\ben\s+este\s+(?:artículo|post|escrito|documento)\s+(?:vamos\s+a|veremos)\b", "cliche_spanish", "Metadiscurso", "Elimina el metadiscurso y entrega el contenido de inmediato."),
    (r"\btake\s+your\s+business\s+to\s+the\s+next\s+level\b", "cliche_english", "Take your business to the next level", "State the concrete outcome or metric."),
    (r"\bin\s+today's\s+competitive\s+(?:landscape|world|market)\b", "cliche_english", "In today's competitive landscape", "Address the audience's immediate friction directly."),
    (r"\bdiscover\s+the\s+power\s+of\b", "cliche_english", "Discover the power of", "Name the mechanism or feature directly."),
    (r"\bdive\s+deep\s+into\b", "cliche_english", "Dive deep into", "Use precise action verbs."),
    (r"\bunlock\s+your\s+potential\b", "cliche_english", "Unlock your potential", "Quantify the capability."),
    (r"\bgame-changer\b", "cliche_english", "Game-changer", "Explain the structural improvement."),
    (r"\bseamlessly\b", "cliche_english", "Seamlessly", "State how it works without filler adverbs."),
    (r"\bdelve\s+into\b", "cliche_english", "Delve into", "Focus directly on the concept."),
    (r"\bas\s+an\s+ai\s+language\s+model\b", "ai_leak", "AI model self-reference", "Remove AI self-identifications."),
]

# Unambiguous unaccented Spanish words (lowercase check with case-insensitive boundary outside URLs/code)
UNACCENTED_SPANISH_MAP: Dict[str, str] = {
    "ano": "año (nota: sin tilde/ñ cambia el sentido)",
    "anos": "años",
    "diseno": "diseño",
    "disenar": "diseñar",
    "diagnostico": "diagnóstico (sustantivo) / revisa acento si es adjetivo",
    "politicas": "políticas",
    "guia": "guía",
    "metodo": "método",
    "nomina": "nómina",
    "categoria": "categoría",
    "calculo": "cálculo",
    "codigo": "código",
    "pagina": "página",
    "paginas": "páginas",
    "tecnico": "técnico",
    "tecnica": "técnica",
    "estrategico": "estratégico",
    "estrategica": "estratégica",
    "automatico": "automático",
    "automatica": "automática",
    "economico": "económico",
    "economica": "económica",
    "sesion": "sesión",
    "version": "versión",
    "numero": "número",
    "unico": "único",
    "unica": "única",
    "tambien": "también",
    "linea": "línea",
    "exito": "éxito",
    "practico": "práctico",
    "practica": "práctica",
    "analisis": "análisis",
    "solucion": "solución",
    "informacion": "información",
    "implementacion": "implementación",
    "automatizacion": "automatización",
    "facturacion": "facturación",
    "operacion": "operación",
    "inversion": "inversión",
    "gestion": "gestión",
    "decision": "decisión",
    "comunicacion": "comunicación",
    "optimizacion": "optimización",
    "contratacion": "contratación",
    "atencion": "atención",
    "configuracion": "configuración",
    "integracion": "integración",
    "evaluacion": "evaluación",
    "validacion": "validación",
    "conversacion": "conversación",
    "conversion": "conversión",
    "medicion": "medición",
    "planificacion": "planificación",
    "publicacion": "publicación",
    "recuperacion": "recuperación",
    "retencion": "retención",
    "atribucion": "atribución",
    "verificacion": "verificación",
}

CLIENT_INTERNAL_JARGON: List[Tuple[str, str]] = [
    (r"\bBANT\b", "Evita jerga interna ('BANT'); habla de 'preguntas de calificación' o 'ajuste mutuo'."),
    (r"\bAEO\b", "Evita jerga interna ('AEO'); escribe 'visibilidad en buscadores y asistentes de IA'."),
    (r"\bGEO\b", "Evita jerga interna ('GEO'); escribe 'visibilidad en respuestas de IA'."),
    (r"\bPWYW\b", "Evita siglas en inglés ('PWYW'); escribe 'aporte flexible' o 'elige tu aporte'."),
    (r"\bOrder\s+Bump\b", "Evita anglicismo interno ('Order Bump'); escribe 'complemento opcional' o 'kit financiero adicional'."),
    (r"\bContext\s+Vault\b", "Evita anglicismo técnico ('Context Vault'); escribe 'memoria real de tu negocio'."),
    (r"\bBreak-Even\s+CPA\b", "Evita jerga de pauta ('Break-Even CPA'); escribe 'costo máximo por cliente rentable'."),
    (r"\bserver-side\b", "Evita jerga técnica ('server-side'); describe el beneficio comercial directo."),
    (r"\bDIY\b", "Evita jerga interna ('DIY'); describe 'a tu ritmo', 'por tu cuenta' o 'academia y comunidad'."),
    (r"\bDWY\b", "Evita jerga interna ('DWY'); describe 'acompañamiento guiado' o 'mentoría aplicada'."),
    (r"\bDFY\b", "Evita jerga interna ('DFY'); describe 'implementación llave en mano' o 'lo construimos por ti'."),
    (r"\b(?:verticales|nuestra\s+vertical|la\s+vertical|esta\s+vertical|mi\s+vertical|cada\s+vertical)\b", "Evita jerga interna ('vertical/verticales'); usa 'línea', 'programa', 'área' o el nombre comercial directo."),
]

ALLOWED_UPPER_SNAKE = {
    "USD_COP", "COP_USD", "SMMLV_2026", "SMMLV_2027", "META_CAPI",
    "GA4_ID", "GTM_ID", "JSON_LD", "WCAG_AAA", "UTF_8",
}

URL_OR_PATH_RE = re.compile(r"https?://\S+|(?:(?<=^)|(?<=[\s(\"'\[,=:\-]))/[A-Za-z0-9_./-]+|`[^`]+`")
SNAKE_ENUM_RE = re.compile(r"\b[A-Z]{2,}(?:_[A-Z0-9]{2,})+\b")


class AntiSlopLinter:
    """Deterministic physical linter validating copy against slop, jargon, orthography, and brand constraints."""

    def __init__(
        self,
        brand: Optional[str] = None,
        vertical: Optional[str] = None,
        extra_taboos: Optional[List[str]] = None,
        allow_internal_jargon: bool = False,
        extra_roots: Optional[List[Path]] = None,
    ):
        self.brand = (brand or os.getenv("PROJECT_NAME") or "default").strip()
        self.vertical = (vertical or "").strip().lower()
        self.allow_internal_jargon = allow_internal_jargon
        self.extra_roots = list(extra_roots or [])
        self.rules: List[AntiSlopRule] = []
        self.private_pricing_rules: List[AntiSlopRule] = []
        self._load_rules(extra_taboos or [])

    def _add_taboo(self, term: str, rule_type: str, label_prefix: str, suggestion: str, is_regex: bool = False) -> None:
        clean = term.strip()
        if len(clean) < 2:
            return
        pat_str = clean if is_regex else rf"\b{re.escape(clean)}\b"
        self.rules.append(
            AntiSlopRule(
                pattern=re.compile(pat_str, re.IGNORECASE),
                rule_type=rule_type,
                label=f"{label_prefix}: {clean}",
                suggestion=suggestion,
            )
        )

    def _load_rules(self, extra_taboos: List[str]) -> None:
        for pattern_str, rule_type, label, suggestion in UNIVERSAL_AI_CLICHES:
            self.rules.append(AntiSlopRule(re.compile(pattern_str, re.IGNORECASE), rule_type, label, suggestion))

        for term in extra_taboos:
            if isinstance(term, str):
                self._add_taboo(term, "brand_taboo", "Término prohibido", f"Evita '{term}' y usa el léxico aprobado.")

        if not self.allow_internal_jargon:
            for pat, sug in CLIENT_INTERNAL_JARGON:
                self.rules.append(AntiSlopRule(re.compile(pat), "internal_jargon_leak", f"Jerga interna ({pat})", sug))

        self._load_dynamic_brandbook()

    def _discover_brand_files(self) -> Tuple[List[Path], List[Path]]:
        bb_paths: List[Path] = []
        vert_paths: List[Path] = []
        target_low = self.brand.lower()
        roots = self.extra_roots + [Path("/mnt/localstorage"), Path("/var/www/localstorage"), Path("/var/www/baiosfera/PROYECTOS")]
        for root in roots:
            if not root.exists():
                continue
            try:
                children = [c for c in root.iterdir() if c.is_dir() and not c.name.startswith(".")]
            except Exception:
                children = []
            for child in children:
                dev = child / "dev"
                if not dev.is_dir():
                    continue
                proj_match = child.name.lower() == target_low
                # Also match workspace/brandbook brand_name inside Project/dev/workspaces/*
                if not proj_match and (dev / "brandbook.json").is_file():
                    try:
                        bname = json.loads((dev / "brandbook.json").read_text(encoding="utf-8")).get("metadata", {}).get("brand_name", "")
                        if bname.strip().lower() == target_low:
                            proj_match = True
                    except Exception:
                        pass
                if proj_match:
                    if (dev / "brandbook.json").is_file():
                        bb_paths.append(dev / "brandbook.json")
                    ws_root = dev / "workspaces"
                    if ws_root.is_dir():
                        for ws in ws_root.iterdir():
                            if self.vertical and ws.name.lower() != self.vertical:
                                continue
                            if (ws / "brand" / "brandbook.json").is_file():
                                bb_paths.append(ws / "brand" / "brandbook.json")
                    v_dir = dev / "verticals"
                    if v_dir.is_dir():
                        for vf in v_dir.glob("*.json"):
                            if not self.vertical or vf.stem.lower() == self.vertical:
                                vert_paths.append(vf)
        return bb_paths, vert_paths

    def _load_dynamic_brandbook(self) -> None:
        bb_paths, vert_paths = self._discover_brand_files()
        seen_terms: Set[str] = set()
        public_allowlist: Set[str] = set()

        for vf in vert_paths:
            try:
                vdata = json.loads(vf.read_text(encoding="utf-8"))
                for t in vdata.get("public_brand_concepts", []) or []:
                    if isinstance(t, str) and t.strip():
                        public_allowlist.add(t.strip().lower())
            except Exception:
                pass

        for bb in bb_paths:
            try:
                data = json.loads(bb.read_text(encoding="utf-8"))
                for t in data.get("public_brand_concepts", []) or []:
                    if isinstance(t, str) and t.strip():
                        public_allowlist.add(t.strip().lower())
                taboos: List[str] = []
                lex = data.get("lexicon", {})
                if isinstance(lex.get("forbidden_terms"), list):
                    taboos.extend(lex["forbidden_terms"])
                vtm = data.get("voice_tone_and_messaging", {})
                if isinstance(vtm.get("forbidden_vocabulary"), list):
                    taboos.extend(vtm["forbidden_vocabulary"])
                for term in taboos:
                    if isinstance(term, str) and term.lower() not in seen_terms and term.lower() not in public_allowlist:
                        seen_terms.add(term.lower())
                        self._add_taboo(term, "dynamic_brandbook_taboo", "Brandbook taboo", f"Término prohibido en brandbook de {self.brand}.")
            except Exception:
                pass

        if not self.allow_internal_jargon:
            seen_priv_pats: Set[str] = set()
            for vf in vert_paths:
                try:
                    vdata = json.loads(vf.read_text(encoding="utf-8"))
                    cat = vdata.get("category_and_positioning", {})
                    for key in ("excluded_terms", "client_facing_jargon_ban"):
                        for term in cat.get(key, []) or []:
                            if isinstance(term, str) and term.lower() not in seen_terms and term.lower() not in public_allowlist:
                                seen_terms.add(term.lower())
                                self._add_taboo(term, "vertical_jargon_ban", "Restricción vertical", f"Término vetado por {vf.name}.")
                    for key, rtype, prefix, hint in (
                        ("forbidden_ai_cliches", "obsolete_ai_framing", "Narrativa IA obsoleta", "Actualiza al problema vigente de diferenciación CO1 y junturas de conversión."),
                        ("forbidden_audience_terms", "forbidden_audience_term", "Profesión cerrada vetada", "Reemplaza profesiones puntuales por Marcas Personales y áreas amplias (salud, legal, psicología, finanzas)."),
                        ("deprecated_timelines", "deprecated_timeline", "Plazo obsoleto", "Actualiza a instalación inicial < 15 días + acompañamiento 90 días + continuidad desde mes 4."),
                    ):
                        for term in (vdata.get(key, []) or []) + (cat.get(key, []) or []):
                            if isinstance(term, str) and term.lower() not in seen_terms and term.lower() not in public_allowlist:
                                seen_terms.add(term.lower())
                                self._add_taboo(term, rtype, prefix, f"{hint} ({vf.name}).")
                    priv = vdata.get("private_call_only_pricing", {})
                    if isinstance(priv, dict) and priv.get("public_page_exposure") is False:
                        for pat in priv.get("blocked_public_patterns", []) or []:
                            if isinstance(pat, str) and pat not in seen_priv_pats:
                                seen_priv_pats.add(pat)
                                self.private_pricing_rules.append(
                                    AntiSlopRule(
                                        pattern=re.compile(pat, re.IGNORECASE),
                                        rule_type="private_pricing_leak",
                                        label=f"Tarifa privada expuesta ({vf.name})",
                                        suggestion="Las tarifas privadas de llamada solo pueden mostrarse en copy/00_* y copy/06_*.",
                                    )
                                )
                except Exception:
                    pass

            for bb in bb_paths:
                try:
                    data = json.loads(bb.read_text(encoding="utf-8"))
                    lex = data.get("lexicon", {})
                    for key, rtype, prefix, hint in (
                        ("forbidden_ai_cliches", "obsolete_ai_framing", "Narrativa IA obsoleta", "Actualiza a diferenciación CO1 y sistema conectado."),
                        ("forbidden_audience_terms", "forbidden_audience_term", "Profesión cerrada vetada", "Habla de Marcas Personales y áreas amplias sin nombrar profesiones."),
                        ("deprecated_timelines", "deprecated_timeline", "Plazo obsoleto", "Usa < 15 días de montaje + 90 días de acompañamiento + continuidad mes 4."),
                    ):
                        for term in (lex.get(key, []) or []) + (data.get(key, []) or []):
                            if isinstance(term, str) and term.lower() not in seen_terms and term.lower() not in public_allowlist:
                                seen_terms.add(term.lower())
                                self._add_taboo(term, rtype, prefix, f"{hint} ({bb.name}).")
                except Exception:
                    pass

    def lint_text(self, text: str, source_name: str = "") -> List[Violation]:
        violations: List[Violation] = []
        in_fenced_block = False
        is_private_doc = Path(source_name).name.startswith(("00_", "06_")) if source_name else False

        for line_idx, raw_line in enumerate(text.splitlines(), start=1):
            stripped = raw_line.strip()
            if stripped.startswith("```"):
                in_fenced_block = not in_fenced_block
                continue
            if in_fenced_block:
                continue

            # Ignore inline code, URLs, and filesystem paths when scanning orthography & enum leaks
            clean_line = URL_OR_PATH_RE.sub(" ", raw_line)
            no_url_line = re.sub(r"https?://\S+", " ", raw_line)

            for rule in self.rules:
                target_str = (
                    clean_line
                    if rule.rule_type in ("internal_jargon_leak", "vertical_jargon_ban")
                    else (no_url_line if rule.rule_type == "forbidden_audience_term" else raw_line)
                )
                m = rule.pattern.search(target_str)
                if m:
                    snippet = stripped[:80]
                    violations.append(Violation(line_idx, rule.rule_type, m.group(0), snippet, rule.suggestion))

            if not self.allow_internal_jargon and not is_private_doc:
                for prule in self.private_pricing_rules:
                    pm = prule.pattern.search(no_url_line)
                    if pm:
                        violations.append(Violation(line_idx, prule.rule_type, pm.group(0), stripped[:80], prule.suggestion))

            if not self.allow_internal_jargon:
                # 1. Check UPPER_SNAKE_CASE leaked state enums
                for em in SNAKE_ENUM_RE.finditer(clean_line):
                    tok = em.group(0)
                    if tok in ALLOWED_UPPER_SNAKE:
                        continue
                    violations.append(
                        Violation(
                            line_idx,
                            "upper_snake_enum_leak",
                            tok,
                            stripped[:80],
                            f"Reemplaza identificador interno '{tok}' por español natural para el usuario.",
                        )
                    )

                # 2. Check unambiguous unaccented Spanish words (lowercase only — skip Title/Code tokens)
                # Also skip JSON key names before ":" in .json inputs
                prose_part = re.sub(r'"[^"]+"\s*:', " ", clean_line)
                for wm in re.finditer(r"\b([a-záéíóúüñ]+)\b", prose_part):
                    word = wm.group(1)
                    if word in UNACCENTED_SPANISH_MAP:
                        violations.append(
                            Violation(
                                line_idx,
                                "spanish_orthography",
                                word,
                                stripped[:80],
                                f"Ortografía: usa '{UNACCENTED_SPANISH_MAP[word]}'.",
                            )
                        )

        return violations

    def lint_file(self, file_path: Path) -> List[Violation]:
        if not file_path.is_file():
            raise FileNotFoundError(f"Archivo no encontrado: {file_path}")
        return self.lint_text(file_path.read_text(encoding="utf-8", errors="replace"), source_name=file_path.name)


def run_unit_tests() -> int:
    import tempfile
    print("============================================================")
    print("  🧪 RUNNING ANTI-SLOP LINTER v2.1 UNIT TESTS")
    print("============================================================")

    linter = AntiSlopLinter(brand="acme-club")
    clean_text = (
        "Accede al estudio privado de arquitectura y diseño. Disfruta de una solución clara, "
        "método práctico y análisis transparente este año."
    )
    v1 = linter.lint_text(clean_text)
    assert len(v1) == 0, f"Expected 0 violations, got {v1}"
    print("✓ Test 1: Clean accented Spanish copy passes with 0 violations.")

    cliche_text = "En el competitivo mundo actual, nuestro software lleva tu negocio al siguiente nivel."
    v2 = linter.lint_text(cliche_text)
    assert any(v.rule_type == "cliche_spanish" for v in v2)
    print("✓ Test 2: Universal AI clichés detected accurately.")

    linter_a = AntiSlopLinter(brand="brand-alpha", extra_taboos=["templo", "sagrado"])
    v3 = linter_a.lint_text("Te invitamos a nuestro templo sagrado.")
    assert len(v3) >= 2
    print("✓ Test 3: Dynamic brand taboos detected accurately.")

    v4 = linter.lint_text("Este metodo sin diseno para tu nomina falla este ano.")
    assert len([v for v in v4 if v.rule_type == "spanish_orthography"]) >= 4
    print("✓ Test 4: Unaccented Spanish words detected accurately.")

    v5 = linter.lint_text("Con nuestro Order Bump, PWYW, modelo DIY/DWY/DFY y nuevas verticales vas a ver BANT.")
    assert len([v for v in v5 if v.rule_type == "internal_jargon_leak"]) >= 7
    assert len(linter.lint_text("Aprende el modelo OPB y CO1 con un video vertical claro.")) == 0, "Public strategic acronyms and legitimate geometry terms should pass!"
    print("✓ Test 5: Backend jargon leaks (incl. DIY/DWY/DFY/verticales) caught while strategic category terms and 'video vertical' allowed.")

    v6 = linter.lint_text("Estado actual: READY_NOW_QUALIFIED en pantalla.")
    assert any(v.rule_type == "upper_snake_enum_leak" for v in v6)
    print("✓ Test 6: Leaked UPPER_SNAKE_CASE enum detected accurately.")

    linter_internal = AntiSlopLinter(brand="acme", allow_internal_jargon=True)
    v7 = linter_internal.lint_text("Spec OPB con READY_NOW_QUALIFIED.")
    assert len(v7) == 0
    print("✓ Test 7: --allow-internal-jargon suppresses client-only rules cleanly.")

    with tempfile.TemporaryDirectory() as tmpd:
        tmp_root = Path(tmpd)
        proj = tmp_root / "TestBrand" / "dev"
        (proj / "verticals").mkdir(parents=True)
        (proj / "verticals" / "solopro.json").write_text(
            json.dumps({
                "forbidden_ai_cliches": ["chats sueltos"],
                "forbidden_audience_terms": ["abogados", "médicos"],
                "deprecated_timelines": ["60 días", "desde el mes 3"],
                "private_call_only_pricing": {
                    "public_page_exposure": False,
                    "blocked_public_patterns": [r"\$599\b"],
                },
            }),
            encoding="utf-8",
        )
        dl = AntiSlopLinter(brand="TestBrand", vertical="solopro", extra_roots=[tmp_root])
        bad = "Para abogados y médicos: deja chats sueltos en 60 días desde el mes 3 por $599."
        v8 = dl.lint_text(bad, source_name="01_landing.md")
        rtypes = {v.rule_type for v in v8}
        assert {"obsolete_ai_framing", "forbidden_audience_term", "deprecated_timeline", "private_pricing_leak"}.issubset(rtypes), rtypes
        v8_script = dl.lint_text("Inversión privada $599 en llamada.", source_name="06_script.md")
        assert len(v8_script) == 0, v8_script
    print("✓ Test 8: Dynamic vertical guardrails (obsolete AI, professions, timelines, private pricing) verified cleanly.")

    print("============================================================")
    print("🎉 All 8 unit tests PASSED successfully (Exit 0)!")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Anti-Slop Strategic Linter & Brand Lexicon Gate v2.0")
    parser.add_argument("--file", "-f", type=Path, help="Path to file to lint (.astro, .md, .json, .ts)")
    parser.add_argument("--text", "-t", type=str, help="Raw text string to lint")
    parser.add_argument("--brand", "-b", type=str, help="Brand identifier")
    parser.add_argument("--vertical", "-v", type=str, help="Optional vertical slug inside workspaces/")
    parser.add_argument("--allow-internal-jargon", action="store_true", help="Relax client-facing jargon/orthography gate for internal specs")
    parser.add_argument("--test", action="store_true", help="Run self-contained physical unit tests")
    parser.add_argument("--quiet", "-q", action="store_true", help="Quiet mode (exit code only)")
    args = parser.parse_args()

    if args.test:
        return run_unit_tests()
    if not args.file and not args.text:
        parser.print_help()
        return 1

    linter = AntiSlopLinter(brand=args.brand, vertical=args.vertical, allow_internal_jargon=args.allow_internal_jargon)
    violations = linter.lint_file(args.file) if args.file else linter.lint_text(args.text)

    if not violations:
        if not args.quiet:
            print(f"✅ Anti-Slop Check PASSED: Zero issues detected for '{linter.brand}'.")
        return 0

    if not args.quiet:
        target_name = str(args.file) if args.file else "provided text"
        print(f"❌ Anti-Slop Violations detected in {target_name} ({len(violations)} issues):")
        for v in violations:
            print(f"  • [Línea {v.line_number}] [{v.rule_type.upper()}] '{v.matched_text}' -> {v.suggestion}")
    return 1


if __name__ == "__main__":
    sys.exit(main())
