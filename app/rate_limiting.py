import time
import asyncio
from typing import Dict, Optional, Tuple
from dataclasses import dataclass, field
from datetime import datetime, timedelta
from sqlalchemy.orm import Session
from fastapi import HTTPException, status
from app.models import Tenant, User
from app.auth import TenantContext

@dataclass
class TokenBucket:
    """Token bucket for rate limiting"""
    capacity: int
    tokens: int
    refill_rate: float  # tokens per second
    last_refill: float = field(default_factory=time.time)
    
    def consume(self, tokens: int = 1) -> bool:
        """
        Try to consume tokens from the bucket.
        
        Args:
            tokens: Number of tokens to consume
            
        Returns:
            bool: True if tokens were consumed, False if bucket is empty
        """
        self._refill()
        
        if self.tokens >= tokens:
            self.tokens -= tokens
            return True
        return False
    
    def _refill(self):
        """Refill the bucket based on time elapsed."""
        now = time.time()
        time_passed = now - self.last_refill
        tokens_to_add = time_passed * self.refill_rate
        
        self.tokens = min(self.capacity, self.tokens + tokens_to_add)
        self.last_refill = now
    
    def get_wait_time(self, tokens: int = 1) -> float:
        """
        Calculate how long to wait before tokens will be available.
        
        Args:
            tokens: Number of tokens needed
            
        Returns:
            float: Time in seconds to wait
        """
        self._refill()
        
        if self.tokens >= tokens:
            return 0.0
        
        tokens_needed = tokens - self.tokens
        return tokens_needed / self.refill_rate


@dataclass
class RateLimitConfig:
    """Configuration for rate limiting"""
    operation: str
    capacity: int
    refill_rate: float  # tokens per second
    burst_size: int = None
    
    def __post_init__(self):
        if self.burst_size is None:
            self.burst_size = self.capacity


class RateLimiter:
    """Rate limiter using token bucket algorithm"""
    
    def __init__(self):
        self.buckets: Dict[str, TokenBucket] = {}
        self.configs: Dict[str, RateLimitConfig] = {
            # Message rate limits
            "send_message": RateLimitConfig(
                operation="send_message",
                capacity=100,  # 100 messages
                refill_rate=10.0,  # 10 messages per second
                burst_size=50
            ),
            "send_message_user": RateLimitConfig(
                operation="send_message_user",
                capacity=50,  # 50 messages per user
                refill_rate=5.0,  # 5 messages per second per user
                burst_size=25
            ),
            "send_message_tenant": RateLimitConfig(
                operation="send_message_tenant",
                capacity=500,  # 500 messages per tenant
                refill_rate=50.0,  # 50 messages per second per tenant
                burst_size=250
            ),
            
            # Merge rate limits
            "merge": RateLimitConfig(
                operation="merge",
                capacity=20,  # 20 merges
                refill_rate=2.0,  # 2 merges per second
                burst_size=10
            ),
            "merge_user": RateLimitConfig(
                operation="merge_user",
                capacity=10,  # 10 merges per user
                refill_rate=1.0,  # 1 merge per second per user
                burst_size=5
            ),
            "merge_tenant": RateLimitConfig(
                operation="merge_tenant",
                capacity=100,  # 100 merges per tenant
                refill_rate=10.0,  # 10 merges per second per tenant
                burst_size=50
            ),
            
            # General API rate limits
            "api_global": RateLimitConfig(
                operation="api_global",
                capacity=1000,  # 1000 requests
                refill_rate=100.0,  # 100 requests per second
                burst_size=500
            ),
            "api_user": RateLimitConfig(
                operation="api_user",
                capacity=200,  # 200 requests per user
                refill_rate=20.0,  # 20 requests per second per user
                burst_size=100
            ),
            "api_tenant": RateLimitConfig(
                operation="api_tenant",
                capacity=1000,  # 1000 requests per tenant
                refill_rate=100.0,  # 100 requests per second per tenant
                burst_size=500
            ),
        }
    
    def _get_bucket_key(self, operation: str, tenant_id: str = None, user_id: str = None) -> str:
        """Generate a unique key for the token bucket."""
        if user_id:
            return f"{operation}:user:{user_id}"
        elif tenant_id:
            return f"{operation}:tenant:{tenant_id}"
        else:
            return f"{operation}:global"
    
    def _get_or_create_bucket(self, operation: str, tenant_id: str = None, user_id: str = None) -> TokenBucket:
        """Get or create a token bucket for the given operation and scope."""
        key = self._get_bucket_key(operation, tenant_id, user_id)
        
        if key not in self.buckets:
            config = self.configs.get(operation)
            if not config:
                raise ValueError(f"Unknown rate limit operation: {operation}")
            
            self.buckets[key] = TokenBucket(
                capacity=config.capacity,
                tokens=config.capacity,  # Start with full bucket
                refill_rate=config.refill_rate
            )
        
        return self.buckets[key]
    
    def check_rate_limit(self, operation: str, tenant_id: str = None, user_id: str = None, tokens: int = 1) -> Tuple[bool, float]:
        """
        Check if an operation is allowed under rate limits.
        
        Args:
            operation: Type of operation (e.g., "send_message", "merge")
            tenant_id: Tenant identifier
            user_id: User identifier
            tokens: Number of tokens to consume
            
        Returns:
            Tuple[bool, float]: (allowed, wait_time_seconds)
        """
        bucket = self._get_or_create_bucket(operation, tenant_id, user_id)
        
        if bucket.consume(tokens):
            return True, 0.0
        else:
            return False, bucket.get_wait_time(tokens)
    
    def check_multi_level_rate_limit(self, operation: str, tenant_id: str, user_id: str, tokens: int = 1) -> Tuple[bool, float]:
        """
        Check rate limits at multiple levels (global, tenant, user).
        
        Args:
            operation: Type of operation
            tenant_id: Tenant identifier
            user_id: User identifier
            tokens: Number of tokens to consume
            
        Returns:
            Tuple[bool, float]: (allowed, wait_time_seconds)
        """
        # Check global rate limit
        global_allowed, global_wait = self.check_rate_limit(operation, tokens=tokens)
        if not global_allowed:
            return False, global_wait
        
        # Check tenant rate limit
        tenant_allowed, tenant_wait = self.check_rate_limit(f"{operation}_tenant", tenant_id=tenant_id, tokens=tokens)
        if not tenant_allowed:
            return False, tenant_wait
        
        # Check user rate limit
        user_allowed, user_wait = self.check_rate_limit(f"{operation}_user", user_id=user_id, tokens=tokens)
        if not user_allowed:
            return False, user_wait
        
        # All checks passed
        return True, 0.0


