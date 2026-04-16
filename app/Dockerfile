# Stage 1 — build the Expo static web bundle.
FROM node:20-alpine AS builder

WORKDIR /app

COPY package.json ./
# npm install (no lockfile yet; once committed, this is reproducible)
RUN npm install --no-audit --no-fund

COPY . .

# EXPO_PUBLIC_* vars are baked at build time.
ARG EXPO_PUBLIC_API_URL=/
ENV EXPO_PUBLIC_API_URL=$EXPO_PUBLIC_API_URL

RUN npx expo export -p web

# Inject PWA manifest link + theme-color into the generated HTML so browsers
# can detect installability criteria at first paint.
RUN sed -i 's|</head>|<link rel="manifest" href="/manifest.webmanifest"><meta name="theme-color" content="#e11d48"></head>|' dist/index.html

# Stage 2 — serve the static bundle with nginx.
FROM nginx:1.27-alpine

COPY --from=builder /app/dist /usr/share/nginx/html

# Default nginx listens on 80; the outer reverse proxy terminates TLS.
EXPOSE 80
