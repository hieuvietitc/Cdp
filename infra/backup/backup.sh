#!/usr/bin/env bash
# CDP PostgreSQL backup — runs daily via cron inside the backup container
# Backups are stored in /backups (mount a host volume or S3 fuse here)
set -euo pipefail

: "${POSTGRES_HOST:=postgres}"
: "${POSTGRES_PORT:=5432}"
: "${POSTGRES_USER:=cdp}"
: "${POSTGRES_PASSWORD:=cdppassword}"
: "${POSTGRES_DB:=cdpdb}"
: "${BACKUP_RETAIN_DAYS:=14}"
: "${BACKUP_DIR:=/backups}"

export PGPASSWORD="$POSTGRES_PASSWORD"

TIMESTAMP=$(date +%Y%m%d_%H%M%S)
BACKUP_FILE="${BACKUP_DIR}/cdp_${TIMESTAMP}.sql.gz"

mkdir -p "$BACKUP_DIR"

echo "[backup] Starting pg_dump → ${BACKUP_FILE}"
pg_dump \
  -h "$POSTGRES_HOST" \
  -p "$POSTGRES_PORT" \
  -U "$POSTGRES_USER" \
  -d "$POSTGRES_DB" \
  --no-password \
  --format=custom \
  --compress=9 \
  --schema=cdp \
  | gzip > "$BACKUP_FILE"

echo "[backup] Backup complete: $(du -sh "$BACKUP_FILE" | cut -f1)"

# Prune old backups
echo "[backup] Pruning backups older than ${BACKUP_RETAIN_DAYS} days..."
find "$BACKUP_DIR" -name "cdp_*.sql.gz" -mtime "+${BACKUP_RETAIN_DAYS}" -delete

echo "[backup] Remaining backups:"
ls -lh "$BACKUP_DIR"/cdp_*.sql.gz 2>/dev/null || echo "  (none)"

echo "[backup] Done."
