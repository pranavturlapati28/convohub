from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from uuid import uuid4

from app.db import get_db
from app.models import Branch, Message
from app.schemas import MessageIn, MessageOut
from app.auth import get_current_user
from app.llm import assistant_reply

from datetime import datetime

router = APIRouter(tags=["messages"])

@router.get("/branches/{branch_id}/messages", response_model=List[MessageOut])
def list_messages(
    branch_id: str,
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    branch = db.get(Branch, branch_id)
    if not branch:
        raise HTTPException(404, "branch not found")

    msgs = (
        db.query(Message)
        .filter(Message.branch_id == branch_id)
        .order_by(Message.created_at.asc())
        .all()
    )
    return [
        {
            "id": m.id,
            "role": m.role,
            "content": m.content,
            "parent_message_id": m.parent_message_id,
        }
        for m in msgs
    ]


from sqlalchemy.exc import SQLAlchemyError

@router.post("/branches/{branch_id}/messages")
def send_user_message(branch_id: str, body: MessageIn, db: Session = Depends(get_db), user=Depends(get_current_user)):
    branch = db.get(Branch, branch_id)
    if not branch:
        raise HTTPException(404, "branch not found")

    try:
        with db.begin_nested():  # one atomic transaction
            q = (db.query(Message)
                   .filter(Message.branch_id == branch_id)
                   .order_by(Message.created_at.desc()))
            if getattr(getattr(db.bind, "dialect", None), "name", "") in ("postgresql", "postgres"):
                q = q.with_for_update()
            last_msg = q.first()
            parent_id_for_user = last_msg.id if last_msg else None

            user_msg = Message(
                id=str(uuid4()),
                branch_id=branch_id,
                parent_message_id=parent_id_for_user,
                role="user",
                content={"text": body.text},
                created_at=datetime.utcnow(),
            )
            db.add(user_msg)
            db.flush()

            prior = (db.query(Message)
                       .filter(Message.branch_id == branch_id)
                       .order_by(Message.created_at.asc())
                       .all())
            def to_text(c):
                if isinstance(c, dict):
                    return c.get("text", "")
                return "" if c is None else str(c)

            history = [{"role": m.role, "content": to_text(m.content)} for m in prior]
            history.append({"role": "user", "content": body.text})

            ai_text = assistant_reply(history)

            ai_msg = Message(
                id=str(uuid4()),
                branch_id=branch_id,
                parent_message_id=user_msg.id,
                role="assistant",
                content={"text": ai_text},
                state_snapshot={"v": 1, "note": "stub"},
                created_at=datetime.utcnow(),
            )
            db.add(ai_msg)

        return {"user_message_id": user_msg.id, "assistant_message_id": ai_msg.id}
    except Exception as e:
        # TEMP: bubble up details so tests show the real error
        raise HTTPException(500, f"failed to write message: {type(e).__name__}: {e}")