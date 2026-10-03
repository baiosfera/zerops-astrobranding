#!/usr/bin/env bash
# ==============================================================================
# Universal Secret & API Key Ingestion for Zerops ZCP & Gentle AI
# Version: 3.7 (Zero-Env Root Architecture: 100% /etc/environment & Zerops Cloud)
# ==============================================================================
set -euo pipefail

INTERACTIVE=false
FILE_ARG=""
PROJECT_ROOT="${PROJECT_ROOT:-/var/www}"

while [[ "$#" -gt 0 ]]; do
    case "$1" in
        -i|--interactive)
            INTERACTIVE=true
            shift ;;
        --file|-f)
            FILE_ARG="${2:-}"
            shift 2 ;;
        *)
            if [ -f "$1" ]; then
                FILE_ARG="$1"
            fi
            shift ;;
    esac
done

echo "============================================================"
echo "  🔑 Ingestión Universal de Claves y Secretos (setup-keys.sh v3.6)"
echo "============================================================"

# Función para sanitizar cualquier valor (elimina \r, espacios iniciales/finales y comillas)
sanitize_val() {
    local val="$1"
    val=$(echo "$val" | tr -d '\r' | sed -e 's/^[[:space:]]*//' -e 's/[[:space:]]*$//' -e 's/^["'"'"']//' -e 's/["'"'"']$//')
    echo "$val"
}

if [ -z "$FILE_ARG" ]; then
    for candidate in "$PROJECT_ROOT/key.md" "$PROJECT_ROOT/keys.md" "$PROJECT_ROOT/key.env" "$PROJECT_ROOT/keys.env"; do
        if [ -f "$candidate" ]; then
            FILE_ARG="$candidate"
            echo "• Archivo de claves detectado automáticamente en: $FILE_ARG"
            break
        fi
    done
fi

if [ -z "$FILE_ARG" ] && [ -t 0 ] && [ "$INTERACTIVE" = false ]; then
    read -r -p "• Ingrese la ruta del archivo de claves (.md / .env) [o Enter para continuar]: " USER_FILE
    USER_FILE=$(sanitize_val "$USER_FILE")
    [ -n "$USER_FILE" ] && [ -f "$USER_FILE" ] && FILE_ARG="$USER_FILE"
fi

# Definición Categorizada de Claves del Ecosistema (10 Grupos Base)
G1_BASE_IA_KEYS=(
    "GITHUB_TOKEN:Token de GitHub (Classic PAT con scopes repo, workflow, delete_repo)"
    "Z_TOKEN:Token de Acceso de Zerops (API Token)"
    "EXA_API_KEY:Clave de API de Exa AI (Búsqueda semántica de código)"
    "JINA_API_KEY:Clave de API de Jina AI (Extracción limpia a Markdown)"
    "TAVILY_API_KEY:Clave de API de Tavily AI (Búsqueda factual y agentes)"
    "FIRECRAWL_API_KEY:Clave de API de Firecrawl (Scraping estructurado y SPAs)"
    "BRAVE_API_KEY:Clave de API de Brave Search (Búsqueda web general)"
    "LINEAR_API_KEY:Clave de API de Linear (Gestión y sincronización de issues/proyectos)"
)

G2_GOOGLE_AUTH_KEYS=(
    "GOOGLE_CLIENT_ID:ID de Cliente OAuth 2.0 de Google Cloud Console"
    "GOOGLE_CLIENT_SECRET:Secreto de Cliente OAuth 2.0 de Google Cloud Console"
    "GOOGLE_REDIRECT_URI:URI de redirección (ej: https://api.tudominio.com/auth/login/google/callback)"
)

G3_ERP_BILLING_KEYS=(
    "FRAPPE_URL:URL de la instancia ERPNext / Frappe Cloud (ej: https://mi-empresa.frappe.cloud)"
    "FRAPPE_API_KEY:Clave API pública de usuario de integración ERPNext"
    "FRAPPE_API_SECRET:Secreto API de usuario de integración ERPNext"
    "FRAPPE_WEBHOOK_SECRET:Secreto HMAC para verificar webhooks de ERPNext"
    "FRAPPE_SITE_NAME:Nombre del sitio en Frappe Cloud (default: frontend)"
)

