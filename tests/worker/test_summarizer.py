import os
from unittest.mock import patch, MagicMock
from datetime import datetime
from worker.summarizer import summarize_pending
from worker.models import Topic, ArticleRaw, TopicArticle


def test_summarize_pending_updates_status_done(db):
    topic = Topic(
        title="Test Topic",
        category="france",
        article_count=1,
        summary_status="pending",
        published_at=datetime.utcnow(),
    )
    db.add(topic)
    db.commit()

    mock_msg = MagicMock()
    mock_msg.content = [MagicMock(text="Résumé factuel du sujet en deux phrases courtes.")]

    with patch("worker.summarizer.Anthropic") as MockAnthropic:
        MockAnthropic.return_value.messages.create.return_value = mock_msg
        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"}):
            count = summarize_pending(db)

    assert count == 1
    db.refresh(topic)
    assert topic.summary_status == "done"
    assert topic.summary == "Résumé factuel du sujet en deux phrases courtes."


def test_summarize_pending_fallback_on_api_error(db):
    topic = Topic(
        title="Test Topic Erreur",
        category="monde",
        article_count=1,
        summary_status="pending",
        published_at=datetime.utcnow(),
    )
    db.add(topic)
    db.commit()

    with patch("worker.summarizer.Anthropic") as MockAnthropic:
        MockAnthropic.return_value.messages.create.side_effect = Exception("API down")
        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"}):
            count = summarize_pending(db)

    assert count == 0
    db.refresh(topic)
    assert topic.summary_status == "failed"
    assert topic.summary is None


def test_summarize_pending_skips_already_done(db):
    topic = Topic(
        title="Déjà résumé",
        category="tech",
        article_count=1,
        summary="Résumé existant.",
        summary_status="done",
        published_at=datetime.utcnow(),
    )
    db.add(topic)
    db.commit()

    with patch("worker.summarizer.Anthropic") as MockAnthropic:
        with patch.dict(os.environ, {"ANTHROPIC_API_KEY": "test-key"}):
            count = summarize_pending(db)

    assert count == 0
    MockAnthropic.return_value.messages.create.assert_not_called()
