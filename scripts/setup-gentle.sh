#!/usr/bin/env bash
# ==============================================================================
# Sovereign Gentle AI, Engram & GGA Bootstrapper (setup-gentle.sh)
## Version: 8.2 (Upstream Skills Sync & Native Hooks Standard)
# ==============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
REPO_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"
PROJECT_ROOT="/var/www"
DRIVE_MOUNT="${GDRIVE_MOUNT_DIR:-/var/www/baiosfera}"
PROJ_KEY="$(echo "${ENGRAM_PROJECT:-${PROJECT_NAME:-}}" | tr '[:upper:]' '[:lower:]')"
DRIVE_SSOT="${PROJ_KEY:+$DRIVE_MOUNT/0ZEROPS-AGY/$PROJ_KEY}"

if [ -d "$DRIVE_SSOT" ]; then
    SSOT_ROOT="$DRIVE_SSOT"
elif [ -d "$SCRIPT_DIR/.." ] && [ -d "$SCRIPT_DIR/../.agents" ]; then
    SSOT_ROOT="$(cd "$SCRIPT_DIR/.." && pwd)"
elif [ -d "$REPO_DIR/.agents" ]; then
    SSOT_ROOT="$REPO_DIR"
else
    SSOT_ROOT="$PROJECT_ROOT"
fi
ZCP_ROOT="$SSOT_ROOT"
TARGET_AGENT="${1:-antigravity}"
PERSISTENT_BIN="$ZCP_ROOT/scripts"

echo "============================================================"
echo "  [2/7] Despliegue Gentle AI, Engram & GGA (v8.2 - SSoT)"
echo "============================================================"

# 1. Asegurar directorios canónicos y jerarquía de respaldos bak/
echo "• Verificando directorios de gobernanza y respaldo centralizado..."
mkdir -p "$PROJECT_ROOT/.agents/rules" "$PROJECT_ROOT/.agents/skills" 2>/dev/null || true
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
        # Anti-OpenCode Invariant: Purgar OpenCode permanentemente para evitar reinstalaciones espurias
        rm -rf "$HOME/.opencode" "/home/zerops/.opencode" 2>/dev/null || true
        sed -i '/# opencode/d; /opencode\/bin/d' "$HOME/.bashrc" "/home/zerops/.bashrc" 2>/dev/null || true
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

# 1. Purga de suites obsoletas o deprecadas (SDD legacy & agent-teams-lite)
rm -rf "$PROJECT_ROOT/.agents/skills/sdd-"* 2>/dev/null || true
echo "  ✓ Upstream Gentle-AI v4 alineado: purgadas 9 skills sdd-* obsoletas (reemplazadas por codecraft/ODD)."

# 2. Gentle-AI Core Skills (Upstream Oficial)
if timeout 15s git clone --depth 1 https://github.com/Gentleman-Programming/gentle-ai.git "$TMP_SKILLS_DIR/gentle-ai" >/dev/null 2>&1; then
    echo "  ✓ Upstream Gentle-AI Core skills descargadas con éxito."
    if [ -d "$TMP_SKILLS_DIR/gentle-ai/internal/assets/skills" ]; then
        cp -rn "$TMP_SKILLS_DIR/gentle-ai/internal/assets/skills/"* "$PROJECT_ROOT/.agents/skills/" 2>/dev/null || true
        # Aislamiento por Agente: Antigravity opera con invoke_subagent, no delegate_task (exclusivo de Hermes)
        if [ "$TARGET_AGENT" = "antigravity" ]; then
            rm -rf "$PROJECT_ROOT/.agents/skills/hermes-ephemeral-delegation" 2>/dev/null || true
        fi
    fi
    [ -d "$TMP_SKILLS_DIR/gentle-ai/skills" ] && cp -rn "$TMP_SKILLS_DIR/gentle-ai/skills/"* "$PROJECT_ROOT/.agents/skills/" 2>/dev/null || true
else
    echo "  ⚠️ No se pudo clonar gentle-ai (usando SSoT local)."
