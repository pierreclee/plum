# Plum MVP — Architecture Backend & Data

**Date :** 2026-06-07
**Statut :** Approuvé
**Auteur :** Pierre (dev solo)

---

## Contexte

Plum est une PWA d'agrégation d'actualités apolitique ciblant les 18-30 ans. Le MVP vise à valider la rétention (J7 > 30%). Le pipeline ingère ~3 000 articles/jour depuis des sources RSS, les regroupe en ~150 sujets via TF-IDF, puis génère des résumés de 1-2 phrases via Claude Haiku 4.5.

**Contraintes :**
- Dev solo (Pierre), itération rapide
- Budget serré, maximiser les free tiers
- Pas d'authentification utilisateur au MVP
- PWA uniquement (pas d'app native)

---

## Architecture choisie : Option B — 2 services séparés

```
Railway Project: plum
├── Service: api       — FastAPI, sert le feed JSON à la PWA
├── Service: worker    — Python script, ingestion + clustering + IA
└── Service: postgres  — PostgreSQL managé Railway
```

**Justification :** L'isolation des deux services garantit qu'un crash du worker n'affecte pas la disponibilité de l'API. Les deux services peuvent scaler indépendamment. La complexité reste maîtrisable pour un dev solo.

---

## Base de données

### Schéma PostgreSQL

```sql
-- Articles bruts ingérés depuis RSS
CREATE TABLE articles_raw (
  id           UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  url_hash     TEXT UNIQUE NOT NULL,   -- SHA256(source_url) pour dédup
  source_url   TEXT NOT NULL,
  title        TEXT NOT NULL,
  content      TEXT,
  published_at TIMESTAMPTZ,
  source_name  TEXT NOT NULL,
  category     TEXT NOT NULL,          -- france|monde|tech|eco|sport
  fetched_at   TIMESTAMPTZ DEFAULT NOW()
);

-- Sujets regroupés par clustering TF-IDF
CREATE TABLE topics (
  id             UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  title          TEXT NOT NULL,
  category       TEXT NOT NULL,
  article_count  INTEGER NOT NULL DEFAULT 0,
  summary        TEXT,
  summary_status TEXT NOT NULL DEFAULT 'pending', -- pending|done|failed
  published_at   TIMESTAMPTZ NOT NULL,
  created_at     TIMESTAMPTZ DEFAULT NOW()
);

CREATE INDEX idx_topics_category_published ON topics(category, published_at DESC);

-- Liaison articles ↔ sujets
CREATE TABLE topic_articles (
  topic_id       UUID REFERENCES topics(id) ON DELETE CASCADE,
  article_raw_id UUID REFERENCES articles_raw(id) ON DELETE CASCADE,
  PRIMARY KEY (topic_id, article_raw_id)
);

-- Sources RSS configurées
CREATE TABLE rss_sources (
  id            UUID PRIMARY KEY DEFAULT gen_random_uuid(),
  url           TEXT UNIQUE NOT NULL,
  name          TEXT NOT NULL,
  category      TEXT NOT NULL,
  active        BOOLEAN DEFAULT TRUE,
  last_fetched_at TIMESTAMPTZ
);

-- État du worker (coordination API ↔ Worker)
CREATE TABLE worker_state (
  id               INTEGER PRIMARY KEY DEFAULT 1,  -- ligne unique
  trigger_refresh  BOOLEAN DEFAULT FALSE,
  last_run_at      TIMESTAMPTZ,
  status           TEXT DEFAULT 'idle'  -- idle|running|done
);

INSERT INTO worker_state (id) VALUES (1);
```

**Pas de Redis au MVP.** PostgreSQL avec index sur `(category, published_at)` tient jusqu'à ~50 000 DAU. Redis sera ajouté si le feed dépasse 500ms en p95.

**Rétention des données :** articles_raw supprimés après 7 jours. Topics conservés 30 jours.

---

## Pipeline Worker

Le worker est un script Python autonome qui tourne **en continu** sur Railway (process permanent, pas un cron Railway). Il utilise `APScheduler` en interne pour déclencher le pipeline 3x/jour, et poll `worker_state.trigger_refresh` toutes les 30 secondes pour le déclenchement manuel. Ce choix est nécessaire : un Railway cron job s'arrête après exécution et ne peut pas écouter les triggers manuels.

### Étape 1 — Collecte RSS

- Lit toutes les `rss_sources` actives
- Fetch en parallèle via `asyncio` + `feedparser`
- Déduplique via `SHA256(url)` avant insertion
- Insère dans `articles_raw`
- En cas d'erreur sur une source : log + skip, les autres continuent

### Étape 2 — Clustering TF-IDF

- Récupère les articles des dernières 24h
- Vectorise `title + content` avec `scikit-learn TfidfVectorizer`
- Calcule la similarité cosinus entre tous les articles
- Seuil de regroupement : similarité > 0.4
- Catégorise par liste de mots-clés fixes par catégorie
- Insère dans `topics` + `topic_articles`

### Étape 3 — Résumés IA

- Récupère les topics avec `summary_status = 'pending'`
- Appels séquentiels (non parallèles) à Claude Haiku 4.5 pour contrôler les coûts
- Prompt système :
  ```
  Tu es un journaliste factuel et apolitique. Résume ce groupe d'articles
  en 1-2 phrases courtes. Aucun jugement de valeur, aucune opinion.
  Présente uniquement les faits.
  ```
- Met à jour `summary` + `summary_status = 'done'`
- Fallback si API indisponible : `summary_status = 'failed'`, topic affiché sans résumé

### Étape 4 — Cleanup

- Supprime `articles_raw` de plus de 7 jours
- Met `worker_state.status = 'idle'`

---

## API FastAPI

### Routes

| Méthode | Route | Description |
|---|---|---|
| `GET` | `/api/feed` | Feed paginé, params : `category`, `limit` (défaut 20), `offset` |
| `GET` | `/api/feed/{topic_id}` | Détail d'un topic + sources |
| `GET` | `/api/categories` | Liste des 5 catégories |
| `POST` | `/api/admin/refresh` | Lève `trigger_refresh = TRUE` |
| `GET` | `/api/admin/worker-status` | État du worker (status, last_run_at) |

### Sécurité admin

Les routes `/api/admin/*` vérifient le header `X-Admin-Key` contre la variable d'environnement `ADMIN_KEY`. Pas d'auth complète au MVP.

### Format de réponse

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
      "sources": ["Le Monde", "Le Figaro", "AFP"]
    }
  ],
  "meta": {
    "total": 47,
    "last_updated": "2026-06-07T08:05:00Z"
  }
}
```

**CORS** activé pour la PWA. **Gzip** activé. Pas de rate limiting au MVP (trafic faible).

---

## PWA

### Fichiers

```
pwa/
├── index.html       — shell de l'app
├── manifest.json    — installable (icône pigeon, couleur #534AB7)
├── sw.js            — service worker, cache offline
└── app/
    ├── feed.js      — fetch /api/feed, render les cards
    ├── streak.js    — logique streak (localStorage)
    └── categories.js — filtre par catégorie
```

### Streak (localStorage uniquement)

```js
const today = new Date().toDateString()
const lastVisit = localStorage.getItem('lastVisit')
const streak = parseInt(localStorage.getItem('streak') || '0')

const yesterday = new Date(Date.now() - 86400000).toDateString()

if (lastVisit === today) {
  // Déjà visité aujourd'hui
} else if (lastVisit === yesterday) {
  localStorage.setItem('streak', streak + 1)
} else {
  localStorage.setItem('streak', 1)
}
localStorage.setItem('lastVisit', today)
```

### Stratégie offline

- Le service worker cache le dernier feed téléchargé
- Si réseau indisponible : affiche le cache avec badge "Dernière mise à jour il y a Xh"
- Pas de background sync au MVP

### Analytics

**Plausible.io** (plan free, RGPD-friendly, sans cookie banner). Intégré via une ligne de script. Metrics suivies : visites uniques/jour, pages vues, durée de session. Pas d'event tracking custom au MVP.

---

## Déploiement Railway

### Configuration des services

**Service `api` :**
- Source : dossier `/api` du repo GitHub
- Start : `uvicorn main:app --host 0.0.0.0 --port $PORT`
- Env vars : `DATABASE_URL`, `ANTHROPIC_API_KEY`, `ADMIN_KEY`

**Service `worker` :**
- Source : dossier `/worker` du repo GitHub
- Start : `python main.py` (process permanent)
- Pas de cron Railway — le scheduling est géré par `APScheduler` en interne
- Schedule interne : `0 7,12,18 * * *` heure de Paris (configurable via env var `TZ=Europe/Paris`)
- Env vars : `DATABASE_URL`, `ANTHROPIC_API_KEY`, `TZ=Europe/Paris`

**Service `postgres` :**
- PostgreSQL managé Railway, backups automatiques inclus

### Structure du repo

```
plum/
├── api/
│   ├── main.py
│   ├── routes/
│   ├── models/
│   └── requirements.txt
├── worker/
│   ├── main.py
│   ├── ingestion.py
│   ├── clustering.py
│   ├── summarizer.py
│   └── requirements.txt
├── pwa/
│   ├── index.html
│   ├── manifest.json
│   └── sw.js
├── docs/
├── CLAUDE.md
└── ROADMAP.md
```

---

## Métriques de succès MVP

| Métrique | Cible |
|---|---|
| Rétention J7 | > 30% |
| Latence feed p95 | < 300ms |
| Disponibilité API | > 99% (hors maintenance) |
| Coût infra mensuel | < 50€ |
| Coût IA mensuel | < 45€ (batch Haiku) |

---

## Hors scope MVP

- Authentification utilisateur
- Push notifications
- Swipe gauche/droite
- Favoris / sauvegarde
- Gamification complète (badges, paliers)
- Sources Telegram
- Personnalisation des catégories
