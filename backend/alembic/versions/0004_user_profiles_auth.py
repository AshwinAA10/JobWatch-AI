"""0004_user_profiles_auth

Revision ID: 0004_user_profiles_auth
Revises: 0003_job_deduplication
Create Date: 2026-09-26 22:30:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from app.models.base import GUID

# revision identifiers, used by Alembic.
revision: str = "0004_user_profiles_auth"
down_revision: Union[str, None] = "0003_job_deduplication"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. users table
    op.create_table(
        "users",
        sa.Column("id", GUID(), nullable=False),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("is_verified", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("last_login_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("email", name="uq_users_email"),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)
    op.create_index("ix_users_is_active", "users", ["is_active"], unique=False)

    # 2. candidate_profiles table
    op.create_table(
        "candidate_profiles",
        sa.Column("id", GUID(), nullable=False),
        sa.Column("user_id", GUID(), nullable=False),
        sa.Column("first_name", sa.String(length=100), nullable=True),
        sa.Column("last_name", sa.String(length=100), nullable=True),
        sa.Column("headline", sa.String(length=255), nullable=True),
        sa.Column("bio", sa.Text(), nullable=True),
        sa.Column("phone", sa.String(length=32), nullable=True),
        sa.Column("city", sa.String(length=100), nullable=True),
        sa.Column("state", sa.String(length=100), nullable=True),
        sa.Column("country", sa.String(length=100), nullable=True),
        sa.Column("years_of_experience", sa.Float(), nullable=True),
        sa.Column("current_job_title", sa.String(length=255), nullable=True),
        sa.Column("current_company", sa.String(length=255), nullable=True),
        sa.Column("highest_education_level", sa.String(length=100), nullable=True),
        sa.Column("profile_visibility", sa.String(length=32), nullable=False, server_default=sa.text("'PRIVATE'")),
        sa.Column("profile_completion_percent", sa.Integer(), nullable=False, server_default=sa.text("0")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["user_id"], ["users.id"], ondelete="CASCADE", name="fk_candidate_profiles_user_id"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("user_id", name="uq_candidate_profiles_user_id"),
    )
    op.create_index("ix_candidate_profiles_user_id", "candidate_profiles", ["user_id"], unique=True)

    # 3. skills table
    op.create_table(
        "skills",
        sa.Column("id", GUID(), nullable=False),
        sa.Column("name", sa.String(length=100), nullable=False),
        sa.Column("normalized_name", sa.String(length=100), nullable=False),
        sa.Column("category", sa.String(length=100), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("normalized_name", name="uq_skills_normalized_name"),
    )
    op.create_index("ix_skills_normalized_name", "skills", ["normalized_name"], unique=True)
    op.create_index("ix_skills_category", "skills", ["category"], unique=False)

    # 4. candidate_skills table
    op.create_table(
        "candidate_skills",
        sa.Column("id", GUID(), nullable=False),
        sa.Column("profile_id", GUID(), nullable=False),
        sa.Column("skill_id", GUID(), nullable=False),
        sa.Column("proficiency", sa.String(length=32), nullable=False, server_default=sa.text("'INTERMEDIATE'")),
        sa.Column("years_experience", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["profile_id"], ["candidate_profiles.id"], ondelete="CASCADE", name="fk_candidate_skills_profile_id"),
        sa.ForeignKeyConstraint(["skill_id"], ["skills.id"], ondelete="CASCADE", name="fk_candidate_skills_skill_id"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("profile_id", "skill_id", name="uq_candidate_skills_profile_skill"),
    )
    op.create_index("ix_candidate_skills_profile_id", "candidate_skills", ["profile_id"], unique=False)
    op.create_index("ix_candidate_skills_skill_id", "candidate_skills", ["skill_id"], unique=False)

    # 5. experiences table
    op.create_table(
        "experiences",
        sa.Column("id", GUID(), nullable=False),
        sa.Column("profile_id", GUID(), nullable=False),
        sa.Column("company_name", sa.String(length=255), nullable=False),
        sa.Column("job_title", sa.String(length=255), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("location", sa.String(length=255), nullable=True),
        sa.Column("employment_type", sa.String(length=64), nullable=True),
        sa.Column("start_date", sa.Date(), nullable=False),
        sa.Column("end_date", sa.Date(), nullable=True),
        sa.Column("is_current", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["profile_id"], ["candidate_profiles.id"], ondelete="CASCADE", name="fk_experiences_profile_id"),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint("end_date IS NULL OR end_date >= start_date", name="ck_experiences_valid_date_range"),
    )
    op.create_index("ix_experiences_profile_id", "experiences", ["profile_id"], unique=False)

    # 6. educations table
    op.create_table(
        "educations",
        sa.Column("id", GUID(), nullable=False),
        sa.Column("profile_id", GUID(), nullable=False),
        sa.Column("institution_name", sa.String(length=255), nullable=False),
        sa.Column("degree", sa.String(length=255), nullable=True),
        sa.Column("field_of_study", sa.String(length=255), nullable=True),
        sa.Column("location", sa.String(length=255), nullable=True),
        sa.Column("start_date", sa.Date(), nullable=True),
        sa.Column("end_date", sa.Date(), nullable=True),
        sa.Column("grade", sa.String(length=64), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["profile_id"], ["candidate_profiles.id"], ondelete="CASCADE", name="fk_educations_profile_id"),
        sa.PrimaryKeyConstraint("id"),
        sa.CheckConstraint("start_date IS NULL OR end_date IS NULL OR end_date >= start_date", name="ck_educations_valid_date_range"),
    )
    op.create_index("ix_educations_profile_id", "educations", ["profile_id"], unique=False)

    # 7. candidate_preferences table
    op.create_table(
        "candidate_preferences",
        sa.Column("id", GUID(), nullable=False),
        sa.Column("profile_id", GUID(), nullable=False),
        sa.Column("desired_titles", sa.JSON(), nullable=False),
        sa.Column("preferred_locations", sa.JSON(), nullable=False),
        sa.Column("workplace_types", sa.JSON(), nullable=False),
        sa.Column("employment_types", sa.JSON(), nullable=False),
        sa.Column("minimum_salary", sa.Integer(), nullable=True),
        sa.Column("maximum_salary", sa.Integer(), nullable=True),
        sa.Column("salary_currency", sa.String(length=3), nullable=False, server_default=sa.text("'USD'")),
        sa.Column("minimum_experience_years", sa.Integer(), nullable=True),
        sa.Column("maximum_experience_years", sa.Integer(), nullable=True),
        sa.Column("willing_to_relocate", sa.Boolean(), nullable=False, server_default=sa.text("false")),
        sa.Column("remote_preference", sa.String(length=32), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["profile_id"], ["candidate_profiles.id"], ondelete="CASCADE", name="fk_candidate_preferences_profile_id"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("profile_id", name="uq_candidate_preferences_profile_id"),
        sa.CheckConstraint("minimum_salary IS NULL OR maximum_salary IS NULL OR maximum_salary >= minimum_salary", name="ck_preferences_salary_range"),
        sa.CheckConstraint("minimum_experience_years IS NULL OR maximum_experience_years IS NULL OR maximum_experience_years >= minimum_experience_years", name="ck_preferences_experience_range"),
    )
    op.create_index("ix_candidate_preferences_profile_id", "candidate_preferences", ["profile_id"], unique=True)

    # 8. resumes table
    op.create_table(
        "resumes",
        sa.Column("id", GUID(), nullable=False),
        sa.Column("profile_id", GUID(), nullable=False),
        sa.Column("filename", sa.String(length=255), nullable=False),
        sa.Column("content_type", sa.String(length=100), nullable=False),
        sa.Column("storage_key", sa.String(length=512), nullable=False),
        sa.Column("file_size", sa.Integer(), nullable=False),
        sa.Column("uploaded_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["profile_id"], ["candidate_profiles.id"], ondelete="CASCADE", name="fk_resumes_profile_id"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_resumes_profile_id", "resumes", ["profile_id"], unique=False)


def downgrade() -> None:
    # Drop tables in reverse dependency order
    op.drop_index("ix_resumes_profile_id", table_name="resumes")
    op.drop_table("resumes")

    op.drop_index("ix_candidate_preferences_profile_id", table_name="candidate_preferences")
    op.drop_table("candidate_preferences")

    op.drop_index("ix_educations_profile_id", table_name="educations")
    op.drop_table("educations")

    op.drop_index("ix_experiences_profile_id", table_name="experiences")
    op.drop_table("experiences")

    op.drop_index("ix_candidate_skills_skill_id", table_name="candidate_skills")
    op.drop_index("ix_candidate_skills_profile_id", table_name="candidate_skills")
    op.drop_table("candidate_skills")

    op.drop_index("ix_skills_category", table_name="skills")
    op.drop_index("ix_skills_normalized_name", table_name="skills")
    op.drop_table("skills")

    op.drop_index("ix_candidate_profiles_user_id", table_name="candidate_profiles")
    op.drop_table("candidate_profiles")

    op.drop_index("ix_users_is_active", table_name="users")
    op.drop_index("ix_users_email", table_name="users")
    op.drop_table("users")
