import logging
from collections import Counter
from datetime import datetime, timezone
from typing import Dict, List, Tuple

from sklearn.feature_extraction.text import TfidfVectorizer
from sklearn.metrics.pairwise import cosine_similarity
from sqlalchemy.orm import Session

from models import ArticleRaw, Topic, TopicArticle

logger = logging.getLogger(__name__)

SIMILARITY_THRESHOLD = 0.3
MAX_TOPICS_PER_CATEGORY = 6


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


def score_cluster(cluster: List[ArticleRaw]) -> float:
    now = datetime.now(timezone.utc)

    nb_articles = len(cluster)
    nb_sources = len({a.source_name for a in cluster if a.source_name})

    dates = [a.published_at for a in cluster if a.published_at]
    if dates:
        most_recent = max(dates)
        if most_recent.tzinfo is None:
            most_recent = most_recent.replace(tzinfo=timezone.utc)
        hours_old = (now - most_recent).total_seconds() / 3600
        recency = 1.0 / (1.0 + hours_old * 0.1)
    else:
        recency = 0.0

    return nb_articles * 2.0 + nb_sources * 1.5 + recency


def select_top_clusters(
    clusters: List[List[ArticleRaw]],
) -> List[Tuple[List[ArticleRaw], str]]:
    """Score all clusters, group by category, keep top MAX_TOPICS_PER_CATEGORY each."""
    by_category: Dict[str, List[Tuple[float, List[ArticleRaw]]]] = {}

    for cluster in clusters:
        category = Counter(a.category for a in cluster).most_common(1)[0][0]
        score = score_cluster(cluster)
        by_category.setdefault(category, []).append((score, cluster))

    selected = []
    for category, scored in by_category.items():
        top = sorted(scored, key=lambda x: x[0], reverse=True)[:MAX_TOPICS_PER_CATEGORY]
        for _, cluster in top:
            selected.append((cluster, category))

    return selected


def cluster_and_save(db: Session) -> int:
    since = datetime.now(timezone.utc).replace(hour=0, minute=0, second=0, microsecond=0)
    articles = db.query(ArticleRaw).filter(ArticleRaw.fetched_at >= since).all()

    if not articles:
        logger.info("No articles to cluster")
        return 0

    clusters = cluster_articles(articles)
    selected = select_top_clusters(clusters)
    saved = 0

    for cluster, category in selected:
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
    logger.info(
        "Created %d topics (from %d clusters, %d articles) — top %d per category",
        saved, len(clusters), len(articles), MAX_TOPICS_PER_CATEGORY,
    )
    return saved
