import logging
from collections import Counter
from datetime import datetime, timezone
from typing import List

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sqlalchemy.orm import Session

from worker.models import ArticleRaw, Topic, TopicArticle

logger = logging.getLogger(__name__)

SIMILARITY_THRESHOLD = 0.3


def cluster_articles(articles: List[ArticleRaw]) -> List[List[ArticleRaw]]:
    if not articles:
        return []
    if len(articles) == 1:
        return [articles]

    texts = [f"{a.title} {a.content or ''}" for a in articles]
    try:
        vectorizer = TfidfVectorizer(max_features=5000)
        tfidf = vectorizer.fit_transform(texts)
        sim = cosine_similarity(tfidf)
    except ValueError:
        return [[a] for a in articles]

    assigned = [False] * len(articles)
    clusters: List[List[ArticleRaw]] = []

    for i in range(len(articles)):
        if assigned[i]:
            continue
        group = [i]
        assigned[i] = True
        for j in range(i + 1, len(articles)):
            if not assigned[j] and sim[i][j] >= SIMILARITY_THRESHOLD:
                group.append(j)
                assigned[j] = True
        clusters.append([articles[k] for k in group])

    return clusters


def pick_title(articles: List[ArticleRaw]) -> str:
    return min(articles, key=lambda a: len(a.title)).title


def cluster_and_save(db: Session) -> int:
    since = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    articles = db.query(ArticleRaw).filter(ArticleRaw.fetched_at >= since).all()

    if not articles:
        logger.info("No articles to cluster")
        return 0

    clusters = cluster_articles(articles)
    saved = 0

    for cluster in clusters:
        category = Counter(a.category for a in cluster).most_common(1)[0][0]
        title = pick_title(cluster)
        published_at = max((a.published_at or datetime.utcnow()) for a in cluster)

        topic = Topic(
            title=title,
            category=category,
            article_count=len(cluster),
            summary_status="pending",
            published_at=published_at,
        )
        db.add(topic)
        db.flush()

        for article in cluster:
            db.add(TopicArticle(topic_id=topic.id, article_raw_id=article.id))

        saved += 1

    db.commit()
    logger.info("Created %d topics from %d articles", saved, len(articles))
    return saved
