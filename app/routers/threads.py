from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List
from app.db import get_db
from app.models import Thread
from app.schemas import ThreadCreate, ThreadOut
from app.auth import get_current_user, get_current_tenant_context, TenantContext
from uuid import uuid4
from datetime import datetime

router = APIRouter(tags=["threads"])

@router.get(
    "/threads",
    response_model=List[ThreadOut],
    summary="List threads",
    description="List all threads accessible to the authenticated user.",
    responses={
        200: {"description": "Threads retrieved successfully"},
        401: {"description": "Authentication required"},
    }
)
def list_threads(
    db: Session = Depends(get_db),
    context: TenantContext = Depends(get_current_tenant_context)
):
    """
    List all threads accessible to the authenticated user.
    
    Args:
        db: Database session
        context: Current tenant context
        
    Returns:
        List[ThreadOut]: List of accessible threads
    """
    threads = (
        db.query(Thread)
        .filter(Thread.tenant_id == context.tenant_id)
        .order_by(Thread.created_at.desc())
        .all()
    )
    
    return [
        ThreadOut(
            id=t.id,
            title=t.title,
            created_at=t.created_at
        )
        for t in threads
    ]

@router.post(
    "/threads", 
    response_model=ThreadOut,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new thread",
    description="Create a new conversation thread. The thread will be owned by the authenticated user.",
    responses={
        201: {"description": "Thread created successfully"},
        400: {"description": "Invalid request data"},
        401: {"description": "Authentication required"},
        422: {"description": "Validation error"},
    }
)
def create_thread(
    body: ThreadCreate, 
    db: Session = Depends(get_db), 
    context: TenantContext = Depends(get_current_tenant_context)
):
    """
    Create a new conversation thread.
    
    Args:
        body: Thread creation data
        db: Database session
        user: Authenticated user
        
    Returns:
        ThreadOut: Created thread information
        
    Raises:
        HTTPException: If thread creation fails
    """
    try:
        t = Thread(
            id=str(uuid4()), 
            tenant_id=context.tenant_id,
            owner_id=context.user_id, 
            title=body.title,
            created_at=datetime.utcnow()
        )
        db.add(t)
        db.commit()
        db.refresh(t)
        
        return ThreadOut(
            id=t.id, 
            title=t.title,
            created_at=t.created_at
        )
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create thread: {str(e)}"
        )
