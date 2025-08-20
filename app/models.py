# app/models.py
import uuid, datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, CheckConstraint, JSON, Text, Boolean, Index, UniqueConstraint
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db import Base

def uid(): return str(uuid.uuid4())
def now(): return datetime.datetime.utcnow()

class Tenant(Base):
    __tablename__ = "tenants"
    id = Column(UUID(as_uuid=False), primary_key=True, default=uid)
    name = Column(String(200), nullable=False)
    domain = Column(String(100), nullable=True, unique=True)
    settings = Column(JSON, nullable=True)  # Tenant-specific settings
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=now, nullable=False)
    updated_at = Column(DateTime, default=now, onupdate=now, nullable=False)

    # relationships
    users = relationship("User", back_populates="tenant", cascade="all, delete-orphan")
    threads = relationship("Thread", back_populates="tenant", cascade="all, delete-orphan")

    __table_args__ = (
        Index('ix_tenants_domain', 'domain'),
        Index('ix_tenants_active', 'is_active'),
    )


class User(Base):
    __tablename__ = "users"
    id = Column(UUID(as_uuid=False), primary_key=True, default=uid)
    tenant_id = Column(UUID(as_uuid=False), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    email = Column(String(255), nullable=False)
    name = Column(String(200), nullable=False)
    role = Column(String(50), nullable=False, default="user")  # admin, user, guest
    permissions = Column(JSON, nullable=True)  # User-specific permissions
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=now, nullable=False)
    updated_at = Column(DateTime, default=now, onupdate=now, nullable=False)

    # relationships
    tenant = relationship("Tenant", back_populates="users")
    owned_threads = relationship("Thread", back_populates="owner", foreign_keys="Thread.owner_id")
    thread_collaborations = relationship("ThreadCollaborator", back_populates="user")

    __table_args__ = (
        UniqueConstraint('tenant_id', 'email', name='uq_user_email_per_tenant'),
        CheckConstraint("role IN ('admin','user','guest')", name="ck_user_role"),
        Index('ix_users_tenant_email', 'tenant_id', 'email'),
        Index('ix_users_active', 'is_active'),
    )


