from pydantic import BaseModel, Field, validator
from typing import Optional, List, Literal, Dict, Any
from datetime import datetime
import uuid
from enum import Enum

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
    strategy: Literal["syntactic", "semantic", "hybrid", "append-last", "resolver"] = Field(
        default="hybrid", 
        description="Merge strategy to use (syntactic/semantic/hybrid for message merging, append-last/resolver for summary/memory merging)"
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
class DiffMode(str, Enum):
    """Diff modes for comparing branches"""
    SUMMARY = "summary"
    MESSAGES = "messages" 
    MEMORY = "memory"

class MemoryDiff(BaseModel):
    """Represents differences in memory between branches"""
    added: List[Dict[str, Any]] = Field(..., description="Memories added in right branch")
    removed: List[Dict[str, Any]] = Field(..., description="Memories removed in right branch")
    modified: List[Dict[str, Any]] = Field(..., description="Memories modified between branches")
    conflicts: List[Dict[str, Any]] = Field(..., description="Conflicting memories that need resolution")

    class Config:
        schema_extra = {
            "example": {
                "added": [
                    {
                        "key": "user_preference_20250821_021401",
                        "value": "Prefers JavaScript for web development",
                        "memory_type": "preference",
                        "confidence": "high"
                    }
                ],
                "removed": [],
                "modified": [],
                "conflicts": []
            }
        }

class SummaryDiff(BaseModel):
    """Represents differences in summaries between branches"""
    left_summary: Optional[str] = Field(None, description="Summary from left branch")
    right_summary: Optional[str] = Field(None, description="Summary from right branch")
    common_content: str = Field(..., description="Content common to both summaries")
    left_only: str = Field(..., description="Content only in left summary")
    right_only: str = Field(..., description="Content only in right summary")

    class Config:
        schema_extra = {
            "example": {
                "left_summary": "Discussion about Python advantages...",
                "right_summary": "Discussion about JavaScript benefits...",
                "common_content": "Both branches discuss programming languages",
                "left_only": "Python advantages: readability, versatility",
                "right_only": "JavaScript benefits: browser compatibility, React"
            }
        }

class MessageRange(BaseModel):
    """Represents a range of messages by ID"""
    start_id: str = Field(..., description="Starting message ID")
    end_id: str = Field(..., description="Ending message ID")
    count: int = Field(..., description="Number of messages in range")
    messages: List[Dict[str, Any]] = Field(..., description="Messages in this range")

    class Config:
        schema_extra = {
            "example": {
                "start_id": "550e8400-e29b-41d4-a716-446655440001",
                "end_id": "550e8400-e29b-41d4-a716-446655440005",
                "count": 5,
                "messages": [
                    {"id": "550e8400-e29b-41d4-a716-446655440001", "role": "user", "content": "Hello"},
                    {"id": "550e8400-e29b-41d4-a716-446655440002", "role": "assistant", "content": "Hi there!"}
                ]
            }
        }

class DiffResponse(BaseModel):
    lca: Optional[str] = Field(None, description="Lowest Common Ancestor message ID")
    src_delta: List[str] = Field(..., description="Messages unique to source branch")
    tgt_delta: List[str] = Field(..., description="Messages unique to target branch")
    merged_order: List[str] = Field(..., description="Chronologically merged message IDs")
    
    # Enhanced diff fields
    mode: DiffMode = Field(..., description="Diff mode used")
    memory_diff: Optional[MemoryDiff] = Field(None, description="Memory differences (for memory mode)")
    summary_diff: Optional[SummaryDiff] = Field(None, description="Summary differences (for summary mode)")
    message_ranges: Optional[List[MessageRange]] = Field(None, description="Message ranges (for messages mode)")
    
    # Metadata
    left_branch_id: str = Field(..., description="Left branch ID")
    right_branch_id: str = Field(..., description="Right branch ID")
    diff_timestamp: datetime = Field(..., description="When this diff was computed")

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
                ],
                "mode": "memory",
                "memory_diff": {
                    "added": [{"key": "new_memory", "value": "New information"}],
                    "removed": [],
                    "modified": [],
                    "conflicts": []
                },
                "left_branch_id": "550e8400-e29b-41d4-a716-446655440001",
                "right_branch_id": "550e8400-e29b-41d4-a716-446655440002",
                "diff_timestamp": "2024-01-15T10:30:00Z"
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

# Auth schemas
class LoginRequest(BaseModel):
    email: str = Field(..., description="User email address")
    tenant_domain: str = Field(..., description="Tenant domain")
    password: str = Field(..., description="User password")

    class Config:
        schema_extra = {
            "example": {
                "email": "admin@example.com",
                "tenant_domain": "example.local",
                "password": "securepassword123"
            }
        }

class LoginResponse(BaseModel):
    access_token: str = Field(..., description="JWT access token")
    token_type: str = Field(..., description="Token type (bearer)")
    user: "UserOut" = Field(..., description="User information")

    class Config:
        schema_extra = {
            "example": {
                "access_token": "eyJhbGciOiJIUzI1NiIsInR5cCI6IkpXVCJ9...",
                "token_type": "bearer",
                "user": {
                    "id": "550e8400-e29b-41d4-a716-446655440000",
                    "email": "admin@example.com",
                    "name": "Admin User",
                    "role": "admin",
                    "tenant_id": "550e8400-e29b-41d4-a716-446655440001",
                    "permissions": ["*"],
                    "created_at": "2024-01-15T10:30:00Z"
                }
            }
        }

