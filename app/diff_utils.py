"""
Enhanced diff utilities for comparing branches with different modes
"""
from typing import List, Dict, Any, Optional, Tuple
from datetime import datetime
from sqlalchemy.orm import Session
from sqlalchemy import func, desc
from app.models import Branch, Message, Memory, Summary
from app.schemas import MemoryDiff, SummaryDiff, MessageRange, DiffMode


def compute_memory_diff(
    db: Session, 
    left_branch_id: str, 
    right_branch_id: str,
    base_branch_id: Optional[str] = None
) -> MemoryDiff:
    """
    Compute three-way diff for memories between branches.
    
    Args:
        db: Database session
        left_branch_id: Left branch ID
        right_branch_id: Right branch ID  
        base_branch_id: Base branch ID for three-way diff (optional)
        
    Returns:
        MemoryDiff: Differences in memories between branches
    """
    # Get memories for each branch
    left_memories = db.query(Memory).filter(
        Memory.thread_id == db.query(Branch.thread_id).filter(Branch.id == left_branch_id).scalar()
    ).all()
    
    right_memories = db.query(Memory).filter(
        Memory.thread_id == db.query(Branch.thread_id).filter(Branch.id == right_branch_id).scalar()
    ).all()
    
    # Convert to dictionaries for easier comparison
    left_memory_map = {m.key: m for m in left_memories}
    right_memory_map = {m.key: m for m in right_memories}
    
    # Get base memories if provided
    base_memory_map = {}
    if base_branch_id:
        base_memories = db.query(Memory).filter(
            Memory.thread_id == db.query(Branch.thread_id).filter(Branch.id == base_branch_id).scalar()
        ).all()
        base_memory_map = {m.key: m for m in base_memories}
    
    added = []
    removed = []
    modified = []
    conflicts = []
    
    # Find added memories (in right but not in left)
    for key, memory in right_memory_map.items():
        if key not in left_memory_map:
            # Check if it's truly new (not in base) or if it was removed from left
            if base_branch_id and key in base_memory_map:
                # Was in base, removed from left, still in right
                removed.append({
                    "key": key,
                    "value": memory.value,
                    "memory_type": memory.memory_type,
                    "confidence": memory.confidence,
                    "source": memory.source,
                    "created_at": memory.created_at.isoformat(),
                    "diff_type": "removed_from_left"
                })
            else:
                # Truly new memory
                added.append({
                    "key": key,
                    "value": memory.value,
                    "memory_type": memory.memory_type,
                    "confidence": memory.confidence,
                    "source": memory.source,
                    "created_at": memory.created_at.isoformat(),
                    "diff_type": "added"
                })
    
    # Find removed memories (in left but not in right)
    for key, memory in left_memory_map.items():
        if key not in right_memory_map:
            # Check if it was in base
            if base_branch_id and key in base_memory_map:
                # Was in base, removed from right, still in left
                removed.append({
                    "key": key,
                    "value": memory.value,
                    "memory_type": memory.memory_type,
                    "confidence": memory.confidence,
                    "source": memory.source,
                    "created_at": memory.created_at.isoformat(),
                    "diff_type": "removed_from_right"
                })
            else:
                # Was added to left, removed from right
                removed.append({
                    "key": key,
                    "value": memory.value,
                    "memory_type": memory.memory_type,
                    "confidence": memory.confidence,
                    "source": memory.source,
                    "created_at": memory.created_at.isoformat(),
                    "diff_type": "removed"
                })
    
    # Find modified memories (in both but different)
    for key in set(left_memory_map.keys()) & set(right_memory_map.keys()):
        left_memory = left_memory_map[key]
        right_memory = right_memory_map[key]
        
        if (left_memory.value != right_memory.value or 
            left_memory.confidence != right_memory.confidence or
            left_memory.source != right_memory.source):
            
            # Check if this is a conflict (both modified from base)
            is_conflict = False
            if base_branch_id and key in base_memory_map:
                base_memory = base_memory_map[key]
                left_changed = (left_memory.value != base_memory.value or 
                              left_memory.confidence != base_memory.confidence)
                right_changed = (right_memory.value != base_memory.value or 
                               right_memory.confidence != base_memory.confidence)
                is_conflict = left_changed and right_changed
            
            memory_diff = {
                "key": key,
                "left_value": left_memory.value,
                "right_value": right_memory.value,
                "memory_type": left_memory.memory_type,
                "left_confidence": left_memory.confidence,
                "right_confidence": right_memory.confidence,
                "left_source": left_memory.source,
                "right_source": right_memory.source,
                "left_updated": left_memory.updated_at.isoformat(),
                "right_updated": right_memory.updated_at.isoformat(),
                "is_conflict": is_conflict
            }
            
            if is_conflict:
                conflicts.append(memory_diff)
            else:
                modified.append(memory_diff)
    
    return MemoryDiff(
        added=added,
        removed=removed,
        modified=modified,
        conflicts=conflicts
    )