G4_WHATSAPP_KEYS=(
    "META_WA_PHONE_NUMBER_ID:Phone Number ID en Meta WhatsApp Cloud API"
    "META_WA_BUSINESS_ACCOUNT_ID:WhatsApp Business Account ID (WABA)"
    "META_WA_ACCESS_TOKEN:Permanent System User Access Token de Meta (EAA...)"
    "META_WEBHOOK_VERIFY_TOKEN:Verify Token para webhook de Meta WhatsApp"
    "META_APP_SECRET:Clave secreta de la App Meta para validar HMAC-SHA256"
    "EVOLUTION_API_URL:URL base de Evolution API v2 (ej: http://evolution:8080)"
    "EVOLUTION_API_KEY:API Key global de Evolution API v2"
    "EVOLUTION_INSTANCE:Nombre de la instancia de WhatsApp en Evolution API"
)

G5_TRACKING_KEYS=(
    "META_PIXEL_ID:ID del Pixel / Dataset de Meta (Facebook Pixel)"
    "META_CAPI_ACCESS_TOKEN:Token de acceso para Meta Conversions API (CAPI)"
    "GTM_ID:ID de contenedor Google Tag Manager (GTM-XXXXXX)"
    "GA4_MEASUREMENT_ID:ID de medición de Google Analytics 4 (G-XXXXXXXXXX)"
    "GA4_API_SECRET:API Secret del Measurement Protocol de GA4"
    "GOOGLE_ADS_CONVERSION_ID:ID de conversión de Google Ads"
)

G6_PAYMENTS_GATEWAYS_KEYS=(
    "WOMPI_PUBLIC_KEY:Llave pública de comercio en Wompi (pub_prod_... / pub_test_...)"
    "WOMPI_PRIVATE_KEY:Llave privada de comercio en Wompi (prv_prod_... / prv_test_...)"
    "WOMPI_INTEGRITY_SECRET:Secreto de integridad SHA-256 para checkout Wompi"
    "WOMPI_EVENTS_SECRET:Secreto de eventos para verificar webhooks de Wompi"
    "EPAYCO_PUBLIC_KEY:Llave pública de comercio en ePayco"
    "EPAYCO_PRIVATE_KEY:Llave privada de comercio en ePayco"
    "EPAYCO_P_KEY:P_KEY secreta para firma SHA-256 ePayco"
    "EPAYCO_P_CUST_ID_CLIENTE:ID de cliente numérico en ePayco"
    "DLOCAL_GO_API_KEY:API Key de dLocal Go (LatAm Multi-país)"
    "DLOCAL_GO_SECRET_KEY:Secret Key de dLocal Go"
    "STRIPE_SECRET_KEY:Secret Key de Stripe (sk_live_... / sk_test_...)"
    "STRIPE_PUBLISHABLE_KEY:Publishable Key de Stripe (pk_live_... / pk_test_...)"
    "STRIPE_WEBHOOK_SECRET:Webhook Signing Secret de Stripe (whsec_...)"
    "MERCADOPAGO_ACCESS_TOKEN:Access Token de Mercado Pago (APP_USR-...)"
    "MERCADOPAGO_PUBLIC_KEY:Public Key de Mercado Pago"
    "MERCADOPAGO_WEBHOOK_SECRET:Webhook Secret de Mercado Pago"
)

G7_EMAIL_MARKETING_KEYS=(
    "ZEPTOMAIL_SEND_MAIL_TOKEN:Send Mail Token de Zoho ZeptoMail (Zoho-enczapikey ...)"
    "ZEPTOMAIL_DEFAULT_FROM_EMAIL:Dirección de correo remitente en ZeptoMail"
    "ZEPTOMAIL_BOUNCE_ADDRESS:Dirección bounce de retorno en ZeptoMail"
    "AWS_ACCESS_KEY_ID:Access Key ID de AWS IAM para Amazon SES v2"
    "AWS_SECRET_ACCESS_KEY:Secret Access Key de AWS IAM para Amazon SES v2"
    "AWS_REGION:Región AWS para SES v2 (ej: us-east-1)"
    "AWS_SES_CONFIGURATION_SET:Configuration Set para entregabilidad SES"
    "RESEND_API_KEY:Clave de API de Resend (re_...)"
    "SMTP_HOST:Servidor SMTP Relay (ej: smtp.zeptomail.com)"
    "SMTP_PORT:Puerto SMTP (587 o 465)"
    "SMTP_USER:Usuario SMTP"
    "SMTP_PASSWORD:Contraseña SMTP"
)

