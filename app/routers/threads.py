from fastapi import APIRouter, Depends
from sqlalchemy.orm import Session
from app.db import get_db
from app.models import Thread
from app.schemas import ThreadCreate, ThreadOut
from app.auth import get_current_user
from uuid import uuid4

router = APIRouter(tags=["threads"])

@router.post("/threads", response_model=ThreadOut)
def create_thread(body: ThreadCreate, db: Session = Depends(get_db), user=Depends(get_current_user)):
    t = Thread(id=str(uuid4()), owner_id=user.id, title=body.title)
    db.add(t); db.commit(); db.refresh(t)
    return ThreadOut(id=t.id, title=t.title)
