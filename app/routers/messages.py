from typing import List, Dict, Any, Optional
from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from uuid import uuid4

from app.db import get_db
from app.models import Branch, Message
from app.schemas import MessageIn, MessageOut, MessageResponse, PaginatedMessages, PaginationParams
from app.auth import get_current_user
from app.llm import assistant_reply
from app.idempotency import IdempotencyKey, validate_idempotency_key

from datetime import datetime

router = APIRouter(tags=["messages"])

@router.get(
    "/branches/{branch_id}/messages", 
    response_model=PaginatedMessages,
    summary="List messages in a branch",
    description="Retrieve messages from a branch with pagination support.",
    responses={
        200: {"description": "Messages retrieved successfully"},
        404: {"description": "Branch not found"},
        401: {"description": "Authentication required"},
    }
)
def list_messages(
    branch_id: str,
    cursor: Optional[str] = Query(None, description="Cursor for pagination (message ID)"),
    limit: int = Query(50, ge=1, le=100, description="Maximum number of messages to return"),
    db: Session = Depends(get_db),
    user=Depends(get_current_user),
):
    """
    List messages in a branch with pagination.
    
    Args:
        branch_id: Branch identifier
        cursor: Pagination cursor (message ID)
        limit: Maximum number of messages to return
        db: Database session
        user: Authenticated user
        
    Returns:
        PaginatedMessages: Paginated list of messages
        
    Raises:
        HTTPException: If branch not found
    """
    branch = db.get(Branch, branch_id)
    if not branch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Branch not found"
        )

    # Build query with pagination
    query = db.query(Message).filter(Message.branch_id == branch_id)
    
    if cursor:
        # Get the cursor message to find its position
        cursor_msg = db.get(Message, cursor)
        if cursor_msg and cursor_msg.branch_id == branch_id:
            # Get messages created after the cursor message
            query = query.filter(Message.created_at > cursor_msg.created_at)
    
    # Order by creation time and limit
    messages = query.order_by(Message.created_at.asc()).limit(limit + 1).all()
    
    # Check if there are more messages
    has_more = len(messages) > limit
    if has_more:
        messages = messages[:-1]  # Remove the extra message
    
    # Determine next cursor
    next_cursor = None
    if has_more and messages:
        next_cursor = messages[-1].id
    
    return PaginatedMessages(
        messages=[
            MessageOut(
                id=m.id,
                role=m.role,
                content=m.content,
                parent_message_id=m.parent_message_id,
                created_at=m.created_at
            )
            for m in messages
        ],
        next_cursor=next_cursor,
        has_more=has_more
    )


@router.post(
    "/branches/{branch_id}/messages",
    response_model=MessageResponse,
    status_code=status.HTTP_201_CREATED,
    summary="Send a message to a branch",
    description="Send a user message to a branch and get an AI response. Supports idempotency keys.",
    responses={
        201: {"description": "Message sent successfully"},
        400: {"description": "Invalid request data"},
        404: {"description": "Branch not found"},
        409: {"description": "Idempotency key conflict"},
        401: {"description": "Authentication required"},
        422: {"description": "Validation error"},
    }
)
def send_user_message(
    branch_id: str, 
    body: MessageIn, 
    idempotency_key: Optional[str] = Query(None, description="Idempotency key to prevent duplicate operations"),
    db: Session = Depends(get_db), 
    user=Depends(get_current_user)
):
    """
    Send a user message to a branch and get an AI response.
    
    Args:
        branch_id: Branch identifier
        body: Message data
        idempotency_key: Optional idempotency key to prevent duplicates
        db: Database session
        user: Authenticated user
        
    Returns:
        MessageResponse: IDs of created user and assistant messages
        
    Raises:
        HTTPException: If operation fails
    """
    branch = db.get(Branch, branch_id)
    if not branch:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, 
            detail="Branch not found"
        )

    # Handle idempotency if key provided
    if idempotency_key:
        validate_idempotency_key(idempotency_key)
        idempotency = IdempotencyKey(db, idempotency_key, "send_message")
        cached_result = idempotency.check_and_lock()
        if cached_result:
            return MessageResponse(**cached_result)

    try:
        # Use explicit commit/rollback if no outer transaction, else nest
        if not db.in_transaction():
            transaction_context = db.begin()
        else:
            transaction_context = db.begin_nested()

        with transaction_context:
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
            db.flush() # Ensure user_msg is persisted before assistant_msg references it

            # Get conversation history
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

        # Only commit if this is the outermost transaction
        if not db.in_nested_transaction():
            db.commit()

        result = MessageResponse(
            user_message_id=user_msg.id, 
            assistant_message_id=ai_msg.id
        )

        # Store result for idempotency
        if idempotency_key:
            idempotency.store_result(result.dict())

        return result

    except Exception as e:
        # Only rollback if this is the outermost transaction
        if not db.in_nested_transaction():
            db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to write message: {type(e).__name__}: {e}"
        )