G8_LOGISTICS_SHIPPING_KEYS=(
    "MIPAQUETE_API_KEY:Clave de API de MiPaquete.com (Agregador Multi-Transportadora & COD Colombia)"
    "MIPAQUETE_DEFAULT_ORIGIN_DANE:Código DANE 8 dígitos origen por defecto en MiPaquete (ej: 05001000)"
    "SKYDROPX_TOKEN:Token Bearer / API Key de Skydropx (Agregador Logístico LatAm)"
    "ENVIA_API_KEY:Token JWT / API Key de Envia.com"
    "COORDINADORA_API_KEY:Clave de API de Coordinadora Mercantil (Opcional contrato directo)"
    "COORDINADORA_CLIENT_ID:ID de cliente / código de cuenta Coordinadora (Opcional)"
    "SERVIENTREGA_USER:Usuario SISCLINET de Servientrega (Opcional contrato directo)"
    "SERVIENTREGA_PASSWORD:Password SISCLINET de Servientrega (Opcional)"
)

G9_CLOUDFLARE_DNS_KEYS=(
    "CLOUDFLARE_API_TOKEN:API Token de Cloudflare con permisos Zone.DNS:Edit, Zone:Read, SSL:Edit"
    "CLOUDFLARE_ZONE_ID:Zone ID del dominio principal en Cloudflare"
    "CLOUDFLARE_ACCOUNT_ID:Account ID de Cloudflare"
    "CLOUDFLARE_BASE_DOMAIN:Dominio raíz administrado en Cloudflare (ej: tudominio.com)"
)

G10_ASTRO_METAPHYSICAL_KEYS=(
    "FREEASTRO_API_KEY:Clave de FreeAstroAPI (Natal, Sideral, BaZi, Védica, Dasha)"
    "ASTROLOGY_API_IO:Clave de Astrology-API.io V3 / AstrologyAPI V1 (Gematría, Core Numbers, Tarot, KP)"
    "VEDASTRO_API_KEY:Clave de VedAstro (Predicciones clásicas y búsqueda semántica BPHS)"
    "ASTROWAY_API_KEY:Clave de AstroWay REST Engine (Swiss Ephemeris 760 Endpoints)"
    "KUNDALI_MCP_KEY:Clave de Servidor MCP Kundali"
    "NASA_API_KEY:Clave de API NASA Ephemeris / NeoWs"
)

# 1. Ingestión Universal desde archivo (.md, .env, markdown tables o multilínea)
declare -A PARSED_KEYS_MAP=()

if [ -n "$FILE_ARG" ] && [ -f "$FILE_ARG" ]; then
    echo "• Ingestando claves desde archivo: $FILE_ARG"
    while IFS='=' read -r k v; do
        [ -z "$k" ] && continue
        export "$k=$v"
        PARSED_KEYS_MAP["$k"]="$v"
    done < <(python3 - "$FILE_ARG" << 'EOF_PY'
import sys

path = sys.argv[1]
keys = {}
current_key = None

with open(path, "r", encoding="utf-8", errors="ignore") as f:
    for line in f:
        line = line.strip()
        if not line or line.startswith("#"):
            continue
        
        # Check export KEY=VAL or KEY=VAL
        if "=" in line:
            left, _, right = line.partition("=")
            left = left.strip()
            if left.startswith("export "):
                left = left[7:].strip()
            if left.isidentifier():
                v = right.strip()
                if not ((v.startswith('"') and v.endswith('"')) or (v.startswith("'") and v.endswith("'"))):
                    v = v.split(" #")[0].strip()
                v = v.strip("\"'")
                keys[left] = v
                current_key = None
                continue

        # Check markdown: - **KEY**: VAL or - KEY: VAL
        if ":" in line and not line.startswith("http"):
            left, _, right = line.partition(":")
            left = left.strip().lstrip("-* ").strip("*")
            if left.isidentifier():
                v = right.strip()
                if not ((v.startswith('"') and v.endswith('"')) or (v.startswith("'") and v.endswith("'"))):
                    v = v.split(" #")[0].strip()
                v = v.strip("\"'")
                keys[left] = v
                current_key = None
                continue

        # Check multiline
        if line.isidentifier():
            current_key = line
        elif current_key:
            v = line.strip()
            if not ((v.startswith('"') and v.endswith('"')) or (v.startswith("'") and v.endswith("'"))):
                v = v.split(" #")[0].strip()
            v = v.strip("\"'")
            keys[current_key] = v
            current_key = None

syns = {
    "FIRE_CRAWL_API": "FIRECRAWL_API_KEY",
    "FIRE_CRAWL_API_KEY": "FIRECRAWL_API_KEY",
    "GITHUB_API_KEY": "GITHUB_TOKEN",
    "ASTRO_WAY_API": "ASTROWAY_API_KEY",
    "ASTRO_API_KEY": "VEDASTRO_API_KEY",
}
for old_k, new_k in syns.items():
    if old_k in keys and new_k not in keys:
        keys[new_k] = keys[old_k]

for k, v in sorted(keys.items()):
    print(f"{k}={v}")
EOF_PY
    )
    echo "  ✓ Total claves parseadas e ingestadas desde archivo: ${#PARSED_KEYS_MAP[@]}"
