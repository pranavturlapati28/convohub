from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import Dict, Any
from app.db import get_db
from app.auth import get_current_tenant_context, TenantContext
from app.usage_tracker import UsageTracker
from app.rate_limiting import quota_manager
from app.schemas import UsageSummary

router = APIRouter(tags=["usage"])

@router.get(
    "/usage",
    response_model=UsageSummary,
    summary="Get usage summary",
    description="Get current usage and quota information for the authenticated user and tenant.",
    responses={
        200: {"description": "Usage summary retrieved successfully"},
        401: {"description": "Authentication required"},
    }
)
def get_usage_summary(
    db: Session = Depends(get_db),
    context: TenantContext = Depends(get_current_tenant_context)
):
    """
    Get usage summary for the current user and tenant.
    
    Args:
        db: Database session
        context: Tenant context
        
    Returns:
        UsageSummary: Current usage and quota information
    """
    summary = UsageTracker.get_usage_summary(db, context.tenant_id, context.user_id)
    
    return UsageSummary(
        tenant_id=context.tenant_id,
        user_id=context.user_id,
        usage=summary
    )


@router.get(
    "/usage/tenant",
    response_model=UsageSummary,
    summary="Get tenant usage summary",
    description="Get current usage and quota information for the entire tenant.",
    responses={
        200: {"description": "Tenant usage summary retrieved successfully"},
        401: {"description": "Authentication required"},
    }
)
def get_tenant_usage_summary(
    db: Session = Depends(get_db),
    context: TenantContext = Depends(get_current_tenant_context)
):
    """
    Get usage summary for the entire tenant.
    
    Args:
        db: Database session
        context: Tenant context
        
    Returns:
        UsageSummary: Current usage and quota information for tenant
    """
    summary = UsageTracker.get_usage_summary(db, context.tenant_id)
    
    return UsageSummary(
        tenant_id=context.tenant_id,
        user_id=None,
        usage=summary
    )


@router.get(
    "/usage/{usage_type}",
    summary="Get specific usage",
    description="Get current usage for a specific type.",
    responses={
        200: {"description": "Usage information retrieved successfully"},
        400: {"description": "Invalid usage type"},
        401: {"description": "Authentication required"},
    }
)
def get_specific_usage(
    usage_type: str,
    db: Session = Depends(get_db),
    context: TenantContext = Depends(get_current_tenant_context)
):
    """
    Get current usage for a specific type.
    
    Args:
        usage_type: Type of usage to check
        db: Database session
        context: Tenant context
        
    Returns:
        dict: Usage information
    """
    valid_types = ["messages_per_day", "merges_per_day", "threads_per_day", "branches_per_day"]
    
    if usage_type not in valid_types:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Invalid usage type. Must be one of: {', '.join(valid_types)}"
        )
    
    current_usage = UsageTracker.get_usage(db, context.tenant_id, usage_type, context.user_id)
    quota = quota_manager.get_tenant_quota(db, context.tenant_id, usage_type)
    
    return {
        "usage_type": usage_type,
        "current_usage": current_usage,
        "quota": quota,
        "remaining": max(0, quota - current_usage),
        "percentage": (current_usage / quota * 100) if quota > 0 else 0
    }
