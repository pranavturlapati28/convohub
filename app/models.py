# app/models.py
import uuid, datetime
from sqlalchemy import Column, String, DateTime, ForeignKey, CheckConstraint, JSON
from sqlalchemy.dialects.postgresql import UUID
from sqlalchemy.orm import relationship
from app.db import Base

def uid(): return str(uuid.uuid4())
def now(): return datetime.datetime.utcnow()

class Thread(Base):
    __tablename__ = "threads"
    id = Column(UUID(as_uuid=False), primary_key=True, default=uid)
    owner_id = Column(UUID(as_uuid=False), nullable=False)
    title = Column(String, nullable=False)
    created_at = Column(DateTime, default=now, nullable=False)

    branches = relationship("Branch", back_populates="thread", cascade="all, delete-orphan")


class Branch(Base):
    __tablename__ = "branches"
    id = Column(UUID(as_uuid=False), primary_key=True, default=uid)
    thread_id = Column(UUID(as_uuid=False), ForeignKey("threads.id", ondelete="CASCADE"), nullable=False)
    name = Column(String, nullable=False)
    base_message_id = Column(UUID(as_uuid=False), nullable=True)

    created_from_branch_id = Column(UUID(as_uuid=False), ForeignKey("branches.id"), nullable=True)
    created_from_message_id = Column(UUID(as_uuid=False), ForeignKey("messages.id", use_alter=True, name="fk_branch_created_from_message"), nullable=True)

    created_at = Column(DateTime, default=now, nullable=False)

    # relationships
    thread = relationship("Thread", back_populates="branches")

    # ↓↓↓ IMPORTANT: disambiguate using the correct FK
    messages = relationship(
        "Message",
        back_populates="branch",
        cascade="all, delete-orphan",
        foreign_keys="Message.branch_id",
    )

    # optional: self-reference to origin branch (for metadata only)
    created_from_branch = relationship(
        "Branch",
        remote_side=[id],
        foreign_keys=[created_from_branch_id],
        uselist=False,
        viewonly=True,
    )

    # optional: reference to the fork point message (metadata only)
    created_from_message = relationship(
        "Message",
        foreign_keys=[created_from_message_id],
        uselist=False,
        viewonly=True,
    )


class Message(Base):
    __tablename__ = "messages"
    id = Column(UUID(as_uuid=False), primary_key=True, default=uid)

    # ↓↓↓ FK to Branch (the one used by Branch.messages)
    branch_id = Column(UUID(as_uuid=False), ForeignKey("branches.id", ondelete="CASCADE"), nullable=False)

    # self-referential parent link
    parent_message_id = Column(UUID(as_uuid=False), ForeignKey("messages.id"), nullable=True)

    role = Column(String, nullable=False)
    content = Column(JSON, nullable=False)
    state_snapshot = Column(JSON, nullable=True)
    origin = Column(String, nullable=False, default="live")  # live | merge | import
    created_at = Column(DateTime, default=now, nullable=False)

    __table_args__ = (
        CheckConstraint("role IN ('user','assistant','system','tool')", name="ck_role"),
    )

    # relationships
    branch = relationship(
        "Branch",
        back_populates="messages",
        foreign_keys=[branch_id],
    )

    # optional: parent/children relationships for DAG traversal
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


class Merge(Base):
    __tablename__ = "merges"
    id = Column(UUID(as_uuid=False), primary_key=True, default=uid)
    thread_id = Column(UUID(as_uuid=False), ForeignKey("threads.id", ondelete="CASCADE"), nullable=False)
    source_branch_id = Column(UUID(as_uuid=False), ForeignKey("branches.id"), nullable=False)
    target_branch_id = Column(UUID(as_uuid=False), ForeignKey("branches.id"), nullable=False)
    strategy = Column(String, nullable=False)  # syntactic | semantic | hybrid
    lca_message_id = Column(UUID(as_uuid=False), ForeignKey("messages.id"), nullable=True)
    merged_into_message_id = Column(UUID(as_uuid=False), ForeignKey("messages.id"), nullable=True)
    summary = Column(JSON, nullable=True)
    created_at = Column(DateTime, default=now, nullable=False)
