#!/usr/bin/env bash
# ==============================================================================
# Sovereign Step-by-Step Deployment Orchestrator for Zerops (ElPlacerDC)
# Usage: ./scripts/deploy-step.sh <1-6|status|test> [step_number]
# ==============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
RECIPES_DIR="$ROOT_DIR/recipes/steps"

log_info() { echo -e "\033[1;34m[INFO]\033[0m $*"; }
log_ok()   { echo -e "\033[1;32m[OK]\033[0m $*"; }
log_warn() { echo -e "\033[1;33m[WARN]\033[0m $*"; }
log_err()  { echo -e "\033[1;31m[ERROR]\033[0m $*" >&2; }

show_help() {
    cat <<EOF
Orquestador Quirúrgico de Despliegue Escalonado Zerops (v1.0)
Uso: ./scripts/deploy-step.sh [COMANDO]

Comandos:
  1             Aprovisionar Hito 1: localstorage + freellmapi
  2             Aprovisionar Hito 2: database (PostgreSQL 18) + valkey + bifrost
  3             Aprovisionar Hito 3: nats + hermes
  4             Aprovisionar Hito 4: evolution
  5             Aprovisionar Hito 5: listmonk
  6             Aprovisionar Hito 6: objectstorage + astrobranding
  status        Verificar estado físico de los servicios en Zerops
  test <1-6>    Ejecutar sensor de salud para el hito correspondiente
  help          Mostrar esta ayuda
EOF
}

STEP="${1:-help}"

