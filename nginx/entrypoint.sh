#!/bin/sh
set -e

# Choose the active template:
#   - If SSL certs exist for $SERVER_NAME, use the full HTTPS config.
#   - Otherwise fall back to HTTP-only (so nginx can still boot while certbot
#     performs its first issuance through /.well-known/acme-challenge/).
CERT_PATH="/etc/letsencrypt/live/${SERVER_NAME}/fullchain.pem"

if [ -f "$CERT_PATH" ]; then
    TEMPLATE=/etc/nginx/templates/default.conf.template
    echo "[nginx] certs found for ${SERVER_NAME}; using HTTPS config"
else
    TEMPLATE=/etc/nginx/templates-http-only/default.conf.template
    echo "[nginx] no certs yet for ${SERVER_NAME}; using HTTP-only bootstrap config"
fi

envsubst '${SERVER_NAME}' < "$TEMPLATE" > /etc/nginx/conf.d/default.conf

exec "$@"