class ThreadCollaborator(Base):
    __tablename__ = "thread_collaborators"
    id = Column(UUID(as_uuid=False), primary_key=True, default=uid)
    thread_id = Column(UUID(as_uuid=False), ForeignKey("threads.id", ondelete="CASCADE"), nullable=False, index=True)
    user_id = Column(UUID(as_uuid=False), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    tenant_id = Column(UUID(as_uuid=False), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    role = Column(String(50), nullable=False, default="viewer")  # owner, editor, viewer
    permissions = Column(JSON, nullable=True)  # Thread-specific permissions
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=now, nullable=False)
    updated_at = Column(DateTime, default=now, onupdate=now, nullable=False)

    # relationships
    thread = relationship("Thread", back_populates="collaborators")
    user = relationship("User", back_populates="thread_collaborations")

    __table_args__ = (
        UniqueConstraint('thread_id', 'user_id', name='uq_thread_collaborator'),
        CheckConstraint("role IN ('owner','editor','viewer')", name="ck_collaborator_role"),
        Index('ix_collaborators_thread_user', 'thread_id', 'user_id'),
        Index('ix_collaborators_active', 'is_active'),
    )


class Thread(Base):
    __tablename__ = "threads"
    id = Column(UUID(as_uuid=False), primary_key=True, default=uid)
    tenant_id = Column(UUID(as_uuid=False), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    owner_id = Column(UUID(as_uuid=False), ForeignKey("users.id", ondelete="CASCADE"), nullable=False, index=True)
    title = Column(String(200), nullable=False)
    description = Column(Text, nullable=True)
    created_at = Column(DateTime, default=now, nullable=False)
    updated_at = Column(DateTime, default=now, onupdate=now, nullable=False)

    # relationships
    tenant = relationship("Tenant", back_populates="threads")
    owner = relationship("User", back_populates="owned_threads", foreign_keys=[owner_id])
    collaborators = relationship("ThreadCollaborator", back_populates="thread", cascade="all, delete-orphan")
    branches = relationship("Branch", back_populates="thread", cascade="all, delete-orphan")
    merges = relationship("Merge", back_populates="thread", cascade="all, delete-orphan")
    summaries = relationship("Summary", back_populates="thread", cascade="all, delete-orphan")
    memories = relationship("Memory", back_populates="thread", cascade="all, delete-orphan")

    __table_args__ = (
        Index('ix_threads_tenant_owner', 'tenant_id', 'owner_id'),
        Index('ix_threads_tenant_created', 'tenant_id', 'created_at'),
    )


class Branch(Base):
    __tablename__ = "branches"
    id = Column(UUID(as_uuid=False), primary_key=True, default=uid)
    tenant_id = Column(UUID(as_uuid=False), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    thread_id = Column(UUID(as_uuid=False), ForeignKey("threads.id", ondelete="CASCADE"), nullable=False, index=True)
    name = Column(String(100), nullable=False)
    description = Column(Text, nullable=True)
    base_message_id = Column(UUID(as_uuid=False), ForeignKey("messages.id"), nullable=True)
    
    # Forking metadata
    created_from_branch_id = Column(UUID(as_uuid=False), ForeignKey("branches.id"), nullable=True)
    created_from_message_id = Column(UUID(as_uuid=False), ForeignKey("messages.id", use_alter=True, name="fk_branch_created_from_message"), nullable=True)
    
    # Status
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=now, nullable=False)
    updated_at = Column(DateTime, default=now, onupdate=now, nullable=False)

    # relationships
    tenant = relationship("Tenant")
    thread = relationship("Thread", back_populates="branches")
    base_message = relationship("Message", foreign_keys=[base_message_id], uselist=False)
    
    # Messages in this branch
    messages = relationship(
        "Message",
        back_populates="branch",
        cascade="all, delete-orphan",
        foreign_keys="Message.branch_id",
    )

    # Forking relationships (metadata only)
    created_from_branch = relationship(
        "Branch",
        remote_side=[id],
        foreign_keys=[created_from_branch_id],
        uselist=False,
        viewonly=True,
    )
    created_from_message = relationship(
        "Message",
        foreign_keys=[created_from_message_id],
        uselist=False,
        viewonly=True,
    )

    __table_args__ = (
        UniqueConstraint('thread_id', 'name', name='uq_branch_name_per_thread'),
        Index('ix_branches_tenant_thread', 'tenant_id', 'thread_id'),
        Index('ix_branches_thread_created', 'thread_id', 'created_at'),
    )


class Message(Base):
    __tablename__ = "messages"
    id = Column(UUID(as_uuid=False), primary_key=True, default=uid)
    
    # Tenant and branch relationships
    tenant_id = Column(UUID(as_uuid=False), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    branch_id = Column(UUID(as_uuid=False), ForeignKey("branches.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # DAG parent relationship (single parent for non-merge nodes)
    parent_message_id = Column(UUID(as_uuid=False), ForeignKey("messages.id"), nullable=True)
    
    # Content
    role = Column(String(20), nullable=False)  # user, assistant, system, tool
    content = Column(JSON, nullable=False)
    state_snapshot = Column(JSON, nullable=True)
    
    # Metadata
    origin = Column(String(20), nullable=False, default="live")  # live, merge, import
    created_at = Column(DateTime, default=now, nullable=False)
    updated_at = Column(DateTime, default=now, onupdate=now, nullable=False)

    # relationships
    tenant = relationship("Tenant")
    branch = relationship("Branch", back_populates="messages", foreign_keys=[branch_id])
    
    # DAG relationships
    parent = relationship(
        "Message",
        remote_side=[id],
        foreign_keys=[parent_message_id],
        uselist=False,
    )
    children = relationship(
        "Message",
        foreign_keys=[parent_message_id],
        primaryjoin="Message.parent_message_id==Message.id",
        viewonly=True,
    )
    
    # Merge relationships
    merges_as_lca = relationship("Merge", foreign_keys="Merge.lca_message_id", uselist=False)
    merges_as_result = relationship("Merge", foreign_keys="Merge.merged_into_message_id", uselist=False)

    __table_args__ = (
        CheckConstraint("role IN ('user','assistant','system','tool')", name="ck_message_role"),
        CheckConstraint("origin IN ('live','merge','import')", name="ck_message_origin"),
        Index('ix_messages_tenant_branch', 'tenant_id', 'branch_id'),
        Index('ix_messages_branch_created', 'branch_id', 'created_at'),
        Index('ix_messages_parent', 'parent_message_id'),
    )


class Edge(Base):
    """Represents explicit edges in the message DAG for multi-parent relationships (merge nodes)"""
    __tablename__ = "edges"
    id = Column(UUID(as_uuid=False), primary_key=True, default=uid)
    
    # Tenant and edge endpoints
    tenant_id = Column(UUID(as_uuid=False), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    from_message_id = Column(UUID(as_uuid=False), ForeignKey("messages.id", ondelete="CASCADE"), nullable=False, index=True)
    to_message_id = Column(UUID(as_uuid=False), ForeignKey("messages.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Edge metadata
    edge_type = Column(String(20), nullable=False, default="parent")  # parent, merge_parent, reference
    weight = Column(String(10), nullable=True)  # For weighted relationships
    
    created_at = Column(DateTime, default=now, nullable=False)

    # relationships
    tenant = relationship("Tenant")
    from_message = relationship("Message", foreign_keys=[from_message_id])
    to_message = relationship("Message", foreign_keys=[to_message_id])

    __table_args__ = (
        CheckConstraint("edge_type IN ('parent','merge_parent','reference')", name="ck_edge_type"),
        UniqueConstraint('from_message_id', 'to_message_id', name='uq_edge_unique'),
        Index('ix_edges_tenant', 'tenant_id'),
        Index('ix_edges_from', 'from_message_id'),
        Index('ix_edges_to', 'to_message_id'),
        Index('ix_edges_type', 'edge_type'),
    )


class Merge(Base):
    __tablename__ = "merges"
    id = Column(UUID(as_uuid=False), primary_key=True, default=uid)
    
    # Merge context
    thread_id = Column(UUID(as_uuid=False), ForeignKey("threads.id", ondelete="CASCADE"), nullable=False, index=True)
    source_branch_id = Column(UUID(as_uuid=False), ForeignKey("branches.id"), nullable=False)
    target_branch_id = Column(UUID(as_uuid=False), ForeignKey("branches.id"), nullable=False)
    
    # Merge strategy and results
    strategy = Column(String(20), nullable=False)  # syntactic, semantic, hybrid
    lca_message_id = Column(UUID(as_uuid=False), ForeignKey("messages.id"), nullable=True)
    merged_into_message_id = Column(UUID(as_uuid=False), ForeignKey("messages.id"), nullable=True)
    
    # Merge metadata
    summary = Column(JSON, nullable=True)
    conflict_resolution = Column(JSON, nullable=True)  # How conflicts were resolved
    created_at = Column(DateTime, default=now, nullable=False)
    updated_at = Column(DateTime, default=now, onupdate=now, nullable=False)

    # relationships
    thread = relationship("Thread", back_populates="merges")
    source_branch = relationship("Branch", foreign_keys=[source_branch_id])
    target_branch = relationship("Branch", foreign_keys=[target_branch_id])
    lca_message = relationship("Message", foreign_keys=[lca_message_id])
    merged_into_message = relationship("Message", foreign_keys=[merged_into_message_id])

    __table_args__ = (
        CheckConstraint("strategy IN ('syntactic','semantic','hybrid')", name="ck_merge_strategy"),
        CheckConstraint("source_branch_id != target_branch_id", name="ck_merge_different_branches"),
        Index('ix_merges_thread_created', 'thread_id', 'created_at'),
        Index('ix_merges_source', 'source_branch_id'),
        Index('ix_merges_target', 'target_branch_id'),
    )


class Summary(Base):
    """Thread-level summaries and metadata"""
    __tablename__ = "summaries"
    id = Column(UUID(as_uuid=False), primary_key=True, default=uid)
    
    # Context
    thread_id = Column(UUID(as_uuid=False), ForeignKey("threads.id", ondelete="CASCADE"), nullable=False, index=True)
    branch_id = Column(UUID(as_uuid=False), ForeignKey("branches.id"), nullable=True)  # Optional branch-specific summary
    
    # Summary content
    summary_type = Column(String(20), nullable=False)  # thread, branch, conversation, topic
    content = Column(Text, nullable=False)
    summary_metadata = Column(JSON, nullable=True)  # Additional summary metadata
    
    # Versioning
    version = Column(String(10), nullable=False, default="1.0")
    is_current = Column(Boolean, default=True, nullable=False)
    
    created_at = Column(DateTime, default=now, nullable=False)
    updated_at = Column(DateTime, default=now, onupdate=now, nullable=False)

    # relationships
    thread = relationship("Thread", back_populates="summaries")
    branch = relationship("Branch")

    __table_args__ = (
        CheckConstraint("summary_type IN ('thread','branch','conversation','topic')", name="ck_summary_type"),
        Index('ix_summaries_thread_type', 'thread_id', 'summary_type'),
        Index('ix_summaries_branch', 'branch_id'),
        Index('ix_summaries_current', 'is_current'),
    )


class Memory(Base):
    """Long-term memory and context for threads"""
    __tablename__ = "memories"
    id = Column(UUID(as_uuid=False), primary_key=True, default=uid)
    
    # Context
    thread_id = Column(UUID(as_uuid=False), ForeignKey("threads.id", ondelete="CASCADE"), nullable=False, index=True)
    
    # Memory content
    memory_type = Column(String(20), nullable=False)  # fact, preference, context, relationship
    key = Column(String(100), nullable=False)  # Memory key/identifier
    value = Column(Text, nullable=False)  # Memory value
    memory_metadata = Column(JSON, nullable=True)  # Additional memory metadata
    
    # Memory properties
    confidence = Column(String(10), nullable=True)  # Confidence level
    source = Column(String(50), nullable=True)  # How this memory was derived
    expires_at = Column(DateTime, nullable=True)  # Optional expiration
    
    created_at = Column(DateTime, default=now, nullable=False)
    updated_at = Column(DateTime, default=now, onupdate=now, nullable=False)

    # relationships
    thread = relationship("Thread", back_populates="memories")

    __table_args__ = (
        CheckConstraint("memory_type IN ('fact','preference','context','relationship')", name="ck_memory_type"),
        UniqueConstraint('thread_id', 'key', name='uq_memory_thread_key'),
        Index('ix_memories_thread_type', 'thread_id', 'memory_type'),
        Index('ix_memories_key', 'key'),
        Index('ix_memories_expires', 'expires_at'),
    )


class IdempotencyRecord(Base):
    __tablename__ = "idempotency_records"
    id = Column(UUID(as_uuid=False), primary_key=True, default=uid)
    tenant_id = Column(UUID(as_uuid=False), ForeignKey("tenants.id", ondelete="CASCADE"), nullable=False, index=True)
    key = Column(String(100), nullable=False, index=True)
    operation = Column(String(50), nullable=False)  # e.g., "merge", "send_message"
    result = Column(JSON, nullable=True)  # Stored result for idempotency
    created_at = Column(DateTime, default=now, nullable=False)
    updated_at = Column(DateTime, default=now, onupdate=now, nullable=False)

    # relationships
    tenant = relationship("Tenant")

    __table_args__ = (
        CheckConstraint("key != ''", name="ck_key_not_empty"),
        UniqueConstraint('tenant_id', 'key', 'operation', name='uq_idempotency_tenant_key_operation'),
        Index('ix_idempotency_tenant', 'tenant_id'),
        Index('ix_idempotency_created', 'created_at'),
    )
