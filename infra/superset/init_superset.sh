#!/usr/bin/env bash
# First-time Superset setup — run once after the container starts
set -euo pipefail

ADMIN_USER="${SUPERSET_ADMIN_USER:-admin}"
ADMIN_PASSWORD="${SUPERSET_ADMIN_PASSWORD:-admin}"
ADMIN_EMAIL="${SUPERSET_ADMIN_EMAIL:-admin@example.com}"

echo "[superset-init] Upgrading metadata DB..."
superset db upgrade

echo "[superset-init] Creating admin user..."
superset fab create-admin \
  --username "$ADMIN_USER" \
  --firstname "CDP" \
  --lastname "Admin" \
  --email "$ADMIN_EMAIL" \
  --password "$ADMIN_PASSWORD" 2>/dev/null || true

echo "[superset-init] Initializing Superset..."
superset init

echo "[superset-init] Registering CDP PostgreSQL datasource..."
python - <<'PYEOF'
import os
from superset import create_app
from superset.extensions import db
from superset.models.core import Database

app = create_app()
with app.app_context():
    cdp_url = os.environ.get("DATABASE_URL", "postgresql://cdp:cdppassword@postgres:5432/cdpdb")
    existing = db.session.query(Database).filter_by(database_name="CDP PostgreSQL").first()
    if not existing:
        d = Database(
            database_name="CDP PostgreSQL",
            sqlalchemy_uri=cdp_url,
            expose_in_sqllab=True,
            allow_run_async=True,
            allow_csv_upload=False,
        )
        db.session.add(d)
        db.session.commit()
        print("[superset-init] CDP PostgreSQL datasource registered.")
    else:
        print("[superset-init] CDP PostgreSQL datasource already exists, skipping.")
PYEOF

echo "[superset-init] Done. Starting Superset..."
exec superset run -p 8088 --with-threads --reload --debugger
