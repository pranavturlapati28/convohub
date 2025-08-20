from typing import List, Dict, Any
from sqlalchemy.orm import Session
from sqlalchemy import text
from app.models import ThreadCollaborator

class RLSManager:
    """Manages PostgreSQL Row-Level Security policies"""
    
    @staticmethod
    def enable_rls_on_table(db: Session, table_name: str) -> None:
        """
        Enable RLS on a table.
        
        Args:
            db: Database session
            table_name: Name of the table
        """
        db.execute(text(f"ALTER TABLE {table_name} ENABLE ROW LEVEL SECURITY"))
        db.commit()
    
    @staticmethod
    def create_tenant_policy(db: Session, table_name: str, policy_name: str) -> None:
        """
        Create a tenant-based RLS policy.
        
        Args:
            db: Database session
            table_name: Name of the table
            policy_name: Name of the policy
        """
        policy_sql = f"""
        CREATE POLICY {policy_name} ON {table_name}
        FOR ALL
        USING (tenant_id = current_setting('app.current_tenant_id')::uuid)
        WITH CHECK (tenant_id = current_setting('app.current_tenant_id')::uuid)
        """
        db.execute(text(policy_sql))
        db.commit()
    
    @staticmethod
    def create_thread_access_policy(db: Session, table_name: str, policy_name: str) -> None:
        """
        Create a thread-based access policy for tables that reference threads.
        
        Args:
            db: Database session
            table_name: Name of the table
            policy_name: Name of the policy
        """
        policy_sql = f"""
        CREATE POLICY {policy_name} ON {table_name}
        FOR ALL
        USING (
            EXISTS (
                SELECT 1 FROM threads t
                LEFT JOIN thread_collaborators tc ON t.id = tc.thread_id
                WHERE t.id = {table_name}.thread_id
                AND (
                    t.owner_id = current_setting('app.current_user_id')::uuid
                    OR tc.user_id = current_setting('app.current_user_id')::uuid
                )
                AND t.tenant_id = current_setting('app.current_tenant_id')::uuid
            )
        )
        WITH CHECK (
            EXISTS (
                SELECT 1 FROM threads t
                LEFT JOIN thread_collaborators tc ON t.id = tc.thread_id
                WHERE t.id = {table_name}.thread_id
                AND (
                    t.owner_id = current_setting('app.current_user_id')::uuid
                    OR tc.user_id = current_setting('app.current_user_id')::uuid
                )
                AND t.tenant_id = current_setting('app.current_tenant_id')::uuid
            )
        )
        """
        db.execute(text(policy_sql))
        db.commit()
    
    @staticmethod
    def create_branch_access_policy(db: Session, table_name: str, policy_name: str) -> None:
        """
        Create a branch-based access policy for tables that reference branches.
        
        Args:
            db: Database session
            table_name: Name of the table
            policy_name: Name of the policy
        """
        policy_sql = f"""
        CREATE POLICY {policy_name} ON {table_name}
        FOR ALL
        USING (
            EXISTS (
                SELECT 1 FROM branches b
                JOIN threads t ON b.thread_id = t.id
                LEFT JOIN thread_collaborators tc ON t.id = tc.thread_id
                WHERE b.id = {table_name}.branch_id
                AND (
                    t.owner_id = current_setting('app.current_user_id')::uuid
                    OR tc.user_id = current_setting('app.current_user_id')::uuid
                )
                AND b.tenant_id = current_setting('app.current_tenant_id')::uuid
            )
        )
        WITH CHECK (
            EXISTS (
                SELECT 1 FROM branches b
                JOIN threads t ON b.thread_id = t.id
                LEFT JOIN thread_collaborators tc ON t.id = tc.thread_id
                WHERE b.id = {table_name}.branch_id
                AND (
                    t.owner_id = current_setting('app.current_user_id')::uuid
                    OR tc.user_id = current_setting('app.current_user_id')::uuid
                )
                AND b.tenant_id = current_setting('app.current_tenant_id')::uuid
            )
        )
        """
        db.execute(text(policy_sql))
        db.commit()
    
    @staticmethod
    def set_current_tenant_and_user(db: Session, tenant_id: str, user_id: str) -> None:
        """
        Set current tenant and user for RLS policies.
        
        Args:
            db: Database session
            tenant_id: Current tenant ID
            user_id: Current user ID
        """
        db.execute(text(f"SET app.current_tenant_id = '{tenant_id}'"))
        db.execute(text(f"SET app.current_user_id = '{user_id}'"))
    
    @staticmethod
    def setup_rls_policies(db: Session) -> None:
        """
        Set up all RLS policies for the application.
        
        Args:
            db: Database session
        """
        # Enable RLS on all tables
        tables_with_tenant = [
            'tenants', 'users', 'threads', 'branches', 'messages', 
            'edges', 'merges', 'summaries', 'memories', 'idempotency_records'
        ]
        
        for table in tables_with_tenant:
            RLSManager.enable_rls_on_table(db, table)
        
        # Create tenant-based policies
        tenant_tables = ['tenants', 'users', 'idempotency_records']
        for table in tenant_tables:
            RLSManager.create_tenant_policy(db, table, f"{table}_tenant_policy")
        
        # Create thread-based access policies
        thread_tables = ['threads', 'thread_collaborators', 'merges', 'summaries', 'memories']
        for table in thread_tables:
            RLSManager.create_thread_access_policy(db, table, f"{table}_thread_policy")
        
        # Create branch-based access policies
        branch_tables = ['branches', 'messages', 'edges']
        for table in branch_tables:
            RLSManager.create_branch_access_policy(db, table, f"{table}_branch_policy")