class QuotaManager:
    """Manages quotas for tenants and users"""
    
    def __init__(self):
        self.quotas: Dict[str, Dict[str, int]] = {
            # Default quotas
            "default": {
                "messages_per_day": 10000,
                "merges_per_day": 1000,
                "threads_per_day": 100,
                "branches_per_day": 1000,
                "storage_mb": 1024,  # 1GB
            },
            # Premium quotas
            "premium": {
                "messages_per_day": 100000,
                "merges_per_day": 10000,
                "threads_per_day": 1000,
                "branches_per_day": 10000,
                "storage_mb": 10240,  # 10GB
            }
        }
    
    def get_tenant_quota(self, db: Session, tenant_id: str, quota_type: str) -> int:
        """
        Get quota for a tenant.
        
        Args:
            db: Database session
            tenant_id: Tenant identifier
            quota_type: Type of quota (e.g., "messages_per_day")
            
        Returns:
            int: Quota value
        """
        tenant = db.query(Tenant).filter(Tenant.id == tenant_id).first()
        if not tenant:
            return self.quotas["default"][quota_type]
        
        # Get quota from tenant settings
        settings = tenant.settings or {}
        plan = settings.get("plan", "default")
        
        return self.quotas.get(plan, self.quotas["default"]).get(quota_type, 0)
    
    def check_quota(self, db: Session, tenant_id: str, quota_type: str, current_usage: int) -> bool:
        """
        Check if quota is exceeded.
        
        Args:
            db: Database session
            tenant_id: Tenant identifier
            quota_type: Type of quota
            current_usage: Current usage count
            
        Returns:
            bool: True if quota is not exceeded
        """
        quota = self.get_tenant_quota(db, tenant_id, quota_type)
        return current_usage < quota


class RateLimitMiddleware:
    """Middleware for rate limiting"""
    
    def __init__(self):
        self.rate_limiter = RateLimiter()
        self.quota_manager = QuotaManager()
    
    def check_rate_limit_and_quota(
        self, 
        db: Session, 
        context: TenantContext, 
        operation: str, 
        quota_type: str = None,
        current_usage: int = 0
    ) -> None:
        """
        Check both rate limits and quotas.
        
        Args:
            db: Database session
            context: Tenant context
            operation: Operation type
            quota_type: Quota type to check
            current_usage: Current usage for quota check
            
        Raises:
            HTTPException: If rate limit or quota is exceeded
        """
        # Check rate limits
        allowed, wait_time = self.rate_limiter.check_multi_level_rate_limit(
            operation, 
            context.tenant_id, 
            context.user_id
        )
        
        if not allowed:
            retry_after = int(wait_time) + 1
            raise HTTPException(
                status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                detail=f"Rate limit exceeded for {operation}. Try again in {retry_after} seconds.",
                headers={"Retry-After": str(retry_after)}
            )
        
        # Check quota if specified
        if quota_type:
            quota_ok = self.quota_manager.check_quota(db, context.tenant_id, quota_type, current_usage)
            if not quota_ok:
                quota = self.quota_manager.get_tenant_quota(db, context.tenant_id, quota_type)
                raise HTTPException(
                    status_code=status.HTTP_429_TOO_MANY_REQUESTS,
                    detail=f"Quota exceeded for {quota_type}. Limit: {quota}, Current: {current_usage}",
                    headers={"Retry-After": "86400"}  # 24 hours
                )


# Global rate limiter instance
rate_limiter = RateLimiter()
quota_manager = QuotaManager()
rate_limit_middleware = RateLimitMiddleware()


def require_rate_limit(operation: str, quota_type: str = None):
    """
    Decorator to require rate limiting for an endpoint.
    
    Args:
        operation: Operation type for rate limiting
        quota_type: Quota type to check
        
    Returns:
        Callable: Decorated function
    """
    def decorator(func):
        async def wrapper(*args, **kwargs):
            # Extract dependencies
            db = None
            context = None
            
            for arg in args:
                if hasattr(arg, '__class__') and 'Session' in str(arg.__class__):
                    db = arg
                elif hasattr(arg, '__class__') and 'TenantContext' in str(arg.__class__):
                    context = arg
            
            if not db or not context:
                raise HTTPException(
                    status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
                    detail="Rate limiting requires database session and tenant context"
                )
            
            # Check rate limits and quotas
            rate_limit_middleware.check_rate_limit_and_quota(
                db, context, operation, quota_type
            )
            
            return await func(*args, **kwargs)
        return wrapper
    return decorator
