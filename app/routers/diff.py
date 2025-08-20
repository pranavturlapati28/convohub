# app/routers/diff.py (new router)
from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from app.db import get_db
from app.models import Branch, Message
from app.merge_utils import find_lca, path_after, interleave_by_created_at

router = APIRouter(tags=["diff"])

@router.get("/diff")
def diff(source_branch_id: str, target_branch_id: str, db: Session = Depends(get_db)):
    src = db.get(Branch, source_branch_id)
    tgt = db.get(Branch, target_branch_id)
    if not src or not tgt or src.thread_id != tgt.thread_id:
        raise HTTPException(400, "branches must exist and be in the same thread")

    tgt_tip = db.query(Message).filter(Message.branch_id==tgt.id).order_by(Message.created_at.desc()).first()
    src_tip = db.query(Message).filter(Message.branch_id==src.id).order_by(Message.created_at.desc()).first()
    if not tgt_tip or not src_tip:
        raise HTTPException(400, "both branches must have at least one message")

    lca_id = find_lca(db, src_tip.id, tgt_tip.id)
    a_path = path_after(db, lca_id, src_tip.id) if lca_id else []
    b_path = path_after(db, lca_id, tgt_tip.id) if lca_id else []
    merged = interleave_by_created_at(a_path, b_path)

    return {
        "lca": lca_id,
        "src_delta": [m.id for m in a_path],
        "tgt_delta": [m.id for m in b_path],
        "merged_order": [m.id for m in merged],
    }
