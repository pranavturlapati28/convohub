"""init tables

Revision ID: 3805d87542bd
Revises:
Create Date: 2025-08-12 20:47:41.854236
"""
from typing import Sequence, Union
from alembic import op
import sqlalchemy as sa

# revision identifiers, used by Alembic.
revision: str = "3805d87542bd"
down_revision: Union[str, Sequence[str], None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1) threads
    op.create_table(
        "threads",
        sa.Column("id", sa.UUID(as_uuid=False), primary_key=True),
        sa.Column("owner_id", sa.UUID(as_uuid=False), nullable=False),
        sa.Column("title", sa.String(), nullable=False),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )

    # 2) branches (DEFER the FK to messages for created_from_message_id)
    op.create_table(
        "branches",
        sa.Column("id", sa.UUID(as_uuid=False), primary_key=True),
        sa.Column(
            "thread_id",
            sa.UUID(as_uuid=False),
            sa.ForeignKey("threads.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("name", sa.String(), nullable=False),
        sa.Column("base_message_id", sa.UUID(as_uuid=False), nullable=True),
        sa.Column(
            "created_from_branch_id",
            sa.UUID(as_uuid=False),
            sa.ForeignKey("branches.id"),
            nullable=True,
        ),
        sa.Column("created_from_message_id", sa.UUID(as_uuid=False), nullable=True),  # FK later
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )
    op.create_unique_constraint(
        "uq_branch_name_per_thread", "branches", ["thread_id", "name"]
    )

    # 3) messages
    op.create_table(
        "messages",
        sa.Column("id", sa.UUID(as_uuid=False), primary_key=True),
        sa.Column(
            "branch_id",
            sa.UUID(as_uuid=False),
            sa.ForeignKey("branches.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "parent_message_id",
            sa.UUID(as_uuid=False),
            sa.ForeignKey("messages.id"),
            nullable=True,
        ),
        sa.Column("role", sa.String(), nullable=False),
        sa.Column("content", sa.JSON(), nullable=False),
        sa.Column("state_snapshot", sa.JSON(), nullable=True),
        sa.Column("origin", sa.String(), nullable=False, server_default="live"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.CheckConstraint(
            "role IN ('user','assistant','system','tool')", name="ck_role"
        ),
    )

    # 4) NOW add the FK from branches.created_from_message_id -> messages.id
    op.create_foreign_key(
        "fk_branches_created_from_message",
        "branches",
        "messages",
        ["created_from_message_id"],
        ["id"],
    )

    # 5) merges
    op.create_table(
        "merges",
        sa.Column("id", sa.UUID(as_uuid=False), primary_key=True),
        sa.Column(
            "thread_id",
            sa.UUID(as_uuid=False),
            sa.ForeignKey("threads.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "source_branch_id", sa.UUID(as_uuid=False), sa.ForeignKey("branches.id"), nullable=False
        ),
        sa.Column(
            "target_branch_id", sa.UUID(as_uuid=False), sa.ForeignKey("branches.id"), nullable=False
        ),
        sa.Column("strategy", sa.String(), nullable=False),
        sa.Column(
            "lca_message_id",
            sa.UUID(as_uuid=False),
            sa.ForeignKey("messages.id"),
            nullable=True,
        ),
        sa.Column(
            "merged_into_message_id",
            sa.UUID(as_uuid=False),
            sa.ForeignKey("messages.id"),
            nullable=True,
        ),
        sa.Column("summary", sa.JSON(), nullable=True),
        sa.Column("created_at", sa.DateTime(), nullable=False),
    )


def downgrade() -> None:
    op.drop_table("merges")
    op.drop_constraint(
        "fk_branches_created_from_message", "branches", type_="foreignkey"
    )
    op.drop_table("messages")
    op.drop_constraint(
        "uq_branch_name_per_thread", "branches", type_="unique"
    )
    op.drop_table("branches")
    op.drop_table("threads")




