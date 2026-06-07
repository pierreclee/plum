import os
from fastapi import APIRouter, Depends, HTTPException, Header
from sqlalchemy.orm import Session
from typing import Optional
from database import get_db
from models import WorkerState
from schemas import WorkerStatusOut

router = APIRouter()


def verify_admin_key(x_admin_key: Optional[str] = Header(None)):
    expected = os.environ.get("ADMIN_KEY", "")
    if not expected or x_admin_key != expected:
        raise HTTPException(status_code=403, detail="Forbidden")


@router.post("/admin/refresh")
def trigger_refresh(
    db: Session = Depends(get_db),
    _=Depends(verify_admin_key),
):
    state = db.query(WorkerState).filter(WorkerState.id == 1).first()
    if not state:
        state = WorkerState(id=1)
        db.add(state)
    state.trigger_refresh = True
    db.commit()
    return {"status": "triggered"}


@router.get("/admin/worker-status", response_model=WorkerStatusOut)
def worker_status(
    db: Session = Depends(get_db),
    _=Depends(verify_admin_key),
):
    state = db.query(WorkerState).filter(WorkerState.id == 1).first()
    if not state:
        return WorkerStatusOut(status="idle", last_run_at=None, trigger_refresh=False)
    return WorkerStatusOut(
        status=state.status,
        last_run_at=state.last_run_at,
        trigger_refresh=state.trigger_refresh,
    )
