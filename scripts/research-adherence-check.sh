#!/usr/bin/env bash
# ==============================================================================
# Research Adherence & Epistemic Grounding Sensor (v1.0)
# Zero LLM Tokens | Bounded Execution < 100ms | 100% Deterministic Physical Sensor
# ==============================================================================
set -euo pipefail

ERRORS=0

echo "============================================================"
echo "  🔍 Validating Epistemic Inflow & Governance v7.8 Adherence"
echo "============================================================"

# 1. Validar 00-SUPREME-DIRECTIVE.md v7.7 / v7.8 y F0
SUPREME_FILE="/var/www/.agents/rules/00-SUPREME-DIRECTIVE.md"
if [ -f "$SUPREME_FILE" ]; then
    if grep -qE 'version: "7\.[7-8]"' "$SUPREME_FILE"; then
        echo "✓ 00-SUPREME-DIRECTIVE.md version validada (v7.7/v7.8)"
    else
        echo "❌ 00-SUPREME-DIRECTIVE.md no tiene version v7.7 o v7.8"
        ERRORS=$((ERRORS + 1))
    fi

    if grep -q "epistemic_attestation" "$SUPREME_FILE"; then
        echo "✓ Contrato <epistemic_attestation> validado en 00-SUPREME-DIRECTIVE.md"
    else
        echo "❌ Falta <epistemic_attestation> en 00-SUPREME-DIRECTIVE.md"
        ERRORS=$((ERRORS + 1))
    fi

    if grep -q "Modality A (JIT inline)" "$SUPREME_FILE" && grep -q "Modality B (subagente obligatorio)" "$SUPREME_FILE"; then
        echo "✓ Separación cuantitativa Modality A vs Modality B validada en F0"
    else
        echo "❌ Falta delimitación cuantitativa Modality A vs B en F0"
        ERRORS=$((ERRORS + 1))
    fi
else
    echo "❌ No existe $SUPREME_FILE"
    ERRORS=$((ERRORS + 1))
fi

# 2. Validar AGENTS.md v7.7 / v7.8 y enrutamiento
AGENTS_FILE="/var/www/AGENTS.md"
if [ -f "$AGENTS_FILE" ]; then
    if grep -qE "Marco Normativo Unificado \(v7\.[7-8]\)" "$AGENTS_FILE"; then
        echo "✓ AGENTS.md Gobernanza version validada (v7.7/v7.8)"
    else
        echo "❌ AGENTS.md no tiene título v7.7 o v7.8"
        ERRORS=$((ERRORS + 1))
    fi

    if grep -q "Technical inquiry, bug diagnosis" "$AGENTS_FILE"; then
        echo "✓ Fila de enrutamiento obligatorio para research en AGENTS.md validada"
    else
        echo "❌ Falta fila de enrutamiento obligatorio para research en AGENTS.md"
        ERRORS=$((ERRORS + 1))
    fi

    if grep -q "Epistemic Inflow violation" "$AGENTS_FILE"; then
        echo "✓ Smell de violación de Epistemic Inflow validado en AGENTS.md"
    else
        echo "❌ Falta smell de Epistemic Inflow en AGENTS.md"
        ERRORS=$((ERRORS + 1))
    fi
else
    echo "❌ No existe $AGENTS_FILE"
    ERRORS=$((ERRORS + 1))
fi

# 3. Validar research/SKILL.md v7.0 y Rule 7
RESEARCH_FILE="/var/www/.agents/skills/research/SKILL.md"
if [ -f "$RESEARCH_FILE" ]; then
    if grep -q 'version: "7\.0"' "$RESEARCH_FILE"; then
        echo "✓ research/SKILL.md version 7.0 validada"
    else
        echo "❌ research/SKILL.md no tiene version 7.0"
        ERRORS=$((ERRORS + 1))
    fi

    if grep -q "Rule 7 (Action-First Execution Lockdown" "$RESEARCH_FILE"; then
        echo "✓ Rule 7 (Action-First Execution Lockdown) validada en research/SKILL.md"
    else
        echo "❌ Falta Rule 7 en research/SKILL.md"
        ERRORS=$((ERRORS + 1))
    fi
else
    echo "❌ No existe $RESEARCH_FILE"
    ERRORS=$((ERRORS + 1))
fi

# 4. Validar setup-gentle.sh SSoT
SETUP_GENTLE="/var/www/baiosfera/0ZEROPS-AGY/0zcp-123/scripts/setup-gentle.sh"
if [ -f "$SETUP_GENTLE" ]; then
    if grep -qE 'version: "7\.[7-8]"' "$SETUP_GENTLE"; then
        echo "✓ Paridad SSoT de setup-gentle.sh validada (v7.7/v7.8)"
    else
        echo "❌ setup-gentle.sh no contiene v7.7 o v7.8"
        ERRORS=$((ERRORS + 1))
    fi
else
    echo "❌ No existe $SETUP_GENTLE"
    ERRORS=$((ERRORS + 1))
fi

echo "------------------------------------------------------------"
if [ "$ERRORS" -eq 0 ]; then
    echo "✅ Sensor de Adherencia Epistémica v7.8 superado exitosamente (exit code 0)."
    exit 0
else
    echo "❌ Sensor de Adherencia Epistémica detectó $ERRORS fallo(s)."
    exit 1
fi
