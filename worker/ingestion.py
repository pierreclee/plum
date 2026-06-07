import asyncio
import hashlib
import logging
from datetime import datetime, timezone
from typing import List, Dict, Any

import feedparser
from sqlalchemy.orm import Session

from models import ArticleRaw, RssSource

logger = logging.getLogger(__name__)

CATEGORY_KEYWORDS: Dict[str, List[str]] = {
    "france": ["france", "paris", "macron", "gouvernement", "assemblée", "sénat", "français", "française", "élysée"],
    "monde": ["monde", "international", "usa", "europe", "ukraine", "russie", "chine", "onu", "biden", "trump", "otan"],
    "tech": ["tech", "ia", "intelligence artificielle", "apple", "google", "meta", "startup", "numérique", "openai", "microsoft"],
    "eco": ["économie", "bourse", "inflation", "pib", "emploi", "entreprise", "budget", "banque", "euro", "cac 40"],
    "sport": ["sport", "football", "tennis", "rugby", "olympique", "ligue 1", "tour de france", "nba", "formule 1"],
}


def url_hash(url: str) -> str:
    return hashlib.sha256(url.encode()).hexdigest()


def guess_category(title: str, content: str = "") -> str:
    text = (title + " " + (content or "")).lower()
    scores = {cat: sum(1 for kw in kws if kw in text) for cat, kws in CATEGORY_KEYWORDS.items()}
    best = max(scores, key=scores.get)
    return best if scores[best] > 0 else "monde"


async def _fetch_source(source: RssSource) -> List[Dict[str, Any]]:
    loop = asyncio.get_running_loop()
    try:
        feed = await loop.run_in_executor(None, feedparser.parse, source.url)
        articles = []
        for entry in feed.entries:
            url = getattr(entry, "link", "")
            if not url:
                continue
            title = getattr(entry, "title", "") or ""
            summary = getattr(entry, "summary", "") or ""
            content_list = getattr(entry, "content", [])
            content = content_list[0].get("value", "") if content_list else summary
            published = getattr(entry, "published_parsed", None)
            published_at = datetime(*published[:6], tzinfo=timezone.utc) if published else datetime.now(timezone.utc)
            articles.append({
                "url_hash": url_hash(url),
                "source_url": url,
                "title": title,
                "content": content[:2000],
                "published_at": published_at,
                "source_name": source.name,
                "category": source.category,
            })
        return articles
    except Exception as exc:
        logger.error("Error fetching %s: %s", source.url, exc)
        return []


async def _fetch_all(sources: List[RssSource]) -> List[Dict[str, Any]]:
    results = await asyncio.gather(*[_fetch_source(s) for s in sources])
    return [article for sublist in results for article in sublist]


def ingest(db: Session) -> int:
    sources = db.query(RssSource).filter(RssSource.active.is_(True)).all()
    if not sources:
        logger.warning("No active RSS sources")
        return 0

    articles = asyncio.run(_fetch_all(sources))
    inserted = 0
    for article in articles:
        if not db.query(ArticleRaw).filter(ArticleRaw.url_hash == article["url_hash"]).first():
            db.add(ArticleRaw(**article))
            inserted += 1
    db.commit()
    logger.info("Ingested %d new articles from %d sources", inserted, len(sources))
    return inserted
