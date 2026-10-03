#!/usr/bin/env bash
set -euo pipefail

# ==============================================================================
# ZCP ZERO-TRUST GDRIVE INSTALLER (V5.4: Mandatory Local Storage & Artifacts Persistence Invariant)
# Supports: Local Storage (POSIX), SeaweedFS (Distributed HA), Object Storage (MinIO S3)
# ==============================================================================

# 0. SELF-CONTAINED EXECUTION SHIELD (Prevent FUSE detach deadlock)
if [[ "${BASH_SOURCE[0]}" == *"/var/www/baiosfera/"* ]] || [[ "$(pwd)" == *"/var/www/baiosfera"* ]]; then
    TMP_RUNNER="/tmp/gdrive_runner_$$.sh"
    cp -f "${BASH_SOURCE[0]}" "$TMP_RUNNER"
    chmod +x "$TMP_RUNNER"
    cd /tmp
    exec "$TMP_RUNNER" "$@"
fi

# 1. EPISTEMIC ANCHORING: Verify systemd
INIT_SYS=$(ps -p 1 -o comm= || true)
if [ "$INIT_SYS" != "systemd" ]; then
    echo "[ZCP-ERROR] Expected systemd as PID 1, found: $INIT_SYS. This script requires a systemd-enabled ZCP container."
    exit 1
fi

# 2. LOCAL CORE INITIALIZATION (ZCP Independence)
LOCAL_ROOT="/var/www/.rclone"
MOUNT_DIR="${GDRIVE_MOUNT_DIR:-/var/www/baiosfera}"

# Clean up legacy symlink if it exists from previous installations
if [ -L "$MOUNT_DIR" ]; then
    sudo rm -f "$MOUNT_DIR"
fi

sudo mkdir -p "$LOCAL_ROOT/bin" "$LOCAL_ROOT/vault/rclone" "$LOCAL_ROOT/config/rclone" "$MOUNT_DIR"
echo "[ZCP-BOOT] Using local core for rclone: $LOCAL_ROOT"

# 3. OS DEPENDENCIES (FUSE, SSHFS & Networking Tools)
export DEBIAN_FRONTEND=noninteractive
sudo apt-get update -qq
sudo apt-get install -y -qq fuse3 curl unzip python3 sshfs netcat-openbsd
grep -q "^user_allow_other" /etc/fuse.conf || echo "user_allow_other" | sudo tee -a /etc/fuse.conf > /dev/null

# 4. DEPENDENCY HIJACKING (Portable Rclone)
if [ ! -x "$LOCAL_ROOT/bin/rclone" ]; then
    echo "[ZCP-BOOT] Downloading standalone Rclone..."
    curl -fsSLO https://downloads.rclone.org/rclone-current-linux-amd64.zip
    unzip -q rclone-current-linux-amd64.zip
    sudo mv rclone-*-linux-amd64/rclone "$LOCAL_ROOT/bin/rclone"
    rm -rf rclone-current-linux-amd64.zip rclone-*-linux-amd64
    sudo chmod +x "$LOCAL_ROOT/bin/rclone"
fi
sudo ln -sf "$LOCAL_ROOT/bin/rclone" /usr/local/bin/rclone

# 5. VAULT CONFIGURATION
# Load environment credentials if not in current shell
if [ -f "/var/www/gdrive.env" ]; then
    set -a
    # shellcheck disable=SC1091
    source /var/www/gdrive.env 2>/dev/null || true
    set +a
fi
if [ -f "/var/www/.env" ]; then
    set -a
    # shellcheck disable=SC1091
    source /var/www/.env 2>/dev/null || true
    set +a
fi
if [ -f "/etc/environment" ]; then
    set -a
    # shellcheck disable=SC1091
    source /etc/environment 2>/dev/null || true
    set +a
fi

