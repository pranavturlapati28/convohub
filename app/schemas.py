from pydantic import BaseModel, Field, validator
from typing import Optional, List, Literal, Dict, Any
from datetime import datetime
import uuid

Role = Literal["user", "assistant", "system", "tool"]

# Base models with common fields
class IdempotencyKey(BaseModel):
    idempotency_key: str = Field(
        ..., 
        description="Unique key to ensure idempotent operations",
        example="msg_1234567890_abc123"
    )

# Thread schemas
class ThreadCreate(BaseModel):
    title: str = Field(
        ..., 
        min_length=1, 
        max_length=200,
        description="Title of the thread",
        example="My first conversation thread"
    )

    class Config:
        schema_extra = {
            "example": {
                "title": "My first conversation thread"
            }
        }

class ThreadOut(BaseModel):
    id: str = Field(..., description="Unique thread identifier")
    title: str = Field(..., description="Thread title")
    created_at: datetime = Field(..., description="Thread creation timestamp")

    class Config:
        schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "title": "My first conversation thread",
                "created_at": "2024-01-15T10:30:00Z"
            }
        }

# Branch schemas
class BranchCreate(BaseModel):
    name: str = Field(
        ..., 
        min_length=1, 
        max_length=100,
        description="Name of the branch",
        example="main"
    )
    created_from_branch_id: Optional[str] = Field(
        None, 
        description="ID of the branch to fork from",
        example="550e8400-e29b-41d4-a716-446655440001"
    )
    created_from_message_id: Optional[str] = Field(
        None, 
        description="ID of the message to fork from",
        example="550e8400-e29b-41d4-a716-446655440002"
    )

    @validator('created_from_branch_id', 'created_from_message_id')
    def validate_uuid(cls, v):
        if v is not None:
            try:
                uuid.UUID(v)
            except ValueError:
                raise ValueError('Must be a valid UUID')
        return v

    class Config:
        schema_extra = {
            "example": {
                "name": "feature-branch",
                "created_from_branch_id": "550e8400-e29b-41d4-a716-446655440001"
            }
        }

class BranchOut(BaseModel):
    id: str = Field(..., description="Unique branch identifier")
    name: str = Field(..., description="Branch name")
    thread_id: str = Field(..., description="Parent thread ID")
    created_from_branch_id: Optional[str] = Field(None, description="Source branch ID if forked")
    created_from_message_id: Optional[str] = Field(None, description="Source message ID if forked")
    created_at: datetime = Field(..., description="Branch creation timestamp")

    class Config:
        schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440001",
                "name": "feature-branch",
                "thread_id": "550e8400-e29b-41d4-a716-446655440000",
                "created_from_branch_id": "550e8400-e29b-41d4-a716-446655440003",
                "created_at": "2024-01-15T10:30:00Z"
            }
        }

# Message schemas
class MessageIn(BaseModel):
    role: Literal["user"] = Field(..., description="Message role")
    text: str = Field(
        ..., 
        min_length=1, 
        max_length=10000,
        description="Message content",
        example="Hello, how are you today?"
    )

    class Config:
        schema_extra = {
            "example": {
                "role": "user",
                "text": "Hello, how are you today?"
            }
        }

class MessageOut(BaseModel):
    id: str = Field(..., description="Unique message identifier")
    role: Role = Field(..., description="Message role")
    content: Dict[str, Any] = Field(..., description="Message content")
    parent_message_id: Optional[str] = Field(None, description="Parent message ID")
    created_at: datetime = Field(..., description="Message creation timestamp")

    class Config:
        schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440002",
                "role": "user",
                "content": {"text": "Hello, how are you today?"},
                "parent_message_id": "550e8400-e29b-41d4-a716-446655440001",
                "created_at": "2024-01-15T10:30:00Z"
            }
        }

class MessageResponse(BaseModel):
    user_message_id: str = Field(..., description="ID of the created user message")
    assistant_message_id: str = Field(..., description="ID of the generated assistant message")

    class Config:
        schema_extra = {
            "example": {
                "user_message_id": "550e8400-e29b-41d4-a716-446655440002",
                "assistant_message_id": "550e8400-e29b-41d4-a716-446655440003"
            }
        }

# Pagination schemas
class PaginationParams(BaseModel):
    cursor: Optional[str] = Field(
        None, 
        description="Cursor for pagination (message ID)",
        example="550e8400-e29b-41d4-a716-446655440002"
    )
    limit: int = Field(
        default=50, 
        ge=1, 
        le=100,
        description="Maximum number of messages to return",
        example=50
    )

