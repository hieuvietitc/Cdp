# ── Stage 1: build JS SDK ─────────────────────────────────────────────────
FROM node:20-alpine AS sdk-builder
WORKDIR /sdk
COPY sdk/js/package.json ./
RUN npm install
COPY sdk/js/src ./src
COPY sdk/js/tsconfig.json ./
RUN npm run build          # → dist/cdp.min.js

# ── Stage 2: Python collector ─────────────────────────────────────────────
FROM python:3.11-slim

WORKDIR /app

COPY shared /app/shared
COPY services/collector/requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt && pip install -e /app/shared

COPY services/collector/app /app/app

# SDK built in stage 1 — served at /sdk/dist/cdp.min.js
COPY --from=sdk-builder /sdk/dist /sdk/dist

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "4"]
