#!/usr/bin/env python3
"""
Anti-Slop Strategic Linter & Brand Lexicon Gate (v1.0)
Validates marketing copy, landing pages, and components against universal AI clichés
and project-specific brandbook taboos with deterministic physical checks.
"""

from __future__ import annotations

import argparse
import json
import os
import re
import sys
from pathlib import Path
from typing import Dict, List, NamedTuple, Optional, Pattern, Tuple


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


# Universal AI Marketing & Prose Cliché Blacklist
UNIVERSAL_AI_CLICHES: List[Tuple[str, str, str]] = [
    # Spanish Clichés
    (r"\blleva(?:r)?\s+tu\s+negocio\s+al\s+siguiente\s+nivel\b", "cliche_spanish", "Lleva tu negocio al siguiente nivel", "Define el resultado exacto, métrica o transformación específica."),
    (r"\ben\s+el\s+(?:competitivo\s+mundo\s+actual|mundo\s+competitivo\s+de\s+hoy)\b", "cliche_spanish", "En el competitivo mundo actual", "Entra directamente al dolor del avatar sin introducciones trilladas."),
    (r"\buna\s+experiencia\s+única\s+e\s+inolvidable\b", "cliche_spanish", "Una experiencia única e inolvidable", "Detalla los elementos sensoriales o beneficios tangibles que la componen."),
    (r"\bdescubre\s+el\s+poder\s+de\b", "cliche_spanish", "Descubre el poder de", "Presenta directamente el mecanismo único o la solución sin hipérboles."),
    (r"\bsumérgete\s+en\b", "cliche_spanish", "Sumérgete en", "Usa verbos de acción concretos (explora, accede, domina, prueba)."),
    (r"\bdesbloquea\s+tu\s+potencial\b", "cliche_spanish", "Desbloquea tu potencial", "Cuantifica la capacidad adquirida o el objetivo desbloqueado."),
    (r"\bun\s+viaje\s+(?:fascinante|apasionante|de\s+transformación)\b", "cliche_spanish", "Un viaje fascinante/apasionante", "Describe la secuencia o proceso real."),
    (r"\bcomo\s+(?:inteligencia\s+artificial|modelo\s+de\s+lenguaje)\b", "ai_leak", "Fuga de identidad de modelo IA", "Elimina cualquier autorreferencia a sistemas de inteligencia artificial."),
    (r"\bes\s+crucial\s+recordar\s+que\b", "cliche_spanish", "Es crucial recordar que", "Presenta la regla o advertencia de forma directa."),
    (r"\ben\s+este\s+(?:artículo|post|escrito|documento)\s+(?:vamos\s+a|veremos)\b", "cliche_spanish", "Metadiscurso de artículo", "Elimina el metadiscurso y entrega el contenido de inmediato."),

    # English Clichés
    (r"\btake\s+your\s+business\s+to\s+the\s+next\s+level\b", "cliche_english", "Take your business to the next level", "State the concrete business outcome or metric."),
    (r"\bin\s+today's\s+competitive\s+(?:landscape|world|market)\b", "cliche_english", "In today's competitive landscape", "Address the audience's immediate friction directly."),
    (r"\ba\s+unique\s+and\s+unforgettable\s+experience\b", "cliche_english", "A unique and unforgettable experience", "Detail the sensory or tangible benefits."),
    (r"\bdiscover\s+the\s+power\s+of\b", "cliche_english", "Discover the power of", "Name the unique mechanism or feature directly."),
    (r"\bdive\s+deep\s+into\b", "cliche_english", "Dive deep into", "Use precise analytical or practical action verbs."),
    (r"\bunlock\s+your\s+potential\b", "cliche_english", "Unlock your potential", "Quantify the capability or transformation."),
    (r"\bgame-changer\b", "cliche_english", "Game-changer", "Explain the operational or structural improvement."),
    (r"\ba\s+testament\s+to\b", "cliche_english", "A testament to", "Provide direct physical proof or data."),
    (r"\bseamlessly\b", "cliche_english", "Seamlessly", "State how the integration or feature operates without filler adverbs."),
    (r"\bdelve\s+into\b", "cliche_english", "Delve into", "Focus directly on the mechanism or concept."),
    (r"\bas\s+an\s+ai\s+language\s+model\b", "ai_leak", "AI language model self-reference", "Remove all synthetic AI self-identifications."),
]

