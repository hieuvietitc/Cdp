import os
from pathlib import Path

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from prometheus_fastapi_instrumentator import Instrumentator

from app.routers import events, health
from app.middleware.rate_limit import RateLimitMiddleware

app = FastAPI(title="CDP Collector API", version="1.0.0", docs_url="/docs")
Instrumentator().instrument(app).expose(app, endpoint="/metrics")

# Rate limiting must be added before CORS so limits apply before preflight processing
app.add_middleware(RateLimitMiddleware)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)

app.include_router(health.router, tags=["health"])
app.include_router(events.router, prefix="/v1", tags=["events"])

# Serve the JS SDK — path resolution supports both Docker (mounted volume)
# and local dev (relative to repo root)
_SDK_CANDIDATES = [
    Path("/sdk/dist"),                          # Docker: volume mount
    Path(__file__).parents[4] / "sdk/js/dist",  # local dev: repo root
]
_sdk_dir = next((p for p in _SDK_CANDIDATES if p.is_dir()), None)
if _sdk_dir:
    app.mount("/sdk", StaticFiles(directory=str(_sdk_dir)), name="sdk")
