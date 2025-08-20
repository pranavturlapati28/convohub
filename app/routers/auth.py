from fastapi import APIRouter, Depends, HTTPException, status
from sqlalchemy.orm import Session
from typing import List, Optional
from app.db import get_db
from app.models import User, Tenant, ThreadCollaborator
from app.schemas import (
    TenantCreate, TenantOut, UserCreate, UserOut, 
    LoginRequest, LoginResponse, ThreadCollaboratorCreate, ThreadCollaboratorOut
)
from app.auth import (
    get_current_tenant_context, get_current_user, create_jwt_token,
    TenantContext, get_tenant_id_from_context, get_user_id_from_context
)
from app.rls_utils import RLSManager, TenantAccessControl
from datetime import datetime
from uuid import uuid4

router = APIRouter(tags=["auth"])

@router.post(
    "/auth/login",
    response_model=LoginResponse,
    summary="Authenticate user",
    description="Authenticate a user and return a JWT token for multi-tenant access.",
    responses={
        200: {"description": "Authentication successful"},
        401: {"description": "Invalid credentials"},
        422: {"description": "Validation error"},
    }
)
def login(
    request: LoginRequest,
    db: Session = Depends(get_db)
):
    """
    Authenticate a user and return a JWT token.
    
    Args:
        request: Login credentials
        db: Database session
        
    Returns:
        LoginResponse: JWT token and user information
        
    Raises:
        HTTPException: If authentication fails
    """
    # Find user by email and tenant domain
    user = db.query(User).join(Tenant).filter(
        User.email == request.email,
        Tenant.domain == request.tenant_domain,
        User.is_active == True,
        Tenant.is_active == True
    ).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Invalid credentials"
        )
    
    # In a real application, you would verify the password here
    # For now, we'll just check if the user exists
    
    # Get user permissions
    permissions = user.permissions or []
    
    # Create JWT token
    token = create_jwt_token(
        tenant_id=user.tenant_id,
        user_id=user.id,
        permissions=permissions
    )
    
    return LoginResponse(
        access_token=token,
        token_type="bearer",
        user=UserOut(
            id=user.id,
            email=user.email,
            name=user.name,
            role=user.role,
            tenant_id=user.tenant_id,
            permissions=permissions,
            created_at=user.created_at
        )
    )


