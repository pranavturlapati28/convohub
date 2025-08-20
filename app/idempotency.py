from typing import Optional, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy.exc import IntegrityError
from fastapi import HTTPException
from datetime import datetime, timedelta
import json
from uuid import uuid4

class IdempotencyKey:
    def __init__(self, db: Session, key: str, operation: str, ttl_hours: int = 24):
        self.db = db
        self.key = key
        self.operation = operation
        self.ttl_hours = ttl_hours
        self._result = None
        self._processed = False

    def check_and_lock(self) -> Optional[Dict[str, Any]]:
        """
        Check if idempotency key exists and return cached result if found.
        If not found, create a placeholder to prevent race conditions.
        """
        from app.models import IdempotencyRecord
        
        # Check for existing record
        existing = self.db.query(IdempotencyRecord).filter(
            IdempotencyRecord.key == self.key,
            IdempotencyRecord.operation == self.operation
        ).first()
        
        if existing:
            # Check if expired
            if existing.created_at < datetime.utcnow() - timedelta(hours=self.ttl_hours):
                # Delete expired record
                self.db.delete(existing)
                self.db.commit()
            else:
                # Return cached result
                if existing.result:
                    return json.loads(existing.result)
                else:
                    # Still processing or failed
                    raise HTTPException(409, f"Operation with key '{self.key}' is already in progress")
        
        # Create placeholder record
        try:
            record = IdempotencyRecord(
                id=str(uuid4()),
                key=self.key,
                operation=self.operation,
                result=None,
                created_at=datetime.utcnow()
            )
            self.db.add(record)
            self.db.commit()
            self._processed = True
            return None
        except IntegrityError:
            # Race condition - another request got there first
            self.db.rollback()
            raise HTTPException(409, f"Operation with key '{self.key}' is already in progress")

    def store_result(self, result: Dict[str, Any]) -> None:
        """Store the operation result for future idempotency checks."""
        if not self._processed:
            raise ValueError("Must call check_and_lock() before store_result()")
        
        from app.models import IdempotencyRecord
        
        record = self.db.query(IdempotencyRecord).filter(
            IdempotencyRecord.key == self.key,
            IdempotencyRecord.operation == self.operation
        ).first()
        
        if record:
            record.result = json.dumps(result)
            record.updated_at = datetime.utcnow()
            self.db.commit()
            self._result = result

    def get_result(self) -> Optional[Dict[str, Any]]:
        """Get the stored result."""
        return self._result

def validate_idempotency_key(key: str) -> None:
    """Validate idempotency key format."""
    if not key or len(key) < 10 or len(key) > 100:
        raise HTTPException(400, "Idempotency key must be between 10 and 100 characters")
    
    # Check for reasonable format (alphanumeric, hyphens, underscores)
    import re
    if not re.match(r'^[a-zA-Z0-9_-]+$', key):
        raise HTTPException(400, "Idempotency key can only contain alphanumeric characters, hyphens, and underscores")
