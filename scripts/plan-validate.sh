#!/usr/bin/env bash
# ==============================================================================
# Deterministic Physical Plan Linter & Validation Sensor (plan-validate.sh)
# Version: 2.5 (Blindaje Anti-Freeze FUSE & 4 Tracks)
# Zero LLM Tokens | Bounded Execution < 100ms | 100% Deterministic
# ==============================================================================
set -euo pipefail
export PYTHONDONTWRITEBYTECODE=1

SCRIPT_DIR="$(dirname "${BASH_SOURCE[0]}")"
trap 'rm -rf "$SCRIPT_DIR/__pycache__" "$SCRIPT_DIR"/*.pyc 2>/dev/null || true' EXIT

PLAN_PATH="${1:-}"

if [ -z "$PLAN_PATH" ]; then
    echo "Usage: plan-validate <path-to-plan.md>"
    exit 1
fi

if [ ! -f "$PLAN_PATH" ]; then
    echo "❌ Error: El archivo de plan no existe en: $PLAN_PATH"
    exit 1
fi

if [ ! -s "$PLAN_PATH" ]; then
    echo "❌ Error: El archivo de plan está vacío: $PLAN_PATH"
    exit 1
fi

PLAN_NAME="$(basename "$PLAN_PATH")"
ERRORS=0

echo "============================================================"
echo "  🔍 Validating Plan Integrity: [$PLAN_NAME]"
echo "============================================================"

# 0. Regla 3 de Planner: Versionamiento Inmutable (_vN)
if [[ "$PLAN_NAME" =~ _v[0-9]+([_\.][0-9]+)* ]]; then
    echo "✓ Versionamiento inmutable canónico validado en nombre de archivo (_vN)"
else
    echo "❌ Violación de Regla 3 de Planner: El nombre del plan [$PLAN_NAME] no incluye versionamiento canónico (_vN, ej: _v1.md, _v2.md, _v7_1.md)"
    ERRORS=$((ERRORS + 1))
fi

# 0.1 Regla 3 de Planner: Invariante de Unicidad Activa en Raíz (plan-archive)
DIR_OF_PLAN="$(dirname "$(realpath "$PLAN_PATH" 2>/dev/null || echo "$PLAN_PATH")")"
ARTIFACTS_ROOT="$(realpath "/var/www/artifacts" 2>/dev/null || echo "/var/www/artifacts")"

if [ "$DIR_OF_PLAN" == "$ARTIFACTS_ROOT" ]; then
    STEM=$(echo "$PLAN_NAME" | sed -E 's/_v[0-9]+.*$//')
    SUPERSEDED_FOUND=0
    for sibling in "$ARTIFACTS_ROOT"/${STEM}_v*.md; do
        [ -e "$sibling" ] || continue
        SIBLING_NAME="$(basename "$sibling")"
        if [ "$SIBLING_NAME" != "$PLAN_NAME" ]; then
            echo "❌ Violación de Invariante de Raíz Limpia: Se detectó versión obsoleta coexistiendo en la raíz de artifacts: $SIBLING_NAME"
            echo "   Ejecuta 'plan-archive' para trasladar versiones superseded a archive/."
            SUPERSEDED_FOUND=$((SUPERSEDED_FOUND + 1))
            ERRORS=$((ERRORS + 1))
        fi
    done
    if [ "$SUPERSEDED_FOUND" -eq 0 ]; then
        echo "✓ Unicidad de plan activo en raíz de artifacts validada (cero versiones obsoletas coexistentes)"
    fi
fi

# 1. Cabecera y Marco de Gobernanza
if grep -qi "Marco de Gobernanza" "$PLAN_PATH" && grep -qi "Supreme Directive" "$PLAN_PATH" && grep -qi "Planner" "$PLAN_PATH"; then
    echo "✓ Marco de gobernanza canónico validado en cabecera"
else
    echo "❌ Falta marco de gobernanza canónico (Supreme Directive, Planner) en cabecera"
    ERRORS=$((ERRORS + 1))
fi

# 2. Declaración de Track
IS_TRACK_A=0
IS_TRACK_B=0
IS_TRACK_C=0
IS_TRACK_D=0

