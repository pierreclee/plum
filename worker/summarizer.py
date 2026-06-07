import json
import logging
import os
from typing import List

from anthropic import Anthropic
from sqlalchemy.orm import Session

from models import Topic, TopicArticle, ArticleRaw

logger = logging.getLogger(__name__)

SYSTEM_PROMPT = (
    "Tu es un journaliste factuel et apolitique. "
    "Réponds uniquement en JSON valide, sans markdown, avec exactement ces deux clés :\n"
    '{"title": "...", "summary": "..."}\n'
    "Règles :\n"
    "- title : 6 à 10 mots, en français, factuel, percutant\n"
    "- summary : 1 seule phrase, maximum 25 mots, en français, faits uniquement\n"
    "Aucun jugement de valeur, aucune opinion."
)


def _build_prompt(topic: Topic, articles: List[ArticleRaw]) -> str:
    lines = [f"Sujet brut : {topic.title}\n\nArticles :"]
    for i, article in enumerate(articles[:5], 1):
        lines.append(f"{i}. {article.title}")
        if article.content:
            lines.append(f"   {article.content[:300]}")
    return "\n".join(lines)


def _parse_response(text: str) -> dict:
    text = text.strip()
    try:
        return json.loads(text)
    except json.JSONDecodeError:
        start = text.find("{")
        end = text.rfind("}") + 1
        if start != -1 and end > start:
            return json.loads(text[start:end])
        raise


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
                max_tokens=200,
                system=SYSTEM_PROMPT,
                messages=[{"role": "user", "content": _build_prompt(topic, articles)}],
            )
            parsed = _parse_response(response.content[0].text)
            if parsed.get("title"):
                topic.title = parsed["title"].strip()
            topic.summary = parsed.get("summary", "").strip()
            topic.summary_status = "done"
            done += 1
        except Exception as exc:
            logger.error("Failed to summarize topic %s: %s", topic.id, exc)
            topic.summary_status = "failed"
        db.commit()

    logger.info("Summarized %d/%d topics", done, len(topics))
    return done
