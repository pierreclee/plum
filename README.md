# Plum

> L'actualité, réinventée. Simple. Rapide. Efficace.

Agrégateur d'actualités apolitique ciblant les 18-30 ans. Plum ingère ~3 000 articles/jour depuis des flux RSS, les regroupe en ~150 sujets via TF-IDF, puis génère un résumé factuel en 1-2 phrases via Claude Haiku 4.5.

---

## Architecture

```
GitHub Repo
├── api/      → Service Railway 1 : FastAPI (feed JSON)
├── worker/   → Service Railway 2 : pipeline RSS→TF-IDF→IA (process continu)
├── pwa/      → PWA statique (Vercel ou Railway static)
└── migrations/  → SQL PostgreSQL
```

Le worker tourne en **process permanent** avec APScheduler. Il lance le pipeline 3x/jour (7h, 12h, 18h heure Paris) et poll la base toutes les 30 secondes pour détecter un déclenchement manuel via `POST /api/admin/refresh`.

---

## Stack technique

| Couche | Techno |
|---|---|
| API | FastAPI 0.115, Uvicorn, SQLAlchemy 2, Pydantic v2 |
| Worker | Python 3.11, feedparser, scikit-learn, anthropic SDK, APScheduler |
| Base de données | PostgreSQL (Railway managé) |
| PWA | HTML/CSS/JS vanilla, Service Worker, manifest.json |
| IA | Claude Haiku 4.5 (`claude-haiku-4-5-20251001`) |
| Analytics | Plausible.io (RGPD-friendly, sans cookie) |

---

## Structure du repo

```
plum/
├── api/
│   ├── main.py              # FastAPI app (CORS, GZip, routes)
│   ├── database.py          # SQLAlchemy engine + session
│   ├── models.py            # ORM : Topic, ArticleRaw, RssSource, WorkerState
│   ├── schemas.py           # Pydantic : TopicOut, FeedResponse, WorkerStatusOut
│   ├── routes/
│   │   ├── feed.py          # GET /api/feed, /api/feed/{id}, /api/categories
│   │   └── admin.py         # POST /api/admin/refresh, GET /api/admin/worker-status
│   ├── Procfile             # web: uvicorn main:app --host 0.0.0.0 --port $PORT
│   └── requirements.txt
├── worker/
│   ├── main.py              # Entry point : APScheduler + poll trigger 30s
│   ├── ingestion.py         # Fetch RSS async (feedparser), dédup SHA256
│   ├── clustering.py        # TF-IDF (scikit-learn), greedy clustering, seuil 0.3
│   ├── summarizer.py        # Appels séquentiels Claude Haiku, fallback failed
│   ├── cleanup.py           # Purge articles > 7j, topics > 30j
│   ├── seed.py              # Initialise rss_sources + worker_state
│   ├── database.py          # SQLAlchemy engine + session (indépendant)
│   ├── models.py            # ORM (miroir de api/models.py)
│   ├── Procfile             # worker: python main.py
│   └── requirements.txt
├── pwa/
│   ├── index.html           # Shell : header streak, nav catégories, feed, offline banner
│   ├── manifest.json        # PWA installable (icône pigeon, #534AB7)
│   ├── sw.js                # Service Worker : network-first feed, cache-first assets
│   └── app/
│       ├── feed.js          # Fetch /api/feed, render cards, fallback cache
│       ├── streak.js        # Streak localStorage (plum_lastVisit, plum_streak)
│       └── categories.js    # Nav catégories, fetch /api/categories
├── migrations/
│   └── 001_initial_schema.sql
├── tests/
│   ├── api/                 # Tests FastAPI avec TestClient + SQLite in-memory
│   └── worker/              # Tests worker avec SQLite in-memory
├── requirements-dev.txt     # pytest, httpx
├── .gitignore
├── ROADMAP.md
└── README.md
```

---

## API

| Méthode | Route | Description |
|---|---|---|
| `GET` | `/api/feed` | Feed paginé (`category`, `limit`, `offset`) |
| `GET` | `/api/feed/{topic_id}` | Détail d'un topic + sources |
| `GET` | `/api/categories` | Liste des 5 catégories |
| `POST` | `/api/admin/refresh` | Déclenche le pipeline manuellement |
| `GET` | `/api/admin/worker-status` | État du worker |
| `GET` | `/health` | Health check |

Les routes `/api/admin/*` requièrent le header `X-Admin-Key: <ADMIN_KEY>`.

### Exemple de réponse `/api/feed`

```json
{
  "data": [
    {
      "id": "uuid",
      "title": "Titre du sujet",
      "summary": "Résumé factuel en 1-2 phrases.",
      "category": "france",
      "article_count": 12,
      "published_at": "2026-06-07T08:00:00Z",
      "sources": ["Le Monde", "Le Figaro", "France Info"]
    }
  ],
  "meta": {
    "total": 47,
    "last_updated": "2026-06-07T08:05:00Z"
  }
}
```

---

## Variables d'environnement

### Service `api`

| Variable | Description |
|---|---|
| `DATABASE_URL` | URL PostgreSQL Railway (`postgresql://...`) |
| `ADMIN_KEY` | Clé secrète pour les routes admin |

### Service `worker`

| Variable | Description |
|---|---|
| `DATABASE_URL` | Même URL PostgreSQL |
| `ANTHROPIC_API_KEY` | Clé API Anthropic |
| `TZ` | `Europe/Paris` (scheduling heure locale) |

---

## Lancer en local

### Prérequis

- Python 3.11+
- PostgreSQL (ou SQLite pour les tests uniquement)

### API

```bash
cd api
pip install -r requirements.txt
DATABASE_URL=sqlite:///./plum.db ADMIN_KEY=dev uvicorn main:app --reload
# → http://localhost:8000
```

### Worker

```bash
cd worker
pip install -r requirements.txt
DATABASE_URL=sqlite:///./plum.db ANTHROPIC_API_KEY=sk-... python main.py
```

### Tests

```bash
pip install -r requirements-dev.txt
pytest tests/ -v
```

---

## Catégories

`france` · `monde` · `tech` · `eco` · `sport`

---

## Métriques MVP

| Métrique | Cible |
|---|---|
| Rétention J7 | > 30% |
| Latence feed p95 | < 300ms |
| Disponibilité API | > 99% |
| Coût infra mensuel | < 50€ |
| Coût IA mensuel | < 45€ |