if grep -qiE "Track A" "$PLAN_PATH"; then
    IS_TRACK_A=1
    echo "✓ Clasificación de Track validada: Track A (Gobernanza, Skills & Platform Tooling)"
elif grep -qiE "Track B" "$PLAN_PATH"; then
    IS_TRACK_B=1
    echo "✓ Clasificación de Track validada: Track B (Chasis Central Zerops Astrobranding)"
elif grep -qiE "Track C" "$PLAN_PATH"; then
    IS_TRACK_C=1
    echo "✓ Clasificación de Track validada: Track C (Workloads & Apps con Plantilla Universal v4)"
elif grep -qiE "Track D" "$PLAN_PATH"; then
    IS_TRACK_D=1
    echo "✓ Clasificación de Track validada: Track D (Direct SSoT Data & Content Ops)"
else
    echo "❌ Falta declaración explícita de Track (Track A, Track B, Track C o Track D)"
    ERRORS=$((ERRORS + 1))
fi

# 3. Sección 1: Diagnóstico y Grounding
if grep -q "## 1. Diagnóstico" "$PLAN_PATH"; then
    echo "✓ Sección 1 (Diagnóstico & Grounding) presente"
else
    echo "❌ Falta Sección 1 (Diagnóstico & Grounding)"
    ERRORS=$((ERRORS + 1))
fi

# 4. Sección 2: Topología de Máquina de Estados
if grep -q "## 2. Topología" "$PLAN_PATH"; then
    echo "✓ Sección 2 (Topología de Estados CoHaLo) presente"
else
    echo "❌ Falta Sección 2 (Topología de Estados CoHaLo)"
    ERRORS=$((ERRORS + 1))
fi

# 5. Sección 3: Invariantes y Reglas No Negociables
if grep -q "## 3. Invariantes" "$PLAN_PATH"; then
    echo "✓ Sección 3 (Invariantes y Reglas No Negociables) presente"
else
    echo "❌ Falta Sección 3 (Invariantes y Reglas No Negociables)"
    ERRORS=$((ERRORS + 1))
fi

# 6. Sección 4: Nodos / Pasos de Ejecución
if grep -q "## 4. Plan de Ejecución" "$PLAN_PATH"; then
    echo "✓ Sección 4 (Plan de Ejecución) presente"
    SECTION_4_TEXT=$(sed -n '/## 4\. Plan de Ejecución/,/## 5/p' "$PLAN_PATH")
    if [ "$IS_TRACK_A" -eq 1 ]; then
        # 6.1 Bucle Canónico de 8 Nodos en Sección 4 (Regla 5 de Planner para Track A)
        MISSING_NODES=0
        for i in {1..8}; do
            if echo "$SECTION_4_TEXT" | grep -qiE "(Nodo $i|Paso $i)"; then
                continue
            else
                echo "❌ Violación de Regla 5 de Planner: Falta el Nodo $i (o Paso $i) en Sección 4 para Track A"
                MISSING_NODES=$((MISSING_NODES + 1))
                ERRORS=$((ERRORS + 1))
            fi
        done
        if [ "$MISSING_NODES" -eq 0 ]; then
            echo "✓ Topología cerrada de 8 Nodos canónicos (N1 a N8) validada en Sección 4 (Track A)"
        fi
    else
        # Para Track B y Track C: validar pasos/hitos modulares (mínimo 2 pasos o secciones)
        STEP_COUNT=$(echo "$SECTION_4_TEXT" | grep -ciE "(###|Paso|Nodo|Fase|Hito)" || true)
        if [ "$STEP_COUNT" -ge 2 ]; then
            echo "✓ Estructura de ejecución modular validada en Sección 4 ($STEP_COUNT pasos/hitos detectados)"
        else
            echo "❌ Sección 4 carece de pasos o hitos de ejecución suficientes (mínimo 2 requeridos)"
            ERRORS=$((ERRORS + 1))
        fi
    fi
else
    echo "❌ Falta Sección 4 (Plan de Ejecución)"
    ERRORS=$((ERRORS + 1))
fi