class TenantCreate(BaseModel):
    name: str = Field(..., description="Tenant name")
    domain: Optional[str] = Field(None, description="Tenant domain")
    settings: Optional[Dict[str, Any]] = Field(None, description="Tenant-specific settings")

    class Config:
        schema_extra = {
            "example": {
                "name": "Acme Corporation",
                "domain": "acme.local",
                "settings": {"theme": "dark", "timezone": "UTC"}
            }
        }

class TenantOut(BaseModel):
    id: str = Field(..., description="Unique tenant identifier")
    name: str = Field(..., description="Tenant name")
    domain: Optional[str] = Field(None, description="Tenant domain")
    settings: Optional[Dict[str, Any]] = Field(None, description="Tenant-specific settings")
    is_active: bool = Field(..., description="Whether tenant is active")
    created_at: datetime = Field(..., description="Tenant creation timestamp")
    updated_at: datetime = Field(..., description="Tenant last update timestamp")

    class Config:
        schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440001",
                "name": "Acme Corporation",
                "domain": "acme.local",
                "settings": {"theme": "dark", "timezone": "UTC"},
                "is_active": True,
                "created_at": "2024-01-15T10:30:00Z",
                "updated_at": "2024-01-15T10:30:00Z"
            }
        }

class UserCreate(BaseModel):
    email: str = Field(..., description="User email address")
    name: str = Field(..., description="User full name")
    role: Literal["admin", "user", "guest"] = Field(default="user", description="User role")
    permissions: Optional[List[str]] = Field(None, description="User permissions")

    @validator('email')
    def validate_email(cls, v):
        if '@' not in v:
            raise ValueError('Must be a valid email address')
        return v

    class Config:
        schema_extra = {
            "example": {
                "email": "john.doe@example.com",
                "name": "John Doe",
                "role": "user",
                "permissions": ["read", "write"]
            }
        }

class UserOut(BaseModel):
    id: str = Field(..., description="Unique user identifier")
    email: str = Field(..., description="User email address")
    name: str = Field(..., description="User full name")
    role: str = Field(..., description="User role")
    tenant_id: str = Field(..., description="Tenant identifier")
    permissions: List[str] = Field(..., description="User permissions")
    created_at: datetime = Field(..., description="User creation timestamp")

    class Config:
        schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440000",
                "email": "john.doe@example.com",
                "name": "John Doe",
                "role": "user",
                "tenant_id": "550e8400-e29b-41d4-a716-446655440001",
                "permissions": ["read", "write"],
                "created_at": "2024-01-15T10:30:00Z"
            }
        }

class ThreadCollaboratorCreate(BaseModel):
    user_id: str = Field(..., description="User identifier")
    role: Literal["owner", "editor", "viewer"] = Field(default="viewer", description="Collaborator role")
    permissions: Optional[List[str]] = Field(None, description="Thread-specific permissions")

    @validator('user_id')
    def validate_uuid(cls, v):
        try:
            uuid.UUID(v)
        except ValueError:
            raise ValueError('Must be a valid UUID')
        return v

    class Config:
        schema_extra = {
            "example": {
                "user_id": "550e8400-e29b-41d4-a716-446655440000",
                "role": "editor",
                "permissions": ["read", "write", "merge"]
            }
        }

class ThreadCollaboratorOut(BaseModel):
    id: str = Field(..., description="Unique collaborator identifier")
    thread_id: str = Field(..., description="Thread identifier")
    user_id: str = Field(..., description="User identifier")
    tenant_id: str = Field(..., description="Tenant identifier")
    role: str = Field(..., description="Collaborator role")
    permissions: List[str] = Field(..., description="Thread-specific permissions")
    is_active: bool = Field(..., description="Whether collaborator is active")
    created_at: datetime = Field(..., description="Collaboration creation timestamp")

    class Config:
        schema_extra = {
            "example": {
                "id": "550e8400-e29b-41d4-a716-446655440006",
                "thread_id": "550e8400-e29b-41d4-a716-446655440002",
                "user_id": "550e8400-e29b-41d4-a716-446655440000",
                "tenant_id": "550e8400-e29b-41d4-a716-446655440001",
                "role": "editor",
                "permissions": ["read", "write", "merge"],
                "is_active": True,
                "created_at": "2024-01-15T10:30:00Z"
            }
        }

# Usage schemas
class UsageSummary(BaseModel):
    tenant_id: str = Field(..., description="Tenant identifier")
    user_id: Optional[str] = Field(None, description="User identifier (if user-specific)")
    usage: Dict[str, Dict[str, Any]] = Field(..., description="Usage information by type")

    class Config:
        schema_extra = {
            "example": {
                "tenant_id": "550e8400-e29b-41d4-a716-446655440001",
                "user_id": "550e8400-e29b-41d4-a716-446655440000",
                "usage": {
                    "messages_per_day": {
                        "current": 150,
                        "quota": 10000,
                        "remaining": 9850,
                        "percentage": 1.5
                    },
                    "merges_per_day": {
                        "current": 5,
                        "quota": 1000,
                        "remaining": 995,
                        "percentage": 0.5
                    }
                }
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
