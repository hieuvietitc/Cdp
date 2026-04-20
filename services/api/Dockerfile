FROM python:3.11-slim

WORKDIR /app

COPY shared /app/shared
COPY services/api/requirements.txt /app/
RUN pip install --no-cache-dir -r requirements.txt && pip install -e /app/shared

COPY services/api/app /app/app

CMD ["uvicorn", "app.main:app", "--host", "0.0.0.0", "--port", "8000", "--workers", "2"]
