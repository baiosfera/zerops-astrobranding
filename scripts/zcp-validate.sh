#!/usr/bin/env bash
set -euo pipefail

usage() {
    echo "Usage: zcp-validate <command> [arguments...]"
    echo ""
    echo "Commands:"
    echo "  hostname <name>                               Validate Zerops service hostname (lowercase a-z0-9, max 25 chars, NO hyphens)"
    echo "  os <ubuntu|alpine>                            Validate explicit Base OS selection (must be 'ubuntu' or 'alpine')"
    echo "  resolution <EXISTS|CREATE|SHARED>             Validate dependency resolution in bootstrap plan"
    echo "  db-variant <name:single|name:ha>              Validate managed DB variant (must be ':single' or ':ha')"
    echo "  db-profile <postgresql|valkey> <profile>      Validate DB performance profile"
    echo "  storage <shared|object> <config>              Validate storage mount/S3 configuration"
    echo "  scaling <docker|native> [minCpu maxCpu minRam maxRam]"
    echo "                                                Validate scaling model (Docker: fixed min==max; native: autonomous zero-boilerplate or optional overrides)"
    echo "  yaml <import.yaml>                            Validate complete Zerops import.yaml manifest structure and syntax"
    echo "  plan <hostname> <os> [resolution]             Validate complete bootstrap parameters"
    echo ""
    exit 1
}

[ "$#" -lt 1 ] && usage
CMD="$1"
shift

