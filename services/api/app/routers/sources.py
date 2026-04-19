import secrets
import uuid

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.orm import Session

from cdp_shared.db import get_db
from cdp_shared.models.source import Source
from cdp_shared.redis_client import get_redis
from app.auth.jwt import get_current_user

router = APIRouter()


class SourceCreate(BaseModel):
    name: str
    type: str  # web | ios | android | server


@router.get("")
def list_sources(db: Session = Depends(get_db), _=Depends(get_current_user)):
    sources = db.execute(select(Source)).scalars().all()
    return [{"id": str(s.id), "name": s.name, "type": s.type, "write_key": s.write_key, "is_active": s.is_active} for s in sources]


@router.post("", status_code=201)
def create_source(body: SourceCreate, db: Session = Depends(get_db), _=Depends(get_current_user)):
    write_key = "wk_" + secrets.token_hex(24)
    source = Source(name=body.name, type=body.type, write_key=write_key)
    db.add(source)
    db.commit()
    get_redis().setex(f"cdp:write_key:{write_key}", 86400, "1")
    return {"id": str(source.id), "name": source.name, "write_key": write_key}


@router.post("/{source_id}/rotate-key")
def rotate_key(source_id: uuid.UUID, db: Session = Depends(get_db), _=Depends(get_current_user)):
    source = db.get(Source, source_id)
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    old_key = source.write_key
    new_key = "wk_" + secrets.token_hex(24)
    source.write_key = new_key
    db.commit()
    r = get_redis()
    r.delete(f"cdp:write_key:{old_key}")
    r.setex(f"cdp:write_key:{new_key}", 86400, "1")
    return {"write_key": new_key}


@router.delete("/{source_id}", status_code=204)
def delete_source(source_id: uuid.UUID, db: Session = Depends(get_db), _=Depends(get_current_user)):
    source = db.get(Source, source_id)
    if not source:
        raise HTTPException(status_code=404, detail="Source not found")
    source.is_active = False
    db.commit()
