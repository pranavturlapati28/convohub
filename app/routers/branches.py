from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.db import get_db
from app.models import Branch, Thread, Message
from app.schemas import BranchCreate, BranchOut
from app.auth import get_current_user, get_current_tenant_context, TenantContext
from uuid import uuid4
from datetime import datetime, timedelta

router = APIRouter(tags=["branches"])

@router.get(
    "/threads/{thread_id}/branches",
    response_model=List[BranchOut],
    status_code=status.HTTP_200_OK,
    summary="List branches in a thread",
    description="Retrieve all branches that belong to a given thread.",
    responses={
        200: {"description": "Branches retrieved successfully"},
        404: {"description": "Thread not found"},
        401: {"description": "Authentication required"},
    }
)
def list_branches(
    thread_id: str,
    db: Session = Depends(get_db),
    context: TenantContext = Depends(get_current_tenant_context)
):
    thread = db.get(Thread, thread_id)
    if not thread or thread.owner_id != context.user_id or thread.tenant_id != context.tenant_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Thread not found"
        )

    branches = (
        db.query(Branch)
        .filter(Branch.thread_id == thread_id, Branch.tenant_id == context.tenant_id)
        .order_by(Branch.created_at.asc())
        .all()
    )

    return [
        BranchOut(
            id=b.id,
            name=b.name,
            thread_id=b.thread_id,
            created_from_branch_id=b.created_from_branch_id,
            created_from_message_id=b.created_from_message_id,
            created_at=b.created_at,
        )
        for b in branches
    ]

@router.post(
    "/threads/{thread_id}/branches",
    response_model=BranchOut,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new branch",
    description="Create a new branch in a thread. Can fork from an existing branch or message.",
    responses={
        201: {"description": "Branch created successfully"},
        400: {"description": "Invalid request data"},
        404: {"description": "Thread not found"},
        401: {"description": "Authentication required"},
        422: {"description": "Validation error"},
    }
)
def create_branch(
    thread_id: str, 
    body: BranchCreate, 
    db: Session = Depends(get_db), 
    context: TenantContext = Depends(get_current_tenant_context)
):
    """
    Create a new branch in a thread.
    
    Args:
        thread_id: Thread identifier
        body: Branch creation data
        db: Database session
        user: Authenticated user
        
    Returns:
        BranchOut: Created branch information
        
    Raises:
        HTTPException: If branch creation fails
    """
    thread = db.get(Thread, thread_id)
    if not thread or thread.owner_id != context.user_id or thread.tenant_id != context.tenant_id:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Thread not found"
        )

    seed_snapshot = None
    if body.created_from_message_id:
        fork_msg = db.get(Message, body.created_from_message_id)
        if not fork_msg:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail="created_from_message_id not found"
            )
        seed_snapshot = fork_msg.state_snapshot
    
    # Copy messages from source branch if forking
    source_messages = []
    if body.created_from_branch_id:
        source_branch = db.get(Branch, body.created_from_branch_id)
        if not source_branch or source_branch.thread_id != thread_id:
            raise HTTPException(
                status_code=status.HTTP_400_BAD_REQUEST, 
                detail="created_from_branch_id not found or wrong thread"
            )
        source_messages = db.query(Message).filter(
            Message.branch_id == body.created_from_branch_id
        ).order_by(Message.created_at.asc()).all()

    try:
        b = Branch(
            id=str(uuid4()),
            tenant_id=context.tenant_id,
            thread_id=thread_id,
            name=body.name,
            created_from_branch_id=body.created_from_branch_id,
            created_from_message_id=body.created_from_message_id,
            created_at=datetime.utcnow(),
        )
        b = Branch(
            id=str(uuid4()),
            tenant_id=context.tenant_id,
            thread_id=thread_id,
            name=body.name,
            created_from_branch_id=body.created_from_branch_id,
            created_from_message_id=body.created_from_message_id,
            created_at=datetime.utcnow(),
        )
        db.add(b)
        db.flush()  # Ensure branch is persisted
        
        seed_id = str(uuid4())
        seed = Message(
            id=seed_id,
            tenant_id=context.tenant_id,
            branch_id=b.id,
            parent_message_id=None,
            role="system",
            content={"text": "Branch created" + (" from snapshot" if seed_snapshot else "")},
            state_snapshot=seed_snapshot,
            created_at=datetime.utcnow() - timedelta(seconds=1),  # Ensure it's first
        )
        db.add(seed)
        db.flush()  # Ensure seed message is persisted
        
        # Update branch with base_message_id
        b.base_message_id = seed_id

        # Copy messages from source branch to create shared history
        if source_messages:
            # Skip the system message (first message) from source
            prev_msg_id = seed_id
            for i, src_msg in enumerate(source_messages[1:], 1):  # Start from index 1
                new_msg = Message(
                    id=str(uuid4()),
                    tenant_id=context.tenant_id,
                    branch_id=b.id,
                    parent_message_id=prev_msg_id,
                    role=src_msg.role,
                    content=src_msg.content,
                    state_snapshot=src_msg.state_snapshot,
                    origin=src_msg.origin,
                    created_at=datetime.utcnow(),  # Use current time for copied messages
                )
                db.add(new_msg)
                prev_msg_id = new_msg.id

        db.commit()
        
        return BranchOut(
            id=b.id,
            name=b.name,
            thread_id=b.thread_id,
            created_from_branch_id=b.created_from_branch_id,
            created_from_message_id=b.created_from_message_id,
            created_at=b.created_at
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create branch: {str(e)}"
        )