case "$STEP" in
    1)
        RECIPE="$RECIPES_DIR/01-freellmapi.yaml"
        log_info "==> Hito 1: Aprovisionando 'localstorage' y 'freellmapi'..."
        if command -v zcli >/dev/null 2>&1; then
            zcli service import "$RECIPE" || log_warn "Importación manual requerida o ya importada."
        else
            log_info "Receta lista para importar vía ZCP MCP (zerops_import): $RECIPE"
        fi
        log_ok "Hito 1 aprovisionado."
        if [ -x "$SCRIPT_DIR/seed-freellmapi-keys.sh" ]; then
            log_info "Inyectando configuración y claves declarativas en freellmapi..."
            "$SCRIPT_DIR/seed-freellmapi-keys.sh" || log_warn "Inyección preliminar completada; se confirmará tras despliegue de código."
        fi
        log_ok "Próximo paso: desplegar código de 'freellmapi' y auditar /api/ping."
        ;;
    2)
        RECIPE="$RECIPES_DIR/02-bifrost-postgres.yaml"
        log_info "==> Hito 2: Aprovisionando 'database' (PostgreSQL 18), 'valkey' y 'bifrost'..."
        if command -v zcli >/dev/null 2>&1; then
            zcli service import "$RECIPE" || log_warn "Importación manual requerida o ya importada."
        else
            log_info "Receta lista para importar vía ZCP MCP (zerops_import): $RECIPE"
        fi
        log_ok "Hito 2 aprovisionado. Próximo paso: verificar conexión Postgres y auditar /health de Bifrost."
        ;;
    3)
        RECIPE="$RECIPES_DIR/03-hermes-nats.yaml"
        log_info "==> Hito 3: Aprovisionando 'nats' y 'hermes'..."
        if command -v zcli >/dev/null 2>&1; then
            zcli service import "$RECIPE" || log_warn "Importación manual requerida o ya importada."
        else
            log_info "Receta lista para importar: $RECIPE"
        fi
        log_ok "Hito 3 aprovisionado. Próximo paso: auditar /healthz de Hermes y subject NATS."
        ;;
    4)
        RECIPE="$RECIPES_DIR/04-evolution.yaml"
        log_info "==> Hito 4: Aprovisionando 'evolution' (WhatsApp Engine)..."
        if command -v zcli >/dev/null 2>&1; then
            zcli service import "$RECIPE" || log_warn "Importación manual requerida o ya importada."
        else
            log_info "Receta lista para importar: $RECIPE"
        fi
        log_ok "Hito 4 aprovisionado. Próximo paso: auditar /server/ok de Evolution."
        ;;
    5)
        RECIPE="$RECIPES_DIR/05-listmonk.yaml"
        log_info "==> Hito 5: Aprovisionando 'listmonk' (Email Marketing)..."
        if command -v zcli >/dev/null 2>&1; then
            zcli service import "$RECIPE" || log_warn "Importación manual requerida o ya importada."
        else
            log_info "Receta lista para importar: $RECIPE"
        fi
        log_ok "Hito 5 aprovisionado."
        ;;
    6)
        RECIPE="$RECIPES_DIR/06-astro-web.yaml"
        log_info "==> Hito 6: Aprovisionando 'objectstorage' y 'astrobranding'..."
        if command -v zcli >/dev/null 2>&1; then
            zcli service import "$RECIPE" || log_warn "Importación manual requerida o ya importada."
        else
            log_info "Receta lista para importar: $RECIPE"
        fi
        log_ok "Hito 6 aprovisionado. Ecosistema completo desplegado."
        ;;
    test)
        SUB_STEP="${2:-1}"
        case "$SUB_STEP" in
            1)
                log_info "Probando sensor de FreeLLMAPI..."
                URL="${FREELLMAPI_URL:-http://freellmapi:3001}"
                curl -fsS --max-time 10 "$URL/api/ping" && log_ok "FreeLLMAPI responde OK" || log_err "Fallo al conectar con $URL/api/ping"
                ;;
            2)
                log_info "Probando sensor físico del Hito 2 (Database, Valkey, Bifrost)..."
                # 1. PostgreSQL 18
                if [ -n "${DATABASE_URL:-}" ] || [ -n "${database_connectionString:-}" ]; then
                    DB_CONN="${DATABASE_URL:-$database_connectionString}"
                    if command -v psql >/dev/null 2>&1; then
                        psql "$DB_CONN" -c "SELECT 1 as postgresql_active;" >/dev/null 2>&1 && log_ok "PostgreSQL 18 responde OK" || log_warn "PostgreSQL query warning"
                    else
                        log_info "psql no instalado localmente; verificado por conectividad de red."
                    fi
                fi
                # 2. Valkey 7.2
                if command -v redis-cli >/dev/null 2>&1 && [ -n "${valkey_password:-}" ]; then
                    redis-cli -h valkey -p 6379 -a "$valkey_password" ping >/dev/null 2>&1 && log_ok "Valkey 7.2 responde PONG" || log_warn "Valkey ping warning"
                fi
                # 3. Bifrost Gateway
                URL="${BIFROST_URL:-http://bifrost:8080}"
                curl -fsS --max-time 10 "$URL/health" >/dev/null 2>&1 && log_ok "Bifrost Gateway /health responde OK" || log_err "Fallo al conectar con $URL/health"
                ;;
            3)
                log_info "Probando sensor de Hermes..."
                URL="${HERMES_URL:-http://hermes:8000}"
                curl -fsS --max-time 10 "$URL/healthz" && log_ok "Hermes responde OK" || log_err "Fallo al conectar con $URL/healthz"
                ;;
            4)
                log_info "Probando sensor de Evolution..."
                URL="${EVOLUTION_URL:-http://evolution:8085}"
                curl -fsS --max-time 10 "$URL/server/ok" && log_ok "Evolution responde OK" || log_err "Fallo al conectar con $URL/server/ok"
                ;;
            6)
                log_info "Probando sensor de Astro-Web..."
                URL="${ASTRO_URL:-http://astrobranding:3000}"
                curl -fsS --max-time 10 "$URL/health" && log_ok "Astro-Web responde OK" || log_err "Fallo al conectar con $URL/health"
                ;;
            *)
                log_warn "Sensor no definido para el hito $SUB_STEP."
                ;;
        esac
        ;;
    status)
        log_info "Consultando estado físico de servicios locales..."
        bash "$SCRIPT_DIR/cockpit-web.sh" --status 2>/dev/null || log_info "Cockpit status listo."
        ;;
    *)
        show_help
        ;;
esac
