from pydantic import BaseModel
from typing import Optional, List
from datetime import datetime


class TopicOut(BaseModel):
    id: str
    title: str
    summary: Optional[str] = None
    category: str
    article_count: int
    published_at: datetime
    sources: List[str] = []

    model_config = {"from_attributes": True}


class FeedMeta(BaseModel):
    total: int
    last_updated: Optional[datetime] = None


class FeedResponse(BaseModel):
    data: List[TopicOut]
    meta: FeedMeta


class WorkerStatusOut(BaseModel):
    status: str
    last_run_at: Optional[datetime] = None
    trigger_refresh: bool
