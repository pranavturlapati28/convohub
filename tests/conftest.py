# tests/conftest.py
import os
import pytest
from fastapi.testclient import TestClient
from sqlalchemy import create_engine, text
from sqlalchemy.orm import sessionmaker

# App imports
from app.main import app
from app.db import Base, get_db

# --- Ensure we use the test DB ---
os.environ.setdefault("ENV", "test")
os.environ.setdefault("DATABASE_URL", "postgresql+psycopg://convo:convo@localhost:5432/convohub")
os.environ.setdefault("TEST_DATABASE_URL", "postgresql+psycopg://convo:convo@localhost:5432/convohub_test")

TEST_DB_URL = os.environ["TEST_DATABASE_URL"]

@pytest.fixture(scope="session")
def engine():
    engine = create_engine(TEST_DB_URL, echo=False, future=True)
    # hard reset the schema to avoid circular-FK drop headaches
    with engine.connect() as conn:
        conn.execute(text("DROP SCHEMA IF EXISTS public CASCADE;"))
        conn.execute(text("CREATE SCHEMA public;"))
        conn.commit()
    Base.metadata.create_all(engine)
    try:
        yield engine
    finally:
        with engine.connect() as conn:
            conn.execute(text("DROP SCHEMA IF EXISTS public CASCADE;"))
            conn.execute(text("CREATE SCHEMA public;"))
            conn.commit()

@pytest.fixture(scope="function")
def db_session(engine):
    TestingSessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)
    session = TestingSessionLocal()
    try:
        yield session
    finally:
        session.rollback()
        session.close()

@pytest.fixture(scope="function")
def client(db_session):
    def _get_db_override():
        try:
            yield db_session
        finally:
            pass
    app.dependency_overrides[get_db] = _get_db_override
    with TestClient(app) as c:
        yield c
    app.dependency_overrides.clear()
