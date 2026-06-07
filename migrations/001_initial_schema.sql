CREATE EXTENSION IF NOT EXISTS "pgcrypto";

CREATE TABLE articles_raw (
  id           TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
  url_hash     TEXT UNIQUE NOT NULL,
  source_url   TEXT NOT NULL,
  title        TEXT NOT NULL,
  content      TEXT,
  published_at TIMESTAMPTZ,
  source_name  TEXT NOT NULL,
  category     TEXT NOT NULL,
  fetched_at   TIMESTAMPTZ DEFAULT NOW()
);

CREATE TABLE topics (
  id             TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
  title          TEXT NOT NULL,
  category       TEXT NOT NULL,
  article_count  INTEGER NOT NULL DEFAULT 0,
  summary        TEXT,
  summary_status TEXT NOT NULL DEFAULT 'pending',
  published_at   TIMESTAMPTZ NOT NULL,
  created_at     TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_topics_category_published ON topics(category, published_at DESC);

CREATE TABLE topic_articles (
  topic_id       TEXT REFERENCES topics(id) ON DELETE CASCADE,
  article_raw_id TEXT REFERENCES articles_raw(id) ON DELETE CASCADE,
  PRIMARY KEY (topic_id, article_raw_id)
);

CREATE TABLE rss_sources (
  id              TEXT PRIMARY KEY DEFAULT gen_random_uuid()::text,
  url             TEXT UNIQUE NOT NULL,
  name            TEXT NOT NULL,
  category        TEXT NOT NULL,
  active          BOOLEAN DEFAULT TRUE,
  last_fetched_at TIMESTAMPTZ
);

CREATE TABLE worker_state (
  id              INTEGER PRIMARY KEY DEFAULT 1,
  trigger_refresh BOOLEAN DEFAULT FALSE,
  last_run_at     TIMESTAMPTZ,
  status          TEXT DEFAULT 'idle'
);

INSERT INTO worker_state (id) VALUES (1) ON CONFLICT DO NOTHING;
