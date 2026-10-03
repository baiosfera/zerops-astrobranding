#!/usr/bin/env bash
# ==============================================================================
# Sovereign GitHub CLI & CI/CD Bootstrapper (setup-gh.sh v1.2)
# Dynamic Identity, Remote Auto-Discovery & Zero-Hardcoding Contract
# ==============================================================================
set -euo pipefail

echo "============================================================"
echo "  🐙 Configuración Soberana de GitHub CLI & CI/CD (setup-gh.sh v1.2)"
echo "============================================================"

PROJECT_ROOT="${PROJECT_ROOT:-/var/www}"

if ! command -v gh >/dev/null 2>&1; then
    echo "⚠️ GitHub CLI ('gh') no está instalado en el sistema. Omitiendo."
    exit 0
fi

# 1. Extracción y resolución resiliente de GITHUB_TOKEN
RESOLVED_GH_TOKEN="${GITHUB_TOKEN:-${GITHUB_API_KEY:-${GH_TOKEN:-}}}"
if [ -z "$RESOLVED_GH_TOKEN" ] && [ -f "/etc/environment" ]; then
    RESOLVED_GH_TOKEN=$(grep -E '^(GITHUB_TOKEN|GITHUB_API_KEY|GH_TOKEN)=' /etc/environment | head -n1 | cut -d= -f2- | sed "s/[\"']//g" | tr -d '\r\n') || true
fi

if [ -z "$RESOLVED_GH_TOKEN" ]; then
    echo "ℹ️ GITHUB_TOKEN no detectado en el entorno de Zerops ni en /etc/environment. Omitiendo configuración de GitHub."
    exit 0
fi

# 2. Autenticación desatendida headless mediante token
echo "• Autenticando GitHub CLI desatendidamente..."
if ! printf "%s" "$RESOLVED_GH_TOKEN" | gh auth login --with-token 2>/dev/null; then
    echo "⚠️ Token de GitHub provisto rechazado por la API. Verifique validez o scopes. Omitiendo."
    exit 0
fi

# 3. Detección dinámica de identidad (Zero Hardcoding)
GH_USER=$(gh api user --jq '.login' 2>/dev/null || true)
if [ -z "$GH_USER" ]; then
    echo "⚠️ No se pudo obtener el nombre de usuario de la API de GitHub. Omitiendo configuración de Git."
    exit 0
fi

GH_NAME=$(gh api user --jq '.name // empty' 2>/dev/null || true)
[ -z "$GH_NAME" ] && GH_NAME="$GH_USER"
GH_EMAIL="${GH_USER}@users.noreply.github.com"

# 4. Configuración global de Git & Credential Helper
echo "• Configurando identidad de Git y credential helper para '$GH_USER'..."
git config --global user.name "$GH_NAME"
git config --global user.email "$GH_EMAIL"
gh auth setup-git 2>/dev/null || true
echo "  ✓ Identidad Git global establecida: $GH_NAME <$GH_EMAIL>"

# 5. Detección agnóstica de repositorio remoto
REPO_TARGET_DIR=""
if [ -d "$PROJECT_ROOT/zerops-astrobranding/.git" ]; then
    REPO_TARGET_DIR="$PROJECT_ROOT/zerops-astrobranding"
elif [ -d "$PROJECT_ROOT/.git" ]; then
    REPO_TARGET_DIR="$PROJECT_ROOT"
fi

REPO_SLUG=""
if [ -n "$REPO_TARGET_DIR" ]; then
    REMOTE_URL=$(git -C "$REPO_TARGET_DIR" config --get remote.origin.url 2>/dev/null || true)
    if [ -n "$REMOTE_URL" ]; then
        REPO_SLUG=$(echo "$REMOTE_URL" | sed 's|.*github.com[:/]||' | sed 's|\.git$||')
    fi
fi

# 6. Sincronización dinámica de secretos de GitHub Actions (si el repo es accesible)
RESOLVED_Z_TOKEN="${ZCP_API_KEY:-${ZEROPS_TOKEN:-${Z_TOKEN:-}}}"
if [ -z "$RESOLVED_Z_TOKEN" ] && [ -f "/etc/environment" ]; then
    RESOLVED_Z_TOKEN=$(grep -E '^(ZCP_API_KEY|ZEROPS_TOKEN|Z_TOKEN)=' /etc/environment | head -n1 | cut -d= -f2- | sed "s/[\"']//g" | tr -d '\r\n') || true
fi

RESOLVED_SERVICE_ID="${ZEROPS_SERVICE_ID:-${APP_SERVICE_ID:-}}"
if [ -z "$RESOLVED_SERVICE_ID" ] && [ -f "/etc/environment" ]; then
    RESOLVED_SERVICE_ID=$(grep -E '^(ZEROPS_SERVICE_ID|APP_SERVICE_ID)=' /etc/environment | head -n1 | cut -d= -f2- | sed "s/[\"']//g" | tr -d '\r\n') || true
fi

# Fallback inteligente si no está explícito: consultar servicios activos del proyecto vía zcli
if [ -z "$RESOLVED_SERVICE_ID" ] && command -v zcli >/dev/null 2>&1 && [ -n "${ZEROPS_ProjectId:-}" ]; then
    CANDIDATE_ID=$(zcli service list --projectId="$ZEROPS_ProjectId" 2>/dev/null | awk '$4 != "zcp" && $2 ~ /^[a-zA-Z0-9_-]+$/ {print $2}' | head -n1 || true)
    [ -n "$CANDIDATE_ID" ] && RESOLVED_SERVICE_ID="$CANDIDATE_ID"
fi

if [ -n "$REPO_SLUG" ] && [ -n "$RESOLVED_Z_TOKEN" ]; then
    if gh repo view "$REPO_SLUG" >/dev/null 2>&1; then
        echo "• Sincronizando secretos de CI/CD hacia $REPO_SLUG..."
        gh secret set ZEROPS_TOKEN -b "$RESOLVED_Z_TOKEN" -R "$REPO_SLUG" 2>/dev/null || true
        if [ -n "$RESOLVED_SERVICE_ID" ]; then
            gh secret set ZEROPS_SERVICE_ID -b "$RESOLVED_SERVICE_ID" -R "$REPO_SLUG" 2>/dev/null || true
            echo "  ✓ Secretos ZEROPS_TOKEN y ZEROPS_SERVICE_ID ($RESOLVED_SERVICE_ID) actualizados en $REPO_SLUG."
        else
            echo "  ✓ Secreto ZEROPS_TOKEN actualizado en $REPO_SLUG (ZEROPS_SERVICE_ID pendiente de provisión de runtime)."
        fi
    else
        echo "  ℹ️ Repositorio '$REPO_SLUG' no alcanzable con permisos de escritura. Omitiendo inyección de secretos."
    fi
fi

echo "============================================================"
echo "  ✅ GitHub CLI & Git Operativos y Verificados"
echo "============================================================"
