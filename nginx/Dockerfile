FROM nginx:1.27-alpine

# envsubst + openssl used by the entrypoint.
RUN apk add --no-cache openssl gettext

COPY default.conf.template /etc/nginx/templates/default.conf.template
COPY default-http-only.conf.template /etc/nginx/templates-http-only/default.conf.template
COPY entrypoint.sh /entrypoint.sh
RUN chmod +x /entrypoint.sh

ENTRYPOINT ["/entrypoint.sh"]
CMD ["nginx", "-g", "daemon off;"]
