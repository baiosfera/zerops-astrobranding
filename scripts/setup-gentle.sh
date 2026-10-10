#!/usr/bin/env bash
# ==============================================================================
# Sovereign Gentle AI, Engram & GGA Bootstrapper (setup-gentle.sh)
## Version: 8.2 (Upstream Skills Sync & Native Hooks Standard)
# ==============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ZCP_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
TARGET_AGENT="${1:-antigravity}"
PROJECT_ROOT="/var/www"
PERSISTENT_BIN="/var/www/baiosfera/0ZEROPS-AGY/0zcp-123/scripts"

echo "============================================================"
echo "  [2/7] Despliegue Gentle AI, Engram & GGA (v8.2 - SSoT)"
echo "============================================================"

# 1. Asegurar directorios canónicos y jerarquía de respaldos bak/
echo "• Verificando directorios de gobernanza y respaldo centralizado..."
mkdir -p "$PROJECT_ROOT/.agents/rules" "$PROJECT_ROOT/.agents/skills" "$PROJECT_ROOT/.agents/references" 2>/dev/null || true
mkdir -p "$ZCP_ROOT/bak/scripts" "$ZCP_ROOT/bak/rules" "$ZCP_ROOT/bak/skills" "$ZCP_ROOT/bak/apis" "$ZCP_ROOT/bak/mcp" 2>/dev/null || true

# 2. Desplegar e Instalar Binarios de Gobernanza (engram, gga, gentle-ai, inject-agent-rule)
mkdir -p "$PROJECT_ROOT/.bin" "$HOME/.local/bin" "/home/zerops/.local/bin" 2>/dev/null || true

# 2a. Descarga y aprovisionamiento autónomo de Engram si no existe localmente
if [ ! -f "$SCRIPT_DIR/engram" ] && [ ! -f "$PROJECT_ROOT/.bin/engram" ]; then
    echo "• Descargando binario oficial de Engram desde GitHub Releases..."
    ENGRAM_ARCH="linux_amd64"
    [ "$(uname -m)" = "aarch64" ] && ENGRAM_ARCH="linux_arm64"
    TMP_ENGRAM="$(mktemp -d 2>/dev/null || mktemp -d -t 'engram_dl.XXXXXX')"
    if curl -sSL "https://github.com/Gentleman-Programming/engram/releases/download/v1.20.0/engram_1.20.0_${ENGRAM_ARCH}.tar.gz" -o "$TMP_ENGRAM/engram.tar.gz" 2>/dev/null; then
        tar -xzf "$TMP_ENGRAM/engram.tar.gz" -C "$TMP_ENGRAM" 2>/dev/null || true
        if [ -f "$TMP_ENGRAM/engram" ]; then
            cp "$TMP_ENGRAM/engram" "$PROJECT_ROOT/.bin/engram"
            cp "$TMP_ENGRAM/engram" "$SCRIPT_DIR/engram" 2>/dev/null || true
            chmod +x "$PROJECT_ROOT/.bin/engram"
            echo "  ✓ Engram instalado con éxito desde GitHub Releases."
        fi
    fi
    rm -rf "$TMP_ENGRAM" 2>/dev/null || true
fi

