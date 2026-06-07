# Plum — Roadmap technique

## Architecture actuelle (MVP) — Option B : 2 services séparés

```
Railway Project
├── API (FastAPI)           — service 1, sert uniquement le feed JSON
├── Worker (Python script)  — service 2, cron Railway natif (3x/jour)
└── PostgreSQL              — partagé entre les deux services
```

**Pourquoi ce choix :**
- Isolation propre — un crash worker n'affecte pas l'API
- Scalabilité indépendante des deux services
- Architecture production-ready dès le départ
- Communication API↔Worker via flag en base de données

**Refresh manuel :** endpoint `POST /api/admin/refresh` qui lève un flag en DB, le worker le détecte et s'exécute immédiatement.

---

## Évolution Phase 2 — Option C : Serverless + Queue

À envisager quand DAU > 10 000 ou quand les coûts Railway deviennent significatifs.

```
Vercel (PWA + API routes)
├── API serverless (FastAPI sur Vercel)
└── Queue (Upstash QStash) → Worker (Fly.io ou Railway)
    └── PostgreSQL (Supabase)
```

**Avantages à cette échelle :**
- Scale automatique sans intervention infra
- Combinaison de free tiers multiples
- Découplage total API / ingestion

**Prérequis avant migration :**
- DAU stable > 10 000
- Coût Railway > 50€/mois
- Au moins un autre dev dans l'équipe pour gérer la complexité

---

## Features Phase 2+

- Swipe gauche/droite (remplace le scroll)
- Favoris / Sauvegarde de missives
- Comptes utilisateurs / Authentification
- Gamification complète (paliers Néophyte → Omniscient)
- Push notifications
- Résumé hebdomadaire personnalisé
- Catégories personnalisables (pigeons)
- Sources Telegram (AFP, etc.)
