# app/routers/diff.py (enhanced router)
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from datetime import datetime
from typing import Optional
from app.db import get_db
from app.models import Branch, Message
from app.schemas import DiffResponse, DiffMode
from app.merge_utils import find_lca, path_after, interleave_by_created_at
from app.diff_utils import (
    compute_memory_diff, 
    compute_summary_diff, 
    compute_message_ranges,
    find_base_branch_for_three_way_diff
)

router = APIRouter(tags=["diff"])

@router.get(
    "/diff",
    response_model=DiffResponse,
    summary="Compare two branches with enhanced diff semantics",
    description="""
    Compare two branches to find their differences with enhanced semantics.
    
    Supports three diff modes:
    - **summary**: Compare summaries between branches
    - **messages**: Compare messages by ID ranges with LCA analysis
    - **memory**: Three-way diff for memory maps (added, removed, modified, conflicts)
    
    Parameters:
    - **left**: Left branch ID (required)
    - **right**: Right branch ID (required) 
    - **mode**: Diff mode - summary, messages, or memory (default: messages)
    """,
    responses={
        200: {"description": "Diff computed successfully"},
        400: {"description": "Invalid request data"},
        404: {"description": "Branch not found"},
        401: {"description": "Authentication required"},
        422: {"description": "Validation error"},
    }
)
def diff(
    left: str = Query(..., description="Left branch ID"),
    right: str = Query(..., description="Right branch ID"),
    mode: DiffMode = Query(DiffMode.MESSAGES, description="Diff mode: summary, messages, or memory"),
    db: Session = Depends(get_db)
):
    """
    Enhanced diff endpoint with three-way diff for memory maps and message diff by message-id ranges.
    
    Args:
        left: Left branch identifier
        right: Right branch identifier
        mode: Diff mode (summary, messages, memory)
        db: Database session
        
    Returns:
        DiffResponse: Enhanced diff information including mode-specific data
        
    Raises:
        HTTPException: If comparison fails
    """
    # Validate branches exist and are in the same thread
    left_branch = db.get(Branch, left)
    right_branch = db.get(Branch, right)
    
    if not left_branch or not right_branch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="One or both branches not found"
        )
    
    if left_branch.thread_id != right_branch.thread_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Branches must be in the same thread"
        )
    
    # Get branch tips for LCA calculation
    left_tip = db.query(Message).filter(
        Message.branch_id == left
    ).order_by(Message.created_at.desc()).first()
    
    right_tip = db.query(Message).filter(
        Message.branch_id == right
    ).order_by(Message.created_at.desc()).first()
    
    if not left_tip or not right_tip:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Both branches must have at least one message"
        )
    
    # Calculate LCA for message-based diff
    lca_id = find_lca(db, left_tip.id, right_tip.id)
    left_path = path_after(db, lca_id, left_tip.id) if lca_id else []
    right_path = path_after(db, lca_id, right_tip.id) if lca_id else []
    merged = interleave_by_created_at(left_path, right_path)
    
    # Initialize response with basic diff info
    response = DiffResponse(
        lca=lca_id,
        src_delta=[m.id for m in left_path],
        tgt_delta=[m.id for m in right_path],
        merged_order=[m.id for m in merged],
        mode=mode,
        left_branch_id=left,
        right_branch_id=right,
        diff_timestamp=datetime.utcnow()
    )
    
    # Add mode-specific diff information
    if mode == DiffMode.MEMORY:
        # Three-way diff for memory maps
        base_branch_id = find_base_branch_for_three_way_diff(db, left, right)
        memory_diff = compute_memory_diff(db, left, right, base_branch_id)
        response.memory_diff = memory_diff
        
    elif mode == DiffMode.SUMMARY:
        # Summary diff
        summary_diff = compute_summary_diff(db, left, right)
        response.summary_diff = summary_diff
        
    elif mode == DiffMode.MESSAGES:
        # Message ranges diff
        message_ranges = compute_message_ranges(db, left, right, lca_id)
        response.message_ranges = message_ranges
    
    return response


@router.get(
    "/diff/memory",
    response_model=DiffResponse,
    summary="Three-way memory diff between branches",
    description="Compute three-way diff for memory maps between branches, identifying added, removed, modified, and conflicting memories.",
    responses={
        200: {"description": "Memory diff computed successfully"},
        400: {"description": "Invalid request data"},
        404: {"description": "Branch not found"},
    }
)
def memory_diff(
    left: str = Query(..., description="Left branch ID"),
    right: str = Query(..., description="Right branch ID"),
    db: Session = Depends(get_db)
):
    """
    Specialized endpoint for three-way memory diff.
    
    Args:
        left: Left branch identifier
        right: Right branch identifier
        db: Database session
        
    Returns:
        DiffResponse: Memory diff information
    """
    return diff(left=left, right=right, mode=DiffMode.MEMORY, db=db)


@router.get(
    "/diff/summary", 
    response_model=DiffResponse,
    summary="Summary diff between branches",
    description="Compare summaries between branches to identify common content and differences.",
    responses={
        200: {"description": "Summary diff computed successfully"},
        400: {"description": "Invalid request data"},
        404: {"description": "Branch not found"},
    }
)
def summary_diff(
    left: str = Query(..., description="Left branch ID"),
    right: str = Query(..., description="Right branch ID"),
    db: Session = Depends(get_db)
):
    """
    Specialized endpoint for summary diff.
    
    Args:
        left: Left branch identifier
        right: Right branch identifier
        db: Database session
        
    Returns:
        DiffResponse: Summary diff information
    """
    return diff(left=left, right=right, mode=DiffMode.SUMMARY, db=db)


@router.get(
    "/diff/messages",
    response_model=DiffResponse,
    summary="Message ranges diff between branches",
    description="Compare messages between branches by ID ranges, organized around the Lowest Common Ancestor.",
    responses={
        200: {"description": "Message ranges diff computed successfully"},
        400: {"description": "Invalid request data"},
        404: {"description": "Branch not found"},
    }
)
def message_ranges_diff(
    left: str = Query(..., description="Left branch ID"),
    right: str = Query(..., description="Right branch ID"),
    db: Session = Depends(get_db)
):
    """
    Specialized endpoint for message ranges diff.
    
    Args:
        left: Left branch identifier
        right: Right branch identifier
        db: Database session
        
    Returns:
        DiffResponse: Message ranges diff information
    """
    return diff(left=left, right=right, mode=DiffMode.MESSAGES, db=db)
