from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import events, health
from app.middleware.rate_limit import RateLimitMiddleware

app = FastAPI(title="CDP Collector API", version="1.0.0", docs_url="/docs")

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
