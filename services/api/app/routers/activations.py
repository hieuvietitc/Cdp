import uuid
from datetime import datetime, timezone

from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy import select
from sqlalchemy.orm import Session

from cdp_shared.db import get_db
from cdp_shared.models.activation import Activation, Destination, ActivationEvent
from cdp_shared.schemas.activation import ActivationCreate, ActivationOut, DestinationCreate, DestinationOut
from app.auth.jwt import get_current_user

router = APIRouter()


# ── Destinations ───────────────────────────────────────────────────────────

@router.get("/destinations", response_model=list[DestinationOut])
def list_destinations(db: Session = Depends(get_db), _=Depends(get_current_user)):
    return db.execute(select(Destination).where(Destination.is_active == True)).scalars().all()


@router.post("/destinations", response_model=DestinationOut, status_code=201)
def create_destination(body: DestinationCreate, db: Session = Depends(get_db), _=Depends(get_current_user)):
    dest = Destination(name=body.name, type=body.type, config=body.config)
    db.add(dest)
    db.commit()
    db.refresh(dest)
    return dest


@router.post("/destinations/{dest_id}/test")
def test_destination(dest_id: uuid.UUID, db: Session = Depends(get_db), _=Depends(get_current_user)):
    dest = db.get(Destination, dest_id)
    if not dest:
        raise HTTPException(status_code=404, detail="Destination not found")
    from app.routers._dest_factory import get_destination_instance
    instance = get_destination_instance(dest)
    ok = instance.test()
    return {"ok": ok}


# ── Activations ────────────────────────────────────────────────────────────

@router.get("/activations", response_model=list[ActivationOut])
def list_activations(db: Session = Depends(get_db), _=Depends(get_current_user)):
    return db.execute(select(Activation).order_by(Activation.created_at.desc())).scalars().all()


@router.post("/activations", response_model=ActivationOut, status_code=201)
def create_activation(body: ActivationCreate, db: Session = Depends(get_db), _=Depends(get_current_user)):
    activation = Activation(
        segment_id=body.segment_id,
        destination_id=body.destination_id,
        trigger_type=body.trigger_type,
        status="pending",
    )
    db.add(activation)
    db.commit()
    db.refresh(activation)

    from app.celery_client import get_celery
    get_celery().send_task(
        "app.tasks.dispatch.run_activation",
        args=[str(activation.id)],
        queue="cdp_activations",
    )
    return activation


@router.get("/activations/{activation_id}", response_model=ActivationOut)
def get_activation(activation_id: uuid.UUID, db: Session = Depends(get_db), _=Depends(get_current_user)):
    act = db.get(Activation, activation_id)
    if not act:
        raise HTTPException(status_code=404, detail="Activation not found")
    return act


@router.get("/activations/{activation_id}/log")
def get_activation_log(
    activation_id: uuid.UUID,
    db: Session = Depends(get_db),
    _=Depends(get_current_user),
):
    rows = db.execute(
        select(ActivationEvent)
        .where(ActivationEvent.activation_id == activation_id)
        .limit(500)
    ).scalars().all()
    return [{"profile_id": str(r.profile_id), "status": r.status, "sent_at": r.sent_at.isoformat()} for r in rows]
