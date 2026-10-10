#!/usr/bin/env bash
# ==============================================================================
# Seed FreeLLMAPI Declarative Configuration in Zerops (Sovereign Secret Injection)
# Usage: ./scripts/seed-freellmapi-keys.sh [--keys /path/to/keys.md]
# ==============================================================================
set -euo pipefail

SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
ROOT_DIR="$(cd "$SCRIPT_DIR/.." && pwd)"

log_info() { echo -e "\033[1;34m[INFO]\033[0m $*"; }
log_ok()   { echo -e "\033[1;32m[OK]\033[0m $*"; }
log_warn() { echo -e "\033[1;33m[WARN]\033[0m $*"; }
log_err()  { echo -e "\033[1;31m[ERROR]\033[0m $*" >&2; }

KEYS_FILE="${1:-}"
ADMIN_EMAIL="${FREELLMAPI_ADMIN_EMAIL:-admin@baiosfera.com}"
ADMIN_PASSWORD="${FREELLMAPI_ADMIN_PASSWORD:-Baiosfera2026!*}"

python3 - <<EOF
import os, sys, re, json, subprocess

keys_file = "$KEYS_FILE"
admin_email = "$ADMIN_EMAIL"
admin_password = "$ADMIN_PASSWORD"

def parse_markdown(filepath):
    keys = {}
    current_platform = None
    if not os.path.exists(filepath):
        return keys
    with open(filepath, 'r') as f:
        for line in f:
            line = line.strip()
            plat_match = re.search(r'\*\*Plataforma:\*\*\s*\`([^\`]+)\`', line)
            if plat_match:
                current_platform = plat_match.group(1).strip()
            key_match = re.search(r'\*\*API Key:\*\*\s*\`([^\`]+)\`', line)
            if key_match and current_platform:
                keys[current_platform] = key_match.group(1).strip()
    return keys

# Candidate locations for free LLM provider keys
b_path_candidates = [
    "/var/www/baiosfera/0ZEROPS-AGY/users-apis/Baiosfera/baiosfera_freellm.md",
    "/var/www/baiosfera/0ZEROPS-AGY/0zcp-123/apis/baiosfera_freellm.md",
]
d_path_candidates = [
    "/var/www/baiosfera/0ZEROPS-AGY/users-apis/Damaren/damaren_freellm.md",
    "/var/www/baiosfera/0ZEROPS-AGY/0zcp-123/apis/freellm_keys.md",
]

b_path = next((p for p in b_path_candidates if os.path.exists(p)), "")
d_path = next((p for p in d_path_candidates if os.path.exists(p)), "")

b_keys = parse_markdown(b_path) if b_path else {}
d_keys = parse_markdown(d_path) if d_path else {}

# Also inspect optional keys_file passed as argument
if keys_file and os.path.exists(keys_file):
    with open(keys_file, 'r') as f:
        content = f.read()
    for plat in ['groq', 'cerebras', 'opencode', 'openrouter', 'ollama', 'huggingface']:
        m = re.search(rf'{plat.upper()}_API_KEY=([^\s]+)', content)
        if m and plat not in b_keys:
            b_keys[plat] = m.group(1).strip()

keys_list = []
for plat, key in b_keys.items():
    if plat != 'aisa' and key:
        keys_list.append({"platform": plat, "key": key, "label": f"{plat}-primary", "enabled": True})

for plat, key in d_keys.items():
    if plat != 'aisa' and key:
        keys_list.append({"platform": plat, "key": key, "label": f"{plat}-secondary", "enabled": True})

custom_providers = []
aisa_key = b_keys.get('aisa') or d_keys.get('aisa')
if aisa_key:
    custom_providers.append({
        "baseUrl": "https://api.aisa.one/v1",
        "apiKey": aisa_key,
        "label": "Aisa One Gateway",
        "models": [{"model": "gpt-4o-mini", "displayName": "Aisa GPT-4o Mini", "supportsTools": True}]
    })

config = {
    "admin": {"email": admin_email, "password": admin_password},
    "keys": keys_list,
    "customProviders": custom_providers,
    "routing": {"strategy": "balanced", "keySelectionStrategy": "least-remaining"}
}

json_str = json.dumps(config, separators=(',', ':'))
print(f"Generated FreeLLMAPI config with {len(keys_list)} keys, {len(custom_providers)} custom providers.")

# Write config directly to destination on persistent volume if mounted or via SSH
out_file = "/tmp/freellmapi_generated_config.json"
with open(out_file, "w") as f:
    f.write(json_str)

EOF

if [ -f "/tmp/freellmapi_generated_config.json" ]; then
    log_info "Transfiriendo configuración a volumen de almacenamiento freellmapi..."
    if ssh -o BatchMode=yes -o ConnectTimeout=5 freellmapi "test -d /mnt/localstorage/freellmapi" 2>/dev/null; then
        scp /tmp/freellmapi_generated_config.json freellmapi:/mnt/localstorage/freellmapi/config.json
        ssh freellmapi "chmod 600 /mnt/localstorage/freellmapi/config.json && cp /mnt/localstorage/freellmapi/config.json /var/www/config.json && echo 'FREELLM_ADMIN_EMAIL=\"$ADMIN_EMAIL\"' | sudo tee -a /etc/environment >/dev/null && echo 'FREELLM_ADMIN_PASSWORD=\"$ADMIN_PASSWORD\"' | sudo tee -a /etc/environment >/dev/null"
        log_ok "Configuración inyectada con éxito en freellmapi."
    else
        log_warn "Servicio freellmapi no alcanzable vía SSH aún. Archivo temporal listo en /tmp/freellmapi_generated_config.json."
    fi
    rm -f /tmp/freellmapi_generated_config.json
fi
log_ok "Proceso de seeding de claves completado."
