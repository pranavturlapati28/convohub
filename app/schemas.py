from pydantic import BaseModel, Field
from typing import Optional, List, Literal, Dict, Any

Role = Literal["user","assistant","system","tool"]

class ThreadCreate(BaseModel):
    title: str

class ThreadOut(BaseModel):
    id: str
    title: str

class BranchCreate(BaseModel):
    name: str
    created_from_branch_id: Optional[str] = None
    created_from_message_id: Optional[str] = None

class MessageIn(BaseModel):
    role: Literal["user"]
    text: str

class MessageOut(BaseModel):
    id: str
    role: Role
    content: Dict[str, Any]
    parent_message_id: Optional[str] = None

class MergeRequest(BaseModel):
    thread_id: str
    source_branch_id: str
    target_branch_id: str
    strategy: Literal["syntactic","semantic","hybrid"] = "hybrid"