# 6.2 Prohibición Estricta de Backups Monolíticos de Repositorios (Universal)
if grep -qiE '(cp\s+-[a-zA-Z]*r[a-zA-Z]*\s+[^[:space:]]*(\.git|/var/www/[a-zA-Z0-9_-]+)\s+.*bak|bak/(repos?|monorepos?)/|bak/[a-zA-Z0-9_-]+_repo)' "$PLAN_PATH"; then
    echo "❌ Violación de Soberanía Git: Prohibido respaldar repositorios enteros hacia carpetas .bak. El control de versiones y rollback de código es nativo de Git/GitHub."
    ERRORS=$((ERRORS + 1))
else
    echo "✓ Cero respaldos monolíticos de repositorios en el plan (Soberanía Git validada)"
fi

# 7. Regla 2 de Planner: Respaldo Pre-Mutación Versionado y Fechado (Obligatorio en Track A, Exento en Track B/C)
if [ "$IS_TRACK_A" -eq 1 ]; then
    if grep -qiE "(Nodo 1|Paso 1).*Backup" "$PLAN_PATH"; then
        # Verificar que no contenga .bak sin versión ni fecha
        if grep -qE '\.bak([[:space:]]|$|/|`|\*)' "$PLAN_PATH"; then
            UNVERSIONED_BAKS=$(grep -oE '[a-zA-Z0-9_\.\-\$\(\)\+%:~]+(\.bak|\.bak/)' "$PLAN_PATH" | grep -vE '(_v[0-9]|\$|date|_202[0-9]|%Y|%m|\+|[0-9]{8}_[0-9]{6}|_bak|\.bak/)' || true)
            if [ -n "$UNVERSIONED_BAKS" ]; then
                echo "❌ Violación de Regla 2 de Planner: Se detectaron respaldos .bak planos sin versionamiento semántico (_v) ni fecha:"
                echo "$UNVERSIONED_BAKS" | while read -r line; do echo "    - $line"; done
                ERRORS=$((ERRORS + 1))
            else
                echo "✓ Respaldos pre-mutación cumplen sintaxis versionada y fechada (Regla 2)"
            fi
        else
            echo "✓ Respaldos pre-mutación formalizados con nomenclatura canónica"
        fi

        # 7.1 Cross-Validation Semántica: Skills mutadas en Sección 4 vs Respaldos en Nodo 1
        SKILL_CHECK_OUTPUT=$(python3 -c '
import re, os, sys

plan_path = sys.argv[1]
try:
    with open(plan_path, "r", encoding="utf-8") as f:
        text = f.read()
except Exception:
    sys.exit(0)

s4_match = re.search(r"## 4\. Plan de Ejecución.*?(?=## 5)", text, re.DOTALL)
s4_text = s4_match.group(0) if s4_match else ""

n1_match = re.search(r"### 🔹 Nodo 1.*?(?=### 🔹 Nodo 2)", s4_text, re.DOTALL)
n1_text = n1_match.group(0) if n1_match else ""

skills_dir = "/var/www/.agents/skills"
if not os.path.isdir(skills_dir):
    sys.exit(0)

skills = [d for d in os.listdir(skills_dir) if os.path.isdir(os.path.join(skills_dir, d)) and not d.startswith(".")]

errors = 0
for sk in skills:
    pattern = r"(\.agents/skills/" + re.escape(sk) + r"\b|skills/" + re.escape(sk) + r"\b|skill\s+" + re.escape(sk) + r"\b)"
    if re.search(pattern, s4_text, re.IGNORECASE):
        has_bak = ("bak/skills/" + sk) in n1_text
        if not has_bak:
            print(f"❌ Infracción Track A: El plan modifica la skill \x27{sk}\x27 en Nodo 4, pero NO declara su respaldo en bak/skills/{sk} en Nodo 1")
            errors += 1
        else:
            print(f"✓ Respaldo pre-mutación de skill \x27{sk}\x27 verificado en Nodo 1")

sys.exit(errors)
' "$PLAN_PATH" 2>&1)
        SKILL_CHECK_STATUS=$?
        if [ "$SKILL_CHECK_STATUS" -ne 0 ]; then
            echo "$SKILL_CHECK_OUTPUT"
            ERRORS=$((ERRORS + SKILL_CHECK_STATUS))
        else
            if [ -n "$SKILL_CHECK_OUTPUT" ]; then
                echo "$SKILL_CHECK_OUTPUT"
            fi
        fi
    else
        echo "❌ Falta declaración explícita de Nodo/Paso 1 de Respaldos Pre-Mutación (N1) para Track A"
        ERRORS=$((ERRORS + 1))
    fi
else
    echo "✓ Track B/C: Exención de respaldo pre-mutación en bak/ validada (versionado nativo Git / Drive SSoT)"
fi

# 8. SSoT Indivisibility & unisetup.sh Mapping (Obligatorio en Track A)
if [ "$IS_TRACK_A" -eq 1 ]; then
    if grep -qiE "(unisetup|0zcp-123/scripts|0zcp-123)" "$PLAN_PATH"; then
        echo "✓ Mapeo SSoT a unisetup.sh y Google Drive validado para Track A"
    else
        echo "❌ Violación SSoT: Los planes de Track A deben contemplar sincronización hacia unisetup.sh y Google Drive"
        ERRORS=$((ERRORS + 1))
    fi

    # 8.1 Track A: Paridad con repositorio soberano zerops-astro-skills
    if grep -qiE "(zerops-astro-skills|git push)" "$PLAN_PATH"; then
        echo "✓ Paridad con repositorio soberano zerops-astro-skills validada para Track A"
    else
        echo "❌ Violación de Paridad Git: Los planes de Track A deben contemplar sincronización y git push hacia zerops-astro-skills"
        ERRORS=$((ERRORS + 1))
    fi
else
    echo "✓ Track B/C: Mapeo de SSoT desacoplado a su entorno correspondiente"
fi

# 9. Sección 5: Matriz de Control de Atestación
if grep -q "## 5.*Matriz de Control" "$PLAN_PATH"; then
    if grep -qiE "(exit code 0|exit 0|HTTP 200|200 OK|exitcode 0)" "$PLAN_PATH"; then
        echo "✓ Sección 5 (Matriz de Control con sensores de atestación física) presente"
        SECTION_5_TEXT=$(sed -n '/## 5.*Matriz de Control/,/## 6/p' "$PLAN_PATH")

        # 9.0 Veto Reality Over Checklist Theater: Prohibido usar exclusivamente 'test -f' en la matriz
        if echo "$SECTION_5_TEXT" | grep -qiE "\|\s*test\s+-f\s+"; then
            echo "❌ Violación Reality Over Checklist Theater: Prohibido usar verificaciones cosméticas 'test -f' en la Matriz de Control; use compiladores AST (py_compile), sintaxis (bash -n), o aserciones de software"
            ERRORS=$((ERRORS + 1))
        fi
        if [ "$IS_TRACK_A" -eq 1 ]; then
            # 9.1 Atestación de los 8 Nodos en Matriz de Control (Track A)
            MISSING_MATRIX_NODES=0
            for i in {1..8}; do
                if echo "$SECTION_5_TEXT" | grep -qiE "(\\\$N_$i\\\$|Nodo $i|Paso $i|N$i\b)"; then
                    continue
                else
                    echo "❌ Falta fila de control para el Nodo $i (N$i) en Matriz de Control (Sección 5) para Track A"
                    MISSING_MATRIX_NODES=$((MISSING_MATRIX_NODES + 1))
                    ERRORS=$((ERRORS + 1))
                fi
            done
            if [ "$MISSING_MATRIX_NODES" -eq 0 ]; then
                echo "✓ Matriz de Control atestigua formalmente los 8 Nodos canónicos (N1 a N8) para Track A"
            fi
        else
            # Para Track B y Track C: validar que contenga tabla Markdown estructurada
            if echo "$SECTION_5_TEXT" | grep -qiE "(\|.*\|.*\|)"; then
                echo "✓ Matriz de Control estructurada en tabla Markdown validada (Track B/C)"
            else
                echo "❌ La Matriz de Control debe contener una tabla estructurada de criterios de aceptación"
                ERRORS=$((ERRORS + 1))
            fi
        fi
    else
        echo "❌ La Matriz de Control no especifica sensores deterministas (exit 0 / HTTP 200)"
        ERRORS=$((ERRORS + 1))
    fi
else
    echo "❌ Falta Sección 5 (Matriz de Control y Criterios de Aceptación)"
    ERRORS=$((ERRORS + 1))
fi

# 10. Auto-Purge & LTM Persistencia
if grep -qi "Auto-Purge" "$PLAN_PATH" && grep -qi "mem_save" "$PLAN_PATH"; then
    echo "✓ Protocolo de Auto-Purge y persistencia en Engram validado"
else
    echo "❌ El plan no define Auto-Purge ni persistencia obligatoria en Engram (mem_save)"
    ERRORS=$((ERRORS + 1))
fi

# 11. Universal Clean-Room Virgin ZCP & Cross-Account Parity (Track A)
if grep -q "Track A" "$PLAN_PATH"; then
    if grep -qiE "(virgen|clean-room|cross-account|cuentas diferentes|proyectos virgenes|cero absoluto)" "$PLAN_PATH"; then
        echo "✓ Contrato de Contenedor Virgen Multi-Cuenta validado para Track A"
    else
        echo "❌ Violación de Regla 4 de Planner: Los planes de Track A deben explicitar el estándar de Contenedor Virgen Multi-Cuenta (0 drift en proyectos limpios)"
        ERRORS=$((ERRORS + 1))
    fi
fi

# 12. Regla de Correspondencia Operativa de Skills Gobernantes & Dúo Inseparable (governance_contracts.md Sec 4)
echo "• Validando correspondencia operativa de skills declaradas (Anti-Compliance Theater)..."
HEADER=$(sed -n '1,/## 1/p' "$PLAN_PATH")

# 12.1 Dúo Inseparable - Entrada: Research (Anti-AMN)
if grep -q "<epistemic_attestation>" "$PLAN_PATH"; then
    echo "  ✓ Research: Recibo formal <epistemic_attestation> validado en Sección 1 (Centinela de Inflow)"
else
    echo "  ❌ Research: Falta recibo formal <epistemic_attestation> en Sección 1 (Anti-AMN)"
    ERRORS=$((ERRORS + 1))
fi

# 12.2 Dúo Inseparable - Salida: Skill-Improver (Zero-Deletion Invariant en Track A)
if grep -q "Track A" "$PLAN_PATH"; then
    if echo "$HEADER" | grep -qi "Skill-Improver"; then
        echo "  ✓ Skill-Improver: Declarada en cabecera para Track A (Centinela de Preservación)"
    else
        echo "  ❌ Violación de Dúo Inseparable: Planes de Track A deben declarar Skill-Improver como Centinela de Preservación"
        ERRORS=$((ERRORS + 1))
    fi
    if grep -qiE "(zero deletion|cero eliminación|no-mutilación|sin pérdida|preservación de flags)" "$PLAN_PATH"; then
        echo "  ✓ Skill-Improver: Invariante de Cero Eliminación / No-Mutilación validado en texto"
    else
        echo "  ❌ Skill-Improver: Falta compromiso explícito de Cero Eliminación / No-Mutilación en el cuerpo del plan"
        ERRORS=$((ERRORS + 1))
    fi
    if sed -n '/## 5.*Matriz de Control/,/## 6/p' "$PLAN_PATH" | grep -qiE "(zero deletion|cero eliminación|no-mutilación|mutilación|preservación|zero-mutilation)"; then
        echo "  ✓ Skill-Improver: Sensor físico de preservación presente en Matriz de Control (Sección 5)"
    else
        echo "  ❌ Skill-Improver: Falta fila de sensor físico de preservación en Matriz de Control (Sección 5)"
        ERRORS=$((ERRORS + 1))
    fi
elif echo "$HEADER" | grep -qi "Skill-Improver"; then
    if sed -n '/## 5.*Matriz de Control/,/## 6/p' "$PLAN_PATH" | grep -qiE "(zero deletion|cero eliminación|no-mutilación|mutilación|preservación|zero-mutilation)"; then
        echo "  ✓ Skill-Improver: Sensor físico de preservación presente en Matriz de Control (Sección 5)"
    else
        echo "  ❌ Skill-Improver declarada en cabecera pero falta fila de sensor físico en Matriz de Control (Sección 5)"
        ERRORS=$((ERRORS + 1))
    fi
fi

# 12.3 Skills Especializadas JIT declaradas en Cabecera (Prohibición de Membrete Cosmético sin Sensor Físico)
if echo "$HEADER" | grep -qi "Docu"; then
    if sed -n '/## 5.*Matriz de Control/,/## 6/p' "$PLAN_PATH" | grep -qiE "(docu-validate|docu_validate|docu.*sensor|docu.*exit 0)"; then
        echo "  ✓ Docu: Sensor físico determinista validado en Matriz de Control (Sección 5)"
    else
        echo "  ❌ Violación Anti-Teatro: 'Docu' declarada en cabecera pero NO cuenta con sensor físico ejecutable en Matriz de Control (Sección 5)"
        ERRORS=$((ERRORS + 1))
    fi
fi

if echo "$HEADER" | grep -qi "CoHaLo"; then
    if sed -n '/## 5.*Matriz de Control/,/## 6/p' "$PLAN_PATH" | grep -qiE "(cohalo-validate|cohalo_validate|cohalo.*sensor|cohalo.*exit 0|harness.*exit 0)"; then
        echo "  ✓ CoHaLo: Sensor físico determinista validado en Matriz de Control (Sección 5)"
    else
        echo "  ❌ Violación Anti-Teatro: 'CoHaLo' declarada en cabecera pero NO cuenta con sensor físico ejecutable en Matriz de Control (Sección 5)"
        ERRORS=$((ERRORS + 1))
    fi
fi

# 13. Radar 360° de Daño Colateral y Riesgos Ocultos (Pre-Audit Obligatorio - Mandato 14)
if grep -qiE "## 6.*(Radar 360|Daño Colateral|Riesgos Ocultos)" "$PLAN_PATH"; then
    if grep -qiE "(aguas arriba|downstream|upstream|causa raíz|pipelines)" "$PLAN_PATH"; then
        echo "✓ Sección 6 (Radar 360° de Daño Colateral & Pre-Audit) presente y fundamentada"
    else
        echo "❌ Sección 6 presente pero carece de análisis de impacto sistémico (aguas arriba/abajo, pipelines)"
        ERRORS=$((ERRORS + 1))
    fi
else
    echo "❌ Falta Sección 6 obligatoria: Radar 360° de Daño Colateral y Riesgos Ocultos (Mandato 14)"
    ERRORS=$((ERRORS + 1))
fi

# 14. Epistemic Surplus & Fracturas Periféricas (Mandato 14)
if grep -qiE "## 7.*(Epistemic Surplus|Fracturas Ocultas|Deuda Técnica)" "$PLAN_PATH"; then
    echo "✓ Sección 7 (Epistemic Surplus: Fracturas Ocultas & Deuda Técnica en la Periferia) presente"
else
    echo "❌ Falta Sección 7 obligatoria: Epistemic Surplus & Detección de Fracturas Periféricas"
    ERRORS=$((ERRORS + 1))
fi

# 15. Veto Técnico y Alternativas Arquitectónicas (Anti-Complacencia)
if grep -qiE "## 8.*(Veto Técnico|Alternativas Arquitectónicas)" "$PLAN_PATH"; then
    echo "✓ Sección 8 (Veto Técnico y Alternativas Arquitectónicas) presente"
else
    echo "❌ Falta Sección 8 obligatoria: Veto Técnico y Alternativas Arquitectónicas"
    ERRORS=$((ERRORS + 1))
fi

echo "------------------------------------------------------------"
if [ "$ERRORS" -eq 0 ]; then
    echo "✅ Plan [$PLAN_NAME] validado deterministamente (exit code 0)."
    exit 0
else
    echo "❌ Plan [$PLAN_NAME] rechazado con $ERRORS infracción(es) contractuales."
    exit 1
fi