# 2b. Descarga y aprovisionamiento autónomo de GGA y sus librerías
mkdir -p "$SCRIPT_DIR/lib/gga" "$PROJECT_ROOT/.bin/lib/gga" "/home/zerops/.local/share/gga/lib" "$HOME/.local/share/gga/lib" 2>/dev/null || true
if [ ! -f "$SCRIPT_DIR/gga" ] || [ ! -f "$SCRIPT_DIR/lib/gga/providers.sh" ] || [ ! -f "$SCRIPT_DIR/lib/gga/cache.sh" ] || [ ! -f "$SCRIPT_DIR/lib/gga/pr_mode.sh" ]; then
    echo "• Descargando GGA y librerías completas desde GitHub oficial..."
    TMP_GGA="$(mktemp -d 2>/dev/null || mktemp -d -t 'gga_dl.XXXXXX')"
    if timeout 15s git clone --depth 1 https://github.com/Gentleman-Programming/gentleman-guardian-angel.git "$TMP_GGA/gga" >/dev/null 2>&1; then
        bash "$TMP_GGA/gga/install.sh" >/dev/null 2>&1 || true
        [ -f "$HOME/.local/bin/gga" ] && cp "$HOME/.local/bin/gga" "$SCRIPT_DIR/gga" 2>/dev/null || true
        [ -f "$TMP_GGA/gga/bin/gga" ] && cp "$TMP_GGA/gga/bin/gga" "$SCRIPT_DIR/gga" 2>/dev/null || true
        [ -d "$TMP_GGA/gga/lib" ] && cp "$TMP_GGA/gga/lib/"*.sh "$SCRIPT_DIR/lib/gga/" 2>/dev/null || true
        echo "  ✓ GGA y librerías descargadas con éxito desde GitHub oficial."
    fi
    rm -rf "$TMP_GGA" 2>/dev/null || true
fi

# 2c. Descarga y aprovisionamiento autónomo de Gentle-AI CLI si no existe localmente
GAI_ARCH="linux_amd64"
[ "$(uname -m)" = "aarch64" ] && GAI_ARCH="linux_arm64"
GAI_LATEST=$(curl -sSL "https://api.github.com/repos/Gentleman-Programming/gentle-ai/releases/latest" 2>/dev/null | grep '"tag_name":' | sed -E 's/.*"([^"]+)".*/\1/' || echo "v4.0.0")
[ -z "$GAI_LATEST" ] && GAI_LATEST="v4.0.0"
GAI_VER="${GAI_LATEST#v}"

NEED_GAI_DL=false
if [ ! -f "$SCRIPT_DIR/gentle-ai" ] || [ ! -f "$PROJECT_ROOT/.bin/gentle-ai" ]; then
    NEED_GAI_DL=true
else
    CURRENT_VER=$("$PROJECT_ROOT/.bin/gentle-ai" --version 2>/dev/null | awk '{print $2}' || echo "0.0.0")
    if [ "$CURRENT_VER" != "$GAI_VER" ]; then
        NEED_GAI_DL=true
    fi
fi

if [ "$NEED_GAI_DL" = true ]; then
    echo "• Descargando binario oficial de Gentle-AI CLI ($GAI_LATEST) desde GitHub Releases..."
    TMP_GAI="$(mktemp -d 2>/dev/null || mktemp -d -t 'gai_dl.XXXXXX')"
    if curl -sSL "https://github.com/Gentleman-Programming/gentle-ai/releases/download/${GAI_LATEST}/gentle-ai_${GAI_VER}_${GAI_ARCH}.tar.gz" -o "$TMP_GAI/gentle-ai.tar.gz" 2>/dev/null; then
        tar -xzf "$TMP_GAI/gentle-ai.tar.gz" -C "$TMP_GAI" 2>/dev/null || true
        if [ -f "$TMP_GAI/gentle-ai" ]; then
            cp "$TMP_GAI/gentle-ai" "$PROJECT_ROOT/.bin/gentle-ai"
            cp "$TMP_GAI/gentle-ai" "$SCRIPT_DIR/gentle-ai" 2>/dev/null || true
            chmod +x "$PROJECT_ROOT/.bin/gentle-ai" "$SCRIPT_DIR/gentle-ai" 2>/dev/null || true
            sudo ln -sf "$PROJECT_ROOT/.bin/gentle-ai" "/usr/local/bin/gentle-ai" 2>/dev/null || true
            echo "  ✓ Gentle-AI CLI $GAI_LATEST instalado con éxito desde GitHub Releases."
        fi
    fi
    rm -rf "$TMP_GAI" 2>/dev/null || true
fi

