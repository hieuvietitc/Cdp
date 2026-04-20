FROM python:3.11-slim

WORKDIR /app

COPY shared /app/shared
COPY services/activation/requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt && pip install -e /app/shared

COPY services/activation/app /app/app

CMD ["celery", "-A", "app.worker", "worker", "-l", "info", "-Q", "cdp_activations", "-c", "2"]
