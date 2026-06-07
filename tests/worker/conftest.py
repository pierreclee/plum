import pytest
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

TEST_DB_URL = "sqlite:///./test_worker.db"


@pytest.fixture(scope="function")
def engine_fixture():
    from worker.database import Base
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
