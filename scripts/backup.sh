#!/usr/bin/env bash
# Database backup. Usage: ./scripts/backup.sh [output_dir]
set -euo pipefail
OUT="${1:-./backups}"; mkdir -p "$OUT"
TS=$(date +%Y%m%d_%H%M%S)
: "${DATABASE_URL:?set DATABASE_URL}"
# Strip the +asyncpg driver suffix for pg_dump.
PG_URL="${DATABASE_URL/+asyncpg/}"
pg_dump "$PG_URL" -Fc -f "$OUT/aisupport_$TS.dump"
echo "Backup written: $OUT/aisupport_$TS.dump"
