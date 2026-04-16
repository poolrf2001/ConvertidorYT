# Despliegue en Digital Ocean

Guía paso a paso para levantar ConvertidorYT en un droplet con Docker, nginx y HTTPS automático (Let's Encrypt).

---

## 1. Crear el droplet

1. En Digital Ocean → **Create → Droplets**.
2. Imagen: **Ubuntu 22.04 LTS**.
3. Plan: Basic / Regular — 2 GB RAM mínimo (ffmpeg consume algo de CPU).
4. Región cercana a tus usuarios.
5. Autenticación: **SSH key** (añade tu clave pública).
6. Hostname descriptivo, p. ej. `convertidoryt`.

Una vez creado, anota la **IP pública**.

## 2. Apuntar el dominio al droplet

En tu proveedor de DNS, crea un registro **A**:

| Tipo | Host | Valor | TTL |
|------|------|-------|-----|
| A | `@` (o subdominio) | IP del droplet | 3600 |

Espera a que propague (`dig +short tudominio.com` debe devolver la IP).

## 3. Acceder y preparar el droplet

```bash
ssh root@IP_DEL_DROPLET

# Actualizar e instalar Docker
apt update && apt upgrade -y
apt install -y ca-certificates curl git ufw
install -m 0755 -d /etc/apt/keyrings
curl -fsSL https://download.docker.com/linux/ubuntu/gpg -o /etc/apt/keyrings/docker.asc
chmod a+r /etc/apt/keyrings/docker.asc
echo "deb [arch=$(dpkg --print-architecture) signed-by=/etc/apt/keyrings/docker.asc] \
  https://download.docker.com/linux/ubuntu $(. /etc/os-release && echo "$VERSION_CODENAME") stable" \
  > /etc/apt/sources.list.d/docker.list
apt update
apt install -y docker-ce docker-ce-cli containerd.io docker-buildx-plugin docker-compose-plugin

# Firewall
ufw allow OpenSSH
ufw allow 80/tcp
ufw allow 443/tcp
ufw --force enable
```

## 4. Clonar el repo y configurar

```bash
cd /opt
git clone https://github.com/poolrf2001/convertidoryt.git
cd convertidoryt

cp .env.example .env
nano .env
```

Edita `.env`:

```
SERVER_NAME=tudominio.com
ALLOWED_ORIGINS=https://tudominio.com
CERTBOT_EMAIL=tu-email@ejemplo.com
```

## 5. Primer arranque (HTTP) y emisión de certificados

El contenedor nginx detecta que aún no hay certificados y arranca con una configuración **solo HTTP**, suficiente para responder al reto ACME de Let's Encrypt.

```bash
docker compose up -d --build
docker compose ps            # los 4 servicios deben estar "running"
curl http://tudominio.com/api/health   # debe responder {"ok":true}
```

Ahora emite el certificado:

```bash
# Opcional: prueba primero con el entorno staging (sin rate limits) si tienes dudas
# STAGING=1 ./init-letsencrypt.sh

./init-letsencrypt.sh
```

El script usa certbot vía webroot; al terminar reinicia nginx y pasa a servir HTTPS.

Verifica:

```bash
curl https://tudominio.com/api/health   # {"ok":true}
```

## 6. Comprobaciones

- Abre `https://tudominio.com` en el navegador.
- Prueba a convertir un video corto (contenido libre/propio).
- En Chrome Android/desktop aparecerá "Añadir a pantalla de inicio" (PWA).
- Los MP3 quedan en el volumen `backend_data` dentro del droplet. Se limpian automáticamente tras `JOB_RETENTION_SECONDS` (24 h por defecto).

## 7. Renovación automática

El contenedor `certbot` ejecuta `certbot renew` cada 12 horas de forma silenciosa. No hace falta cron en el host.

## 8. Actualizar la app

```bash
cd /opt/convertidoryt
git pull
docker compose up -d --build
```

## 9. Ver logs

```bash
docker compose logs -f backend
docker compose logs -f nginx
```

## 10. Backups (recomendado)

Haz backup periódico del volumen `backend_data` (contiene `jobs.db`). Ejemplo:

```bash
docker run --rm -v convertidoryt_backend_data:/data -v $(pwd):/backup alpine \
    tar czf /backup/backend-$(date +%F).tgz -C /data .
```

---

## Troubleshooting

- **`init-letsencrypt.sh` falla con "connection refused"** → el DNS no ha propagado o el firewall bloquea 80. Verifica `dig +short tudominio.com` y `ufw status`.
- **La web carga pero `/api` devuelve 502** → backend no arrancó; revisa `docker compose logs backend`.
- **PWA no se instala** → asegúrate de usar HTTPS y que `manifest.webmanifest` se sirve en `https://tudominio.com/manifest.webmanifest`.
- **Disco lleno** → revisa el volumen `backend_data`; baja `JOB_RETENTION_SECONDS` en `.env`.