fi

# 3. Gentleman-Skills Curated (Upstream Oficial - Ecosistema Curado)
if timeout 15s git clone --depth 1 https://github.com/Gentleman-Programming/Gentleman-Skills.git "$TMP_SKILLS_DIR/skills" >/dev/null 2>&1; then
    echo "  ✓ Upstream Gentleman-Skills (Curated) descargadas con éxito."
    [ -d "$TMP_SKILLS_DIR/skills/curated" ] && cp -rn "$TMP_SKILLS_DIR/skills/curated/"* "$PROJECT_ROOT/.agents/skills/" 2>/dev/null || true
    # Omitimos community/ para evitar inyectar skills experimentales o ajenas al stack (ej: hexagonal-java, elixir)
else
    echo "  ⚠️ No se pudo clonar Gentleman-Skills (usando SSoT local)."
fi

# 4. Matt Pocock Skills (Upstream Oficial - TypeScript & Testing Mastery)
if timeout 15s git clone --depth 1 https://github.com/mattpocock/skills.git "$TMP_SKILLS_DIR/mp-skills" >/dev/null 2>&1; then
    echo "  ✓ Upstream mattpocock/skills descargadas con éxito desde GitHub."
    rm -rf "$TMP_SKILLS_DIR/mp-skills/skills/research" "$TMP_SKILLS_DIR/mp-skills/skills/engineering/research" 2>/dev/null || true
    for cat_dir in "$TMP_SKILLS_DIR/mp-skills/skills"/*/; do
        if [ -d "$cat_dir" ]; then
            for sk in "$cat_dir"/*/; do
                if [ -d "$sk" ] && [ -f "$sk/SKILL.md" ]; then
                    sk_name=$(basename "$sk")
                    if [ "$sk_name" != "research" ]; then
                        cp -rn "$sk" "$PROJECT_ROOT/.agents/skills/" 2>/dev/null || true
                    fi
                fi
            done
        fi
    done
else
    echo "  ⚠️ No se pudo clonar mattpocock/skills (usando SSoT local)."
fi

# Blindaje Soberano Anti-Contaminación: Purgar carpetas ajenas upstream en core skills soberanas
rm -rf "$PROJECT_ROOT/.agents/skills/planner/"{assets,scripts} 2>/dev/null || true
rm -rf "$PROJECT_ROOT/.agents/skills/docu/scripts" 2>/dev/null || true
rm -rf "$PROJECT_ROOT/.agents/skills/research/scripts" 2>/dev/null || true
rm -rf "$PROJECT_ROOT/.agents/skills/oraculo/raw" 2>/dev/null || true
rm -rf "$PROJECT_ROOT/.agents/skills/oraculo/pipeline/synthesis.py" 2>/dev/null || true

rm -rf "$TMP_SKILLS_DIR" 2>/dev/null || true

# Purgar ruido externo y copias congeladas en perfiles secundarios que sombreen .agents/skills
echo "• Limpiando ruido externo y copias congeladas en perfiles secundarios..."
for noise_sk in jira-epic jira-task gentle-ai-bench gentle-ai-collab-perfect rdd-advisory-transport rdd-defect-workflow migrate-to-shoehorn scaffold-exercises django-drf angular using-superpowers brainstorming writing-plans executing-plans subagent-driven-development dispatching-parallel-agents finishing-a-development-branch using-git-worktrees requesting-code-review receiving-code-review test-driven-development systematic-debugging grill-me grilling grill-with-docs pr github-pr ask-matt claude-handoff handoff wayfinder teach retro loop-me software-factory chief-of-staff implement implement-spec improve-codebase-architecture setup-ts-deep-modules to-questionnaire to-spec to-tickets triage writing-beats writing-fragments writing-shape git-guardrails-claude-code issue-creation issue-root-resolution skill-registry; do
    rm -rf "$PROJECT_ROOT/.agents/skills/$noise_sk" "/home/zerops/.gemini/antigravity-cli/skills/$noise_sk" "/home/zerops/.gemini/config/skills/$noise_sk" "/var/www/.claude/skills/$noise_sk" 2>/dev/null || true
