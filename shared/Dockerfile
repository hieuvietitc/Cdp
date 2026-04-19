FROM python:3.11-slim

WORKDIR /app

COPY shared/pyproject.toml /app/shared/
COPY shared/cdp_shared /app/shared/cdp_shared/
COPY migrations /app/migrations/
COPY alembic.ini /app/

RUN pip install -e /app/shared

CMD ["alembic", "upgrade", "head"]
