#!/usr/bin/env bash
# Database restore. Usage: ./scripts/restore.sh path/to/backup.dump
set -euo pipefail
DUMP="${1:?path to .dump required}"
: "${DATABASE_URL:?set DATABASE_URL}"
PG_URL="${DATABASE_URL/+asyncpg/}"
pg_restore --clean --if-exists -d "$PG_URL" "$DUMP"
echo "Restore complete from $DUMP"
