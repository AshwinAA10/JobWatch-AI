"""0009_application_tracking

Revision ID: 0009_application_tracking
Revises: 0008_saved_jobs
Create Date: 2026-10-01 21:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from app.models.base import GUID

# revision identifiers, used by Alembic.
revision: str = "0009_application_tracking"
down_revision: Union[str, None] = "0008_saved_jobs"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. applications table
    op.create_table(
        "applications",
        sa.Column("id", GUID(), nullable=False),
        sa.Column("profile_id", GUID(), nullable=False),
        sa.Column("job_id", GUID(), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("applied_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("last_status_changed_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("company_name", sa.String(length=255), nullable=False),
        sa.Column("job_title", sa.String(length=512), nullable=False),
        sa.Column("job_location", sa.String(length=255), nullable=True),
        sa.Column("external_application_url", sa.String(length=2048), nullable=True),
        sa.Column("match_score_at_application", sa.Float(), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["profile_id"], ["candidate_profiles.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["job_id"], ["jobs.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("profile_id", "job_id", name="uq_applications_profile_job"),
    )
    op.create_index(op.f("ix_applications_profile_id"), "applications", ["profile_id"], unique=False)
    op.create_index(op.f("ix_applications_job_id"), "applications", ["job_id"], unique=False)
    op.create_index(op.f("ix_applications_status"), "applications", ["status"], unique=False)
    op.create_index(op.f("ix_applications_applied_at"), "applications", ["applied_at"], unique=False)
    op.create_index(op.f("ix_applications_last_status_changed_at"), "applications", ["last_status_changed_at"], unique=False)

    # 2. application_history table
    op.create_table(
        "application_history",
        sa.Column("id", GUID(), nullable=False),
        sa.Column("application_id", GUID(), nullable=False),
        sa.Column("old_status", sa.String(length=32), nullable=True),
        sa.Column("new_status", sa.String(length=32), nullable=False),
        sa.Column("changed_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("note", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["application_id"], ["applications.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_application_history_application_id"), "application_history", ["application_id"], unique=False)
    op.create_index(op.f("ix_application_history_changed_at"), "application_history", ["changed_at"], unique=False)

    # 3. application_notes table
    op.create_table(
        "application_notes",
        sa.Column("id", GUID(), nullable=False),
        sa.Column("application_id", GUID(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["application_id"], ["applications.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_application_notes_application_id"), "application_notes", ["application_id"], unique=False)

    # 4. interviews table
    op.create_table(
        "interviews",
        sa.Column("id", GUID(), nullable=False),
        sa.Column("application_id", GUID(), nullable=False),
        sa.Column("interview_type", sa.String(length=32), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("scheduled_at", sa.DateTime(timezone=True), nullable=False),
        sa.Column("duration_minutes", sa.Integer(), nullable=True),
        sa.Column("interviewer_names", sa.String(length=255), nullable=True),
        sa.Column("location", sa.String(length=255), nullable=True),
        sa.Column("meeting_url", sa.String(length=2048), nullable=True),
        sa.Column("notes", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.text("now()"), nullable=False),
        sa.ForeignKeyConstraint(["application_id"], ["applications.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(op.f("ix_interviews_application_id"), "interviews", ["application_id"], unique=False)
    op.create_index(op.f("ix_interviews_scheduled_at"), "interviews", ["scheduled_at"], unique=False)
    op.create_index(op.f("ix_interviews_status"), "interviews", ["status"], unique=False)


def downgrade() -> None:
    op.drop_index(op.f("ix_interviews_status"), table_name="interviews")
    op.drop_index(op.f("ix_interviews_scheduled_at"), table_name="interviews")
    op.drop_index(op.f("ix_interviews_application_id"), table_name="interviews")
    op.drop_table("interviews")

    op.drop_index(op.f("ix_application_notes_application_id"), table_name="application_notes")
    op.drop_table("application_notes")

    op.drop_index(op.f("ix_application_history_changed_at"), table_name="application_history")
    op.drop_index(op.f("ix_application_history_application_id"), table_name="application_history")
    op.drop_table("application_history")

    op.drop_index(op.f("ix_applications_last_status_changed_at"), table_name="applications")
    op.drop_index(op.f("ix_applications_applied_at"), table_name="applications")
    op.drop_index(op.f("ix_applications_status"), table_name="applications")
    op.drop_index(op.f("ix_applications_job_id"), table_name="applications")
    op.drop_index(op.f("ix_applications_profile_id"), table_name="applications")
    op.drop_table("applications")