GDRIVE_CLIENT_ID="${GDRIVE_CLIENT_ID:-${GOOGLE_CLIENT_ID:-}}"
GDRIVE_CLIENT_SECRET="${GDRIVE_CLIENT_SECRET:-${GOOGLE_CLIENT_SECRET:-}}"
GDRIVE_REFRESH_TOKEN="${GDRIVE_REFRESH_TOKEN:-}"
GDRIVE_REMOTE_NAME="${GDRIVE_REMOTE_NAME:-baiosfera}"

if [ -z "$GDRIVE_CLIENT_ID" ] || [ -z "$GDRIVE_CLIENT_SECRET" ] || [ -z "$GDRIVE_REFRESH_TOKEN" ]; then
    echo "❌ [GDRIVE-ERROR] Missing Google Drive OAuth credentials."
    echo "   Ensure GDRIVE_CLIENT_ID, GDRIVE_CLIENT_SECRET, and GDRIVE_REFRESH_TOKEN are set in"
    echo "   Zerops project env, /var/www/.env, or exported in the environment."
    exit 1
fi

RCLONE_CONF="$LOCAL_ROOT/config/rclone/rclone.conf"
sudo tee "$RCLONE_CONF" > /dev/null << EOF
[${GDRIVE_REMOTE_NAME}]
type = drive
scope = drive
client_id = ${GDRIVE_CLIENT_ID}
client_secret = ${GDRIVE_CLIENT_SECRET}
token = {"access_token":"ya29","token_type":"Bearer","refresh_token":"${GDRIVE_REFRESH_TOKEN}","expiry":"2000-01-01T00:00:00Z"}
EOF
sudo chmod 644 "$RCLONE_CONF"

# 5b. PRE-MOUNT VS CODE & INOTIFY SHIELD (Dynamic Watcher Exclusions)
echo "[ZCP-BOOT] Configuring dynamic VS Code / Code-Server file watcher exclusions..."
python3 -c "
import os, json

storage_dirs = []
if os.path.exists('/mnt'):
    for d in os.listdir('/mnt'):
        if d != 'lost+found' and os.path.isdir(os.path.join('/mnt', d)):
            storage_dirs.append(d)

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

for sdir in storage_dirs:
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

# 6. UNIVERSAL DYNAMIC DISCOVERY & TRIPARTITE STORAGE INTEGRATION
# Method 1: Explicit parameter passed to script or environment variable
EXPLICIT_STORAGE="${1:-${LOCAL_STORAGE:-${STORAGE_TARGET:-}}}"
STORAGE_TYPE="none"
DISCOVERED_TARGET=""

# Candidate hostnames to probe
CANDIDATES=("baiostorage" "storage" "seaweed" "seaweedfs" "sharedfiles" "sharedstorage" "localstorage" "vol" "volume" "data" "disk" "filestore" "appstorage" "s3storage" "media" "backups")

