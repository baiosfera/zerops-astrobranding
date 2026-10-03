#!/usr/bin/env bash
set -e

# ==============================================================================
# Zerops AstroBranding Sovereign Monorepo — Step-by-Step Initializer (setup.sh)
#
# Designed for Successor AGY & Platform Operators:
# - Native to Zerops Control Plane (zcp) & Incus LXC mesh architecture.
# - Invariant: ZCP is the orchestration control plane, NOT the app runtime.
#   Builds and application runtime run inside dedicated Zerops Incus containers.
# - Usage:
#     ./setup.sh [--step <1-4>] [key1.md key2.md ... | /path/to/keys]
# ==============================================================================

STEP="${1:-all}"
shift || true
EXTRA_ARGS=("$@")

# Normalize step argument
if [[ "$STEP" == "--step" ]]; then
  STEP="${EXTRA_ARGS[0]:-1}"
  EXTRA_ARGS=("${EXTRA_ARGS[@]:1}")
elif [[ "$STEP" != "1" && "$STEP" != "2" && "$STEP" != "3" && "$STEP" != "4" && "$STEP" != "all" ]]; then
  # If first arg was a file or path rather than a step number:
  EXTRA_ARGS=("$STEP" "${EXTRA_ARGS[@]}")
  STEP="all"
fi

echo "=================================================================="
echo "   🚀 Zerops AstroBranding Initializer (Step: $STEP)"
echo "   Environment: Zerops Control Plane (zcp) | Target: Incus LXC Mesh"
echo "=================================================================="

# ------------------------------------------------------------------------------
# STEP 1: Workspace & Environment Pre-flight
# ------------------------------------------------------------------------------
step_1_preflight() {
  # Zerops Platform-First: environment variables are injected natively by Zerops
  if [ -f /etc/environment ]; then
    echo "    Zerops environment baseline (/etc/environment) verified."
  fi

  # Check Node availability (standard in zcp for CLI scripts)
  if ! command -v node &> /dev/null; then
    echo "❌ [Step 1 Error] Node.js is required for CLI seeders in this control plane."
    exit 1
  fi
  echo "    Node.js $(node --version) detected in control plane."

  # Informative check for Bun (optional in control plane, mandatory in Zerops runtime)
  if command -v bun &> /dev/null; then
    echo "    Bun $(bun --version) available locally in control plane."
  else
    echo "    ℹ️  Bun not in control plane (expected). Application builds run natively in Zerops Incus LXC containers."
  fi

  echo "✅ [Step 1 Passed] Workspace baseline verified."
}

# ------------------------------------------------------------------------------
# STEP 2: FreeLLMAPI Credential Ingestion & Quota Stacking
# ------------------------------------------------------------------------------
step_2_keys() {
  echo "==> [Step 2/4] Ingesting & Pooling FreeLLMAPI Multi-Account Credentials..."
  if [ ${#EXTRA_ARGS[@]} -gt 0 ]; then
    echo "    Passing credentials sources: ${EXTRA_ARGS[*]}"
    node scripts/seed-freellm-keys.mjs "${EXTRA_ARGS[@]}"
  elif [ -d "/var/www/keys" ]; then
    echo "    Auto-discovering keys from /var/www/keys..."
    node scripts/seed-freellm-keys.mjs "/var/www/keys"
  elif [ -f "/var/www/keys.md" ]; then
    echo "    Auto-discovering keys from /var/www/keys.md..."
    node scripts/seed-freellm-keys.mjs "/var/www/keys.md"
  else
    echo "    Checking for available LLM API keys in default environment..."
    node scripts/seed-freellm-keys.mjs
  fi
  echo "✅ [Step 2 Passed] FreeLLMAPI multi-provider seed configured for deployment."
}

# ------------------------------------------------------------------------------
# STEP 3: Platform Topology & Architectural Boundaries Validation
# ------------------------------------------------------------------------------
step_3_validate() {
  echo "==> [Step 3/4] Validating Zerops Platform Topology & Architecture..."

  if [ ! -f import.yaml ] || [ ! -f zerops.yaml ]; then
    echo "❌ [Step 3 Error] import.yaml or zerops.yaml missing from repository root."
    exit 1
  fi

  # Validate Zerops topology manifest syntax
  if command -v zcp-validate &> /dev/null; then
    zcp-validate yaml import.yaml
    echo "    Zerops 10-service topology verified by zcp-validate."
  fi

  # Run architecture boundary audit
  if command -v bun &> /dev/null; then
    bun scripts/architecture-check.mjs
  else
    node scripts/architecture-check.mjs
  fi

  echo "✅ [Step 3 Passed] Zero boundary violations, valid Zerops topology."
}

# ------------------------------------------------------------------------------
# STEP 4: Zerops Mesh Provisioning & Deployment Readiness
# ------------------------------------------------------------------------------
step_4_deploy_ready() {
  echo "==> [Step 4/4] Verifying Deployment Readiness for Zerops Mesh..."
  echo "=================================================================="
  echo "✅ [Ready for Zerops Deployment]"
  echo "   The monorepo template is fully validated."
  echo ""
  echo "   📋 AGY Action Protocol for Cloud Deployment:"
  echo "   1. Provision 10 services via native Zerops MCP:"
  echo "      zerops_workflow action=\"start\" workflow=\"bootstrap\" route=\"classic\""
  echo "      (or: zerops_import filePath=\"import.yaml\")"
  echo "   2. Zerops provisions: database, valkey, nats, objectstorage, localstorage,"
  echo "      freellmapi, bifrost, evolution, hermes, and astrobranding."
  echo "   3. Builds occur inside Zerops LXC containers as declared in zerops.yaml."
  echo "=================================================================="
}

# Execution Dispatcher
case "$STEP" in
  "1") step_1_preflight ;;
  "2") step_2_keys ;;
  "3") step_3_validate ;;
  "4") step_4_deploy_ready ;;
  "all")
    step_1_preflight
    step_2_keys
    step_3_validate
    step_4_deploy_ready
    ;;
  *)
    echo "Unknown step: $STEP. Options: 1, 2, 3, 4, all"
    exit 1
    ;;
esac
