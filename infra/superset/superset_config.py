import os

SECRET_KEY = os.environ.get("SUPERSET_SECRET_KEY", "superset-change-me-in-production")
SQLALCHEMY_DATABASE_URI = os.environ.get(
    "SUPERSET_DB_URL",
    "postgresql://cdp:cdppassword@postgres:5432/cdpdb"
)

# CDP data source — pre-registered in init script
CDP_DATABASE_URL = os.environ.get(
    "DATABASE_URL",
    "postgresql://cdp:cdppassword@postgres:5432/cdpdb"
)

WTF_CSRF_ENABLED = True
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_SECURE = False  # set True behind HTTPS
TALISMAN_ENABLED = False

# Feature flags
FEATURE_FLAGS = {
    "ENABLE_TEMPLATE_PROCESSING": True,
    "DASHBOARD_NATIVE_FILTERS": True,
    "DASHBOARD_CROSS_FILTERS": True,
}

# Cache
CACHE_CONFIG = {
    "CACHE_TYPE": "RedisCache",
    "CACHE_DEFAULT_TIMEOUT": 300,
    "CACHE_KEY_PREFIX": "superset_",
    "CACHE_REDIS_URL": os.environ.get("REDIS_URL", "redis://redis:6379/3"),
}

DATA_CACHE_CONFIG = {
    "CACHE_TYPE": "RedisCache",
    "CACHE_DEFAULT_TIMEOUT": 600,
    "CACHE_KEY_PREFIX": "superset_data_",
    "CACHE_REDIS_URL": os.environ.get("REDIS_URL", "redis://redis:6379/3"),
}

RESULTS_BACKEND = None  # set to Redis for async queries at scale

# Row limit guards
SQL_MAX_ROW = 100000
SAMPLES_ROW_LIMIT = 1000
ROW_LIMIT = 10000