discover_tripartite_storage() {
    # 1. Check explicit override
    if [ -n "$EXPLICIT_STORAGE" ]; then
        DISCOVERED_TARGET="$EXPLICIT_STORAGE"
        # Determine explicit type
        if env | grep -q "${EXPLICIT_STORAGE}_apiUrl=" || [ "${S3_ENDPOINT:-}" != "" ]; then
            STORAGE_TYPE="object-storage"
            return 0
        elif curl -s -m 2 "http://${EXPLICIT_STORAGE}.zerops:8888/" >/dev/null 2>&1 || nc -z -w 2 "$EXPLICIT_STORAGE" 8888 2>/dev/null; then
            STORAGE_TYPE="seaweedfs"
            return 0
        else
            STORAGE_TYPE="local-storage"
            return 0
        fi
    fi

    # 2. Primary: Probe and wait for Local Storage (POSIX persistent volume law)
    echo "[ZCP-BOOT] Probing and waiting for persistent localstorage (timeout 15s)..."
    for cand in "localstorage" "storage" "sharedfiles" "sharedstorage" "vol" "volume" "data" "disk"; do
        for attempt in $(seq 1 15); do
            if ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o ConnectTimeout=2 -o BatchMode=yes "$cand" "test -d /data" 2>/dev/null; then
                DISCOVERED_TARGET="$cand"
                STORAGE_TYPE="local-storage"
                echo "[ZCP-BOOT] Persistent local-storage target ready: $cand (connected in ${attempt}s)"
                return 0
            fi
            sleep 1
        done
    done

    # 3. Probe any *_hostname environment variable for local-storage
    for var in $(env | grep -E '_hostname=' | sed 's/.*_hostname=//' || true); do
        if [ "$var" != "zcp" ] && [ "$var" != "core" ]; then
            if ssh -o StrictHostKeyChecking=no -o UserKnownHostsFile=/dev/null -o ConnectTimeout=2 -o BatchMode=yes "$var" "test -d /data" 2>/dev/null; then
                DISCOVERED_TARGET="$var"
                STORAGE_TYPE="local-storage"
                return 0
            fi
        fi
    done

    # 4. Probe for SeaweedFS (Check internal Filer HTTP port 8888)
    for cand in "${CANDIDATES[@]}"; do
        if curl -s -m 1 "http://${cand}.zerops:8888/" >/dev/null 2>&1 || nc -z -w 1 "$cand" 8888 2>/dev/null; then
            DISCOVERED_TARGET="$cand"
            STORAGE_TYPE="seaweedfs"
            return 0
        fi
    done

    # 5. Probe for Object Storage (Check env variables for *_apiUrl)
    for var in $(env | grep -E '_apiUrl=' | sed 's/_apiUrl=.*//' || true); do
        DISCOVERED_TARGET="$var"
        STORAGE_TYPE="object-storage"
        return 0
    done

    # 6. Probe for existing mounts in /mnt/
    local mnt_cand
    mnt_cand=$(ls -1 /mnt/ 2>/dev/null | grep -v 'lost+found' | head -n 1 || true)
    if [ -n "$mnt_cand" ]; then
        DISCOVERED_TARGET="$mnt_cand"
        STORAGE_TYPE="local-storage"
        return 0
    fi

    return 1
}

discover_tripartite_storage || true

AFTER_SERVICES="network-online.target"
BIND_MOUNT_SCRIPT=""
EXEC_STOP="ExecStop=/bin/bash -c 'if mountpoint -q $MOUNT_DIR; then /usr/bin/fusermount3 -uz $MOUNT_DIR || true; fi'"
EXEC_STOP_POST="ExecStopPost=/bin/bash -c 'if mountpoint -q $MOUNT_DIR; then /usr/bin/fusermount3 -uz $MOUNT_DIR || true; fi'"

