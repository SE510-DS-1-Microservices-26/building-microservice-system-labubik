"""create workflow_instances table

Revision ID: 0001
Revises:
Create Date: 2025-01-01 00:00:00.000000
"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from sqlalchemy.dialects import postgresql

revision: str = "0001"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.execute(
        """
        DO $$ BEGIN
            CREATE TYPE workflowstate AS ENUM (
                'started',
                'order_created',
                'order_confirmed',
                'completed',
                'compensating',
                'cancelled',
                'failed'
            );
        EXCEPTION
            WHEN duplicate_object THEN null;
        END $$;
        """
    )
    op.create_table(
        "workflow_instances",
        sa.Column("workflow_id", postgresql.UUID(as_uuid=True), primary_key=True),
        sa.Column("type", sa.String(), nullable=False),
        sa.Column(
            "state",
            postgresql.ENUM(
                "started",
                "order_created",
                "order_confirmed",
                "completed",
                "compensating",
                "cancelled",
                "failed",
                name="workflowstate",
                create_type=False,
            ),
            nullable=False,
        ),
        sa.Column("payload", sa.Text(), nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(), nullable=False),
        sa.Column("updated_at", sa.DateTime(), nullable=False),
        sa.Column("last_error", sa.Text(), nullable=True),
    )


def downgrade() -> None:
    op.drop_table("workflow_instances")
    op.execute("DROP TYPE workflowstate")