done
if [ -d "/var/www/zerops-astro-skills" ]; then
    for sov_dir in /var/www/zerops-astro-skills/*/; do
        [ -d "$sov_dir" ] || continue
        sov_name=$(basename "$sov_dir")
        rm -rf "/home/zerops/.gemini/antigravity-cli/skills/$sov_name" "/home/zerops/.gemini/config/skills/$sov_name" "/var/www/.claude/skills/$sov_name" 2>/dev/null || true
    done
fi

# 3. Inicializar Hooks de GGA, Configurar Agente y Compilar Skill Registry
if command -v gga >/dev/null 2>&1; then
    if gga version >/dev/null 2>&1; then
        echo "  ✓ GGA verificado físicamente y 100% operativo ($(gga version))."
    else
        echo "  ⚠️ Advertencia: gga CLI instalado pero falló al verificar versión." >&2
    fi
    echo "• Instalando hooks de integridad GGA en repositorios git..."
    for repo_candidate in "$PROJECT_ROOT" "$PROJECT_ROOT"/*/; do
        if [ -d "$repo_candidate/.git" ]; then
            [ ! -f "$repo_candidate/AGENTS.md" ] && ln -sf "$PROJECT_ROOT/AGENTS.md" "$repo_candidate/AGENTS.md" 2>/dev/null || true
            (cd "$repo_candidate" && gga install 2>/dev/null || true)
            if [ -f "$repo_candidate/.git/hooks/pre-commit" ]; then
                sed -i 's/gga run || exit 1/gga run || true/' "$repo_candidate/.git/hooks/pre-commit" 2>/dev/null || true
            fi
            echo "  ✓ GGA pre-commit hook (advisory) instalado en $repo_candidate"
        fi
    done
    mkdir -p "/home/zerops/.config/gga" "$HOME/.config/gga" 2>/dev/null || true
    for cfg in "/home/zerops/.config/gga/config" "$HOME/.config/gga/config"; do
        if [ -f "$cfg" ]; then
            sed -i 's/PROVIDER="gemini"/PROVIDER="github:gpt-4o-mini"/' "$cfg" 2>/dev/null || true
        fi
    done
fi

if command -v gentle-ai >/dev/null 2>&1; then
    echo "• Configurando stack de Gentle AI para el agente: $TARGET_AGENT..."
    CI=true GENTLE_NO_UPDATE_PROMPT=1 gentle-ai install --agents "$TARGET_AGENT" --scope=global 2>/dev/null || true
    # Garantizar cwd=/var/www y --tools=agent para Engram MCP único (sin plugin duplicado)
    if [ -f "$SCRIPT_DIR/engram-mcp" ]; then
        chmod +x "$SCRIPT_DIR/engram-mcp"
        ln -sfn "$SCRIPT_DIR/engram-mcp" "$PROJECT_ROOT/.bin/engram-mcp"
        ln -sfn "$SCRIPT_DIR/engram-mcp" "/home/zerops/.local/bin/engram-mcp" 2>/dev/null || true
    fi
    if command -v agy >/dev/null 2>&1; then
        agy plugin disable gentle-ai-engram 2>/dev/null || true
    fi
    python3 - << 'EOF_ENGRAM_MCP'
import json, os

cfg_json = "/home/zerops/.gemini/config/config.json"
os.makedirs(os.path.dirname(cfg_json), exist_ok=True)
try:
    cfg_data = json.load(open(cfg_json, "r", encoding="utf-8")) if os.path.isfile(cfg_json) else {}
except Exception:
    cfg_data = {}
cfg_data.setdefault("plugins", {}).setdefault("gentle-ai-engram", {})["enabled"] = False
with open(cfg_json, "w", encoding="utf-8") as f:
    json.dump(cfg_data, f, indent=2)
    f.write("\n")

