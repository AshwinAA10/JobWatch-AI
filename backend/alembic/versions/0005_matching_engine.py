"""0005_matching_engine

Revision ID: 0005_matching_engine
Revises: 0004_user_profiles_auth
Create Date: 2026-09-29 07:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from app.models.base import GUID

# revision identifiers, used by Alembic.
revision: str = "0005_matching_engine"
down_revision: Union[str, None] = "0004_user_profiles_auth"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. job_requirements table
    op.create_table(
        "job_requirements",
        sa.Column("id", GUID(), nullable=False),
        sa.Column("job_id", GUID(), nullable=False),
        sa.Column("required_skills", sa.JSON(), nullable=False),
        sa.Column("preferred_skills", sa.JSON(), nullable=False),
        sa.Column("minimum_experience_years", sa.Float(), nullable=True),
        sa.Column("maximum_experience_years", sa.Float(), nullable=True),
        sa.Column("minimum_salary", sa.Integer(), nullable=True),
        sa.Column("maximum_salary", sa.Integer(), nullable=True),
        sa.Column("salary_currency", sa.String(length=3), nullable=True),
        sa.Column("required_education_level", sa.String(length=100), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["job_id"], ["jobs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("job_id", name="uq_job_requirements_job_id"),
    )
    op.create_index("ix_job_requirements_job_id", "job_requirements", ["job_id"], unique=True)

    # 2. job_matches table
    op.create_table(
        "job_matches",
        sa.Column("id", GUID(), nullable=False),
        sa.Column("user_id", GUID(), nullable=False),
        sa.Column("profile_id", GUID(), nullable=False),
        sa.Column("job_id", GUID(), nullable=False),
        sa.Column("score", sa.Float(), nullable=False),
        sa.Column("scoring_version", sa.String(length=32), nullable=False, server_default="v1"),
        sa.Column("breakdown", sa.JSON(), nullable=False),
        sa.Column("matched_criteria", sa.JSON(), nullable=False),
        sa.Column("missing_criteria", sa.JSON(), nullable=False),
        sa.Column("mismatches", sa.JSON(), nullable=False),
        sa.Column("reasons", sa.JSON(), nullable=False),
        sa.Column("calculated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["profile_id"], ["candidate_profiles.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["job_id"], ["jobs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("profile_id", "job_id", name="uq_job_matches_profile_job"),
    )
    op.create_index("ix_job_matches_user_id", "job_matches", ["user_id"], unique=False)
    op.create_index("ix_job_matches_profile_id", "job_matches", ["profile_id"], unique=False)
    op.create_index("ix_job_matches_job_id", "job_matches", ["job_id"], unique=False)
    op.create_index("ix_job_matches_score", "job_matches", ["score"], unique=False)
    op.create_index("ix_job_matches_calculated_at", "job_matches", ["calculated_at"], unique=False)
    op.create_index("ix_job_matches_profile_score", "job_matches", ["profile_id", "score"], unique=False)
    op.create_index("ix_job_matches_job_score", "job_matches", ["job_id", "score"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_job_matches_job_score", table_name="job_matches")
    op.drop_index("ix_job_matches_profile_score", table_name="job_matches")
    op.drop_index("ix_job_matches_calculated_at", table_name="job_matches")
    op.drop_index("ix_job_matches_score", table_name="job_matches")
    op.drop_index("ix_job_matches_job_id", table_name="job_matches")
    op.drop_index("ix_job_matches_profile_id", table_name="job_matches")
    op.drop_index("ix_job_matches_user_id", table_name="job_matches")
    op.drop_table("job_matches")

    op.drop_index("ix_job_requirements_job_id", table_name="job_requirements")
    op.drop_table("job_requirements")