# Sovereign Brand Taboos & Forbidden Vocabulary (Domain-Specific Invariants)
BRAND_TABOOS: Dict[str, List[Tuple[str, str, str]]] = {
    "elplacerdc": [
        (r"\bsagrad[ao]s?\b", "brand_taboo", "Término místico sagrado/a", "El Placer de Compartir es hedonista, erótico y consensuado; no místico."),
        (r"\bsantuario\b", "brand_taboo", "Término místico santuario", "Sustituye por 'sede cultural', 'club privado' o 'espacio'."),
        (r"\btemplo\b", "brand_taboo", "Término místico templo", "Sustituye por 'entorno de conexión' o 'espacio seguro'."),
        (r"\baltar\b", "brand_taboo", "Término místico altar", "Prohibido en la narrativa de El Placer de Compartir."),
        (r"\bte\s+reconoceremos\s+al\s+instante\b", "brand_taboo", "Frase prohibida de admisión", "Sustituye por validación rigurosa de perfil y código de acceso."),
        (r"\bcuántic[ao]s?\b", "brand_taboo", "Jerga cuántica no verificada", "Usa términos relacionales, psicológicos o de consentimiento."),
        (r"\bchamanic[ao]s?\b", "brand_taboo", "Término chamánico", "Prohibido en la narrativa de El Placer de Compartir."),
        (r"\bmístic[ao]s?\b", "brand_taboo", "Término místico", "Sustituye por sensualidad, erotismo o conexión auténtica."),
        (r"\besotéric[ao]s?\b", "brand_taboo", "Término esotérico", "Usa marco secular, ético y hedonista."),
    ],
    "catalinaglamur": [
        (r"\bbarat[ao]s?\b", "brand_taboo", "Término barato/a", "Catalina Glamur es alta gama y lujo silencioso; usa 'inversión accesible' o evita referencias a bajo costo."),
        (r"\bganga\b", "brand_taboo", "Término ganga", "Prohibido en marcas de lujo."),
        (r"\bdescuentazo\b", "brand_taboo", "Término descuentazo", "Sustituye por 'condición preferencial' o 'privilegio de membresía'."),
        (r"\bliquidación\b", "brand_taboo", "Término liquidación", "Prohibido en colecciones de alta joyería o moda de autor."),
    ],
    "damaren": [
        (r"\bbarat[ao]s?\b", "brand_taboo", "Término barato/a", "Damaren prioriza calidad artesanal y diseño."),
        (r"\bdescuentazo\b", "brand_taboo", "Término descuentazo", "Usa 'beneficio exclusivo'."),
    ],
}


class AntiSlopLinter:
    """Deterministic physical linter validating copy against slop and brand constraints."""

    def __init__(self, brand: Optional[str] = None):
        self.brand = (brand or os.getenv("PROJECT_NAME") or "elplacerdc").strip().lower()
        self.rules: List[AntiSlopRule] = []
        self._load_rules()

    def _load_rules(self) -> None:
        # 1. Load universal AI clichés
        for pattern_str, rule_type, label, suggestion in UNIVERSAL_AI_CLICHES:
            self.rules.append(
                AntiSlopRule(
                    pattern=re.compile(pattern_str, re.IGNORECASE),
                    rule_type=rule_type,
                    label=label,
                    suggestion=suggestion,
                )
            )

        # 2. Load static brand taboos
        if self.brand in BRAND_TABOOS:
            for pattern_str, rule_type, label, suggestion in BRAND_TABOOS[self.brand]:
                self.rules.append(
                    AntiSlopRule(
                        pattern=re.compile(pattern_str, re.IGNORECASE),
                        rule_type=rule_type,
                        label=label,
                        suggestion=suggestion,
                    )
                )

        # 3. Dynamically discover brandbook taboos from disk if present
        self._load_dynamic_brandbook()

    def _load_dynamic_brandbook(self) -> None:
        brand_dirs = [
            Path(f"/var/www/localstorage/{self.brand.upper()}/dev/brandbook.json"),
            Path(f"/var/www/localstorage/{self.brand}/dev/brandbook.json"),
            Path(f"/var/www/baiosfera/PROYECTOS/{self.brand.upper()}/dev/brandbook.json"),
            Path(f"/var/www/baiosfera/PROYECTOS/{self.brand}/dev/brandbook.json"),
        ]
        for bb_path in brand_dirs:
            if bb_path.is_file():
                try:
                    with open(bb_path, "r", encoding="utf-8") as f:
                        data = json.load(f)
                    taboos = data.get("lexicon", {}).get("forbidden_terms", [])
                    if isinstance(taboos, list):
                        for term in taboos:
                            if isinstance(term, str) and len(term.strip()) > 2:
                                clean_term = term.strip()
                                pat = re.compile(rf"\b{re.escape(clean_term)}\b", re.IGNORECASE)
                                self.rules.append(
                                    AntiSlopRule(
                                        pattern=pat,
                                        rule_type="dynamic_brandbook_taboo",
                                        label=f"Brandbook taboo: {clean_term}",
                                        suggestion=f"Término prohibido en brandbook.json de {self.brand}.",
                                    )
                                )
                except Exception:
                    pass
                break

    def lint_text(self, text: str) -> List[Violation]:
        violations: List[Violation] = []
        lines = text.splitlines()

        for line_idx, line in enumerate(lines, start=1):
            for rule in self.rules:
                match = rule.pattern.search(line)
                if match:
                    snippet = line.strip()
                    if len(snippet) > 80:
                        start_pos = max(0, match.start() - 20)
                        end_pos = min(len(line), match.end() + 20)
                        snippet = f"...{line[start_pos:end_pos].strip()}..."
                    violations.append(
                        Violation(
                            line_number=line_idx,
                            rule_type=rule.rule_type,
                            matched_text=match.group(0),
                            snippet=snippet,
                            suggestion=rule.suggestion,
                        )
                    )
        return violations

    def lint_file(self, file_path: Path) -> List[Violation]:
        if not file_path.is_file():
            raise FileNotFoundError(f"Archivo no encontrado: {file_path}")
        content = file_path.read_text(encoding="utf-8", errors="replace")
        return self.lint_text(content)