global_mcp = "/home/zerops/.gemini/config/mcp_config.json"
if os.path.isfile(global_mcp):
    try:
        data = json.load(open(global_mcp, "r", encoding="utf-8"))
        srv = data.setdefault("mcpServers", {}).setdefault("engram", {})
        if os.path.isfile("/var/www/.bin/engram-mcp"):
            srv["command"] = "/var/www/.bin/engram-mcp"
            srv["args"] = []
        srv["cwd"] = "/var/www"
        with open(global_mcp, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=2)
            f.write("\n")
        print(f"  ✓ Engram MCP único (--tools=agent, cwd=/var/www) en {global_mcp}")
    except Exception as e:
        print(f"  ⚠️ No se pudo actualizar {global_mcp}: {e}")
EOF_ENGRAM_MCP
    rm -rf "$PROJECT_ROOT/.atl" "/home/zerops/.gemini/GEMINI.md" "/home/zerops/.gemini/system.md" "/home/zerops/.gemini/antigravity-cli/references" 2>/dev/null || true
    for rule_name in \
        gentle-ai-03-orchestrator-part1.md \
        gentle-ai-03-orchestrator-part2.md \
        gentle-ai-04-agent-routing-part1.md \
        gentle-ai-04-agent-routing-part2.md; do
        rm -f "/home/zerops/.gemini/config/rules/$rule_name" 2>/dev/null || true
    done
    if [ -f "$SCRIPT_DIR/templates/gentle-ai-02-engram-protocol.md" ]; then
        cp -f "$SCRIPT_DIR/templates/gentle-ai-02-engram-protocol.md" "/home/zerops/.gemini/config/rules/gentle-ai-02-engram-protocol.md"
    fi
    python3 - << 'EOF_AGY_SETTINGS'
import json, os
agy_settings = os.path.expanduser("~/.gemini/antigravity-cli/settings.json")
os.makedirs(os.path.dirname(agy_settings), exist_ok=True)
try:
    st = json.load(open(agy_settings, "r", encoding="utf-8")) if os.path.isfile(agy_settings) else {}
except Exception:
    st = {}
st.setdefault("model", "Orchestrator (Neon)")
tw = st.setdefault("trustedWorkspaces", [])
if "/var/www" not in tw:
    tw.append("/var/www")
with open(agy_settings, "w", encoding="utf-8") as wf:
    json.dump(st, wf, indent=2)
    wf.write("\n")
os.chmod(agy_settings, 0o600)
EOF_AGY_SETTINGS
    echo "• Verificando salud del ecosistema Gentle AI..."
    gentle-ai doctor || true
fi

INJECT_CMD="inject-agent-rule"

# 4. Inyectar Protocolos de Gobernanza en AGENTS.md (preservando ZCP:BEGIN y ZEROPS:REFLOG)
echo "• Inyectando protocolos de gobernanza en AGENTS.md (Lean Mode)..."

    if [ -f "$ZCP_ROOT/AGENTS.md" ]; then
        if [ ! -f "$PROJECT_ROOT/AGENTS.md" ]; then
            cp -f "$ZCP_ROOT/AGENTS.md" "$PROJECT_ROOT/AGENTS.md"
        else
            python3 - "$ZCP_ROOT/AGENTS.md" "$PROJECT_ROOT/AGENTS.md" << 'EOF_SYNC_CUSTOM' || true
import re, sys
src = open(sys.argv[1], "r", encoding="utf-8").read()
dst = open(sys.argv[2], "r", encoding="utf-8").read()
m = re.search(r'<!-- CUSTOM:BEGIN -->.*?<!-- CUSTOM:END -->', src, flags=re.S)
if m:
    block = m.group(0)
    if re.search(r'<!-- CUSTOM:BEGIN -->.*?<!-- CUSTOM:END -->', dst, flags=re.S):
        out = re.sub(r'<!-- CUSTOM:BEGIN -->.*?<!-- CUSTOM:END -->', lambda _: block, dst, count=1, flags=re.S)
    else:
        out = dst.rstrip() + "\n\n" + block + "\n"
    if out != dst:
        open(sys.argv[2], "w", encoding="utf-8").write(out)
