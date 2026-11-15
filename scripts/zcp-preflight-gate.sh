#!/usr/bin/env bash
# ==============================================================================
# zcp-preflight-gate: Physical Pre-Flight Platform Validator & Linter (v1.0)
# Enforces Zerops Invariants, RFC hostnames, Alpine permissions & Autoscaling
# Zero Token Overhead | Bounded Execution < 150ms | 100% Deterministic
# ==============================================================================
set -euo pipefail
export PYTHONDONTWRITEBYTECODE=1

TARGET=""
CHECK_LIVE=false

for arg in "$@"; do
    case "$arg" in
        --check-live) CHECK_LIVE=true ;;
        -h|--help)
            echo "Usage: zcp-preflight-gate [--check-live] <path-to-yaml-or-directory>"
            exit 0
            ;;
        *)
            if [ -z "$TARGET" ]; then
                TARGET="$arg"
            fi
            ;;
    esac
done

if [ -z "$TARGET" ]; then
    echo "Usage: zcp-preflight-gate [--check-live] <path-to-yaml-or-directory>"
    exit 1
fi

if [ ! -e "$TARGET" ]; then
    echo "❌ Error: Target no existe en: $TARGET"
    exit 1
fi

python3 -B - << 'EOF' "$TARGET" "$CHECK_LIVE"
import sys, os, re, json, yaml

target = os.path.abspath(sys.argv[1])
force_check_live = sys.argv[2].lower() == "true"
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

KNOWN_SERVICE_ATTRS = {
    "connectionString", "connectionTlsString", "hostname", "port", "portTls",
    "user", "superUser", "password", "superUserPassword", "dbName",
    "zeropsUser", "zeropsPassword", "apiUrl", "apiCdnUrl", "staticCdnUrl",
    "storageCdnUrl", "serviceId",
}
KNOWN_SERVICE_HOSTNAMES = {
    "nats", "database", "db", "valkey", "cache", "redis",
    "qdrant", "localstorage", "objectstorage", "s3",
}

def collect_live_hostnames():
    hosts = set()
    for k in os.environ:
        for suffix in ("_hostname", "_connectionString", "_serviceId"):
            if k.endswith(suffix):
                prefix = k[:-len(suffix)]
                if re.fullmatch(r'[a-z0-9]{1,25}', prefix):
                    hosts.add(prefix)
    cache_path = "/tmp/.zerops_discover_cache.json"
    if os.path.exists(cache_path):
        try:
            with open(cache_path, "r", encoding="utf-8") as cf:
                data = json.load(cf)
                for svc in data.get("services", []):
                    hn = svc.get("hostname")
                    if hn:
                        hosts.add(hn)
        except Exception:
            pass
    return hosts

live_hostnames = collect_live_hostnames()
is_project_runtime_target = (
    target.startswith("/var/www/")
    and not any(p in target for p in ["/zerops-astrobranding/", "/zerops-astro-skills/", "/baiosfera/"])
)
check_live_default = force_check_live or (is_project_runtime_target and bool(os.environ.get("PROJECT_NAME") and live_hostnames))

print("============================================================")
print(f"  🔍 ZCP Pre-Flight Gate: Validating {len(files_to_check)} manifest(s)")
print("============================================================")

hostname_regex = re.compile(r'^[a-z0-9]{1,25}$')
env_ref_regex = re.compile(r'\$\{([A-Za-z_][A-Za-z0-9_]*)\}')

def inspect_env_block(env_dict, section_label, fname, declared_hostnames, check_live_refs):
    global errors, warnings
    if not isinstance(env_dict, dict):
        return
    for k, v in env_dict.items():
        if v is None:
            continue
        val_str = str(v)
        # 1. Circular same-key self-shadowing (KEY: ${KEY}) fails Zerops deploy
        if re.fullmatch(r'\s*\$\{' + re.escape(str(k)) + r'\}\s*', val_str):
            print(f"❌ [{fname}] Self-shadowing ilegal en {section_label}: '{k}: {val_str}'. Usá una clave distinta en Shared Vault (ej. '${{{k}_VAULT}}') o eliminala.")
            errors += 1
            continue

        # 2. Service reference checks (${svc_attr})
        for ref in env_ref_regex.findall(val_str):
            if "_" not in ref:
                continue
            svc, attr = ref.split("_", 1)
            if not re.fullmatch(r'[a-z][a-z0-9]{0,24}', svc):
                continue
            if attr not in KNOWN_SERVICE_ATTRS and svc not in KNOWN_SERVICE_HOSTNAMES:
                continue

            if declared_hostnames is not None:
                if svc not in declared_hostnames:
                    print(f"❌ [{fname}] Referencia rota en {section_label}: '{k}: {val_str}' apunta a servicio '{svc}' ausente del manifiesto.")
                    errors += 1
            else:
                if check_live_refs and svc not in live_hostnames:
                    print(f"❌ [{fname}] Dependencia ausente en {section_label}: '{k}: {val_str}' requiere servicio '{svc}', pero NO existe en el proyecto vivo ({sorted(live_hostnames)}).")
                    errors += 1
                elif svc == "nats":
                    print(f"⚠️ [{fname}] Acoplamiento rígido a NATS en {section_label}: '{k}: {val_str}'. En proyectos sin NATS esto falla preflight; preferí inyección opcional por Vault o configuración condicional.")
                    warnings += 1

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
        is_import = 'services' in doc and isinstance(doc.get('services'), list)
        services = doc.get('services', []) if is_import else doc.get('zerops', [])
        if not isinstance(services, list):
            continue

        declared_hostnames = None
        if is_import and len(services) > 1:
            declared_hostnames = {s.get('hostname') for s in services if isinstance(s, dict) and s.get('hostname')}

        file_check_live = force_check_live or (check_live_default and fpath == target)

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

            # Env checks (service-level, build.envVariables, run.envVariables)
            inspect_env_block(s.get('envVariables'), f"{hname or 'service'}.envVariables", fname, declared_hostnames, file_check_live)

            build_block = s.get('build', {})
            if isinstance(build_block, dict):
                inspect_env_block(build_block.get('envVariables'), f"{hname or 'setup'}.build.envVariables", fname, declared_hostnames, file_check_live)

            # Prepare commands & run env check
            run_block = s.get('run', {})
            if isinstance(run_block, dict):
                inspect_env_block(run_block.get('envVariables'), f"{hname or 'setup'}.run.envVariables", fname, declared_hostnames, file_check_live)
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
