from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from app.routers import profiles, segments, activations, sources, auth, analytics

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
