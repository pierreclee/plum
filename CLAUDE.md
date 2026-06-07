# PLUM — Contexte projet & Instructions

## Le projet

Plum est une application d'actualités réinventée. Le concept : un agrégateur d'actu **apolitique**, qui livre l'info de manière **simple, rapide et efficace** — comme un pigeon voyageur moderne.

### Identité
- **Nom** : Plum
- **Mascotte** : Le pigeon voyageur — symbole français, messager universel, mémorable
- **Tagline** : "L'actualité, réinventée. Simple. Rapide. Efficace."
- **Palette** : Violet nuit (#534AB7) · Blanc · Gris — élégant, sans prétention
- **Ton** : Drôle mais sérieux, marque les esprits

### Le problème
- L'info est devenue du bruit : notifications intrusives, fake news, algorithmes opaques
- Fatigue informationnelle massive, surtout chez les 18-34 ans
- Aucun agrégateur apolitique, simple et visuellement engageant en France
- 74% des 18-34 ans disent manquer d'une source d'info fiable, courte et apolitique (IFOP 2024)

### Cible MVP
- 18-30 ans, étudiants & jeunes actifs
- CSP+ urbain, curieux, connecté
- Lassé des réseaux sociaux & médias traditionnels
- Consommateur de HugoDécrypte, Politico, Reels

---

## Scope MVP — Version minimale

### Objectif
**Valider la rétention** : est-ce que les gens reviennent lire Plum chaque jour ?
- Métrique clé : Rétention J7 > 30%
- Tracking : visites uniques/jour + streak moyen

### Plateforme
**PWA (Progressive Web App)** — pas d'app native pour le MVP
- Zéro friction de distribution (un lien suffit)
- Pas de review Apple/Google
- Installable sur l'écran d'accueil via manifest.json
- Itération immédiate

### Features IN (MVP)
1. **Flux d'actualités** — Feed scrollable avec les sujets du jour, chaque sujet résumé en 1-2 phrases
2. **Résumés IA** — Synthèse automatique par sujet via Claude Haiku 4.5
3. **3-5 catégories fixes** — France, Monde, Tech, Éco, Sport (pas de pigeons personnalisables au MVP)
4. **Streak counter** — Compteur de jours consécutifs d'ouverture (localStorage côté client)
5. **PWA installable** — manifest.json + service worker basique

### Features OUT (phase 2+)
- Swipe gauche/droite (scroll simple suffit)
- Favoris / Sauvegarde de missives
- Comptes utilisateurs / Authentification (MVP = anonyme)
- Gamification complète (paliers, badges, Néophyte → Omniscient)
- Push notifications (nécessite des comptes)
- Résumé hebdomadaire

---

## Pipeline technique

```
Sources (RSS + Telegram) → Ingestion (cron/workers) → Dédup/Tri (TF-IDF algo) → Résumé IA (Haiku batch) → API JSON (REST) → PWA (feed + streak)
```

### Ingestion
- **Sources** : ~300 sources via flux RSS + canaux Telegram (AFP, etc.)
- **Volume** : ~3 000 articles/jour ingérés
- **Coût** : APIs Telegram et RSS gratuites, seul coût = serveur (~5€/mois)

### Tri & Classification (algorithme, pas IA)
- Regrouper les articles qui traitent du même sujet (TF-IDF + similarité cosinus)
- Catégoriser par mots-clés / taxonomie dans les 5 catégories
- Dédupliquer les doublons
- ~3 000 articles → ~150 sujets uniques/jour

### Résumés IA
- **Modèle** : Claude Haiku 4.5
- **Input** : Articles regroupés par sujet (~10 600 tokens/sujet)
- **Output** : 1-2 phrases de résumé factuel et apolitique (~60 tokens)
- **Volume** : ~150 appels/jour
- **Coût** : ~23-45€/mois (batch API = -50%)
- **Important** : Ce coût est quasi-fixe — il dépend du volume de news, PAS du nombre d'utilisateurs

### Budget infra total
| Scénario | Mensuel | Annuel |
|----------|---------|--------|
| Beta (500-1K DAU) | 43 – 120 € | 512 – 1 445 € |
| Scale (10K DAU) | 93 – 205 € | 1 116 – 2 460 € |
| Mass market (100K DAU) | 205 – 520 € | 2 460 – 6 240 € |

---

## Contraintes techniques
- **Dev solo** — Pierre code seul, donc favoriser des technos productives et bien documentées
- **Budget serré** — Maximiser les free tiers (Supabase, Upstash, Cloudflare, Firebase)
- **Itération rapide** — Pouvoir déployer et tester vite, pas d'over-engineering
- **Scalabilité future** — Les choix MVP ne doivent pas bloquer le scale vers 100K+ users

---

## Première tâche

**Brainstorme sur l'architecture backend et data du projet.** Avant d'écrire la moindre ligne de code, je veux que tu réfléchisses en profondeur à :

### 1. Architecture backend
- Quel framework/langage pour l'API ? (Node/Express, FastAPI, etc.)
- Monolithe ou microservices pour le MVP ?
- Comment structurer les workers d'ingestion (cron jobs, queue, event-driven) ?
- Hébergement : Hetzner VPS, Railway, Fly.io, Vercel — qu'est-ce qui fait le plus de sens ?

### 2. Architecture data
- Quel schéma de base de données ? (articles bruts, sujets regroupés, résumés, catégories)
- PostgreSQL (Supabase) vs. autre chose ?
- Faut-il un cache (Redis/Upstash) dès le MVP ? Pour quoi exactement ?
- Comment stocker et servir efficacement le feed temps réel ?

### 3. Pipeline d'ingestion
- Comment architecturer la collecte RSS + Telegram de manière fiable ?
- Quelle fréquence de polling ? Temps réel vs. batch toutes les X minutes ?
- Comment gérer les sources qui tombent, les doublons, les articles mal formés ?

### 4. Pipeline IA
- Comment orchestrer les appels Haiku (batch API vs. temps réel) ?
- Quel prompt engineering pour des résumés factuels et apolitiques ?
- Comment gérer le fallback si l'API est down ?

### 5. Servant la PWA
- API REST classique ou quelque chose de plus léger ?
- Pagination du feed, caching côté client, stratégie offline ?
- Analytics minimal pour tracker la rétention ?

**Propose-moi 2-3 options d'architecture avec les trade-offs de chacune (simplicité, coût, scalabilité, vitesse de dev). Recommande celle que tu préfères pour un dev solo en MVP.**

Ne code rien encore. Je veux d'abord qu'on valide l'architecture ensemble.
