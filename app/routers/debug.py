from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.db import get_db
from app.core.settings import settings

router = APIRouter(tags=["debug"])

@router.get("/v1/_debug/config")
def dbg_config():
    return {
        "ENV": settings.ENV,
        "DATABASE_URL": settings.DATABASE_URL,
        "TEST_DATABASE_URL": settings.TEST_DATABASE_URL,
    }

@router.get("/v1/_debug/db")
def dbg_db(db: Session = Depends(get_db)):
    # 1) is 'threads' table present?
    exists = db.execute(text("""
        SELECT EXISTS (
          SELECT 1 FROM information_schema.tables
          WHERE table_schema='public' AND table_name='threads'
        )
    """)).scalar()
    return {"threads_table_exists": bool(exists)}