# 2d. Aprovisionamiento autónomo de inject-agent-rule desde SSoT
if [ -f "$SCRIPT_DIR/inject-agent-rule" ]; then
    cp -f "$SCRIPT_DIR/inject-agent-rule" "$PROJECT_ROOT/.bin/inject-agent-rule"
    chmod +x "$PROJECT_ROOT/.bin/inject-agent-rule"
    sudo ln -sf "$PROJECT_ROOT/.bin/inject-agent-rule" "/usr/local/bin/inject-agent-rule" 2>/dev/null || true
    echo "  ✓ inject-agent-rule desplegado desde SSoT."
fi

for b in "engram" "gga" "gentle-ai" "inject-agent-rule"; do
    if [ -f "$SCRIPT_DIR/$b" ]; then
        cp "$SCRIPT_DIR/$b" "$PROJECT_ROOT/.bin/$b" 2>/dev/null || true
        chmod +x "$PROJECT_ROOT/.bin/$b" 2>/dev/null || true
        sudo ln -sf "$PROJECT_ROOT/.bin/$b" "/usr/local/bin/$b" 2>/dev/null || true
        rm -f "/home/zerops/.local/bin/$b" "$HOME/.local/bin/$b" 2>/dev/null || true
    fi
done

# Aprovisionar librerías de GGA en ubicaciones canónicas
if [ -d "$SCRIPT_DIR/lib/gga" ]; then
    mkdir -p "$PROJECT_ROOT/.bin/lib/gga" "/home/zerops/.local/share/gga/lib" "$HOME/.local/share/gga/lib" 2>/dev/null || true
    sudo mkdir -p /usr/local/lib 2>/dev/null || true
    cp -r "$SCRIPT_DIR/lib/gga/"*.sh "$PROJECT_ROOT/.bin/lib/gga/" 2>/dev/null || true
    cp -r "$SCRIPT_DIR/lib/gga/"*.sh "/home/zerops/.local/share/gga/lib/" 2>/dev/null || true
    cp -r "$SCRIPT_DIR/lib/gga/"*.sh "$HOME/.local/share/gga/lib/" 2>/dev/null || true
    sudo cp -r "$SCRIPT_DIR/lib/gga/"*.sh /usr/local/lib/ 2>/dev/null || true
    chmod +x "$PROJECT_ROOT/.bin/lib/gga/"*.sh "/home/zerops/.local/share/gga/lib/"*.sh "$HOME/.local/share/gga/lib/"*.sh 2>/dev/null || true
fi

sudo chown -R zerops:zerops "$PROJECT_ROOT/.bin" "/home/zerops/.local/bin" "/home/zerops/.local/share/gga" 2>/dev/null || true

# 2b. Instalación y Sincronización de Skills EN VIVO desde Upstream Oficial (Gentleman-Programming)
echo "• Sincronizando e instalando skills EN VIVO desde repositorios oficiales de Gentleman-Programming..."
TMP_SKILLS_DIR="$(mktemp -d 2>/dev/null || mktemp -d -t 'gentle_skills.XXXXXX')"

# 1. SDD Suite & Canonical ATL Skills (Upstream Oficial)
if timeout 15s git clone --depth 1 https://github.com/Gentleman-Programming/agent-teams-lite.git "$TMP_SKILLS_DIR/atl" >/dev/null 2>&1; then
    echo "  ✓ Upstream ATL/SDD skills descargadas con éxito."
    [ -d "$TMP_SKILLS_DIR/atl/skills" ] && cp -R "$TMP_SKILLS_DIR/atl/skills/"* "$PROJECT_ROOT/.agents/skills/" 2>/dev/null || true
else
    echo "  ⚠️ No se pudo clonar agent-teams-lite (usando SSoT local)."
fi