if [ -n "$DISCOVERED_TARGET" ] && [ "$STORAGE_TYPE" != "none" ]; then
    STORAGE_DIR="/mnt/$DISCOVERED_TARGET"
    STORAGE_MOUNT="$STORAGE_DIR/baiosfera"
    EXPORT_DIR="$STORAGE_DIR/.rclone_export"
    
    echo "[ZCP-BOOT] Discovered $STORAGE_TYPE target: $DISCOVERED_TARGET"

    case "$STORAGE_TYPE" in
        "local-storage")
            # In ZCP control-plane, if not yet mounted, attach via SSHFS to the service's /data volume
            if ! mountpoint -q "$STORAGE_DIR"; then
                sudo mkdir -p "$STORAGE_DIR"
                echo "[ZCP-BOOT] Attaching $DISCOVERED_TARGET:/data to $STORAGE_DIR via SSHFS..."
                sudo sshfs -o StrictHostKeyChecking=no,UserKnownHostsFile=/dev/null,allow_other,default_permissions,reconnect,ServerAliveInterval=15,ServerAliveCountMax=3 "${DISCOVERED_TARGET}:/data" "$STORAGE_DIR" || true
            fi
            ;;

        "seaweedfs")
            # Mount SeaweedFS filer via weed mount or zsc helper if available
            if ! mountpoint -q "$STORAGE_DIR"; then
                sudo mkdir -p "$STORAGE_DIR"
                echo "[ZCP-BOOT] Mounting SeaweedFS filer ($DISCOVERED_TARGET.zerops:8888) to $STORAGE_DIR..."
                if [ -x "/opt/zerops/bin/weed-3-85" ]; then
                    sudo /opt/zerops/bin/weed-3-85 mount -filer="${DISCOVERED_TARGET}.zerops:8888" -dir="$STORAGE_DIR" -volumeServerAccess=direct -cacheCapacityMB=0 -concurrentWriters=1 -chunkSizeLimitMB=1 &
                    sleep 2
                elif command -v zsc >/dev/null 2>&1; then
                    sudo zsc shared-storage mount "$DISCOVERED_TARGET" --background || true
                    sleep 2
                else
                    echo "[ZCP-BOOT] SeaweedFS client not bundled; falling back to HTTP Filer API bridge."
                fi
            fi
            ;;

        "object-storage")
            # Extract credentials and register S3 remote in rclone.conf
            S3_API_URL=$(env | grep -E "^${DISCOVERED_TARGET}_apiUrl=" | sed "s/.*_apiUrl=//" || echo "${S3_ENDPOINT:-}")
            S3_KEY_ID=$(env | grep -E "^${DISCOVERED_TARGET}_accessKeyId=" | sed "s/.*_accessKeyId=//" || echo "${S3_ACCESS_KEY:-}")
            S3_SEC_KEY=$(env | grep -E "^${DISCOVERED_TARGET}_secretAccessKey=" | sed "s/.*_secretAccessKey=//" || echo "${S3_SECRET_KEY:-}")
            S3_BUCKET_NAME=$(env | grep -E "^${DISCOVERED_TARGET}_bucketName=" | sed "s/.*_bucketName=//" || echo "${S3_BUCKET:-}")

            if [ -n "$S3_API_URL" ] && [ -n "$S3_KEY_ID" ]; then
                echo "[ZCP-BOOT] Configuring Zerops Object Storage (MinIO S3) in Rclone..."
                sudo tee -a "$RCLONE_CONF" > /dev/null << S3EOF

[zerops_s3]
type = s3
provider = Minio
env_auth = false
access_key_id = $S3_KEY_ID
secret_access_key = $S3_SEC_KEY
endpoint = $S3_API_URL
region = us-east-1
force_path_style = true
S3EOF
                sudo chmod 644 "$RCLONE_CONF"
                sudo mkdir -p "$STORAGE_DIR"

                # Mount S3 bucket directly to /mnt/$DISCOVERED_TARGET
                if ! mountpoint -q "$STORAGE_DIR"; then
                    echo "[ZCP-BOOT] Mounting MinIO bucket ($S3_BUCKET_NAME) to $STORAGE_DIR via Rclone FUSE..."
                    "$LOCAL_ROOT/bin/rclone" mount "zerops_s3:$S3_BUCKET_NAME" "$STORAGE_DIR" \
                        --config "$RCLONE_CONF" \
                        --vfs-cache-mode full \
                        --allow-other \
                        --daemon || true
                    sleep 2
                fi
            fi
            ;;
    esac

    # Generate Portable Runtime Kit in Storage for other runtime services
    if [ -d "$STORAGE_DIR" ] && [ "$STORAGE_TYPE" != "object-storage" ]; then
        sudo mkdir -p "$EXPORT_DIR/bin" "$EXPORT_DIR/config" 2>/dev/null || true
        if [ -d "$EXPORT_DIR/bin" ]; then
            sudo cp "$LOCAL_ROOT/bin/rclone" "$EXPORT_DIR/bin/"
            sudo cp "$RCLONE_CONF" "$EXPORT_DIR/config/"
            sudo chmod 644 "$EXPORT_DIR/config/rclone.conf"
            
            RUNTIME_SCRIPT="$EXPORT_DIR/gdrive"
            sudo tee "$RUNTIME_SCRIPT" > /dev/null << 'EOF'
