from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session
from uuid import uuid4
from app.db import get_db
from app.models import Branch, Message, Merge
from app.schemas import MergeRequest

router = APIRouter(tags=["merges"])

from app.merge_utils import find_lca, path_after, interleave_by_created_at

@router.post("/merge")
def merge(req: MergeRequest, db: Session = Depends(get_db)):
    src = db.get(Branch, req.source_branch_id)
    tgt = db.get(Branch, req.target_branch_id)
    if not src or not tgt or src.thread_id != tgt.thread_id or tgt.thread_id != req.thread_id:
        raise HTTPException(400, "branches must exist and belong to the same thread")

    tgt_tip = db.query(Message).filter(Message.branch_id==tgt.id).order_by(Message.created_at.desc()).first()
    src_tip = db.query(Message).filter(Message.branch_id==src.id).order_by(Message.created_at.desc()).first()
    if not tgt_tip or not src_tip:
        raise HTTPException(400, "both branches must have at least one message")

    lca_id = find_lca(db, src_tip.id, tgt_tip.id)
    a_path = path_after(db, lca_id, src_tip.id) if lca_id else []
    b_path = path_after(db, lca_id, tgt_tip.id) if lca_id else []

    merged_stream = interleave_by_created_at(a_path, b_path)
    diff_summary = {
        "lca": lca_id,
        "src_delta": [m.id for m in a_path],
        "tgt_delta": [m.id for m in b_path],
        "merged_order": [m.id for m in merged_stream],
    }

    parent_id = tgt_tip.id
    merge_commit_id = str(uuid4())
    merge_msg = Message(
        id=merge_commit_id,
        branch_id=tgt.id,
        parent_message_id=parent_id,
        role="assistant",
        content={"text": f"[merge:{req.strategy}] merged {src.id} -> {tgt.id}", "diff": diff_summary},
        state_snapshot={"v": 1, "note": "merged-stub"},
        origin="merge",
    )
    with db.begin_nested():
        db.add(merge_msg)
        db.flush()
        m = Merge(
            id=str(uuid4()),
            thread_id=tgt.thread_id,
            source_branch_id=src.id,
            target_branch_id=tgt.id,
            strategy=req.strategy,
            lca_message_id=lca_id,
            merged_into_message_id=merge_commit_id,
            summary=diff_summary,
        )
        db.add(m)

    return {"merge_id": m.id, "merged_into_message_id": merge_commit_id}
