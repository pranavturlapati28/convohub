#!/usr/bin/env python3
"""
Script to set up PostgreSQL Row-Level Security (RLS) policies for ConvoHub.
"""

import os
import sys
from sqlalchemy import create_engine, text
from app.core.settings import settings

def setup_rls():
    """Set up RLS policies for the application."""
    
    # Create database engine
    engine = create_engine(settings.DATABASE_URL)
    
    with engine.connect() as conn:
        # Enable RLS on all tables
        tables_with_tenant = [
            'tenants', 'users', 'threads', 'branches', 'messages', 
            'edges', 'merges', 'summaries', 'memories', 'idempotency_records',
            'thread_collaborators'
        ]
        
        print("Enabling RLS on tables...")
        for table in tables_with_tenant:
            try:
                conn.execute(text(f"ALTER TABLE {table} ENABLE ROW LEVEL SECURITY"))
                print(f"  ✓ Enabled RLS on {table}")
            except Exception as e:
                print(f"  ⚠ Warning: Could not enable RLS on {table}: {e}")
        
        # Create tenant-based policies
        print("\nCreating tenant-based policies...")
        tenant_tables = ['tenants', 'users', 'idempotency_records']
        for table in tenant_tables:
            try:
                policy_sql = f"""
                CREATE POLICY {table}_tenant_policy ON {table}
                FOR ALL
                USING (tenant_id = current_setting('app.current_tenant_id')::uuid)
                WITH CHECK (tenant_id = current_setting('app.current_tenant_id')::uuid)
                """
                conn.execute(text(policy_sql))
                print(f"  ✓ Created tenant policy for {table}")
            except Exception as e:
                print(f"  ⚠ Warning: Could not create tenant policy for {table}: {e}")
        
        # Create thread-based access policies
        print("\nCreating thread-based access policies...")
        thread_tables = ['threads', 'thread_collaborators', 'merges', 'summaries', 'memories']
        for table in thread_tables:
            try:
                policy_sql = f"""
                CREATE POLICY {table}_thread_policy ON {table}
                FOR ALL
                USING (
                    EXISTS (
                        SELECT 1 FROM threads t
                        LEFT JOIN thread_collaborators tc ON t.id = tc.thread_id
                        WHERE t.id = {table}.thread_id
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
                        WHERE t.id = {table}.thread_id
                        AND (
                            t.owner_id = current_setting('app.current_user_id')::uuid
                            OR tc.user_id = current_setting('app.current_user_id')::uuid
                        )
                        AND t.tenant_id = current_setting('app.current_tenant_id')::uuid
                    )
                )
                """
                conn.execute(text(policy_sql))
                print(f"  ✓ Created thread policy for {table}")
            except Exception as e:
                print(f"  ⚠ Warning: Could not create thread policy for {table}: {e}")
        
        # Create branch-based access policies
        print("\nCreating branch-based access policies...")
        branch_tables = ['branches', 'messages', 'edges']
        for table in branch_tables:
            try:
                policy_sql = f"""
                CREATE POLICY {table}_branch_policy ON {table}
                FOR ALL
                USING (
                    EXISTS (
                        SELECT 1 FROM branches b
                        JOIN threads t ON b.thread_id = t.id
                        LEFT JOIN thread_collaborators tc ON t.id = tc.thread_id
                        WHERE b.id = {table}.branch_id
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
                        WHERE b.id = {table}.branch_id
                        AND (
                            t.owner_id = current_setting('app.current_user_id')::uuid
                            OR tc.user_id = current_setting('app.current_user_id')::uuid
                        )
                        AND b.tenant_id = current_setting('app.current_tenant_id')::uuid
                    )
                )
                """
                conn.execute(text(policy_sql))
                print(f"  ✓ Created branch policy for {table}")
            except Exception as e:
                print(f"  ⚠ Warning: Could not create branch policy for {table}: {e}")
        
        # Commit all changes
        conn.commit()
        print("\n✅ RLS setup completed successfully!")

if __name__ == "__main__":
    setup_rls()