class TenantAccessControl:
    """Manages tenant access control and permissions"""
    
    @staticmethod
    def check_tenant_access(db: Session, tenant_id: str, user_id: str) -> bool:
        """
        Check if user has access to tenant.
        
        Args:
            db: Database session
            tenant_id: Tenant ID
            user_id: User ID
            
        Returns:
            bool: True if user has access
        """
        from app.models import User
        
        user = db.query(User).filter(
            User.id == user_id,
            User.tenant_id == tenant_id,
            User.is_active == True
        ).first()
        
        return user is not None
    
    @staticmethod
    def check_thread_access(db: Session, thread_id: str, user_id: str, tenant_id: str) -> bool:
        """
        Check if user has access to thread.
        
        Args:
            db: Database session
            thread_id: Thread ID
            user_id: User ID
            tenant_id: Tenant ID
            
        Returns:
            bool: True if user has access
        """
        from app.models import Thread, ThreadCollaborator
        
        # Check if user is thread owner
        thread = db.query(Thread).filter(
            Thread.id == thread_id,
            Thread.tenant_id == tenant_id,
            Thread.owner_id == user_id
        ).first()
        
        if thread:
            return True
        
        # Check if user is a collaborator
        collaborator = db.query(ThreadCollaborator).filter(
            ThreadCollaborator.thread_id == thread_id,
            ThreadCollaborator.user_id == user_id,
            ThreadCollaborator.tenant_id == tenant_id,
            ThreadCollaborator.is_active == True
        ).first()
        
        return collaborator is not None
    
    @staticmethod
    def get_user_permissions(db: Session, user_id: str, tenant_id: str, thread_id: str = None) -> List[str]:
        """
        Get user permissions for tenant and optionally thread.
        
        Args:
            db: Database session
            user_id: User ID
            tenant_id: Tenant ID
            thread_id: Optional thread ID
            
        Returns:
            List[str]: List of permissions
        """
        from app.models import User, ThreadCollaborator
        
        # Get user permissions
        user = db.query(User).filter(
            User.id == user_id,
            User.tenant_id == tenant_id
        ).first()
        
        if not user:
            return []
        
        permissions = user.permissions or []
        
        # If thread_id provided, get thread-specific permissions
        if thread_id:
            collaborator = db.query(ThreadCollaborator).filter(
                ThreadCollaborator.thread_id == thread_id,
                ThreadCollaborator.user_id == user_id,
                ThreadCollaborator.tenant_id == tenant_id,
                ThreadCollaborator.is_active == True
            ).first()
            
            if collaborator and collaborator.permissions:
                permissions.extend(collaborator.permissions)
        
        return list(set(permissions))  # Remove duplicates
    
    @staticmethod
    def require_permission(permission: str):
        """
        Decorator to require a specific permission.
        
        Args:
            permission: Required permission
            
        Returns:
            Callable: Decorated function
        """
        def decorator(db: Session, user_id: str, tenant_id: str, thread_id: str = None):
            permissions = TenantAccessControl.get_user_permissions(db, user_id, tenant_id, thread_id)
            
            if permission not in permissions and "*" not in permissions:
                raise Exception(f"Permission '{permission}' required")
            
            return True
        return decorator
