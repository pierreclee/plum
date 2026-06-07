from datetime import datetime
from worker.clustering import cluster_articles, pick_title, cluster_and_save
from worker.models import ArticleRaw, Topic, TopicArticle


def make_article(title: str, content: str = "", category: str = "france") -> ArticleRaw:
    from worker.ingestion import url_hash
    return ArticleRaw(
        url_hash=url_hash(title),
        source_url=f"https://example.com/{title[:20]}",
        title=title,
        content=content,
        source_name="Test",
        category=category,
        published_at=datetime.utcnow(),
    )


def test_similar_articles_cluster_together():
    a1 = make_article("Macron annonce une réforme des retraites à l'Élysée")
    a2 = make_article("Le président Macron présente sa réforme des retraites")
    clusters = cluster_articles([a1, a2])
    assert len(clusters) == 1
    assert len(clusters[0]) == 2


def test_dissimilar_articles_form_separate_clusters():
    a1 = make_article("Macron visite l'Élysée pour une réunion de cabinet")
    a2 = make_article("Apple présente le nouveau iPhone avec puce M4")
    clusters = cluster_articles([a1, a2])
    assert len(clusters) == 2


def test_empty_input_returns_empty():
    assert cluster_articles([]) == []


def test_single_article_returns_one_cluster():
    clusters = cluster_articles([make_article("Un seul article")])
    assert len(clusters) == 1
    assert len(clusters[0]) == 1


def test_pick_title_picks_shortest():
    a1 = make_article("Titre court")
    a2 = make_article("Un titre beaucoup plus long que le précédent")
    assert pick_title([a1, a2]) == "Titre court"


def test_cluster_and_save_creates_topics(db):
    articles = [
        ArticleRaw(url_hash="h1", source_url="u1",
                   title="Macron réforme l'économie française",
                   content="Le gouvernement annonce une réforme économique majeure",
                   source_name="Test", category="france", published_at=datetime.utcnow()),
        ArticleRaw(url_hash="h2", source_url="u2",
                   title="La réforme économique du gouvernement Macron avance",
                   content="Le président annonce une vaste réforme de l'économie",
                   source_name="Test2", category="france", published_at=datetime.utcnow()),
    ]
    for a in articles:
        db.add(a)
    db.commit()

    count = cluster_and_save(db)
    assert count >= 1
    assert db.query(Topic).count() >= 1


def test_cluster_and_save_returns_zero_when_no_articles(db):
    count = cluster_and_save(db)
    assert count == 0