class PaginatedMessages(BaseModel):
    messages: List[MessageOut] = Field(..., description="List of messages")
    next_cursor: Optional[str] = Field(None, description="Cursor for next page")
    has_more: bool = Field(..., description="Whether there are more messages")

    class Config:
        schema_extra = {
            "example": {
                "messages": [
                    {
                        "id": "550e8400-e29b-41d4-a716-446655440002",
                        "role": "user",
                        "content": {"text": "Hello"},
                        "parent_message_id": None,
                        "created_at": "2024-01-15T10:30:00Z"
                    }
                ],
                "next_cursor": "550e8400-e29b-41d4-a716-446655440003",
                "has_more": True
            }
        }

# Merge schemas
class MergeRequest(BaseModel):
    thread_id: str = Field(..., description="Thread ID")
    source_branch_id: str = Field(..., description="Source branch ID")
    target_branch_id: str = Field(..., description="Target branch ID")
    strategy: Literal["syntactic", "semantic", "hybrid"] = Field(
        default="hybrid", 
        description="Merge strategy to use"
    )
    idempotency_key: str = Field(
        ..., 
        description="Unique key to ensure idempotent merge operations",
        example="merge_1234567890_abc123"
    )

    @validator('thread_id', 'source_branch_id', 'target_branch_id')
    def validate_uuid(cls, v):
        try:
            uuid.UUID(v)
        except ValueError:
            raise ValueError('Must be a valid UUID')
        return v

    class Config:
        schema_extra = {
            "example": {
                "thread_id": "550e8400-e29b-41d4-a716-446655440000",
                "source_branch_id": "550e8400-e29b-41d4-a716-446655440001",
                "target_branch_id": "550e8400-e29b-41d4-a716-446655440002",
                "strategy": "hybrid",
                "idempotency_key": "merge_1234567890_abc123"
            }
        }

class MergeResponse(BaseModel):
    merge_id: str = Field(..., description="Unique merge identifier")
    merged_into_message_id: str = Field(..., description="ID of the merge commit message")

    class Config:
        schema_extra = {
            "example": {
                "merge_id": "550e8400-e29b-41d4-a716-446655440004",
                "merged_into_message_id": "550e8400-e29b-41d4-a716-446655440005"
            }
        }

# Diff schemas
class DiffResponse(BaseModel):
    lca: Optional[str] = Field(None, description="Lowest Common Ancestor message ID")
    src_delta: List[str] = Field(..., description="Messages unique to source branch")
    tgt_delta: List[str] = Field(..., description="Messages unique to target branch")
    merged_order: List[str] = Field(..., description="Chronologically merged message IDs")

    class Config:
        schema_extra = {
            "example": {
                "lca": "550e8400-e29b-41d4-a716-446655440002",
                "src_delta": ["550e8400-e29b-41d4-a716-446655440003"],
                "tgt_delta": ["550e8400-e29b-41d4-a716-446655440004"],
                "merged_order": [
                    "550e8400-e29b-41d4-a716-446655440002",
                    "550e8400-e29b-41d4-a716-446655440003",
                    "550e8400-e29b-41d4-a716-446655440004"
                ]
            }
        }

# Edge schemas
class EdgeCreate(BaseModel):
    from_message_id: str = Field(..., description="Source message ID")
    edge_type: Literal["parent", "merge_parent", "reference"] = Field(
        default="parent", 
        description="Type of edge relationship"
    )
    weight: Optional[str] = Field(None, description="Optional weight for the edge")

    @validator('from_message_id')
    def validate_uuid(cls, v):
        try:
            uuid.UUID(v)
        except ValueError:
            raise ValueError('Must be a valid UUID')
        return v

    class Config:
        schema_extra = {
            "example": {
                "from_message_id": "550e8400-e29b-41d4-a716-446655440001",
                "edge_type": "merge_parent",
                "weight": "0.8"
            }
        }

class EdgeOut(BaseModel):
    id: str = Field(..., description="Unique edge identifier")
    from_message_id: str = Field(..., description="Source message ID")
    to_message_id: str = Field(..., description="Target message ID")
    edge_type: str = Field(..., description="Type of edge relationship")
    weight: Optional[str] = Field(None, description="Edge weight")
    created_at: datetime = Field(..., description="Edge creation timestamp")

    class Config:
        schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440006",
                "from_message_id": "550e8400-e29b-41d4-a716-446655440001",
                "to_message_id": "550e8400-e29b-41d4-a716-446655440002",
                "edge_type": "merge_parent",
                "weight": "0.8",
                "created_at": "2024-01-15T10:30:00Z"
            }
        }

# Error schemas
class ErrorResponse(BaseModel):
    error: str = Field(..., description="Error message")
    detail: Optional[str] = Field(None, description="Additional error details")
    code: Optional[str] = Field(None, description="Error code")

    class Config:
        schema_extra = {
            "example": {
                "error": "Branch not found",
                "detail": "The specified branch ID does not exist",
                "code": "BRANCH_NOT_FOUND"
            }
        }
