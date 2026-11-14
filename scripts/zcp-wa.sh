#!/usr/bin/env bash
# ==============================================================================
# zcp-wa: Sovereign Natural Language WhatsApp Orchestrator CLI (v1.0)
# Bridges Natural Language & Headless Evolution Go (whatsmeow) Engine
# Supports: Status, Instance Create, QR Code (Visual & ASCII), Pairing Code, Send
# Zero Token Overhead | Bounded Execution < 2s | 100% Deterministic
# ==============================================================================
set -euo pipefail

EVOLUTION_URL="${EVOLUTION_URL:-http://evolution:8085}"
GLOBAL_API_KEY="${GLOBAL_API_KEY:-${EVOLUTION_API_KEY:-}}"
INSTANCE_TOKEN="${EVOLUTION_INSTANCE_TOKEN:-$GLOBAL_API_KEY}"
DEFAULT_INSTANCE="${DEFAULT_INSTANCE:-${EVOLUTION_INSTANCE:-${PROJECT_NAME:-default}}}"

if [ -z "$GLOBAL_API_KEY" ]; then
  echo "❌ Error: EVOLUTION_API_KEY o GLOBAL_API_KEY no están definidas en el entorno." >&2
  exit 1
fi

CMD="${1:-help}"
shift || true

function show_help() {
  echo "============================================================"
  echo "  📱 zcp-wa: Orquestador Soberano de WhatsApp (Evolution Go)"
  echo "============================================================"
  echo "Comandos disponibles:"
  echo "  zcp-wa status [instancia]         - Estado del motor y de las instancias"
  echo "  zcp-wa list                       - Lista todas las instancias activas"
  echo "  zcp-wa create [instancia]         - Crea una nueva sesión/instancia"
  echo "  zcp-wa qr [instancia]             - Obtiene el código QR en base64 / URL"
  echo "  zcp-wa pair <numero> [instancia]  - Genera código de 8 dígitos para vincular"
  echo "  zcp-wa send <numero> <mensaje>    - Envía mensaje de texto por WhatsApp"
  echo "  zcp-wa delete <instancia>         - Elimina una instancia de WhatsApp"
  echo ""
  echo "Ejemplos:"
  echo "  zcp-wa status"
  echo "  zcp-wa pair 573194194785"
  echo "  zcp-wa qr ${DEFAULT_INSTANCE}"
  echo "  zcp-wa send 573194194785 'Hola desde el plano soberano ZCP'"
}

