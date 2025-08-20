from fastapi import APIRouter, Depends, HTTPException, status, Query
from sqlalchemy.orm import Session
from typing import List, Optional
from app.db import get_db
from app.models import Edge, Message
from app.schemas import EdgeCreate, EdgeOut
from app.auth import get_current_user
from app.dag_utils import EdgeManager, DAGValidator
from datetime import datetime

router = APIRouter(tags=["edges"])

@router.post(
    "/messages/{message_id}/edges",
    response_model=EdgeOut,
    status_code=status.HTTP_201_CREATED,
    summary="Add an edge to a message",
    description="Add an explicit edge in the message DAG. Supports multi-parent relationships for merge nodes.",
    responses={
        201: {"description": "Edge created successfully"},
        400: {"description": "Invalid request data or would create cycle"},
        404: {"description": "Message not found"},
        409: {"description": "Edge already exists"},
        401: {"description": "Authentication required"},
        422: {"description": "Validation error"},
    }
)
def add_edge(
    message_id: str,
    body: EdgeCreate,
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    """
    Add an edge to a message in the DAG.
    
    Args:
        message_id: Target message ID
        body: Edge creation data
        db: Database session
        user: Authenticated user
        
    Returns:
        EdgeOut: Created edge information
        
    Raises:
        HTTPException: If edge creation fails
    """
    # Verify target message exists
    target_message = db.get(Message, message_id)
    if not target_message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Target message not found"
        )
    
    # Verify source message exists
    source_message = db.get(Message, body.from_message_id)
    if not source_message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Source message not found"
        )
    
    # Verify both messages are in the same branch
    if target_message.branch_id != source_message.branch_id:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Source and target messages must be in the same branch"
        )
    
    try:
        edge = EdgeManager.add_edge(
            db=db,
            from_message_id=body.from_message_id,
            to_message_id=message_id,
            edge_type=body.edge_type,
            weight=body.weight
        )
        
        return EdgeOut(
            id=edge.id,
            from_message_id=edge.from_message_id,
            to_message_id=edge.to_message_id,
            edge_type=edge.edge_type,
            weight=edge.weight,
            created_at=edge.created_at
        )
        
    except HTTPException:
        raise
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create edge: {str(e)}"
        )


@router.get(
    "/messages/{message_id}/edges",
    response_model=List[EdgeOut],
    summary="Get edges for a message",
    description="Get all edges connected to a message (incoming, outgoing, or both).",
    responses={
        200: {"description": "Edges retrieved successfully"},
        404: {"description": "Message not found"},
        401: {"description": "Authentication required"},
    }
)
def get_edges(
    message_id: str,
    direction: str = Query("both", description="Direction: 'in', 'out', or 'both'"),
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    """
    Get edges for a message.
    
    Args:
        message_id: Message ID
        direction: Edge direction to retrieve
        db: Database session
        user: Authenticated user
        
    Returns:
        List[EdgeOut]: List of edges
        
    Raises:
        HTTPException: If message not found
    """
    # Verify message exists
    message = db.get(Message, message_id)
    if not message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Message not found"
        )
    
    try:
        edges = EdgeManager.get_edges(db, message_id, direction)
        
        return [
            EdgeOut(
                id=edge.id,
                from_message_id=edge.from_message_id,
                to_message_id=edge.to_message_id,
                edge_type=edge.edge_type,
                weight=edge.weight,
                created_at=edge.created_at
            )
            for edge in edges
        ]
        
    except ValueError as e:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=str(e)
        )


@router.delete(
    "/messages/{message_id}/edges/{from_message_id}",
    status_code=status.HTTP_204_NO_CONTENT,
    summary="Remove an edge",
    description="Remove an edge between two messages.",
    responses={
        204: {"description": "Edge removed successfully"},
        404: {"description": "Message or edge not found"},
        401: {"description": "Authentication required"},
    }
)
def remove_edge(
    message_id: str,
    from_message_id: str,
    db: Session = Depends(get_db),
    user=Depends(get_current_user)
):
    """
    Remove an edge between two messages.
    
    Args:
        message_id: Target message ID
        from_message_id: Source message ID
        db: Database session
        user: Authenticated user
        
    Raises:
        HTTPException: If edge removal fails
    """
    # Verify target message exists
    target_message = db.get(Message, message_id)
    if not target_message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Target message not found"
        )
    
    # Verify source message exists
    source_message = db.get(Message, from_message_id)
    if not source_message:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Source message not found"
        )
    
    success = EdgeManager.remove_edge(db, from_message_id, message_id)
    
    if not success:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Edge not found"
        )