# 2. Gentle-AI Core Skills (Upstream Oficial)
if timeout 15s git clone --depth 1 https://github.com/Gentleman-Programming/gentle-ai.git "$TMP_SKILLS_DIR/gentle-ai" >/dev/null 2>&1; then
    echo "  ✓ Upstream Gentle-AI Core skills descargadas con éxito."
    if [ -d "$TMP_SKILLS_DIR/gentle-ai/internal/assets/skills" ]; then
        cp -R "$TMP_SKILLS_DIR/gentle-ai/internal/assets/skills/"* "$PROJECT_ROOT/.agents/skills/" 2>/dev/null || true
        # Aislamiento por Agente: Antigravity opera con invoke_subagent, no delegate_task (exclusivo de Hermes)
        if [ "$TARGET_AGENT" = "antigravity" ]; then
            rm -rf "$PROJECT_ROOT/.agents/skills/hermes-ephemeral-delegation" 2>/dev/null || true
        fi
    fi
    [ -d "$TMP_SKILLS_DIR/gentle-ai/skills" ] && cp -R "$TMP_SKILLS_DIR/gentle-ai/skills/"* "$PROJECT_ROOT/.agents/skills/" 2>/dev/null || true
else
    echo "  ⚠️ No se pudo clonar gentle-ai (usando SSoT local)."
fi

# 3. Gentleman-Skills Curated (Upstream Oficial - Ecosistema Curado)
if timeout 15s git clone --depth 1 https://github.com/Gentleman-Programming/Gentleman-Skills.git "$TMP_SKILLS_DIR/skills" >/dev/null 2>&1; then
    echo "  ✓ Upstream Gentleman-Skills (Curated) descargadas con éxito."
    [ -d "$TMP_SKILLS_DIR/skills/curated" ] && cp -R "$TMP_SKILLS_DIR/skills/curated/"* "$PROJECT_ROOT/.agents/skills/" 2>/dev/null || true
    # Omitimos community/ para evitar inyectar skills experimentales o ajenas al stack (ej: hexagonal-java, elixir)
else
    echo "  ⚠️ No se pudo clonar Gentleman-Skills (usando SSoT local)."
fi

# 4. Matt Pocock Skills (Upstream Oficial - TypeScript & Testing Mastery)
if timeout 15s git clone --depth 1 https://github.com/mattpocock/skills.git "$TMP_SKILLS_DIR/mp-skills" >/dev/null 2>&1; then
    echo "  ✓ Upstream mattpocock/skills descargadas con éxito."
    # Descartar deterministamente la skill research de Matt Pocock para blindar el motor soberano de 12 motores
    rm -rf "$TMP_SKILLS_DIR/mp-skills/skills/research" "$TMP_SKILLS_DIR/mp-skills/skills/engineering/research" 2>/dev/null || true
    for cat_dir in "$TMP_SKILLS_DIR/mp-skills/skills"/*/; do
        if [ -d "$cat_dir" ]; then
            for sk in "$cat_dir"/*/; do
                if [ -d "$sk" ] && [ -f "$sk/SKILL.md" ]; then
                    sk_name=$(basename "$sk")
                    if [ "$sk_name" != "research" ]; then
                        cp -R "$sk" "$PROJECT_ROOT/.agents/skills/" 2>/dev/null || true
                    fi
                fi
            done
        fi
    done
else
    echo "  ⚠️ No se pudo clonar mattpocock/skills (usando SSoT local)."
fi

rm -rf "$TMP_SKILLS_DIR" 2>/dev/null || true

# Replicación Universal de Skills hacia el perfil global de Antigravity CLI
echo "• Sincronizando catálogo completo de skills hacia perfil de Antigravity..."
mkdir -p "/home/zerops/.gemini/antigravity-cli/skills" 2>/dev/null || true
if [ -d "$PROJECT_ROOT/.agents/skills" ]; then
    cp -rn "$PROJECT_ROOT/.agents/skills/"* "/home/zerops/.gemini/antigravity-cli/skills/" 2>/dev/null || true
fi

