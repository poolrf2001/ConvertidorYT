#!/usr/bin/env bash
#
# Backup the backend data volume (SQLite DB + any pending downloads) to a
# dated tarball. Run from the repo root on the droplet, ideally from cron.
#
# Cron example (as root), keeps 7 days:
#   0 3 * * * /opt/convertidoryt/scripts/backup.sh /var/backups/convertidoryt 7 >> /var/log/convertidoryt-backup.log 2>&1
#
set -euo pipefail

DEST="${1:-/var/backups/convertidoryt}"
KEEP_DAYS="${2:-7}"
VOLUME="${COMPOSE_PROJECT_NAME:-convertidoryt}_backend_data"

mkdir -p "$DEST"
STAMP="$(date +%Y%m%d-%H%M%S)"
OUT="$DEST/backend-${STAMP}.tgz"

docker run --rm \
    -v "${VOLUME}:/data:ro" \
    -v "${DEST}:/backup" \
    alpine tar czf "/backup/$(basename "$OUT")" -C /data .

# Retention: delete archives older than $KEEP_DAYS days.
find "$DEST" -maxdepth 1 -name 'backend-*.tgz' -mtime "+${KEEP_DAYS}" -delete

echo "Backup OK: $OUT"
