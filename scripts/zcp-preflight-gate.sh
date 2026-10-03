#!/usr/bin/env bash
# ==============================================================================
# zcp-preflight-gate: Physical Pre-Flight Platform Validator & Linter (v1.0)
# Enforces Zerops Invariants, RFC hostnames, Alpine permissions & Autoscaling
# Zero Token Overhead | Bounded Execution < 150ms | 100% Deterministic
# ==============================================================================
set -euo pipefail
export PYTHONDONTWRITEBYTECODE=1

TARGET="${1:-}"

if [ -z "$TARGET" ]; then
    echo "Usage: zcp-preflight-gate <path-to-yaml-or-directory>"
    exit 1
fi

if [ ! -e "$TARGET" ]; then
    echo "❌ Error: Target no existe en: $TARGET"
    exit 1
fi

python3 - << 'EOF' "$TARGET"
import sys, os, re, yaml

target = sys.argv[1]
files_to_check = []

if os.path.isfile(target):
    files_to_check.append(target)
else:
    for root, _, files in os.walk(target):
        for f in files:
            if f.endswith(('.yaml', '.yml')) and not f.startswith('.'):
                files_to_check.append(os.path.join(root, f))

errors = 0
warnings = 0

print("============================================================")
print(f"  🔍 ZCP Pre-Flight Gate: Validating {len(files_to_check)} manifest(s)")
print("============================================================")

hostname_regex = re.compile(r'^[a-z0-9]{1,25}$')

for fpath in files_to_check:
    fname = os.path.basename(fpath)
    try:
        with open(fpath, 'r', encoding='utf-8') as f:
            content = f.read()
    except Exception as e:
        print(f"❌ Error leyendo {fname}: {e}")
        errors += 1
        continue

    # 1. Parse YAML
    try:
        docs = list(yaml.safe_load_all(content))
    except Exception as e:
        print(f"❌ Error de sintaxis YAML en {fname}: {e}")
        errors += 1
        continue

    for doc in docs:
        if not isinstance(doc, dict):
            continue

        # Zerops services can be in 'services' list (import.yaml) or 'zerops' list (zerops.yaml)
        services = doc.get('services', [])
        if not services and 'zerops' in doc:
            services = doc.get('zerops', [])
        
        for s in services:
            if not isinstance(s, dict):
                continue
            
            # Hostname check
            hname = s.get('hostname') or s.get('setup')
            if hname:
                if not hostname_regex.match(hname):
                    print(f"❌ [{fname}] Hostname inválido '{hname}': debe ser minúscula alfanumérica [a-z0-9], max 25 chars, sin guiones.")
                    errors += 1

            # Autoscaling check in import.yaml
            if 'verticalAutoscaling' in s:
                vas = s.get('verticalAutoscaling', {})
                cpu_mode = vas.get('cpuMode')
                if cpu_mode == 'DEDICATED':
                    print(f"⚠️ [{fname}] '{hname}' usa cpuMode: DEDICATED en arranque. La Ley de Autoescalado Frugal exige SHARED.")
                    warnings += 1

            # Prepare commands check in Alpine
            run_block = s.get('run', {})
            base_os = str(run_block.get('base', '') or s.get('base', '') or '')
            prep_cmds = run_block.get('prepareCommands', [])
            if isinstance(prep_cmds, list) and 'alpine' in base_os.lower():
                for cmd in prep_cmds:
                    if isinstance(cmd, str) and re.search(r'\bapk\s+add\b', cmd) and not re.search(r'\bsudo\s+apk\b', cmd):
                        print(f"❌ [{fname}] Permiso denegado latente en '{hname}': 'apk add' en Alpine exige 'sudo apk add'.")
                        errors += 1

print("------------------------------------------------------------")
if errors == 0:
    print(f"✅ ZCP Pre-Flight Gate superado exitosamente ({warnings} advertencia(s)).")
    sys.exit(0)
else:
    print(f"❌ ZCP Pre-Flight Gate RECHAZADO con {errors} error(es) bloqueantes.")
    sys.exit(1)
EOF
