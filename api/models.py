import uuid
from datetime import datetime, timezone
from sqlalchemy import Column, String, Integer, Boolean, DateTime, Text, ForeignKey
from .database import Base


def new_uuid() -> str:
    return str(uuid.uuid4())


def utcnow():
    return datetime.now(timezone.utc)


class ArticleRaw(Base):
    __tablename__ = "articles_raw"

    id = Column(String, primary_key=True, default=new_uuid)
    url_hash = Column(String, unique=True, nullable=False)
    source_url = Column(String, nullable=False)
    title = Column(String, nullable=False)
    content = Column(Text)
    published_at = Column(DateTime(timezone=True))
    source_name = Column(String, nullable=False)
    category = Column(String, nullable=False)
    fetched_at = Column(DateTime(timezone=True), default=utcnow)


class Topic(Base):
    __tablename__ = "topics"

    id = Column(String, primary_key=True, default=new_uuid)
    title = Column(String, nullable=False)
    category = Column(String, nullable=False)
    article_count = Column(Integer, nullable=False, default=0)
    summary = Column(Text)
    summary_status = Column(String, nullable=False, default="pending")
    published_at = Column(DateTime(timezone=True), nullable=False)
    created_at = Column(DateTime(timezone=True), default=utcnow)


class TopicArticle(Base):
    __tablename__ = "topic_articles"

    topic_id = Column(String, ForeignKey("topics.id", ondelete="CASCADE"), primary_key=True)
    article_raw_id = Column(String, ForeignKey("articles_raw.id", ondelete="CASCADE"), primary_key=True)


class RssSource(Base):
    __tablename__ = "rss_sources"

    id = Column(String, primary_key=True, default=new_uuid)
    url = Column(String, unique=True, nullable=False)
    name = Column(String, nullable=False)
    category = Column(String, nullable=False)
    active = Column(Boolean, default=True)
    last_fetched_at = Column(DateTime(timezone=True))


class WorkerState(Base):
    __tablename__ = "worker_state"

    id = Column(Integer, primary_key=True, default=1)
    trigger_refresh = Column(Boolean, default=False)
    last_run_at = Column(DateTime(timezone=True))
    status = Column(String, default="idle")
