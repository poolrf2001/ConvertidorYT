# ConvertidorYT

Convertidor de videos de YouTube a MP3 con interfaz web y app móvil nativa (iOS/Android), un único código base gracias a Expo. Incluye:

- Selección de calidad (128, 192 o 320 kbps).
- Metadatos ID3: título, artista y carátula embebida.
- Soporte de playlists completas.
- PWA instalable en móvil (sin pasar por tiendas).

## Aviso legal

Proyecto para **uso personal y educativo**. Descargar contenido de YouTube puede violar sus Términos de Servicio y la ley de derechos de autor. Úsalo solo con:
- contenido de tu propiedad,
- videos con licencia Creative Commons, o
- contenido autorizado por el titular de los derechos.

El uso que hagas es tu responsabilidad.

## Arquitectura

```
ConvertidorYT/
├── backend/    # FastAPI + yt-dlp + ffmpeg + mutagen (SQLite)
├── app/        # Expo (React Native) – Web + iOS + Android
└── nginx/      # reverse proxy (local HTTP, producción con TLS)
```

## Requisitos

- Python 3.10+
- Node 20+
- **ffmpeg** en el PATH
  - macOS: `brew install ffmpeg`
  - Ubuntu/Debian: `sudo apt install ffmpeg`
  - Windows: descarga desde https://ffmpeg.org/download.html y añade la ruta al PATH
- **Docker + Docker Compose** (para la opción B de arranque local)

---

## Opción A — Dev local sin Docker (recomendado para iterar rápido)

Dos terminales:

```bash
# Terminal 1 — backend
cd backend
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

```bash
# Terminal 2 — app
cd app
npm install
cp .env.example .env              # EXPO_PUBLIC_API_URL=http://localhost:8000
npx expo start
```

- Web: `http://localhost:8081`.
- Móvil: instala **Expo Go**, escanea el QR. El móvil debe estar en la misma red LAN y `EXPO_PUBLIC_API_URL` debe apuntar a la IP del PC (p. ej. `http://192.168.1.10:8000`).

## Opción B — Stack completo en local con Docker

Levanta los 3 contenedores (backend + app + nginx reverse proxy) igual que en producción, pero sin dominio ni TLS:

```bash
docker compose -f docker-compose.local.yml up --build
```

- Web: `http://localhost:8080`.
- Backend directo: `http://localhost:8000` (expuesto para hacer `curl`).
- Datos persistentes: `./.local-data/` (ignorado por git).

Para parar:

```bash
docker compose -f docker-compose.local.yml down
```

Úsalo para probar el build de producción antes de subirlo al droplet.

## Endpoints del backend

| Método | Ruta | Descripción |
|-------|------|-------------|
| POST | `/api/convert` | Inicia conversión: `{url, quality, playlist}` → `{job_id}` |
| GET | `/api/jobs/{id}` | Consulta estado, progreso y archivos |
| GET | `/api/download/{id}/{index}` | Descarga el MP3 producido |
| GET | `/api/health` | Health check |

## Pruebas manuales

1. Pega la URL de un video Creative Commons corto.
2. Elige 192 kbps y pulsa **Convertir a MP3**.
3. Espera a que la barra de progreso llegue al 100% y aparezca el archivo.
4. Descarga (web) o guarda en biblioteca (móvil).
5. Abre el MP3 en VLC/iTunes y verifica los tags ID3.

## Despliegue en producción

Cuando estés listo para mover el stack a un droplet con dominio + TLS, sigue la guía completa en [DEPLOY.md](DEPLOY.md). El `docker-compose.yml` raíz corresponde al perfil de producción; `docker-compose.local.yml` es solo para desarrollo.

## Límites por defecto

Configurables en `backend/.env` (o via env vars en producción):

| Variable | Default | Descripción |
|----------|---------|-------------|
| `MAX_DURATION_SECONDS` | 1200 (20 min) | Máxima duración por video |
| `MAX_PLAYLIST_ITEMS` | 20 | Máximo de pistas en una playlist |
| `JOB_RETENTION_SECONDS` | 86400 (24 h) | Cuánto guardar MP3s antes de borrarlos |

## Limitaciones conocidas

- Persistencia en SQLite local (suficiente para un solo host).
- Sin cuentas de usuario — hay rate limiting por IP.
- Para playlists muy largas conviene una cola real (Celery/Redis).

## Licencia

MIT.
