import os
from unittest.mock import patch
from datetime import datetime
from api.models import WorkerState


def test_refresh_without_key_returns_403(client):
    res = client.post("/api/admin/refresh")
    assert res.status_code == 403


def test_refresh_with_wrong_key_returns_403(client):
    with patch.dict(os.environ, {"ADMIN_KEY": "correct-secret"}):
        res = client.post("/api/admin/refresh", headers={"X-Admin-Key": "wrong"})
    assert res.status_code == 403


def test_refresh_with_correct_key_sets_trigger(client, db):
    with patch.dict(os.environ, {"ADMIN_KEY": "correct-secret"}):
        res = client.post("/api/admin/refresh", headers={"X-Admin-Key": "correct-secret"})
    assert res.status_code == 200
    assert res.json()["status"] == "triggered"
    state = db.query(WorkerState).first()
    assert state is not None
    assert state.trigger_refresh is True


def test_worker_status_without_key_returns_403(client):
    res = client.get("/api/admin/worker-status")
    assert res.status_code == 403


def test_worker_status_no_state_returns_idle(client):
    with patch.dict(os.environ, {"ADMIN_KEY": "secret"}):
        res = client.get("/api/admin/worker-status", headers={"X-Admin-Key": "secret"})
    assert res.status_code == 200
    assert res.json()["status"] == "idle"
    assert res.json()["trigger_refresh"] is False


def test_worker_status_returns_db_state(client, db):
    state = WorkerState(
        id=1, status="done",
        last_run_at=datetime(2026, 6, 7, 8, 0, 0),
        trigger_refresh=False,
    )
    db.add(state)
    db.commit()

    with patch.dict(os.environ, {"ADMIN_KEY": "secret"}):
        res = client.get("/api/admin/worker-status", headers={"X-Admin-Key": "secret"})
    assert res.status_code == 200
    assert res.json()["status"] == "done"