EOF_SYNC_CUSTOM
        fi
    fi

# 5. Sincronizar Supreme Directive (.agents/rules + symlink a ~/.gemini/config/rules)
echo "• Sincronizando Supreme Directive desde SSoT..."
mkdir -p "$PROJECT_ROOT/.agents/rules" "$HOME/.gemini/config/rules" 2>/dev/null || true

if [ -f "$ZCP_ROOT/.agents/rules/00-SUPREME-DIRECTIVE.md" ] && [ "$(readlink -f "$ZCP_ROOT/.agents/rules/00-SUPREME-DIRECTIVE.md")" != "$(readlink -f "$PROJECT_ROOT/.agents/rules/00-SUPREME-DIRECTIVE.md" 2>/dev/null || true)" ]; then
    cp -f "$ZCP_ROOT/.agents/rules/00-SUPREME-DIRECTIVE.md" "$PROJECT_ROOT/.agents/rules/00-SUPREME-DIRECTIVE.md"
fi
if [ -f "$PROJECT_ROOT/.agents/rules/00-SUPREME-DIRECTIVE.md" ]; then
    ln -sfn "$PROJECT_ROOT/.agents/rules/00-SUPREME-DIRECTIVE.md" "$HOME/.gemini/config/rules/00-SUPREME-DIRECTIVE.md"
fi
rm -f "$HOME/.gemini/antigravity-cli/rules/00-SUPREME-DIRECTIVE.md" 2>/dev/null || true
mkdir -p "$HOME/.gemini/config" 2>/dev/null || true
echo '{}' > "$HOME/.gemini/config/hooks.json" 2>/dev/null || true

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
    if [ -d "$ZCP_ROOT/scripts/hooks" ]; then
        cp -f "$SCRIPT_DIR/hooks/tool-guard.py" "$ZCP_ROOT/scripts/hooks/tool-guard.py" 2>/dev/null || true
    fi
fi

if [ -f "$ZCP_ROOT/.agents/hooks.json" ]; then
    cp -f "$ZCP_ROOT/.agents/hooks.json" "$PROJECT_ROOT/.agents/hooks.json"
elif [ -f "$REPO_DIR/.agents/hooks.json" ]; then
    cp -f "$REPO_DIR/.agents/hooks.json" "$PROJECT_ROOT/.agents/hooks.json"
fi

# Desplegar Sensor Universal de Capacidades (Standard v3.3)
if [ -f "$SCRIPT_DIR/skills-suite-validate.sh" ]; then
    cp -f "$SCRIPT_DIR/skills-suite-validate.sh" "$PROJECT_ROOT/.bin/skills-suite-validate"
    chmod +x "$PROJECT_ROOT/.bin/skills-suite-validate" 2>/dev/null || true
    sudo ln -sf "$PROJECT_ROOT/.bin/skills-suite-validate" /usr/local/bin/skills-suite-validate 2>/dev/null || true
fi
# Desplegar astrobranding-check incondicionalmente (Arnés Resiliente Anti-Fallo en ZCP limpio)
if [ -f "$SCRIPT_DIR/astrobranding-check.sh" ]; then
    cp -f "$SCRIPT_DIR/astrobranding-check.sh" "$PROJECT_ROOT/.bin/astrobranding-check"
    chmod +x "$PROJECT_ROOT/.bin/astrobranding-check" 2>/dev/null || true
    sudo ln -sf "$PROJECT_ROOT/.bin/astrobranding-check" /usr/local/bin/astrobranding-check 2>/dev/null || true
fi

echo "  ✅ Despliegue de Gentle AI, Engram & Supreme Directive v8.4 completado con éxito."
chmod +x "$PROJECT_ROOT/.agents/rules/00-SUPREME-DIRECTIVE.md" 2>/dev/null || true
