"""
Initialise la base de données avec des sources RSS de départ.
Lancer une seule fois : python -m worker.seed
"""
import logging
from database import SessionLocal, engine, Base
from models import RssSource, WorkerState

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

INITIAL_SOURCES = [
    {"url": "https://www.lemonde.fr/rss/une.xml", "name": "Le Monde", "category": "france"},
    {"url": "https://www.lefigaro.fr/rss/figaro_actualites.xml", "name": "Le Figaro", "category": "france"},
    {"url": "https://www.francetvinfo.fr/titres.rss", "name": "France Info", "category": "france"},
    {"url": "https://feeds.bbci.co.uk/news/world/rss.xml", "name": "BBC World", "category": "monde"},
    {"url": "https://rss.nytimes.com/services/xml/rss/nyt/World.xml", "name": "NY Times World", "category": "monde"},
    {"url": "https://techcrunch.com/feed/", "name": "TechCrunch", "category": "tech"},
    {"url": "https://www.01net.com/rss/actualites/", "name": "01net", "category": "tech"},
    {"url": "https://www.lesechos.fr/rss/rss_une.xml", "name": "Les Échos", "category": "eco"},
    {"url": "https://www.lequipe.fr/rss/actu_rss.xml", "name": "L'Équipe", "category": "sport"},
]


def seed() -> None:
    Base.metadata.create_all(bind=engine)
    db = SessionLocal()
    try:
        added = 0
        for data in INITIAL_SOURCES:
            if not db.query(RssSource).filter(RssSource.url == data["url"]).first():
                db.add(RssSource(**data))
                added += 1

        if not db.query(WorkerState).filter(WorkerState.id == 1).first():
            db.add(WorkerState(id=1))

        db.commit()
        logger.info("Seeded %d RSS sources", added)
    finally:
        db.close()


if __name__ == "__main__":
    seed()