fi

[ -z "${GITHUB_TOKEN:-}" ] && [ -n "${GITHUB_API_KEY:-}" ] && export GITHUB_TOKEN="$GITHUB_API_KEY"

# Auto-adopción nativa del token ZCP y paridad Z_TOKEN / ZEROPS_TOKEN
if [ -z "${ZCP_API_KEY:-}" ] && [ -f /etc/environment ]; then
    ZCP_API_KEY=$(grep -m1 '^ZCP_API_KEY=' /etc/environment | cut -d= -f2- | sed 's/["'\'']//g') || true
fi

if [ -n "${ZCP_API_KEY:-}" ]; then
    echo "  🛡️ Plataforma Zerops detectada (\$ZCP_API_KEY activa). Adoptando token oficial de runtime..."
    export Z_TOKEN="$ZCP_API_KEY"
    export ZEROPS_TOKEN="$ZCP_API_KEY"
    if [ -f /etc/environment ] && ! grep -q "^ZCP_API_KEY=" /etc/environment; then
        echo "ZCP_API_KEY=\"$ZCP_API_KEY\"" | sudo tee -a /etc/environment >/dev/null 2>&1 || true
    fi
elif [ -n "${ZEROPS_TOKEN:-}" ] && [ -z "${Z_TOKEN:-}" ]; then
    export Z_TOKEN="$ZEROPS_TOKEN"
elif [ -n "${Z_TOKEN:-}" ] && [ -z "${ZEROPS_TOKEN:-}" ]; then
    export ZEROPS_TOKEN="$Z_TOKEN"
fi

# Auto-derivaciones inteligentes de configuración
if [ -n "${AWS_ACCESS_KEY_ID:-}" ] && [ -n "${AWS_SECRET_ACCESS_KEY:-}" ]; then
    [ -z "${AWS_REGION:-}" ] && export AWS_REGION="us-east-1"
    [ -z "${SMTP_HOST:-}" ] && export SMTP_HOST="email-smtp.us-east-1.amazonaws.com"
    [ -z "${SMTP_PORT:-}" ] && export SMTP_PORT="587"
    [ -z "${SMTP_USER:-}" ] && export SMTP_USER="$AWS_ACCESS_KEY_ID"
    [ -z "${SMTP_PASSWORD:-}" ] && export SMTP_PASSWORD="$AWS_SECRET_ACCESS_KEY"
fi

if [ -n "${ZEPTOMAIL_SEND_MAIL_TOKEN:-}" ]; then
    [ -z "${SMTP_HOST:-}" ] && export SMTP_HOST="smtp.zeptomail.com"
    [ -z "${SMTP_PORT:-}" ] && export SMTP_PORT="587"
    [ -z "${SMTP_USER:-}" ] && export SMTP_USER="emailapikey"
    [ -z "${SMTP_PASSWORD:-}" ] && export SMTP_PASSWORD="$ZEPTOMAIL_SEND_MAIL_TOKEN"
fi