def run_unit_tests() -> int:
    """Deterministic physical unit tests for AntiSlopLinter."""
    print("============================================================")
    print("  🧪 RUNNING ANTI-SLOP LINTER UNIT TESTS")
    print("============================================================")

    # Test 1: Clean text passes with zero violations
    linter = AntiSlopLinter(brand="elplacerdc")
    clean_text = (
        "Accede al club privado The Corset Society. Disfruta de un entorno seguro, "
        "confortable y exclusivo en Bogotá para adultos de mente abierta."
    )
    v1 = linter.lint_text(clean_text)
    assert len(v1) == 0, f"Expected 0 violations, got {len(v1)}: {v1}"
    print("✓ Test 1: Clean brand copy passes with 0 violations.")

    # Test 2: Universal AI cliché is detected
    cliche_text = "En el competitivo mundo actual, nuestro software lleva tu negocio al siguiente nivel."
    v2 = linter.lint_text(cliche_text)
    assert len(v2) >= 2, f"Expected at least 2 violations, got {len(v2)}"
    rule_types = {v.rule_type for v in v2}
    assert "cliche_spanish" in rule_types, "Expected cliche_spanish violation"
    print("✓ Test 2: Universal AI clichés detected accurately.")

    # Test 3: Brand taboo is detected for elplacerdc
    taboo_text = "Te invitamos a nuestro templo sagrado donde te reconoceremos al instante."
    v3 = linter.lint_text(taboo_text)
    assert len(v3) >= 3, f"Expected at least 3 violations, got {len(v3)}"
    matched = [v.matched_text.lower() for v in v3]
    assert any("templo" in m for m in matched), "Expected 'templo' match"
    assert any("sagrado" in m for m in matched), "Expected 'sagrado' match"
    print("✓ Test 3: Brand taboos for 'elplacerdc' detected accurately.")

    # Test 4: Brand taboo is detected for catalinaglamur
    linter_cat = AntiSlopLinter(brand="catalinaglamur")
    cat_text = "Aprovecha este descuentazo en joyas baratas para tu boda."
    v4 = linter_cat.lint_text(cat_text)
    assert len(v4) >= 2, f"Expected at least 2 violations, got {len(v4)}"
    print("✓ Test 4: Brand taboos for 'catalinaglamur' detected accurately.")

    print("============================================================")
    print("🎉 All 4 unit tests PASSED successfully (Exit 0)!")
    return 0


def main() -> int:
    parser = argparse.ArgumentParser(description="Anti-Slop Strategic Linter & Brand Lexicon Gate")
    parser.add_argument("--file", "-f", type=Path, help="Path to file to lint (.astro, .md, .ts, etc.)")
    parser.add_argument("--text", "-t", type=str, help="Raw text string to lint")
    parser.add_argument("--brand", "-b", type=str, help="Brand identifier (elplacerdc, catalinaglamur, etc.)")
    parser.add_argument("--test", action="store_true", help="Run self-contained physical unit tests")
    parser.add_argument("--quiet", "-q", action="store_true", help="Quiet mode (exit code only)")

    args = parser.parse_args()

    if args.test:
        return run_unit_tests()

    if not args.file and not args.text:
        parser.print_help()
        return 1

    linter = AntiSlopLinter(brand=args.brand)
    violations: List[Violation] = []

    if args.file:
        violations = linter.lint_file(args.file)
    elif args.text:
        violations = linter.lint_text(args.text)

    if not violations:
        if not args.quiet:
            print(f"✅ Anti-Slop Check PASSED: Zero clichés or brand taboos detected for '{linter.brand}'.")
        return 0

    if not args.quiet:
        target_name = str(args.file) if args.file else "provided text"
        print(f"❌ Anti-Slop Violations detected in {target_name} ({len(violations)} issues found):")
        for v in violations:
            print(f"  • [Línea {v.line_number}] [{v.rule_type.upper()}] '{v.matched_text}'")
            print(f"    Snippet:    {v.snippet}")
            print(f"    Sugerencia: {v.suggestion}")
            print()

    return 1


if __name__ == "__main__":
    sys.exit(main())
