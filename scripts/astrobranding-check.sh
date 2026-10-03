#!/usr/bin/env bash
if [ -d "/var/www/zerops-astrobranding" ] && [ -f "/var/www/zerops-astrobranding/scripts/architecture-check.mjs" ]; then
    cd /var/www/zerops-astrobranding || exit 1
    if command -v bun; then
        bun scripts/architecture-check.mjs "$@"
    else
        node scripts/architecture-check.mjs "$@"
    fi
else
    echo "ℹ️ [astrobranding-check] /var/www/zerops-astrobranding no inicializado aún (omitiendo check de arquitectura)."
    exit 0
fi