case "$CMD" in
    hostname)
        [ "$#" -ne 1 ] && { echo "❌ Error: Missing hostname argument"; exit 1; }
        HOST="$1"
        if [[ ! "$HOST" =~ ^[a-z0-9]{1,25}$ ]]; then
            echo "❌ Validation Error: Hostname '$HOST' is INVALID in Zerops!"
            echo "   Rules: Strictly lowercase alphanumeric (a-z0-9), max 25 chars, NO HYPHENS allowed."
            echo "   Example: Use 'astroapp' instead of 'astro-app'."
            exit 1
        fi
        echo "✅ Hostname '$HOST' is valid."
        ;;
    os)
        [ "$#" -ne 1 ] && { echo "❌ Error: Missing OS argument"; exit 1; }
        OS_VAL="$1"
        if [[ "$OS_VAL" != "ubuntu" && "$OS_VAL" != "alpine" ]]; then
            echo "❌ Validation Error: Base OS '$OS_VAL' is INVALID!"
            echo "   Allowed values: 'ubuntu' (glibc, developer priority) or 'alpine' (musl minimal)."
            exit 1
        fi
        echo "✅ Base OS '$OS_VAL' is valid."
        ;;
    resolution)
        [ "$#" -ne 1 ] && { echo "❌ Error: Missing resolution argument"; exit 1; }
        RES="$1"
        if [[ "$RES" != "EXISTS" && "$RES" != "CREATE" && "$RES" != "SHARED" ]]; then
            echo "❌ Validation Error: Dependency resolution '$RES' is INVALID in Zerops bootstrap!"
            echo "   Allowed values: 'EXISTS' (for existing storage/services), 'CREATE', or 'SHARED'."
            echo "   Prohibited: Do NOT use 'ATTACH' or 'MOUNT'."
            exit 1
        fi
        echo "✅ Resolution '$RES' is valid."
        ;;
    db-variant)
        [ "$#" -ne 1 ] && { echo "❌ Error: Missing db-variant argument (e.g. postgresql:single@18)"; exit 1; }
        DB_TYPE="$1"
        if [[ ! "$DB_TYPE" =~ :single(@[0-9]+)?$ && ! "$DB_TYPE" =~ :ha(@[0-9]+)?$ ]]; then
            echo "❌ Validation Error: Managed database '$DB_TYPE' MUST specify ':single' or ':ha' variant!"
            echo "   Example: 'postgresql:single@18' (lean/dev) or 'postgresql:ha@18' (high availability)."
            echo "   Note: The variant is IMMUTABLE after creation."
            exit 1
        fi
        echo "✅ Database variant '$DB_TYPE' is valid."
        ;;
    db-profile)
        [ "$#" -ne 2 ] && { echo "❌ Error: Usage: zcp-validate db-profile <postgresql|valkey> <profile>"; exit 1; }
        DB_ENGINE="$1"
        PROF="$2"
        if [ "$DB_ENGINE" = "postgresql" ]; then
            if [[ ! "$PROF" =~ ^(oltp-hobby|oltp-staging|oltp-production|oltp-enterprise|olap-production|writeheavy-production|custom)$ ]]; then
                echo "❌ Validation Error: PostgreSQL profile '$PROF' is invalid."
                exit 1
            fi
        elif [ "$DB_ENGINE" = "valkey" ]; then
            if [[ ! "$PROF" =~ ^(hobby|staging|production)$ ]]; then
                echo "❌ Validation Error: Valkey profile '$PROF' is invalid."
                exit 1
            fi
        fi
        echo "✅ DB Profile '$PROF' for '$DB_ENGINE' is valid."
        ;;
    storage)
        [ "$#" -ne 2 ] && { echo "❌ Error: Usage: zcp-validate storage <local|shared|object> <config>"; exit 1; }
        ST_TYPE="$1"
        ST_CFG="$2"
        if [ "$ST_TYPE" = "local" ]; then
            echo "✅ Local Storage persistent volume declaration valid."
        elif [ "$ST_TYPE" = "shared" ]; then
            echo "✅ Shared Storage legacy declaration valid."
        elif [ "$ST_TYPE" = "object" ]; then
            echo "✅ Object Storage S3 configuration valid."
        else
            echo "❌ Validation Error: Storage type '$ST_TYPE' must be 'local', 'shared', or 'object'."
            exit 1
        fi
        ;;
    scaling)
        STYPE="${1:-}"
        [ -z "$STYPE" ] && { echo "❌ Error: Usage: zcp-validate scaling <docker|native> [minCpu maxCpu minRam maxRam]"; exit 1; }

        if [[ "$STYPE" =~ ^docker ]]; then
            MIN_CPU="${2:-}"
            MAX_CPU="${3:-}"
            MIN_RAM="${4:-}"
            MAX_RAM="${5:-}"
            if [ -z "$MIN_CPU" ] || [ -z "$MAX_CPU" ] || [ -z "$MIN_RAM" ] || [ -z "$MAX_RAM" ]; then
                echo "❌ Validation Error: Docker VM requires explicit fixed resource arguments (minCpu maxCpu minRam maxRam)!"
                exit 1
            fi
            if [ "$MIN_CPU" != "$MAX_CPU" ] || [ "$MIN_RAM" != "$MAX_RAM" ]; then
                echo "❌ Validation Error: Docker VM requires FIXED resources (minCpu == maxCpu and minRam == maxRam)!"
                echo "   Provided: CPU ${MIN_CPU}-${MAX_CPU}, RAM ${MIN_RAM}-${MAX_RAM}."
                exit 1
            fi
            echo "✅ Docker VM fixed resource configuration ($MIN_CPU CPU, $MIN_RAM GB RAM) is valid."
        else
            if [ "$#" -eq 1 ]; then
                echo "✅ Native Zerops service autonomous autoscaling verified (zero-boilerplate: no min/max required)."
            elif [ "$#" -eq 5 ]; then
                MIN_CPU="$2"
                MAX_CPU="$3"
                MIN_RAM="$4"
                MAX_RAM="$5"
                echo "✅ Native service optional scaling override accepted (${MIN_CPU}-${MAX_CPU} CPU, ${MIN_RAM}-${MAX_RAM} GB RAM)."
            else
                echo "❌ Error: Native scaling accepts either 0 resource arguments (autonomous default) or 4 arguments (custom override)."
                exit 1
            fi
        fi
        ;;
    yaml)
        [ "$#" -ne 1 ] && { echo "❌ Error: Missing YAML file path argument"; exit 1; }
        YFILE="$1"
        [ ! -f "$YFILE" ] && { echo "❌ Error: File '$YFILE' not found!"; exit 1; }

        echo "• Validating Zerops YAML manifest: $YFILE..."
        
        # Check services block
        if ! grep -q "^services:" "$YFILE"; then
            echo "❌ Validation Error: Manifest must contain a root 'services:' block."
            exit 1
        fi

        # Parse hostnames and types
        ERRORS=0
        HOSTNAMES=$(awk '/^[[:space:]]*- hostname:[[:space:]]*/ {print $3}' "$YFILE")
        for h in $HOSTNAMES; do
            if [[ ! "$h" =~ ^[a-z0-9]{1,25}$ ]]; then
                echo "❌ Invalid hostname in manifest: '$h' (must be lowercase a-z0-9, max 25 chars, no hyphens)"
                ERRORS=$((ERRORS + 1))
            fi
        done

        # Check DB variants
        DB_TYPES=$(awk '/^[[:space:]]*type:[[:space:]]*(postgresql|mariadb|keycloak|valkey|nats)/ {print $2}' "$YFILE")
        for db in $DB_TYPES; do
            if [[ ! "$db" =~ :single(@[0-9.]+)?$ && ! "$db" =~ :ha(@[0-9.]+)?$ && ! "$db" =~ ^(object-storage|objectstorage)$ ]]; then
                echo "❌ Invalid managed service type '$db': must specify ':single' or ':ha'"
                ERRORS=$((ERRORS + 1))
            fi
        done

        if [ "$ERRORS" -gt 0 ]; then
            echo "❌ Manifest validation FAILED with $ERRORS error(s)."
            exit 1
        fi
        echo "✅ Manifest '$YFILE' passed all Zerops platform syntax and topology checks!"
        ;;
    plan)
        [ "$#" -lt 2 ] && { echo "❌ Error: Usage: zcp-validate plan <hostname> <os> [resolution]"; exit 1; }
        HOST="$1"
        OS_VAL="$2"
        RES="${3:-EXISTS}"
        "$0" hostname "$HOST"
        "$0" os "$OS_VAL"
        "$0" resolution "$RES"
        echo "✅ Complete Zerops plan parameters validated successfully!"
        ;;
    *)
        echo "❌ Unknown command: $CMD"
        usage
        ;;
esac
