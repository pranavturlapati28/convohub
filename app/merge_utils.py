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
    a_anc = build_ancestor_set(db, a_tip)
    cur = db.get(Message, b_tip)
    while cur:
        if cur.id in a_anc:
            return cur.id
        if not cur.parent_message_id:
            break
        cur = db.get(Message, cur.parent_message_id)
    return None  # different roots

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
