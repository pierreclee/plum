import logging
import time
from datetime import datetime, timezone

from apscheduler.schedulers.background import BackgroundScheduler
from sqlalchemy.orm import Session

from database import SessionLocal, engine, Base
from models import WorkerState
from ingestion import ingest
from clustering import cluster_and_save
from summarizer import summarize_pending
from cleanup import cleanup

logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s %(levelname)s %(name)s %(message)s",
)
logger = logging.getLogger(__name__)


def run_pipeline() -> None:
    logger.info("Pipeline starting")
    db: Session = SessionLocal()
    try:
        state = db.query(WorkerState).filter(WorkerState.id == 1).first()
        if not state:
            state = WorkerState(id=1)
            db.add(state)

        state.status = "running"
        state.trigger_refresh = False
        db.commit()

        ingest(db)
        cluster_and_save(db)
        summarize_pending(db)
        cleanup(db)

        state.status = "done"
        state.last_run_at = datetime.now(timezone.utc)
        db.commit()
        logger.info("Pipeline complete")
    except Exception as exc:
        logger.error("Pipeline failed: %s", exc, exc_info=True)
        try:
            state.status = "idle"
            db.commit()
        except Exception:
            pass
    finally:
        db.close()


def poll_trigger() -> None:
    db: Session = SessionLocal()
    try:
        state = db.query(WorkerState).filter(WorkerState.id == 1).first()
        if state and state.trigger_refresh and state.status != "running":
            logger.info("Manual refresh triggered via API")
            db.close()
            run_pipeline()
    except Exception as exc:
        logger.error("Trigger poll error: %s", exc)
    finally:
        try:
            db.close()
        except Exception:
            pass


if __name__ == "__main__":
    Base.metadata.create_all(bind=engine)

    scheduler = BackgroundScheduler(timezone="Europe/Paris")
    scheduler.add_job(run_pipeline, "cron", hour="7,12,18", minute=0, id="scheduled_pipeline")
    scheduler.add_job(poll_trigger, "interval", seconds=30, id="trigger_poll")
    scheduler.start()

    logger.info("Worker started — scheduled at 7h, 12h, 18h Paris time")

    try:
        while True:
            time.sleep(60)
    except (KeyboardInterrupt, SystemExit):
        scheduler.shutdown()
        logger.info("Worker stopped")
