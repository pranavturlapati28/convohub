from fastapi import Depends, HTTPException, status, Header
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from sqlalchemy.orm import Session
from sqlalchemy.exc import SQLAlchemyError
from typing import Optional, List, Dict, Any
import jwt
from datetime import datetime, timedelta
import uuid
from app.db import get_db
from app.models import User, Tenant, ThreadCollaborator, Thread
from app.core.settings import settings

# JWT configuration
JWT_ALGORITHM = "HS256"
JWT_EXPIRY_HOURS = 24

security = HTTPBearer()

class AuthError(Exception):
    """Custom authentication error"""
    pass

class TenantContext:
    """Context for current tenant and user"""
    def __init__(self, tenant_id: str, user_id: str, permissions: List[str] = None):
        self.tenant_id = tenant_id
        self.user_id = user_id
        self.permissions = permissions or []

def create_jwt_token(tenant_id: str, user_id: str, permissions: List[str] = None) -> str:
    """
    Create a JWT token for a user in a tenant.
    
    Args:
        tenant_id: Tenant identifier
        user_id: User identifier
        permissions: List of user permissions
        
    Returns:
        str: JWT token
    """
    payload = {
        "sub": tenant_id,  # JWT sub claim contains tenant_id
        "user_id": user_id,
        "permissions": permissions or [],
        "exp": datetime.utcnow() + timedelta(hours=JWT_EXPIRY_HOURS),
        "iat": datetime.utcnow(),
        "jti": str(uuid.uuid4())  # JWT ID for uniqueness
    }
    
    return jwt.encode(payload, settings.JWT_SECRET, algorithm=JWT_ALGORITHM)

def verify_jwt_token(token: str) -> Dict[str, Any]:
    """
    Verify and decode a JWT token.
    
    Args:
        token: JWT token string
        
    Returns:
        Dict: Decoded token payload
        
    Raises:
        AuthError: If token is invalid
    """
    try:
        payload = jwt.decode(token, settings.JWT_SECRET, algorithms=[JWT_ALGORITHM])
        return payload
    except jwt.ExpiredSignatureError:
        raise AuthError("Token has expired")
    except jwt.InvalidTokenError:
        raise AuthError("Invalid token")

def get_current_tenant_context(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: Session = Depends(get_db)
) -> TenantContext:
    """
    Get current tenant context from JWT token.
    
    Args:
        credentials: HTTP Bearer credentials
        db: Database session
        
    Returns:
        TenantContext: Current tenant and user context
        
    Raises:
        HTTPException: If authentication fails
    """
    try:
        # Verify JWT token
        payload = verify_jwt_token(credentials.credentials)
        
        tenant_id = payload.get("sub")
        user_id = payload.get("user_id")
        permissions = payload.get("permissions", [])
        
        if not tenant_id or not user_id:
            raise AuthError("Invalid token payload")
        
        # Verify tenant exists and is active
        tenant = db.query(Tenant).filter(
            Tenant.id == tenant_id,
            Tenant.is_active == True
        ).first()
        
        if not tenant:
            raise AuthError("Tenant not found or inactive")
        
        # Verify user exists and belongs to tenant
        user = db.query(User).filter(
            User.id == user_id,
            User.tenant_id == tenant_id,
            User.is_active == True
        ).first()
        
        if not user:
            raise AuthError("User not found or inactive")
        
        return TenantContext(tenant_id, user_id, permissions)
        
    except AuthError as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail=str(e),
            headers={"WWW-Authenticate": "Bearer"}
        )
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Authentication failed",
            headers={"WWW-Authenticate": "Bearer"}
        )

def get_current_user(
    context: TenantContext = Depends(get_current_tenant_context),
    db: Session = Depends(get_db)
) -> User:
    """
    Get current user from tenant context.
    
    Args:
        context: Tenant context
        db: Database session
        
    Returns:
        User: Current user object
    """
    user = db.query(User).filter(
        User.id == context.user_id,
        User.tenant_id == context.tenant_id
    ).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="User not found"
        )
    
    return user

def require_permission(permission: str):
    """
    Decorator to require a specific permission.
    
    Args:
        permission: Required permission
        
    Returns:
        Callable: Decorated function
    """
    def decorator(context: TenantContext = Depends(get_current_tenant_context)):
        if permission not in context.permissions:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Permission '{permission}' required"
            )
        return context
    return decorator

def check_thread_access(
    thread_id: str,
    context: TenantContext = Depends(get_current_tenant_context),
    db: Session = Depends(get_db)
) -> bool:
    """
    Check if current user has access to a thread.
    
    Args:
        thread_id: Thread identifier
        context: Tenant context
        db: Database session
        
    Returns:
        bool: True if user has access
        
    Raises:
        HTTPException: If access is denied
    """
    # Check if user is thread owner
    thread = db.query(Thread).filter(
        Thread.id == thread_id,
        Thread.tenant_id == context.tenant_id
    ).first()
    
    if thread and thread.owner_id == context.user_id:
        return True
    
    # Check if user is a collaborator
    collaborator = db.query(ThreadCollaborator).filter(
        ThreadCollaborator.thread_id == thread_id,
        ThreadCollaborator.user_id == context.user_id,
        ThreadCollaborator.tenant_id == context.tenant_id,
        ThreadCollaborator.is_active == True
    ).first()
    
    if collaborator:
        return True
    
    raise HTTPException(
        status_code=status.HTTP_403_FORBIDDEN,
        detail="Access denied to thread"
    )

def get_tenant_id_from_context(
    context: TenantContext = Depends(get_current_tenant_context)
) -> str:
    """Get tenant ID from context."""
    return context.tenant_id

def get_user_id_from_context(
    context: TenantContext = Depends(get_current_tenant_context)
) -> str:
    """Get user ID from context."""
    return context.user_id

# Legacy compatibility
def get_current_user_legacy():
    """Legacy function for backward compatibility."""
    return User(id="00000000-0000-0000-0000-000000000001")
