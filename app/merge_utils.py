from typing import Optional, List, Dict
from sqlalchemy.orm import Session
from app.models import Message

def build_ancestor_set(db: Session, tip_id: str) -> set[str]:
    seen = set()
    cur = db.get(Message, tip_id)
    while cur:
        seen.add(cur.id)
        if not cur.parent_message_id:
            break
        cur = db.get(Message, cur.parent_message_id)
    return seen

def find_lca(db: Session, a_tip: str, b_tip: str) -> Optional[str]:
    # First try exact ID matching
    a_anc = build_ancestor_set(db, a_tip)
    cur = db.get(Message, b_tip)
    while cur:
        if cur.id in a_anc:
            return cur.id
        if not cur.parent_message_id:
            break
        cur = db.get(Message, cur.parent_message_id)
    
    # If no exact match, try content-based matching
    a_tip_msg = db.get(Message, a_tip)
    b_tip_msg = db.get(Message, b_tip)
    
    if not a_tip_msg or not b_tip_msg:
        return None
    
    # Build content-based ancestor sets
    a_content_anc = build_content_ancestor_set(db, a_tip_msg)
    cur = b_tip_msg
    while cur:
        if cur.id in a_content_anc:
            return cur.id
        if not cur.parent_message_id:
            break
        cur = db.get(Message, cur.parent_message_id)
    
    return None  # different roots

def build_content_ancestor_set(db: Session, tip_msg) -> set[str]:
    """Build set of message IDs that share content with ancestors of tip_msg"""
    seen = set()
    cur = tip_msg
    while cur:
        seen.add(cur.id)
        # Also find messages with same content in other branches
        # Use JSON string comparison to avoid PostgreSQL JSON operator issues
        similar_msgs = db.query(Message).filter(
            Message.role == cur.role
        ).all()
        for msg in similar_msgs:
            # Compare content as JSON strings
            if (msg.content.get('text') == cur.content.get('text') and 
                msg.role == cur.role):
                seen.add(msg.id)
        
        if not cur.parent_message_id:
            break
        cur = db.get(Message, cur.parent_message_id)
    return seen

def path_after(db: Session, from_id: str, tip_id: str) -> List[Message]:
    path: List[Message] = []
    cur = db.get(Message, tip_id)
    while cur and cur.id != from_id:
        path.append(cur)
        cur = db.get(Message, cur.parent_message_id) if cur.parent_message_id else None
    path.reverse()
    return path

def interleave_by_created_at(a_path: List[Message], b_path: List[Message]) -> List[Message]:
    merged: List[Message] = []
    i = j = 0
    while i < len(a_path) or j < len(b_path):
        if j >= len(b_path) or (i < len(a_path) and a_path[i].created_at <= b_path[j].created_at):
            merged.append(a_path[i]); i += 1
        else:
            merged.append(b_path[j]); j += 1
    return merged