# 3. Inicializar Hooks de GGA, Configurar Agente y Compilar Skill Registry
if command -v gga >/dev/null 2>&1; then
    if gga version >/dev/null 2>&1; then
        echo "  ✓ GGA verificado físicamente y 100% operativo ($(gga version))."
    else
        echo "  ⚠️ Advertencia: gga CLI instalado pero falló al verificar versión." >&2
    fi
    echo "• Instalando hooks de integridad GGA en el workspace..."
    if [ -d "$PROJECT_ROOT/.git" ]; then
        gga install "$PROJECT_ROOT" 2>/dev/null || true
    else
        echo "  ℹ️ Saltando gga install: $PROJECT_ROOT no es un repositorio git inicializado."
    fi
fi

if command -v gentle-ai >/dev/null 2>&1; then
    echo "• Configurando stack de Gentle AI para el agente: $TARGET_AGENT..."
    CI=true GENTLE_NO_UPDATE_PROMPT=1 gentle-ai install --agents "$TARGET_AGENT" --scope=global 2>/dev/null || true
    echo "• Compilando registro de skills (.atl/skill-registry.md)..."
    gentle-ai skill-registry refresh --force 2>/dev/null || true
    echo "• Verificando salud del ecosistema Gentle AI..."
    gentle-ai doctor || true

    # 3b. Optimización de Prompt Prefix en GEMINI.md (Dual-RAG JIT Mode)
    if [ -f "/home/zerops/.gemini/GEMINI.md" ]; then
        echo "• Optimizando GEMINI.md (Offloading sdd-orchestrator a Dual-RAG JIT)..."
        python3 - << 'EOF_OPT'
import os

gemini_path = "/home/zerops/.gemini/GEMINI.md"
dest_local = "/home/zerops/.gemini/antigravity-cli/skills/_shared/sdd-orchestrator-full.md"
dest_drive = "/var/www/baiosfera/0ZEROPS-AGY/0zcp-123/references/sdd-orchestrator-full.md"

if os.path.isfile(gemini_path):
    with open(gemini_path, "r", encoding="utf-8") as f:
        content = f.read()

    start_marker = "<!-- gentle-ai:sdd-orchestrator -->"
    end_marker = "<!-- /gentle-ai:sdd-orchestrator -->"

    start_idx = content.find(start_marker)
    end_idx = content.find(end_marker)

    if start_idx != -1 and end_idx != -1 and (end_idx - start_idx) > 1000:
        extracted = content[start_idx:end_idx + len(end_marker)]
        os.makedirs(os.path.dirname(dest_local), exist_ok=True)
        with open(dest_local, "w", encoding="utf-8") as f:
            f.write(extracted)
        os.makedirs(os.path.dirname(dest_drive), exist_ok=True)
        with open(dest_drive, "w", encoding="utf-8") as f:
            f.write(extracted)

        replacement = """<!-- gentle-ai:sdd-orchestrator -->
## Agent Teams Lite — Orchestrator (Dual-RAG JIT Mode)

Spec-Driven Development (SDD) orchestrator protocol is offloaded to conserve token budget.
When the user requests an SDD change, phase agent delegation, or Agent Teams workflow, read:
file:///home/zerops/.gemini/antigravity-cli/skills/_shared/sdd-orchestrator-full.md
<!-- /gentle-ai:sdd-orchestrator -->"""
        new_content = content[:start_idx] + replacement + content[end_idx + len(end_marker):]
        with open(gemini_path, "w", encoding="utf-8") as f:
            f.write(new_content)
        print("  ✓ GEMINI.md optimizado: sdd-orchestrator offloaded a Dual-RAG JIT (-11.000 tokens).")
EOF_OPT
    fi
fi

INJECT_CMD="inject-agent-rule"