def compute_summary_diff(
    db: Session,
    left_branch_id: str,
    right_branch_id: str
) -> SummaryDiff:
    """
    Compute diff for summaries between branches.
    
    Args:
        db: Database session
        left_branch_id: Left branch ID
        right_branch_id: Right branch ID
        
    Returns:
        SummaryDiff: Differences in summaries between branches
    """
    # Get current summaries for each branch
    left_summary = db.query(Summary).filter(
        Summary.thread_id == db.query(Branch.thread_id).filter(Branch.id == left_branch_id).scalar(),
        Summary.is_current == True
    ).first()
    
    right_summary = db.query(Summary).filter(
        Summary.thread_id == db.query(Branch.thread_id).filter(Branch.id == right_branch_id).scalar(),
        Summary.is_current == True
    ).first()
    
    left_content = left_summary.content if left_summary else ""
    right_content = right_summary.content if right_summary else ""
    
    # Simple text-based diff (in a real implementation, you might use difflib)
    # For now, we'll do a basic comparison
    left_words = set(left_content.lower().split())
    right_words = set(right_content.lower().split())
    
    common_words = left_words & right_words
    left_only_words = left_words - right_words
    right_only_words = right_words - left_words
    
    # Reconstruct text based on word differences
    common_content = " ".join(sorted(common_words))
    left_only = " ".join(sorted(left_only_words))
    right_only = " ".join(sorted(right_only_words))
    
    return SummaryDiff(
        left_summary=left_content,
        right_summary=right_content,
        common_content=common_content,
        left_only=left_only,
        right_only=right_only
    )


