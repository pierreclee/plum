from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy.orm import Session
from typing import Optional
from database import get_db
from models import Topic, TopicArticle, ArticleRaw, WorkerState
from schemas import FeedResponse, TopicOut, FeedMeta

router = APIRouter()

CATEGORIES = ["france", "monde", "tech", "eco", "sport"]


@router.get("/categories", response_model=list[str])
def get_categories():
    return CATEGORIES


@router.get("/feed", response_model=FeedResponse)
def get_feed(
    category: Optional[str] = None,
    limit: int = Query(default=20, ge=1, le=100),
    offset: int = Query(default=0, ge=0),
    db: Session = Depends(get_db),
):
    if category and category not in CATEGORIES:
        raise HTTPException(status_code=422, detail=f"Invalid category. Must be one of: {CATEGORIES}")

    query = db.query(Topic).filter(Topic.summary_status.in_(["done", "failed"]))
    if category:
        query = query.filter(Topic.category == category)

    total = query.count()
    topics = query.order_by(Topic.published_at.desc()).offset(offset).limit(limit).all()

    state = db.query(WorkerState).first()
    last_updated = state.last_run_at if state else None

    data = [_build_topic_out(topic, db) for topic in topics]
    return FeedResponse(data=data, meta=FeedMeta(total=total, last_updated=last_updated))


@router.get("/feed/{topic_id}", response_model=TopicOut)
def get_topic(topic_id: str, db: Session = Depends(get_db)):
    topic = db.query(Topic).filter(Topic.id == topic_id).first()
    if not topic:
        raise HTTPException(status_code=404, detail="Topic not found")
    return _build_topic_out(topic, db)


def _build_topic_out(topic: Topic, db: Session) -> TopicOut:
    sources = (
        db.query(ArticleRaw.source_name)
        .join(TopicArticle, TopicArticle.article_raw_id == ArticleRaw.id)
        .filter(TopicArticle.topic_id == topic.id)
        .distinct()
        .all()
    )
    return TopicOut(
        id=topic.id,
        title=topic.title,
        summary=topic.summary,
        category=topic.category,
        article_count=topic.article_count,
        published_at=topic.published_at,
        sources=[s[0] for s in sources],
    )