#!/usr/bin/env bash
set -e
if [ -z "$1" ]; then
    echo "Usage: $0 <target_mount_directory>"
    exit 1
fi
TARGET="$1"
mkdir -p "$TARGET"
LOCAL_CACHE="/tmp/.rclone_cache_$(cat /proc/sys/kernel/random/uuid 2>/dev/null || tr -dc 'a-zA-Z0-9' < /dev/urandom | head -c 16)"
mkdir -p "$LOCAL_CACHE"

DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
"$DIR/bin/rclone" mount baiosfera: "$TARGET" \
    --config "$DIR/config/rclone.conf" \
    --cache-dir "$LOCAL_CACHE" \
    --vfs-cache-mode full \
    --dir-cache-time 60s \
    --allow-other \
    --allow-non-empty \
    --daemon
echo "GDrive mounted at $TARGET using local cache $LOCAL_CACHE"
EOF
            sudo chmod +x "$RUNTIME_SCRIPT"
        fi
    fi

    # Bind mount setup: wait for primary FUSE mount, then bind into storage target
    BIND_MOUNT_SCRIPT="ExecStartPost=/bin/bash -c 'while ! mountpoint -q $MOUNT_DIR; do sleep 1; done; if [ -d \"$STORAGE_DIR\" ]; then (umount -l $STORAGE_MOUNT 2>/dev/null || true); mkdir -p $STORAGE_MOUNT && mount --bind $MOUNT_DIR $STORAGE_MOUNT; fi'"
    
    # Clean unmount of bind mount before unmounting main FUSE
    EXEC_STOP="ExecStop=/bin/bash -c 'if mountpoint -q $STORAGE_MOUNT; then umount -l $STORAGE_MOUNT || true; fi; if mountpoint -q $MOUNT_DIR; then /usr/bin/fusermount3 -uz $MOUNT_DIR || true; fi'"
    EXEC_STOP_POST="ExecStopPost=/bin/bash -c 'if mountpoint -q $STORAGE_MOUNT; then umount -l $STORAGE_MOUNT || true; fi; if mountpoint -q $MOUNT_DIR; then /usr/bin/fusermount3 -uz $MOUNT_DIR || true; fi'"
    
    # Expose Storage directly in /var/www/ for convenient access alongside codebases
    if [ -d "$STORAGE_DIR" ]; then
        sudo ln -sfn "$STORAGE_DIR" "/var/www/$DISCOVERED_TARGET"
        echo "[ZCP-BOOT] Symlinked $STORAGE_TYPE ($STORAGE_DIR) to /var/www/$DISCOVERED_TARGET"
    fi
else
    echo "[ZCP-BOOT] No external Zerops Storage service detected. Running in standalone local core mode."
fi

# 7. SYSTEMD INJECTION (LOCAL MOUNT + RESILIENT STORAGE BIND MOUNT)
SERVICE_FILE="/etc/systemd/system/rclone-baiosfera.service"
sudo tee "$SERVICE_FILE" > /dev/null << EOF
[Unit]
Description=Rclone Mount Baiosfera (Local Core + Zerops $STORAGE_TYPE Bind Mount)
After=$AFTER_SERVICES

[Service]
Type=simple
ExecStartPre=/bin/bash -c '(umount -l /mnt/*/baiosfera 2>/dev/null || true); (fusermount3 -uz $MOUNT_DIR 2>/dev/null || true); (umount -l $MOUNT_DIR 2>/dev/null || true)'
ExecStart=$LOCAL_ROOT/bin/rclone mount ${GDRIVE_REMOTE_NAME}: $MOUNT_DIR \\
    --config $RCLONE_CONF \\
    --cache-dir $LOCAL_ROOT/vault/rclone \\
    --vfs-cache-mode full \\
    --vfs-cache-max-size 25G \\
    --vfs-cache-max-age 1h \\
    --dir-cache-time 60s \\
    --buffer-size 32M \\
    --allow-other \\
    --allow-non-empty \\
    --log-level INFO