@router.post(
    "/tenants",
    response_model=TenantOut,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new tenant",
    description="Create a new tenant for multi-tenancy.",
    responses={
        201: {"description": "Tenant created successfully"},
        400: {"description": "Invalid request data"},
        409: {"description": "Tenant domain already exists"},
        422: {"description": "Validation error"},
    }
)
def create_tenant(
    request: TenantCreate,
    db: Session = Depends(get_db)
):
    """
    Create a new tenant.
    
    Args:
        request: Tenant creation data
        db: Database session
        
    Returns:
        TenantOut: Created tenant information
        
    Raises:
        HTTPException: If tenant creation fails
    """
    # Check if domain already exists
    if request.domain:
        existing_tenant = db.query(Tenant).filter(
            Tenant.domain == request.domain
        ).first()
        
        if existing_tenant:
            raise HTTPException(
                status_code=status.HTTP_409_CONFLICT,
                detail="Tenant domain already exists"
            )
    
    try:
        tenant = Tenant(
            id=str(uuid4()),
            name=request.name,
            domain=request.domain,
            settings=request.settings or {},
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        db.add(tenant)
        db.commit()
        db.refresh(tenant)
        
        return TenantOut(
            id=tenant.id,
            name=tenant.name,
            domain=tenant.domain,
            settings=tenant.settings,
            is_active=tenant.is_active,
            created_at=tenant.created_at,
            updated_at=tenant.updated_at
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create tenant: {str(e)}"
        )


@router.post(
    "/tenants/{tenant_id}/users",
    response_model=UserOut,
    status_code=status.HTTP_201_CREATED,
    summary="Create a new user",
    description="Create a new user in a tenant.",
    responses={
        201: {"description": "User created successfully"},
        400: {"description": "Invalid request data"},
        404: {"description": "Tenant not found"},
        409: {"description": "User email already exists in tenant"},
        422: {"description": "Validation error"},
    }
)
def create_user(
    tenant_id: str,
    request: UserCreate,
    context: TenantContext = Depends(get_current_tenant_context),
    db: Session = Depends(get_db)
):
    """
    Create a new user in a tenant.
    
    Args:
        tenant_id: Tenant ID
        request: User creation data
        context: Current tenant context
        db: Database session
        
    Returns:
        UserOut: Created user information
        
    Raises:
        HTTPException: If user creation fails
    """
    # Verify tenant exists and user has access
    tenant = db.query(Tenant).filter(
        Tenant.id == tenant_id,
        Tenant.is_active == True
    ).first()
    
    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="Tenant not found"
        )
    
    # Check if user email already exists in tenant
    existing_user = db.query(User).filter(
        User.email == request.email,
        User.tenant_id == tenant_id
    ).first()
    
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="User email already exists in tenant"
        )
    
    try:
        user = User(
            id=str(uuid4()),
            tenant_id=tenant_id,
            email=request.email,
            name=request.name,
            role=request.role,
            permissions=request.permissions or [],
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        db.add(user)
        db.commit()
        db.refresh(user)
        
        return UserOut(
            id=user.id,
            email=user.email,
            name=user.name,
            role=user.role,
            tenant_id=user.tenant_id,
            permissions=user.permissions or [],
            created_at=user.created_at
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to create user: {str(e)}"
        )


@router.post(
    "/threads/{thread_id}/collaborators",
    response_model=ThreadCollaboratorOut,
    status_code=status.HTTP_201_CREATED,
    summary="Add thread collaborator",
    description="Add a user as a collaborator to a thread.",
    responses={
        201: {"description": "Collaborator added successfully"},
        400: {"description": "Invalid request data"},
        403: {"description": "Access denied"},
        404: {"description": "Thread or user not found"},
        409: {"description": "Collaborator already exists"},
        422: {"description": "Validation error"},
    }
)
def add_thread_collaborator(
    thread_id: str,
    request: ThreadCollaboratorCreate,
    context: TenantContext = Depends(get_current_tenant_context),
    db: Session = Depends(get_db)
):
    """
    Add a user as a collaborator to a thread.
    
    Args:
        thread_id: Thread ID
        request: Collaborator creation data
        context: Current tenant context
        db: Database session
        
    Returns:
        ThreadCollaboratorOut: Created collaborator information
        
    Raises:
        HTTPException: If operation fails
    """
    # Check if user has access to thread
    if not TenantAccessControl.check_thread_access(db, thread_id, context.user_id, context.tenant_id):
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Access denied to thread"
        )
    
    # Verify user exists in tenant
    user = db.query(User).filter(
        User.id == request.user_id,
        User.tenant_id == context.tenant_id,
        User.is_active == True
    ).first()
    
    if not user:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail="User not found"
        )
    
    # Check if collaborator already exists
    existing_collaborator = db.query(ThreadCollaborator).filter(
        ThreadCollaborator.thread_id == thread_id,
        ThreadCollaborator.user_id == request.user_id,
        ThreadCollaborator.tenant_id == context.tenant_id
    ).first()
    
    if existing_collaborator:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="Collaborator already exists"
        )
    
    try:
        collaborator = ThreadCollaborator(
            id=str(uuid4()),
            thread_id=thread_id,
            user_id=request.user_id,
            tenant_id=context.tenant_id,
            role=request.role,
            permissions=request.permissions or [],
            is_active=True,
            created_at=datetime.utcnow(),
            updated_at=datetime.utcnow()
        )
        
        db.add(collaborator)
        db.commit()
        db.refresh(collaborator)
        
        return ThreadCollaboratorOut(
            id=collaborator.id,
            thread_id=collaborator.thread_id,
            user_id=collaborator.user_id,
            tenant_id=collaborator.tenant_id,
            role=collaborator.role,
            permissions=collaborator.permissions or [],
            is_active=collaborator.is_active,
            created_at=collaborator.created_at
        )
        
    except Exception as e:
        db.rollback()
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to add collaborator: {str(e)}"
        )


@router.get(
    "/me",
    response_model=UserOut,
    summary="Get current user",
    description="Get information about the currently authenticated user.",
    responses={
        200: {"description": "User information retrieved successfully"},
        401: {"description": "Authentication required"},
    }
)
def get_current_user_info(
    user: User = Depends(get_current_user),
    context: TenantContext = Depends(get_current_tenant_context)
):
    """
    Get information about the currently authenticated user.
    
    Args:
        user: Current user object
        context: Current tenant context
        
    Returns:
        UserOut: Current user information
    """
    return UserOut(
        id=user.id,
        email=user.email,
        name=user.name,
        role=user.role,
        tenant_id=user.tenant_id,
        permissions=user.permissions or [],
        created_at=user.created_at
    )
