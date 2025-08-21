from datetime import date, datetime, timedelta
from typing import Optional
from sqlalchemy.orm import Session
from sqlalchemy import func
from app.models import UsageRecord, Tenant, User
from app.rate_limiting import quota_manager


class UsageTracker:
    """Tracks usage for quota management"""
    
    @staticmethod
    def increment_usage(
        db: Session, 
        tenant_id: str, 
        usage_type: str, 
        user_id: Optional[str] = None,
        count: int = 1
    ) -> None:
        """
        Increment usage for a tenant and optionally user.
        
        Args:
            db: Database session
            tenant_id: Tenant identifier
            usage_type: Type of usage (e.g., "messages_per_day")
            user_id: Optional user identifier
            count: Amount to increment
        """
        today = date.today()
        
        # Find existing usage record
        usage_record = db.query(UsageRecord).filter(
            UsageRecord.tenant_id == tenant_id,
            UsageRecord.user_id == user_id,
            UsageRecord.usage_type == usage_type,
            UsageRecord.date == today
        ).first()
        
        if usage_record:
            # Update existing record
            usage_record.count += count
            usage_record.updated_at = datetime.utcnow()
        else:
            # Create new record
            usage_record = UsageRecord(
                tenant_id=tenant_id,
                user_id=user_id,
                usage_type=usage_type,
                count=count,
                date=today,
                created_at=datetime.utcnow(),
                updated_at=datetime.utcnow()
            )
            db.add(usage_record)
        
        db.commit()
    
    @staticmethod
    def get_usage(
        db: Session, 
        tenant_id: str, 
        usage_type: str, 
        user_id: Optional[str] = None,
        days: int = 1
    ) -> int:
        """
        Get current usage for a tenant and optionally user.
        
        Args:
            db: Database session
            tenant_id: Tenant identifier
            usage_type: Type of usage
            user_id: Optional user identifier
            days: Number of days to look back
            
        Returns:
            int: Total usage count
        """
        end_date = date.today()
        start_date = end_date - timedelta(days=days-1)
        
        query = db.query(func.sum(UsageRecord.count)).filter(
            UsageRecord.tenant_id == tenant_id,
            UsageRecord.usage_type == usage_type,
            UsageRecord.date >= start_date,
            UsageRecord.date <= end_date
        )
        
        if user_id:
            query = query.filter(UsageRecord.user_id == user_id)
        
        result = query.scalar()
        return result or 0
    
    @staticmethod
    def check_and_increment_usage(
        db: Session, 
        tenant_id: str, 
        usage_type: str, 
        user_id: Optional[str] = None,
        count: int = 1
    ) -> bool:
        """
        Check quota and increment usage if allowed.
        
        Args:
            db: Database session
            tenant_id: Tenant identifier
            usage_type: Type of usage
            user_id: Optional user identifier
            count: Amount to increment
            
        Returns:
            bool: True if quota allows the increment
        """
        current_usage = UsageTracker.get_usage(db, tenant_id, usage_type, user_id)
        quota = quota_manager.get_tenant_quota(db, tenant_id, usage_type)
        
        if current_usage + count <= quota:
            UsageTracker.increment_usage(db, tenant_id, usage_type, user_id, count)
            return True
        
        return False
    
    @staticmethod
    def get_usage_summary(
        db: Session, 
        tenant_id: str, 
        user_id: Optional[str] = None
    ) -> dict:
        """
        Get usage summary for a tenant and optionally user.
        
        Args:
            db: Database session
            tenant_id: Tenant identifier
            user_id: Optional user identifier
            
        Returns:
            dict: Usage summary with current usage and quotas
        """
        usage_types = [
            "messages_per_day",
            "merges_per_day", 
            "threads_per_day",
            "branches_per_day"
        ]
        
        summary = {}
        for usage_type in usage_types:
            current_usage = UsageTracker.get_usage(db, tenant_id, usage_type, user_id)
            quota = quota_manager.get_tenant_quota(db, tenant_id, usage_type)
            
            summary[usage_type] = {
                "current": current_usage,
                "quota": quota,
                "remaining": max(0, quota - current_usage),
                "percentage": (current_usage / quota * 100) if quota > 0 else 0
            }
        
        return summary
    
    @staticmethod
    def cleanup_old_records(db: Session, days_to_keep: int = 30) -> int:
        """
        Clean up old usage records.
        
        Args:
            db: Database session
            days_to_keep: Number of days of records to keep
            
        Returns:
            int: Number of records deleted
        """
        cutoff_date = date.today() - timedelta(days=days_to_keep)
        
        deleted_count = db.query(UsageRecord).filter(
            UsageRecord.date < cutoff_date
        ).delete()
        
        db.commit()
        return deleted_count


class RateLimitHeaders:
    """Helper for setting rate limit headers"""
    
    @staticmethod
    def get_rate_limit_headers(
        db: Session,
        tenant_id: str,
        user_id: str,
        operation: str
    ) -> dict:
        """
        Get rate limit headers for response.
        
        Args:
            db: Database session
            tenant_id: Tenant identifier
            user_id: User identifier
            operation: Operation type
            
        Returns:
            dict: Headers dictionary
        """
        from app.rate_limiting import rate_limiter
        
        headers = {}
        
        # Get current usage for quota-based operations
        if operation in ["send_message", "merge"]:
            usage_type = f"{operation}s_per_day"
            current_usage = UsageTracker.get_usage(db, tenant_id, usage_type, user_id)
            quota = quota_manager.get_tenant_quota(db, tenant_id, usage_type)
            
            headers.update({
                "X-RateLimit-Limit": str(quota),
                "X-RateLimit-Remaining": str(max(0, quota - current_usage)),
                "X-RateLimit-Reset": str(int((date.today() + timedelta(days=1)).strftime("%s")))
            })
        
        # Get token bucket info for rate limiting
        bucket_key = rate_limiter._get_bucket_key(operation, tenant_id, user_id)
        if bucket_key in rate_limiter.buckets:
            bucket = rate_limiter.buckets[bucket_key]
            headers.update({
                "X-RateLimit-Bucket-Tokens": str(int(bucket.tokens)),
                "X-RateLimit-Bucket-Capacity": str(bucket.capacity),
                "X-RateLimit-Bucket-RefillRate": str(bucket.refill_rate)
            })
        
        return headers
