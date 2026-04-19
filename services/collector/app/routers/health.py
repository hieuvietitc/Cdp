from fastapi import APIRouter
from app.services.queue import get_queue_service

router = APIRouter()


@router.get("/health")
async def health():
    redis_ok = get_queue_service().ping()
    return {"status": "ok", "redis": "ok" if redis_ok else "error"}
