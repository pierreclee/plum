import sys
import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

# Ajoute api/ au sys.path pour que les imports plats fonctionnent (database, models, etc.)
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', '..', 'api'))

TEST_DB_URL = "sqlite:///./test_api.db"


@pytest.fixture(scope="function")
def engine_fixture():
    from database import Base
    eng = create_engine(TEST_DB_URL, connect_args={"check_same_thread": False})
    Base.metadata.create_all(bind=eng)
    yield eng
    Base.metadata.drop_all(bind=eng)


@pytest.fixture
def db(engine_fixture):
    Session = sessionmaker(autocommit=False, autoflush=False, bind=engine_fixture)
    session = Session()
    try:
        yield session
    finally:
        session.close()


@pytest.fixture
def client(db):
    from main import app
    from database import get_db

    def override_get_db():
        yield db

    app.dependency_overrides[get_db] = override_get_db
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
