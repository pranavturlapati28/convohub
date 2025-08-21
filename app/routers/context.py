from typing import Optional, List
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy import func, desc

from app.db import get_db
from app.models import Branch, Thread, Summary, Memory
from app.context_builder import ContextBuilder, ContextPolicy, ConversationContext
from app.auth import get_current_tenant_context, TenantContext

router = APIRouter(tags=["context"])


@router.get(
    "/context/{branch_id}",
    response_model=ConversationContext,
    summary="Build conversation context",
    description="Return context {system, messages_window, summary, memory} for a branch using a policy.",
    responses={
        200: {"description": "Context built successfully"},
        404: {"description": "Branch not found"},
        401: {"description": "Authentication required"},
        422: {"description": "Validation error"},
    }
)
def get_context(
    branch_id: str,
    window_size: int = Query(50, ge=1, le=500, description="Number of recent messages to include"),
    use_summary: bool = Query(True, description="Whether to include thread summary"),
    use_memory: bool = Query(True, description="Whether to include relevant memories"),
    max_tokens: int = Query(8000, ge=512, le=100000, description="Maximum tokens for context"),
    db: Session = Depends(get_db),
    context: TenantContext = Depends(get_current_tenant_context)
):
    """
    Build conversation context for a branch using a policy.
    
    Args:
        branch_id: Branch identifier
        window_size: Number of recent messages to include
        use_summary: Whether to include thread summary
        use_memory: Whether to include relevant memories
        max_tokens: Maximum tokens for context
        db: Database session
        context: Tenant context
        
    Returns:
        ConversationContext: Complete conversation context
        
    Raises:
        HTTPException: If branch not found
    """
    # Verify branch exists and user has access
    branch = db.query(Branch).filter(
        Branch.id == branch_id,
        Branch.tenant_id == context.tenant_id
    ).first()
    
    if not branch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Branch not found"
        )
    
    # Build context using policy
    policy = ContextPolicy(
        window_size=window_size,
        use_summary=use_summary,
        use_memory=use_memory,
        max_tokens=max_tokens
    )
    
    ctx = ContextBuilder(db).build_context(branch_id, policy)
    return ctx


@router.get(
    "/threads/{thread_id}/summaries",
    summary="List thread summaries",
    description="Get all summaries for a thread, including current and historical versions.",
    responses={
        200: {"description": "Summaries retrieved successfully"},
        404: {"description": "Thread not found"},
        401: {"description": "Authentication required"},
    }
)
def list_thread_summaries(
    thread_id: str,
    db: Session = Depends(get_db),
    context: TenantContext = Depends(get_current_tenant_context)
):
    """List all summaries for a thread."""
    # Verify thread exists and user has access
    thread = db.query(Thread).filter(
        Thread.id == thread_id,
        Thread.tenant_id == context.tenant_id
    ).first()
    
    if not thread:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Thread not found"
        )
    
    summaries = db.query(Summary).filter(
        Summary.thread_id == thread_id
    ).order_by(Summary.created_at.desc()).all()
    
    return {
        "thread_id": thread_id,
        "summaries": [
            {
                "id": s.id,
                "summary_type": s.summary_type,
                "content": s.content,
                "is_current": s.is_current,
                "version": s.version,
                "created_at": s.created_at.isoformat(),
                "updated_at": s.updated_at.isoformat(),
                "metadata": s.summary_metadata
            }
            for s in summaries
        ]
    }


@router.get(
    "/threads/{thread_id}/memories",
    summary="List thread memories",
    description="Get all memories for a thread, organized by type.",
    responses={
        200: {"description": "Memories retrieved successfully"},
        404: {"description": "Thread not found"},
        401: {"description": "Authentication required"},
    }
)
def list_thread_memories(
    thread_id: str,
    memory_type: Optional[str] = Query(None, description="Filter by memory type (fact, preference, context, relationship)"),
    db: Session = Depends(get_db),
    context: TenantContext = Depends(get_current_tenant_context)
):
    """List all memories for a thread."""
    # Verify thread exists and user has access
    thread = db.query(Thread).filter(
        Thread.id == thread_id,
        Thread.tenant_id == context.tenant_id
    ).first()
    
    if not thread:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Thread not found"
        )
    
    query = db.query(Memory).filter(Memory.thread_id == thread_id)
    
    if memory_type:
        query = query.filter(Memory.memory_type == memory_type)
    
    memories = query.order_by(Memory.created_at.desc()).all()
    
    # Group by memory type
    grouped_memories = {}
    for memory in memories:
        if memory.memory_type not in grouped_memories:
            grouped_memories[memory.memory_type] = []
        
        grouped_memories[memory.memory_type].append({
            "id": memory.id,
            "key": memory.key,
            "value": memory.value,
            "confidence": memory.confidence,
            "source": memory.source,
            "created_at": memory.created_at.isoformat(),
            "updated_at": memory.updated_at.isoformat(),
            "metadata": memory.memory_metadata
        })
    
    return {
        "thread_id": thread_id,
        "memory_type_filter": memory_type,
        "total_memories": len(memories),
        "memories_by_type": grouped_memories
    }