# 4. Inyectar Protocolos de Gobernanza en AGENTS.md
echo "• Inyectando protocolos de gobernanza en AGENTS.md (Lean Mode)..."
    
    mkdir -p "$PROJECT_ROOT/.agents/references"
    if [ -f "$ZCP_ROOT/.agents/references/gentle_governance_encyclopedia.md" ]; then
        cp -f "$ZCP_ROOT/.agents/references/gentle_governance_encyclopedia.md" "$PROJECT_ROOT/.agents/references/gentle_governance_encyclopedia.md"
    fi

    # Sincronización atómica de AGENTS.md desde Google Drive SSoT (o fallback canónico)
    if [ -f "$ZCP_ROOT/AGENTS.md" ]; then
        cp -f "$ZCP_ROOT/AGENTS.md" "$PROJECT_ROOT/AGENTS.md"
    fi

# 5. Sincronizar Supreme Directive y Referencias desde Google Drive SSoT
echo "• Sincronizando Supreme Directive y Referencias desde SSoT..."
mkdir -p "$PROJECT_ROOT/.agents/rules" "$PROJECT_ROOT/.agents/references" "$ZCP_ROOT/.agents/references" 2>/dev/null || true

if [ -f "$ZCP_ROOT/.agents/rules/00-SUPREME-DIRECTIVE.md" ]; then
    cp -f "$ZCP_ROOT/.agents/rules/00-SUPREME-DIRECTIVE.md" "$PROJECT_ROOT/.agents/rules/00-SUPREME-DIRECTIVE.md"
fi
if [ -d "$ZCP_ROOT/.agents/references" ]; then
    cp -f "$ZCP_ROOT/.agents/references/"*.md "$PROJECT_ROOT/.agents/references/" 2>/dev/null || true
fi

# Sincronizar con perfil global Antigravity
if [ -d "$HOME/.gemini/antigravity-cli" ]; then
    mkdir -p "$HOME/.gemini/antigravity-cli/rules" "$HOME/.gemini/antigravity-cli/references" 2>/dev/null || true
    cp -f "$PROJECT_ROOT/.agents/rules/00-SUPREME-DIRECTIVE.md" "$HOME/.gemini/antigravity-cli/rules/00-SUPREME-DIRECTIVE.md" 2>/dev/null || true
    cp -f "$PROJECT_ROOT/.agents/references/"*_encyclopedia.md "$HOME/.gemini/antigravity-cli/references/" 2>/dev/null || true
fi
if [ -d "$HOME/.gemini/config" ] && [ -f "$ZCP_ROOT/.agents/hooks.json" ]; then
    cp -f "$ZCP_ROOT/.agents/hooks.json" "$HOME/.gemini/config/hooks.json" 2>/dev/null || true
fi

# 6. Configuración Idempotente de Exclusiones de File Watchers en Code-Server / VS Code
echo "• Configurando exclusiones dinámicas de observadores de archivos (VS Code / Code-Server)..."
python3 -c "
import os, json

shared_dirs = []
if os.path.exists('/mnt'):
    for d in os.listdir('/mnt'):
        if d != 'lost+found' and os.path.isdir(os.path.join('/mnt', d)):
            shared_dirs.append(d)

base_watcher = {
    '**/mnt/**': True,
    '**/baiosfera/**': True,
    '**/.rclone/**': True,
    '**/.git/objects/**': True,
    '**/.git/subtree-cache/**': True,
    '**/node_modules/**': True,
    '**/.cache/**': True,
    '**/tmp/**': True
}

base_search = {
    '**/mnt/**': True,
    '**/baiosfera/**': True,
    '**/.rclone/**': True,
    '**/node_modules/**': True
}

for sdir in shared_dirs:
    base_watcher[f'**/{sdir}/**'] = True
    base_search[f'**/{sdir}/**'] = True

targets = [
    '/home/zerops/.local/share/code-server/User/settings.json',
    '/var/www/.vscode/settings.json'
]

