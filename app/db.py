from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker, DeclarativeBase
from app.core.settings import settings

# OLD:
# DB_URL = settings.TEST_DATABASE_URL or settings.DATABASE_URL

# NEW: only use TEST_DATABASE_URL when ENV == "test"
if settings.ENV == "test" and settings.TEST_DATABASE_URL:
    DB_URL = settings.TEST_DATABASE_URL
else:
    DB_URL = settings.DATABASE_URL

engine = create_engine(DB_URL, echo=False, future=True)
SessionLocal = sessionmaker(bind=engine, autoflush=False, autocommit=False)

class Base(DeclarativeBase):
    pass

def get_db():
    db = SessionLocal()
    try:
        yield db
    finally:
        db.close()
