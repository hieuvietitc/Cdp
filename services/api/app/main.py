import logging
import sys

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import profiles, segments, activations, sources, auth, analytics

logger = logging.getLogger(__name__)

# Hard-fail on startup if JWT secret is the default placeholder
from cdp_shared.config import settings as _settings
if _settings.jwt_secret_key in ("changeme", "changeme-in-production", ""):
    logger.critical(
        "JWT_SECRET_KEY is set to the insecure default value. "
        "Set a strong random secret in your .env before running in production."
    )
    # In production (non-dev), refuse to start
    import os
    if os.environ.get("ENVIRONMENT", "production") != "development":
        sys.exit(1)

app = FastAPI(title="CDP Admin API", version="1.0.0", docs_url="/docs")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.include_router(auth.router, prefix="/api/v1/auth", tags=["auth"])
app.include_router(profiles.router, prefix="/api/v1/profiles", tags=["profiles"])
app.include_router(segments.router, prefix="/api/v1/segments", tags=["segments"])
app.include_router(activations.router, prefix="/api/v1", tags=["activations"])
app.include_router(sources.router, prefix="/api/v1/sources", tags=["sources"])
app.include_router(analytics.router, prefix="/api/v1/analytics", tags=["analytics"])


@app.get("/health")
def health():
    return {"status": "ok"}
