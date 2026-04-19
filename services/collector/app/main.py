from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import events, health

app = FastAPI(title="CDP Collector API", version="1.0.0", docs_url="/docs")

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["GET", "POST", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization"],
)

app.include_router(health.router, tags=["health"])
app.include_router(events.router, prefix="/v1", tags=["events"])