def compute_message_ranges(
    db: Session,
    left_branch_id: str,
    right_branch_id: str,
    lca_id: Optional[str] = None
) -> List[MessageRange]:
    """
    Compute message ranges for diff by message ID ranges.
    
    Args:
        db: Database session
        left_branch_id: Left branch ID
        right_branch_id: Right branch ID
        lca_id: Lowest Common Ancestor message ID
        
    Returns:
        List[MessageRange]: Message ranges for comparison
    """
    ranges = []
    
    # Get all messages for both branches
    left_messages = db.query(Message).filter(
        Message.branch_id == left_branch_id
    ).order_by(Message.created_at).all()
    
    right_messages = db.query(Message).filter(
        Message.branch_id == right_branch_id
    ).order_by(Message.created_at).all()
    
    # Create ranges based on LCA
    if lca_id:
        # Find LCA in both branches
        left_lca_idx = next((i for i, m in enumerate(left_messages) if m.id == lca_id), -1)
        right_lca_idx = next((i for i, m in enumerate(right_messages) if m.id == lca_id), -1)
        
        if left_lca_idx >= 0 and right_lca_idx >= 0:
            # Common range (up to LCA)
            common_messages = left_messages[:left_lca_idx + 1]
            if common_messages:
                ranges.append(MessageRange(
                    start_id=common_messages[0].id,
                    end_id=common_messages[-1].id,
                    count=len(common_messages),
                    messages=[{
                        "id": m.id,
                        "role": m.role,
                        "content": m.content,
                        "created_at": m.created_at.isoformat()
                    } for m in common_messages]
                ))
            
            # Left-only range (after LCA)
            left_only = left_messages[left_lca_idx + 1:]
            if left_only:
                ranges.append(MessageRange(
                    start_id=left_only[0].id,
                    end_id=left_only[-1].id,
                    count=len(left_only),
                    messages=[{
                        "id": m.id,
                        "role": m.role,
                        "content": m.content,
                        "created_at": m.created_at.isoformat()
                    } for m in left_only]
                ))
            
            # Right-only range (after LCA)
            right_only = right_messages[right_lca_idx + 1:]
            if right_only:
                ranges.append(MessageRange(
                    start_id=right_only[0].id,
                    end_id=right_only[-1].id,
                    count=len(right_only),
                    messages=[{
                        "id": m.id,
                        "role": m.role,
                        "content": m.content,
                        "created_at": m.created_at.isoformat()
                    } for m in right_only]
                ))
        else:
            # LCA not found in one or both branches, treat as completely different
            if left_messages:
                ranges.append(MessageRange(
                    start_id=left_messages[0].id,
                    end_id=left_messages[-1].id,
                    count=len(left_messages),
                    messages=[{
                        "id": m.id,
                        "role": m.role,
                        "content": m.content,
                        "created_at": m.created_at.isoformat()
                    } for m in left_messages]
                ))
            
            if right_messages:
                ranges.append(MessageRange(
                    start_id=right_messages[0].id,
                    end_id=right_messages[-1].id,
                    count=len(right_messages),
                    messages=[{
                        "id": m.id,
                        "role": m.role,
                        "content": m.content,
                        "created_at": m.created_at.isoformat()
                    } for m in right_messages]
                ))
    else:
        # No LCA found, treat as completely different
        if left_messages:
            ranges.append(MessageRange(
                start_id=left_messages[0].id,
                end_id=left_messages[-1].id,
                count=len(left_messages),
                messages=[{
                    "id": m.id,
                    "role": m.role,
                    "content": m.content,
                    "created_at": m.created_at.isoformat()
                } for m in left_messages]
            ))
        
        if right_messages:
            ranges.append(MessageRange(
                start_id=right_messages[0].id,
                end_id=right_messages[-1].id,
                count=len(right_messages),
                messages=[{
                    "id": m.id,
                    "role": m.role,
                    "content": m.content,
                    "created_at": m.created_at.isoformat()
                } for m in right_messages]
            ))
    
    return ranges


def find_base_branch_for_three_way_diff(
    db: Session,
    left_branch_id: str,
    right_branch_id: str
) -> Optional[str]:
    """
    Find the base branch for three-way diff by looking for common ancestor.
    
    Args:
        db: Database session
        left_branch_id: Left branch ID
        right_branch_id: Right branch ID
        
    Returns:
        Optional[str]: Base branch ID if found
    """
    # Get the branches
    left_branch = db.get(Branch, left_branch_id)
    right_branch = db.get(Branch, right_branch_id)
    
    if not left_branch or not right_branch:
        return None
    
    # Look for a branch that both left and right were created from
    # This is a simplified approach - in a real implementation you might
    # want to traverse the branch creation history
    
    # Check if they share a common base message
    left_base = left_branch.base_message_id
    right_base = right_branch.base_message_id
    
    if left_base == right_base and left_base:
        # They share the same base message, find the branch that contains it
        base_branch = db.query(Branch).filter(
            Branch.id != left_branch_id,
            Branch.id != right_branch_id,
            Branch.thread_id == left_branch.thread_id
        ).filter(
            db.query(Message).filter(
                Message.id == left_base,
                Message.branch_id == Branch.id
            ).exists()
        ).first()
        
        if base_branch:
            return base_branch.id
    
    return None
