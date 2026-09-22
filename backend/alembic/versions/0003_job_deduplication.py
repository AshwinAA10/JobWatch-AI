"""0003_job_deduplication

Revision ID: 0003_job_deduplication
Revises: 0002_monitoring_runs
Create Date: 2026-09-22 14:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from app.models.base import GUID

# revision identifiers, used by Alembic.
revision: str = "0003_job_deduplication"
down_revision: Union[str, None] = "0002_monitoring_runs"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Add canonical_job_id and self-canonical check constraint to jobs table
    op.add_column("jobs", sa.Column("canonical_job_id", GUID(), nullable=True))
    op.create_index("ix_jobs_canonical_job_id", "jobs", ["canonical_job_id"], unique=False)
    op.create_foreign_key(
        "fk_jobs_canonical_job_id",
        "jobs",
        "jobs",
        ["canonical_job_id"],
        ["id"],
        ondelete="SET NULL",
    )
    op.create_check_constraint(
        "ck_jobs_no_self_canonical",
        "jobs",
        "canonical_job_id != id",
    )

    # 2. Create job_duplicates relationship table
    op.create_table(
        "job_duplicates",
        sa.Column("id", GUID(), nullable=False),
        sa.Column("canonical_job_id", GUID(), nullable=False),
        sa.Column("duplicate_job_id", GUID(), nullable=False),
        sa.Column("match_type", sa.String(length=64), nullable=False, server_default=sa.text("'HIGH_CONFIDENCE'")),
        sa.Column("confidence_score", sa.Float(), nullable=False, server_default=sa.text("1.0")),
        sa.Column("matched_fields", sa.JSON(), nullable=True),
        sa.Column("reason", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["canonical_job_id"], ["jobs.id"], ondelete="CASCADE", name="fk_job_duplicates_canonical_job"),
        sa.ForeignKeyConstraint(["duplicate_job_id"], ["jobs.id"], ondelete="CASCADE", name="fk_job_duplicates_duplicate_job"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("duplicate_job_id", name="uq_job_duplicates_duplicate_job_id"),
        sa.CheckConstraint("canonical_job_id != duplicate_job_id", name="ck_job_duplicates_no_self_duplicate"),
    )
    op.create_index("ix_job_duplicates_canonical_job_id", "job_duplicates", ["canonical_job_id"], unique=False)
    op.create_index("ix_job_duplicates_duplicate_job_id", "job_duplicates", ["duplicate_job_id"], unique=False)


def downgrade() -> None:
    # 1. Drop job_duplicates table
    op.drop_index("ix_job_duplicates_duplicate_job_id", table_name="job_duplicates")
    op.drop_index("ix_job_duplicates_canonical_job_id", table_name="job_duplicates")
    op.drop_table("job_duplicates")

    # 2. Remove canonical_job_id and constraints from jobs table
    op.drop_constraint("ck_jobs_no_self_canonical", "jobs", type_="check")
    op.drop_constraint("fk_jobs_canonical_job_id", "jobs", type_="foreignkey")
    op.drop_index("ix_jobs_canonical_job_id", table_name="jobs")
    op.drop_column("jobs", "canonical_job_id")
