# ConvertidorYT

Convertidor de videos de YouTube a MP3 con interfaz web y app móvil nativa (iOS/Android), un único código base gracias a Expo. Incluye:

- Selección de calidad (128, 192 o 320 kbps).
- Metadatos ID3: título, artista y carátula embebida.
- Soporte de playlists completas.

## Aviso legal

Este proyecto es para **uso personal y educativo**. Descargar contenido de YouTube puede violar sus Términos de Servicio y la ley de derechos de autor de tu país. Úsalo solo con:
- contenido de tu propiedad,
- videos con licencia Creative Commons, o
- contenido autorizado explícitamente por el titular de los derechos.

El uso que hagas es tu responsabilidad.

## Arquitectura

```
ConvertidorYT/
├── backend/    # FastAPI + yt-dlp + ffmpeg + mutagen
└── app/        # Expo (React Native) – Web + iOS + Android
```

## Requisitos

- Python 3.10+
- Node 20+
- **ffmpeg** en el PATH
  - macOS: `brew install ffmpeg`
  - Ubuntu/Debian: `sudo apt install ffmpeg`
  - Windows: descarga desde https://ffmpeg.org/download.html y añade la ruta al PATH

## Arranque del backend

```bash
cd backend
python -m venv venv
source venv/bin/activate          # Windows: venv\Scripts\activate
pip install -r requirements.txt
cp .env.example .env
uvicorn main:app --reload --host 0.0.0.0 --port 8000
```

Comprueba: `curl http://localhost:8000/api/health` → `{"ok": true}`.

## Arranque de la app (web + móvil)

```bash
cd app
npm install
cp .env.example .env              # apunta al backend (localhost:8000 por defecto)
npx expo start
```

- **Web**: abre `http://localhost:8081`.
- **Android / iOS**: instala **Expo Go** en tu móvil y escanea el QR del terminal. El móvil debe estar en la misma red y `EXPO_PUBLIC_API_URL` debe apuntar a la IP LAN del PC (p. ej. `http://192.168.1.10:8000`).

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

## Limitaciones conocidas

- El registro de jobs vive en memoria (reiniciar borra el historial).
- No hay autenticación ni cuotas.
- Para playlists muy largas conviene una cola real (Celery/Redis).

## Licencia

MIT.
