from unittest.mock import patch, MagicMock
from worker.ingestion import url_hash, guess_category, ingest
from worker.models import RssSource, ArticleRaw


def test_url_hash_is_deterministic():
    assert url_hash("https://example.com/a") == url_hash("https://example.com/a")


def test_url_hash_differs_for_different_urls():
    assert url_hash("https://example.com/a") != url_hash("https://example.com/b")


def test_guess_category_france():
    assert guess_category("Macron visite l'Élysée", "Le gouvernement annonce") == "france"


def test_guess_category_tech():
    assert guess_category("Apple lance un nouveau produit IA", "") == "tech"


def test_guess_category_sport():
    assert guess_category("Ligue 1 : résultats du weekend", "") == "sport"


def test_guess_category_fallback_to_monde():
    assert guess_category("Un événement quelconque", "") == "monde"


def test_ingest_inserts_new_articles(db):
    source = RssSource(url="https://example.com/rss", name="Test", category="france", active=True)
    db.add(source)
    db.commit()

    mock_feed = MagicMock()
    mock_feed.entries = [
        MagicMock(
            link="https://example.com/article-1",
            title="Article Test France",
            summary="Contenu de test",
            content=[],
            published_parsed=(2026, 6, 7, 8, 0, 0, 0, 0, 0),
        )
    ]

    with patch("worker.ingestion.feedparser.parse", return_value=mock_feed):
        count = ingest(db)

    assert count == 1
    assert db.query(ArticleRaw).count() == 1


def test_ingest_deduplicates(db):
    source = RssSource(url="https://example.com/rss", name="Test", category="france", active=True)
    db.add(source)
    db.commit()

    mock_feed = MagicMock()
    mock_feed.entries = [
        MagicMock(
            link="https://example.com/article-1",
            title="Article Test",
            summary="Contenu",
            content=[],
            published_parsed=(2026, 6, 7, 8, 0, 0, 0, 0, 0),
        )
    ]

    with patch("worker.ingestion.feedparser.parse", return_value=mock_feed):
        count1 = ingest(db)
        count2 = ingest(db)

    assert count1 == 1
    assert count2 == 0
    assert db.query(ArticleRaw).count() == 1


def test_ingest_skips_failed_source(db):
    source = RssSource(url="https://bad-source.example.com/rss", name="Bad", category="monde", active=True)
    db.add(source)
    db.commit()

    with patch("worker.ingestion.feedparser.parse", side_effect=Exception("Network error")):
        count = ingest(db)

    assert count == 0
