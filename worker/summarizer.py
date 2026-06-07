import logging
import os
from typing import List

from anthropic import Anthropic
from sqlalchemy.orm import Session

from models import Topic, TopicArticle, ArticleRaw

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "Tu es un journaliste factuel et apolitique. "
    "Résume ce groupe d'articles en 1-2 phrases courtes. "
    "Aucun jugement de valeur, aucune opinion. "
    "Présente uniquement les faits."
)


def _build_prompt(topic: Topic, articles: List[ArticleRaw]) -> str:
    lines = [f"Sujet : {topic.title}\n\nArticles :"]
    for i, article in enumerate(articles[:5], 1):
        lines.append(f"{i}. {article.title}")
        if article.content:
            lines.append(f"   {article.content[:300]}")
    return "\n".join(lines)


def summarize_pending(db: Session) -> int:
    client = Anthropic(api_key=os.environ["ANTHROPIC_API_KEY"])
    topics = db.query(Topic).filter(Topic.summary_status == "pending").all()
    done = 0

    for topic in topics:
        articles = (
            db.query(ArticleRaw)
            .join(TopicArticle, TopicArticle.article_raw_id == ArticleRaw.id)
            .filter(TopicArticle.topic_id == topic.id)
            .all()
        )
        try:
            response = client.messages.create(
                model="claude-haiku-4-5-20251001",
                max_tokens=150,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": _build_prompt(topic, articles)}],
            )
            topic.summary = response.content[0].text.strip()
            topic.summary_status = "done"
            done += 1
        except Exception as exc:
            logger.error("Failed to summarize topic %s: %s", topic.id, exc)
            topic.summary_status = "failed"
        db.commit()

    logger.info("Summarized %d/%d topics", done, len(topics))
    return done