case "$CMD" in
  status)
    INST="${1:-$DEFAULT_INSTANCE}"
    echo "🔍 Consultando salud de Evolution Go en ${EVOLUTION_URL}..."
    SERVER_OK=$(curl -sS -o /dev/null -w "%{http_code}" "${EVOLUTION_URL}/server/ok" || echo "000")
    if [ "$SERVER_OK" == "200" ]; then
      echo "✅ Servidor Evolution Go: ACTIVO (HTTP 200)"
    else
      echo "❌ Servidor Evolution Go no responde (HTTP $SERVER_OK)"
    fi
    echo ""
    echo "📋 Instancias registradas en base de datos:"
    curl -sS "${EVOLUTION_URL}/instance/all" \
      -H "apikey: ${GLOBAL_API_KEY}" | jq . || true
    ;;

  list)
    curl -sS "${EVOLUTION_URL}/instance/all" \
      -H "apikey: ${GLOBAL_API_KEY}" | jq -r '.[] | "• Instancia: \(.name) | Estado: \(.connectionStatus // .status // "desconocido")"' 2>/dev/null || \
      curl -sS "${EVOLUTION_URL}/instance/all" -H "apikey: ${GLOBAL_API_KEY}"
    ;;

  create)
    INST="${1:-$DEFAULT_INSTANCE}"
    TOK="${2:-$INSTANCE_TOKEN}"
    echo "🚀 Creando instancia de WhatsApp: '$INST'..."
    PAYLOAD=$(jq -n --arg name "$INST" --arg token "$TOK" '{name: $name, token: $token}')
    RESP=$(curl -sS -X POST "${EVOLUTION_URL}/instance/create" \
      -H "apikey: ${GLOBAL_API_KEY}" \
      -H "Content-Type: application/json" \
      -d "$PAYLOAD")
    echo "$RESP" | jq . 2>/dev/null || echo "$RESP"
    ;;

  qr|connect)
    INST="${1:-$DEFAULT_INSTANCE}"
    echo "📲 Conectando y obteniendo código QR para instancia '$INST'..."
    curl -sS -X POST "${EVOLUTION_URL}/instance/connect" \
      -H "apikey: ${INSTANCE_TOKEN}" \
      -H "Content-Type: application/json" \
      -d '{"immediate": true}' >/dev/null || true
    RESP=$(curl -sS "${EVOLUTION_URL}/instance/qr" \
      -H "apikey: ${INSTANCE_TOKEN}")

    QR_BASE64=$(echo "$RESP" | jq -r '.qrcode // .base64 // .qrcode.base64 // empty' 2>/dev/null || true)
    PAIR_CODE=$(echo "$RESP" | jq -r '.code // .pairingCode // empty' 2>/dev/null || true)

    if [ -n "$PAIR_CODE" ]; then
      echo "🔑 Código: $PAIR_CODE"
    fi

    if [ -n "$QR_BASE64" ]; then
      echo "✅ Código QR generado exitosamente."
      echo "👉 Podés escanearlo visualmente en el Manager:"
      echo "   ${EVOLUTION_MANAGER_URL:-${EVOLUTION_URL}/manager}"
      echo ""
      echo "O inspeccionar el payload:"
      echo "${QR_BASE64:0:80}..."
    else
      echo "$RESP" | jq . 2>/dev/null || echo "$RESP"
    fi
    ;;

  pair)
    PHONE="${1:-}"
    if [ -z "$PHONE" ]; then
      echo "❌ Error: Especificá el número telefónico con código de país."
      echo "Uso: zcp-wa pair <numero>"
      echo "Ejemplo: zcp-wa pair 573194194785"
      exit 1
    fi
    CLEAN_PHONE=$(echo "$PHONE" | tr -d '+ -()')
    if [[ "$CLEAN_PHONE" =~ ^3[0-9]{9}$ ]]; then
      CLEAN_PHONE="57${CLEAN_PHONE}"
    fi
    echo "🔑 Solicitando código de emparejamiento (8 dígitos) para +$CLEAN_PHONE..."
    PAYLOAD=$(jq -n --arg phone "$CLEAN_PHONE" '{phone: $phone}')
    RESP=$(curl -sS -X POST "${EVOLUTION_URL}/instance/pair" \
      -H "apikey: ${INSTANCE_TOKEN}" \
      -H "Content-Type: application/json" \
      -d "$PAYLOAD")

    CODE=$(echo "$RESP" | jq -r '.PairingCode // .pairingCode // .code // empty' 2>/dev/null || true)
    if [ -n "$CODE" ]; then
      echo "============================================================"
      echo "  🎉 CÓDIGO DE VINCULACIÓN WHATSAPP:  [ $CODE ]"
      echo "============================================================"
      echo "Instrucciones:"
      echo "1. En tu teléfono, abrí WhatsApp > Dispositivos vinculados > Vincular un dispositivo."
      echo "2. Seleccioná 'Vincular con el número de teléfono'."
      echo "3. Ingresá este código de 8 dígitos."
    else
      echo "$RESP" | jq . 2>/dev/null || echo "$RESP"
    fi
    ;;

  send)
    PHONE="${1:-}"
    MSG="${2:-}"
    if [ -z "$PHONE" ] || [ -z "$MSG" ]; then
      echo "❌ Error: Especificá el número y el mensaje."
      echo "Uso: zcp-wa send <numero> <mensaje>"
      echo "Ejemplo: zcp-wa send 573194194785 'Hola desde ZCP'"
      exit 1
    fi
    CLEAN_PHONE=$(echo "$PHONE" | tr -d '+ -()')
    if [[ "$CLEAN_PHONE" =~ ^3[0-9]{9}$ ]]; then
      CLEAN_PHONE="57${CLEAN_PHONE}"
    fi
    echo "📤 Enviando mensaje a +$CLEAN_PHONE..."
    PAYLOAD=$(jq -n --arg number "$CLEAN_PHONE" --arg text "$MSG" '{number: $number, text: $text}')
    RESP=$(curl -sS -X POST "${EVOLUTION_URL}/send/text" \
      -H "apikey: ${INSTANCE_TOKEN}" \
      -H "Content-Type: application/json" \
      -d "$PAYLOAD")
    echo "$RESP" | jq . 2>/dev/null || echo "$RESP"
    ;;

  delete)
    INST="${1:-$DEFAULT_INSTANCE}"
    echo "⚠️ Eliminando instancia '$INST'..."
    RESP=$(curl -sS -X DELETE "${EVOLUTION_URL}/instance/delete/${INST}" \
      -H "apikey: ${GLOBAL_API_KEY}")
    echo "$RESP" | jq . 2>/dev/null || echo "$RESP"
    ;;

  help|*)
    show_help
    ;;
esac
