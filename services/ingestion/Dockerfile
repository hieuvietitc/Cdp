FROM python:3.11-slim

WORKDIR /app

COPY shared /app/shared
COPY services/ingestion/requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt && pip install -e /app/shared

COPY services/ingestion/app /app/app

CMD ["python", "-m", "app.scheduler"]
