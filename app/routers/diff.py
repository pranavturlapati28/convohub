# app/routers/diff.py (new router)
from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from app.db import get_db
from app.models import Branch, Message
from app.schemas import DiffResponse
from app.merge_utils import find_lca, path_after, interleave_by_created_at

router = APIRouter(tags=["diff"])

@router.get(
    "/diff",
    response_model=DiffResponse,
    summary="Compare two branches",
    description="Compare two branches to find their differences and lowest common ancestor.",
    responses={
        200: {"description": "Diff computed successfully"},
        400: {"description": "Invalid request data"},
        404: {"description": "Branch not found"},
        401: {"description": "Authentication required"},
        422: {"description": "Validation error"},
    }
)
def diff(
    source_branch_id: str, 
    target_branch_id: str, 
    db: Session = Depends(get_db)
):
    """
    Compare two branches to find their differences.
    
    Args:
        source_branch_id: Source branch identifier
        target_branch_id: Target branch identifier
        db: Database session
        
    Returns:
        DiffResponse: Diff information including LCA and deltas
        
    Raises:
        HTTPException: If comparison fails
    """
    src = db.get(Branch, source_branch_id)
    tgt = db.get(Branch, target_branch_id)
    if not src or not tgt or src.thread_id != tgt.thread_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Branches must exist and be in the same thread"
        )

    tgt_tip = db.query(Message).filter(
        Message.branch_id == tgt.id
    ).order_by(Message.created_at.desc()).first()
    src_tip = db.query(Message).filter(
        Message.branch_id == src.id
    ).order_by(Message.created_at.desc()).first()
    
    if not tgt_tip or not src_tip:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Both branches must have at least one message"
        )

    lca_id = find_lca(db, src_tip.id, tgt_tip.id)
    a_path = path_after(db, lca_id, src_tip.id) if lca_id else []
    b_path = path_after(db, lca_id, tgt_tip.id) if lca_id else []
    merged = interleave_by_created_at(a_path, b_path)

    return DiffResponse(
        lca=lca_id,
        src_delta=[m.id for m in a_path],
        tgt_delta=[m.id for m in b_path],
        merged_order=[m.id for m in merged],
    )
