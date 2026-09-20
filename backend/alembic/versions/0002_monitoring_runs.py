"""0002_monitoring_runs

Revision ID: 0002_monitoring_runs
Revises: 0001_initial_schema
Create Date: 2026-09-20 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from app.models.base import GUID

# revision identifiers, used by Alembic.
revision: str = "0002_monitoring_runs"
down_revision: Union[str, None] = "0001_initial_schema"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    op.create_table(
        "monitoring_runs",
        sa.Column("id", GUID(), nullable=False),
        sa.Column("career_source_id", GUID(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default=sa.text("'PENDING'")),
        sa.Column("trigger_type", sa.String(length=32), nullable=False, server_default=sa.text("'SCHEDULED'")),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("jobs_fetched", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("jobs_created", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("jobs_updated", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("jobs_skipped", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("error_count", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("attempt", sa.Integer(), nullable=False, server_default=sa.text("1")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["career_source_id"], ["career_sources.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_monitoring_runs_career_source_id", "monitoring_runs", ["career_source_id"], unique=False)
    op.create_index("ix_monitoring_runs_status", "monitoring_runs", ["status"], unique=False)
    op.create_index("ix_monitoring_runs_created_at", "monitoring_runs", ["created_at"], unique=False)
    op.create_index("ix_monitoring_runs_source_started", "monitoring_runs", ["career_source_id", "started_at"], unique=False)


def downgrade() -> None:
    op.drop_table("monitoring_runs")
