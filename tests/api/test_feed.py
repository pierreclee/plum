from datetime import datetime
from api.models import Topic, WorkerState


def test_get_categories(client):
    res = client.get("/api/categories")
    assert res.status_code == 200
    assert set(res.json()) == {"france", "monde", "tech", "eco", "sport"}


def test_get_feed_empty(client):
    res = client.get("/api/feed")
    assert res.status_code == 200
    body = res.json()
    assert body["data"] == []
    assert body["meta"]["total"] == 0


def test_get_feed_returns_done_topics(client, db):
    topic = Topic(
        title="Macron annonce une réforme",
        category="france",
        article_count=3,
        summary="Résumé du sujet.",
        summary_status="done",
        published_at=datetime(2026, 6, 7, 8, 0, 0),
    )
    db.add(topic)
    db.commit()

    res = client.get("/api/feed")
    assert res.status_code == 200
    data = res.json()["data"]
    assert len(data) == 1
    assert data[0]["title"] == "Macron annonce une réforme"
    assert data[0]["summary"] == "Résumé du sujet."


def test_get_feed_includes_failed_topics_without_summary(client, db):
    topic = Topic(
        title="Sujet sans résumé",
        category="monde",
        article_count=2,
        summary_status="failed",
        published_at=datetime(2026, 6, 7, 9, 0, 0),
    )
    db.add(topic)
    db.commit()

    res = client.get("/api/feed")
    assert res.status_code == 200
    assert len(res.json()["data"]) == 1
    assert res.json()["data"][0]["summary"] is None


def test_get_feed_filters_by_category(client, db):
    db.add(Topic(title="Sujet France", category="france", article_count=1,
                 summary_status="done", published_at=datetime.utcnow()))
    db.add(Topic(title="Sujet Tech", category="tech", article_count=1,
                 summary_status="done", published_at=datetime.utcnow()))
    db.commit()

    res = client.get("/api/feed?category=france")
    assert res.status_code == 200
    data = res.json()["data"]
    assert len(data) == 1
    assert data[0]["category"] == "france"


def test_get_feed_topic_detail_not_found(client):
    res = client.get("/api/feed/nonexistent-id")
    assert res.status_code == 404


def test_get_feed_topic_detail(client, db):
    topic = Topic(
        title="Sujet détail",
        category="tech",
        article_count=1,
        summary="Un résumé.",
        summary_status="done",
        published_at=datetime.utcnow(),
    )
    db.add(topic)
    db.commit()

    res = client.get(f"/api/feed/{topic.id}")
    assert res.status_code == 200
    assert res.json()["id"] == topic.id


def test_get_feed_invalid_category_returns_422(client):
    res = client.get("/api/feed?category=invalid")
    assert res.status_code == 422
