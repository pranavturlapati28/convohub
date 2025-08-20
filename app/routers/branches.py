from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db import get_db
from app.models import Branch, Thread, Message
from app.schemas import BranchCreate
from app.auth import get_current_user
from uuid import uuid4

router = APIRouter(tags=["branches"])

@router.post("/threads/{thread_id}/branches")
def create_branch(thread_id: str, body: BranchCreate, db: Session = Depends(get_db), user=Depends(get_current_user)):
    thread = db.get(Thread, thread_id)
    if not thread or thread.owner_id != user.id:
        raise HTTPException(404, "thread not found")

    seed_snapshot = None
    if body.created_from_message_id:
        fork_msg = db.get(Message, body.created_from_message_id)
        if not fork_msg:
            raise HTTPException(400, "created_from_message_id not found")
        seed_snapshot = fork_msg.state_snapshot

    with db.begin_nested():
        b = Branch(
            id=str(uuid4()),
            thread_id=thread_id,
            name=body.name,
            created_from_branch_id=body.created_from_branch_id,
            created_from_message_id=body.created_from_message_id,
        )
        db.add(b)

        seed_id = str(uuid4())
        seed = Message(
            id=seed_id,
            branch_id=b.id,
            parent_message_id=None,
            role="system",
            content={"text": "Branch created" + (" from snapshot" if seed_snapshot else "")},
            state_snapshot=seed_snapshot,
        )
        db.add(seed)
        b.base_message_id = seed_id

    return {"id": b.id, "name": b.name}
