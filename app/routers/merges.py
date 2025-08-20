from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from uuid import uuid4
from app.db import get_db
from app.models import Branch, Message, Merge
from app.schemas import MergeRequest, MergeResponse
from app.idempotency import IdempotencyKey, validate_idempotency_key
from datetime import datetime

router = APIRouter(tags=["merges"])

from app.merge_utils import find_lca, path_after, interleave_by_created_at

@router.post(
    "/merge",
    response_model=MergeResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Merge two branches",
    description="Merge a source branch into a target branch. Supports idempotency keys to prevent duplicate merges.",
    responses={
        201: {"description": "Merge completed successfully"},
        400: {"description": "Invalid request data"},
        404: {"description": "Branch not found"},
        409: {"description": "Idempotency key conflict"},
        401: {"description": "Authentication required"},
        422: {"description": "Validation error"},
    }
)
def merge(
    req: MergeRequest, 
    db: Session = Depends(get_db)
):
    """
    Merge a source branch into a target branch.
    
    Args:
        req: Merge request data including idempotency key
        db: Database session
        
    Returns:
        MergeResponse: Merge operation result
        
    Raises:
        HTTPException: If merge operation fails
    """
    # Validate idempotency key
    validate_idempotency_key(req.idempotency_key)
    
    # Check for existing merge with same idempotency key
    idempotency = IdempotencyKey(db, req.idempotency_key, "merge")
    cached_result = idempotency.check_and_lock()
    if cached_result:
        return MergeResponse(**cached_result)

    src = db.get(Branch, req.source_branch_id)
    tgt = db.get(Branch, req.target_branch_id)
    if not src or not tgt or src.thread_id != tgt.thread_id or tgt.thread_id != req.thread_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST, 
            detail="Branches must exist and belong to the same thread"
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
        created_at=datetime.utcnow(),
    )
    
    try:
        # Use explicit commit/rollback if no outer transaction, else nest
        if not db.in_transaction():
            transaction_context = db.begin()
        else:
            transaction_context = db.begin_nested()

        with transaction_context:
            db.add(merge_msg)
            db.flush() # Ensure merge_msg is persisted before Merge references it
            
            m = Merge(
                id=str(uuid4()),
                thread_id=tgt.thread_id,
                source_branch_id=src.id,
                target_branch_id=tgt.id,
                strategy=req.strategy,
                lca_message_id=lca_id,
                merged_into_message_id=merge_commit_id,
                summary=diff_summary,
                created_at=datetime.utcnow(),
            )
            db.add(m)

        # Only commit if this is the outermost transaction
        if not db.in_nested_transaction():
            db.commit()

        result = MergeResponse(
            merge_id=m.id, 
            merged_into_message_id=merge_commit_id
        )

        # Store result for idempotency
        idempotency.store_result(result.dict())

        return result
        
    except Exception as e:
        # Only rollback if this is the outermost transaction
        if not db.in_nested_transaction():
            db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to merge branches: {str(e)}"
        )
