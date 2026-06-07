import logging
from datetime import datetime, timedelta, timezone
from sqlalchemy.orm import Session
from worker.models import ArticleRaw, Topic

logger = logging.getLogger(__name__)


def cleanup(db: Session) -> None:
    seven_days_ago = datetime.now(timezone.utc) - timedelta(days=7)
    thirty_days_ago = datetime.now(timezone.utc) - timedelta(days=30)

    deleted_articles = (
        db.query(ArticleRaw).filter(ArticleRaw.fetched_at < seven_days_ago).delete()
    )
    deleted_topics = (
        db.query(Topic).filter(Topic.created_at < thirty_days_ago).delete()
    )
    db.commit()
    logger.info("Cleaned %d articles and %d topics", deleted_articles, deleted_topics)