$EXEC_STOP
$BIND_MOUNT_SCRIPT
$EXEC_STOP_POST
Restart=on-failure
RestartSec=5
User=root
Group=root

[Install]
WantedBy=multi-user.target
EOF

# Clean up empty lines
sudo sed -i '/^[[:space:]]*$/d' "$SERVICE_FILE"
sudo chmod 644 "$SERVICE_FILE"
sudo systemctl daemon-reload

# 8. ACTIVATION
sudo systemctl stop rclone-baiosfera.service || true
# Clean any stale mounts before fresh start
if [ -n "$DISCOVERED_TARGET" ] && mountpoint -q "/mnt/$DISCOVERED_TARGET/baiosfera"; then
    sudo umount -l "/mnt/$DISCOVERED_TARGET/baiosfera" || true
fi
if mountpoint -q "$MOUNT_DIR"; then
    sudo fusermount3 -uz "$MOUNT_DIR" || true
fi

sudo systemctl enable --now rclone-baiosfera.service

echo "[ZCP-BOOT] Esperando disponibilidad del montaje FUSE en $MOUNT_DIR (timeout 15s)..."
MOUNT_READY=false
for i in $(seq 1 15); do
    if mountpoint -q "$MOUNT_DIR"; then
        MOUNT_READY=true
        echo "  ✓ Montaje FUSE detectado y verificado en ${i}s."
        break
    fi
    if ! systemctl is-active --quiet rclone-baiosfera.service; then
        echo "❌ [GDRIVE-ERROR] rclone-baiosfera.service falló durante el arranque:"
        sudo journalctl -u rclone-baiosfera.service -n 25 --no-pager
        exit 1
    fi
    sleep 1
done

if [ "$MOUNT_READY" = false ]; then
    echo "❌ [GDRIVE-ERROR] Timeout de 15s esperando punto de montaje FUSE en $MOUNT_DIR."
    sudo journalctl -u rclone-baiosfera.service -n 25 --no-pager
    exit 1
fi

echo "[ZCP-BOOT] GDrive mounted natively at primary path: $MOUNT_DIR"
if [ -n "$DISCOVERED_TARGET" ] && [ -d "/mnt/$DISCOVERED_TARGET" ]; then
    echo "[ZCP-BOOT] GDrive integrated at $STORAGE_TYPE path: /mnt/$DISCOVERED_TARGET/baiosfera"
fi

# 9. ARTIFACTS PERSISTENCE INVARIANT (Google Drive SSoT Live Symlink)
SSOT_ARTIFACTS="$MOUNT_DIR/0ZEROPS-AGY/0zcp-123/artifacts"
LOCAL_ARTIFACTS="/var/www/artifacts"
sudo mkdir -p "$SSOT_ARTIFACTS" 2>/dev/null || true
if [ -d "$LOCAL_ARTIFACTS" ] && [ ! -L "$LOCAL_ARTIFACTS" ]; then
    echo "[ZCP-BOOT] Migrando artefactos locales preexistentes hacia Google Drive SSoT..."
    sudo cp -rn "$LOCAL_ARTIFACTS"/* "$SSOT_ARTIFACTS/" 2>/dev/null || true
    sudo rm -rf "$LOCAL_ARTIFACTS"
fi
if [ ! -L "$LOCAL_ARTIFACTS" ]; then
    sudo ln -sfn "$SSOT_ARTIFACTS" "$LOCAL_ARTIFACTS"
fi
echo "[ZCP-BOOT] Symlink /var/www/artifacts -> $SSOT_ARTIFACTS verificado y activo."