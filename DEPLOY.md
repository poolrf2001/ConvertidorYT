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

Manual:

```bash
cd /opt/convertidoryt
git pull
docker compose up -d --build
```

Automático via GitHub Actions: configura los siguientes secrets del repo (`Settings → Secrets and variables → Actions`):

| Secret | Valor |
|--------|-------|
| `DROPLET_HOST` | IP o dominio del droplet |
| `DROPLET_USER` | usuario SSH (normalmente `root`) |
| `DROPLET_SSH_KEY` | clave privada con acceso al droplet |

Cada push a `main` dispara `.github/workflows/deploy.yml` que entra por SSH, hace `git pull` y reconstruye los contenedores.

## 9. Ver logs

```bash
docker compose logs -f backend
docker compose logs -f nginx
```

## 10. Backups automáticos

Hay un script listo en `scripts/backup.sh`. Configúralo en cron:

```bash
# como root en el droplet
crontab -e
# añade:
0 3 * * * /opt/convertidoryt/scripts/backup.sh /var/backups/convertidoryt 7 >> /var/log/convertidoryt-backup.log 2>&1
```

Deja 7 días de retención y borra automáticamente los tarballs viejos.

## 11. Monitorización

**Uptime externo** (gratis):
- Crea una cuenta en [UptimeRobot](https://uptimerobot.com/) o [Better Stack](https://betterstack.com/).
- Monitor HTTPS cada 5 min sobre `https://tudominio.com/api/health`.
- Alerta por email/Telegram si cae.

**Alerta de disco** (dentro del droplet):

```bash
cat > /usr/local/bin/disk-alert.sh <<'SH'
#!/bin/sh
USED=$(df -P / | awk 'NR==2 {print $5}' | tr -d '%')
if [ "$USED" -ge 85 ]; then
    echo "Disco al ${USED}% en $(hostname)" | mail -s "Disk alert" tu-email@ejemplo.com
fi
SH
chmod +x /usr/local/bin/disk-alert.sh
# añade a crontab:
# 0 * * * * /usr/local/bin/disk-alert.sh
```

## 12. Endurecer SSH con fail2ban

```bash
apt install -y fail2ban
cat > /etc/fail2ban/jail.d/sshd.conf <<'CONF'
[sshd]
enabled = true
port = ssh
maxretry = 5
bantime = 3600
findtime = 600
CONF
systemctl enable --now fail2ban
fail2ban-client status sshd
```

Opcional: deshabilita login por contraseña dejando solo clave SSH en `/etc/ssh/sshd_config` (`PasswordAuthentication no`).

---

## Troubleshooting

- **`init-letsencrypt.sh` falla con "connection refused"** → el DNS no ha propagado o el firewall bloquea 80. Verifica `dig +short tudominio.com` y `ufw status`.
- **La web carga pero `/api` devuelve 502** → backend no arrancó; revisa `docker compose logs backend`.
- **PWA no se instala** → asegúrate de usar HTTPS y que `manifest.webmanifest` se sirve en `https://tudominio.com/manifest.webmanifest`.
- **Disco lleno** → revisa el volumen `backend_data`; baja `JOB_RETENTION_SECONDS` en `.env`.