for target in targets:
    os.makedirs(os.path.dirname(target), exist_ok=True)
    data = {}
    if os.path.exists(target):
        try:
            with open(target, 'r') as f:
                data = json.load(f)
        except Exception:
            data = {}
    
    current_we = data.get('files.watcherExclude', {})
    current_we.update(base_watcher)
    data['files.watcherExclude'] = current_we
    
    current_se = data.get('search.exclude', {})
    current_se.update(base_search)
    data['search.exclude'] = current_se
    
    data['terminal.integrated.persistentSessionReviveProcess'] = 'onExitAndWindowClose'
    data['terminal.integrated.persistentSessionScrollback'] = 10000
    data['remote.autoForwardPorts'] = False
    
    with open(target, 'w') as f:
        json.dump(data, f, indent=2)

if os.path.exists('/home/zerops'):
    os.system('chown -R zerops:zerops /home/zerops/.local/share/code-server /var/www/.vscode 2>/dev/null || true')
"

# 7. Despliegue de Hooks de Ciclo de Vida Nativos de Antigravity (hooks.json & tool-guard.py)
echo "• Desplegando arnés físico de interceptores y guardianes de ciclo de vida (hooks.json)..."
mkdir -p "$PROJECT_ROOT/.bin/hooks" "$PROJECT_ROOT/.agents" "$ZCP_ROOT/scripts/hooks" 2>/dev/null || true
if [ -f "$SCRIPT_DIR/hooks/tool-guard.py" ]; then
    cp -f "$SCRIPT_DIR/hooks/tool-guard.py" "$PROJECT_ROOT/.bin/hooks/tool-guard.py"
    chmod +x "$PROJECT_ROOT/.bin/hooks/tool-guard.py"
fi

if [ -f "$ZCP_ROOT/.agents/hooks.json" ]; then
    cp -f "$ZCP_ROOT/.agents/hooks.json" "$PROJECT_ROOT/.agents/hooks.json"
fi

# Desplegar meta-sensores globales y guardianes de arquitectura
if [ -f "$PROJECT_ROOT/.agents/skills/docu/scripts/docu-validate.sh" ]; then
    chmod +x "$PROJECT_ROOT/.agents/skills/docu/scripts/docu-validate.sh"
    ln -sf "$PROJECT_ROOT/.agents/skills/docu/scripts/docu-validate.sh" "$PROJECT_ROOT/.bin/docu-validate" 2>/dev/null || true
    sudo ln -sf "$PROJECT_ROOT/.agents/skills/docu/scripts/docu-validate.sh" /usr/local/bin/docu-validate 2>/dev/null || true
fi
if [ -f "$PROJECT_ROOT/.agents/skills/research/scripts/research-validate.sh" ]; then
    chmod +x "$PROJECT_ROOT/.agents/skills/research/scripts/research-validate.sh"
    ln -sf "$PROJECT_ROOT/.agents/skills/research/scripts/research-validate.sh" "$PROJECT_ROOT/.bin/research-validate" 2>/dev/null || true
    sudo ln -sf "$PROJECT_ROOT/.agents/skills/research/scripts/research-validate.sh" /usr/local/bin/research-validate 2>/dev/null || true
fi
# Desplegar astrobranding-check incondicionalmente (Arnés Resiliente Anti-Fallo en ZCP limpio)
if [ -f "$SCRIPT_DIR/astrobranding-check.sh" ]; then
    cp -f "$SCRIPT_DIR/astrobranding-check.sh" "$PROJECT_ROOT/.bin/astrobranding-check"
    chmod +x "$PROJECT_ROOT/.bin/astrobranding-check" 2>/dev/null || true
    sudo ln -sf "$PROJECT_ROOT/.bin/astrobranding-check" /usr/local/bin/astrobranding-check 2>/dev/null || true
fi

echo "  ✅ Despliegue de Gentle AI, Engram & Supreme Directive v7.9 completado con éxito."
chmod +x "$PROJECT_ROOT/.agents/rules/00-SUPREME-DIRECTIVE.md" 2>/dev/null || true
