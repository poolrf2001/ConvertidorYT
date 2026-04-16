#!/usr/bin/env bash
#
# Bootstraps Let's Encrypt certificates for the domain defined in .env.
# Run ONCE after DNS is pointing to the droplet and docker compose is up
# with the HTTP-only nginx config (nginx starts HTTP-only when certs are
# missing, so this script can perform the ACME handshake).
#
# Usage: ./init-letsencrypt.sh
#
set -euo pipefail

if [ ! -f .env ]; then
    echo "ERROR: .env not found. Copy .env.example to .env and edit it first." >&2
    exit 1
fi
# shellcheck disable=SC1091
set -a; . ./.env; set +a

: "${SERVER_NAME:?SERVER_NAME must be set in .env}"
: "${CERTBOT_EMAIL:?CERTBOT_EMAIL must be set in .env}"

STAGING="${STAGING:-0}"  # set STAGING=1 for Let's Encrypt staging (no rate limits)

echo "### Requesting certificate for ${SERVER_NAME} (staging=${STAGING}) ###"

STAGING_FLAG=""
if [ "$STAGING" = "1" ]; then
    STAGING_FLAG="--staging"
fi

docker compose run --rm --entrypoint "" certbot \
    certbot certonly --webroot -w /var/www/certbot \
        --email "$CERTBOT_EMAIL" \
        --agree-tos --no-eff-email \
        $STAGING_FLAG \
        -d "$SERVER_NAME"

echo "### Reloading nginx to pick up the new certificate ###"
docker compose restart nginx

echo "### Done. Visit https://${SERVER_NAME} ###"
