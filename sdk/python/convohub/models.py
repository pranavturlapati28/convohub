"""
ConvoHub Python SDK Models

Data models for the ConvoHub API.
"""

from dataclasses import dataclass
from typing import List, Dict, Any, Optional
from datetime import datetime
from enum import Enum


class DiffMode(str, Enum):
    """Diff modes for comparing branches"""
    SUMMARY = "summary"
    MESSAGES = "messages"
    MEMORY = "memory"


@dataclass
class Thread:
    """Thread model"""
    id: str
    title: str
    description: Optional[str] = None
    owner_id: Optional[str] = None
    tenant_id: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@dataclass
class Branch:
    """Branch model"""
    id: str
    thread_id: str
    name: str
    description: Optional[str] = None
    base_message_id: Optional[str] = None
    created_from_branch_id: Optional[str] = None
    created_from_message_id: Optional[str] = None
    is_active: bool = True
    tenant_id: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@dataclass
class Message:
    """Message model"""
    id: str
    branch_id: str
    role: str
    content: Dict[str, Any]
    parent_message_id: Optional[str] = None
    tenant_id: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@dataclass
class Merge:
    """Merge model"""
    id: str
    thread_id: str
    source_branch_id: str
    target_branch_id: str
    strategy: str
    lca_message_id: Optional[str] = None
    merged_into_message_id: Optional[str] = None
    conflict_resolution: Optional[Dict[str, Any]] = None
    tenant_id: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None


@dataclass
class MemoryDiff:
    """Memory diff model"""
    added: List[Dict[str, Any]]
    removed: List[Dict[str, Any]]
    modified: List[Dict[str, Any]]
    conflicts: List[Dict[str, Any]]


@dataclass
class SummaryDiff:
    """Summary diff model"""
    left_summary: Optional[str]
    right_summary: Optional[str]
    common_content: str
    left_only: str
    right_only: str


@dataclass
class MessageRange:
    """Message range model"""
    start_id: str
    end_id: str
    count: int
    messages: List[Dict[str, Any]]


@dataclass
class DiffResponse:
    """Diff response model"""
    lca: Optional[str]
    src_delta: List[str]
    tgt_delta: List[str]
    merged_order: List[str]
    mode: DiffMode
    memory_diff: Optional[MemoryDiff] = None
    summary_diff: Optional[SummaryDiff] = None
    message_ranges: Optional[List[MessageRange]] = None
    left_branch_id: str = ""
    right_branch_id: str = ""
    diff_timestamp: Optional[datetime] = None