# 2. Auditar todas las claves
COLLECTED_EXPORTS=""

audit_group() {
    local group_title="$1"
    local is_required="$2"
    shift 2
    local keys_array=("$@")
    local missing_in_group=()

    echo ""
    echo "• [Módulo] $group_title"
    for item in "${keys_array[@]}"; do
        KEY_NAME="${item%%:*}"
        KEY_DESC="${item#*:}"
        
        RAW_VAL="${!KEY_NAME:-}"
        if [ -n "$RAW_VAL" ]; then
            CLEAN_VAL=$(sanitize_val "$RAW_VAL")
            export "$KEY_NAME=$CLEAN_VAL"
            echo "  ✅ $KEY_NAME: Configurada"
            COLLECTED_EXPORTS+="$KEY_NAME=$CLEAN_VAL"$'\n'
        else
            missing_in_group+=("$KEY_NAME:$KEY_DESC")
        fi
    done

    if [ "$INTERACTIVE" = true ] && [ ${#missing_in_group[@]} -gt 0 ]; then
        for item in "${missing_in_group[@]}"; do
            KEY_NAME="${item%%:*}"
            KEY_DESC="${item#*:}"
            read -r -s -p "  🔑 $KEY_NAME ($KEY_DESC) [o 'skip']: " INPUT_VAL
            echo ""
            CLEAN_INPUT=$(sanitize_val "$INPUT_VAL")
            if [ -n "$CLEAN_INPUT" ] && [ "$CLEAN_INPUT" != "skip" ] && [ "$CLEAN_INPUT" != "none" ]; then
                export "$KEY_NAME=$CLEAN_INPUT"
                COLLECTED_EXPORTS+="$KEY_NAME=$CLEAN_INPUT"$'\n'
                echo "    ✓ $KEY_NAME registrada"
            fi
        done
    elif [ ${#missing_in_group[@]} -gt 0 ] && [ "$is_required" = true ]; then
        echo "  ⚠️ ${#missing_in_group[@]} clave(s) base no detectadas. Se solicitarán al ejecutar operaciones."
    fi
}

audit_group "1. Base IA & Git" true "${G1_BASE_IA_KEYS[@]}"
audit_group "2. Google OAuth & Auth" false "${G2_GOOGLE_AUTH_KEYS[@]}"
audit_group "3. ERPNext & Facturación DIAN" false "${G3_ERP_BILLING_KEYS[@]}"
audit_group "4. WhatsApp Cloud & Evolution API" false "${G4_WHATSAPP_KEYS[@]}"
audit_group "5. Tracking & Conversiones (CAPI/GA4)" false "${G5_TRACKING_KEYS[@]}"
audit_group "6. Pasarelas de Pago (Wompi, ePayco, dLocal Go, Stripe, Mercado Pago)" false "${G6_PAYMENTS_GATEWAYS_KEYS[@]}"
audit_group "7. Email Marketing & Despacho de Correos" false "${G7_EMAIL_MARKETING_KEYS[@]}"
audit_group "8. Logística, Envíos & Pago Contra Entrega COD" false "${G8_LOGISTICS_SHIPPING_KEYS[@]}"
audit_group "9. Cloudflare API & Automatización DNS" false "${G9_CLOUDFLARE_DNS_KEYS[@]}"
audit_group "10. Motores Astrológicos & MCP" false "${G10_ASTRO_METAPHYSICAL_KEYS[@]}"

# 2.1 Ingestión Dinámica Universal de Claves Adicionales (Presentes, Nuevas y Futuras)
echo ""
echo "• [Módulo Dinámico] Ingestión de Claves Adicionales del Proyecto (Presentes y Futuras)"
DYNAMIC_KEYS_ADDED=0
for k in "${!PARSED_KEYS_MAP[@]}"; do
    if ! echo "$COLLECTED_EXPORTS" | grep -q "^$k="; then
        v="${PARSED_KEYS_MAP[$k]}"
        if [ -n "$v" ]; then
            masked_val="${v:0:3}...${v: -3}"
            [ ${#v} -le 8 ] && masked_val="<set>"
            echo "  🔑 $k: Ingestada dinámicamente ($masked_val)"
            COLLECTED_EXPORTS+="$k=$v"$'\n'
            DYNAMIC_KEYS_ADDED=$((DYNAMIC_KEYS_ADDED + 1))
        fi
    fi
done
[ "$DYNAMIC_KEYS_ADDED" -eq 0 ] && echo "  ℹ️ Todas las claves del archivo corresponden a los grupos auditados."

# 3. Persistir de forma universal y sanitizada en el entorno local
if [ -n "$COLLECTED_EXPORTS" ]; then
    echo ""
    echo "• Persistiendo variables de entorno en /etc/environment, .env y subshells..."
    sudo touch /etc/environment 2>/dev/null || true
    while IFS='=' read -r k v; do
        if [ -n "$k" ] && [ -n "$v" ]; then
            sudo sed -i "/^$k=/d" /etc/environment 2>/dev/null || true
            sudo bash -c "echo '$k=\"$v\"' >> /etc/environment" 2>/dev/null || true
        fi
    done <<< "$COLLECTED_EXPORTS"
    
    # Inyectar en subshells de usuario (sin escribir /var/www/.env para proteger el arranque en Zerops)
    for env_file in "$HOME/.env" "/home/zerops/.env"; do
        mkdir -p "$(dirname "$env_file")" 2>/dev/null || true
        touch "$env_file" 2>/dev/null || true
        while IFS='=' read -r k v; do
            if [ -n "$k" ] && [ -n "$v" ]; then
                sed -i "/^$k=/d" "$env_file" 2>/dev/null || true
                echo "$k=$v" >> "$env_file"
            fi
        done <<< "$COLLECTED_EXPORTS"
    done

    # Inyectar en profile.d para que cualquier subshell / login cargue variables desde /etc/environment
    sudo bash -c "cat << 'PROFILE_EOF' > /etc/profile.d/zerops_env.sh
set -a
[ -f /etc/environment ] && . /etc/environment
set +a
PROFILE_EOF" 2>/dev/null || true
    
    for rc in "$HOME/.bashrc" "/home/zerops/.bashrc" "/root/.bashrc"; do
        if [ -f "$rc" ]; then
            while IFS='=' read -r k v; do
                if [ -n "$k" ] && [ -n "$v" ]; then
                    sed -i "/export $k=/d" "$rc" 2>/dev/null || true
                    echo "export $k=\"$v\"" >> "$rc"
                fi
            done <<< "$COLLECTED_EXPORTS"
        fi
    done
    sudo chown -R zerops:zerops /home/zerops/.env 2>/dev/null || true
    rm -f /var/www/.env /var/www/gdrive.env 2>/dev/null || true
fi

# 4. Desplegar herramienta zeropsenv en el PATH
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
PERSISTENT_BIN="/var/www/.bin"
ZEROPSENV_SRC=""
if [ -f "$SCRIPT_DIR/zeropsenv" ]; then
    ZEROPSENV_SRC="$SCRIPT_DIR/zeropsenv"
elif [ -f "$SCRIPT_DIR/zeropsenv.sh" ]; then
    ZEROPSENV_SRC="$SCRIPT_DIR/zeropsenv.sh"
fi

if [ -n "$ZEROPSENV_SRC" ]; then
    echo "• Desplegando CLI zeropsenv (v2.0) en el PATH..."
    mkdir -p "$PERSISTENT_BIN" "$HOME/.local/bin" "/home/zerops/.local/bin" 2>/dev/null || true
    cp "$ZEROPSENV_SRC" "$PERSISTENT_BIN/zeropsenv" 2>/dev/null || true
    chmod +x "$PERSISTENT_BIN/zeropsenv" 2>/dev/null || true
    sudo ln -sf "$PERSISTENT_BIN/zeropsenv" /usr/local/bin/zeropsenv 2>/dev/null || true
    ln -sf "$PERSISTENT_BIN/zeropsenv" "$HOME/.local/bin/zeropsenv" 2>/dev/null || true
    ln -sf "$PERSISTENT_BIN/zeropsenv" "/home/zerops/.local/bin/zeropsenv" 2>/dev/null || true
    echo "  ✅ CLI zeropsenv disponible en el PATH"
fi

echo ""
echo "============================================================"
echo "  ✅ Ingestión de Claves Finalizada con Éxito (setup-keys.sh v3.4)"
echo "============================================================"
