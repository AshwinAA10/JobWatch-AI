"""0001_initial_schema

Revision ID: 0001_initial_schema
Revises: 
Create Date: 2026-09-17 12:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from app.models.base import GUID

# revision identifiers, used by Alembic.
revision: str = "0001_initial_schema"
down_revision: Union[str, None] = None
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 1. Create companies table
    op.create_table(
        "companies",
        sa.Column("id", GUID(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("slug", sa.String(length=255), nullable=False),
        sa.Column("website_url", sa.String(length=2048), nullable=True),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_companies_slug", "companies", ["slug"], unique=True)
    op.create_index("ix_companies_is_active", "companies", ["is_active"], unique=False)

    # 2. Create career_sources table
    op.create_table(
        "career_sources",
        sa.Column("id", GUID(), nullable=False),
        sa.Column("company_id", GUID(), nullable=False),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("source_type", sa.String(length=64), nullable=False),
        sa.Column("base_url", sa.String(length=2048), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_career_sources_company_id", "career_sources", ["company_id"], unique=False)
    op.create_index("ix_career_sources_source_type", "career_sources", ["source_type"], unique=False)
    op.create_index("ix_career_sources_is_active", "career_sources", ["is_active"], unique=False)

    # 3. Create jobs table
    op.create_table(
        "jobs",
        sa.Column("id", GUID(), nullable=False),
        sa.Column("company_id", GUID(), nullable=False),
        sa.Column("career_source_id", GUID(), nullable=False),
        sa.Column("external_id", sa.String(length=255), nullable=True),
        sa.Column("title", sa.String(length=512), nullable=False),
        sa.Column("description", sa.Text(), nullable=True),
        sa.Column("location", sa.String(length=255), nullable=True),
        sa.Column("employment_type", sa.String(length=64), nullable=True),
        sa.Column("workplace_type", sa.String(length=64), nullable=True),
        sa.Column("application_url", sa.String(length=2048), nullable=True),
        sa.Column("source_url", sa.String(length=2048), nullable=True),
        sa.Column("posted_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("first_seen_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("last_seen_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("is_active", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["company_id"], ["companies.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["career_source_id"], ["career_sources.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("career_source_id", "external_id", name="uq_jobs_source_external_id"),
    )
    op.create_index("ix_jobs_company_id", "jobs", ["company_id"], unique=False)
    op.create_index("ix_jobs_career_source_id", "jobs", ["career_source_id"], unique=False)
    op.create_index("ix_jobs_external_id", "jobs", ["external_id"], unique=False)
    op.create_index("ix_jobs_is_active", "jobs", ["is_active"], unique=False)
    op.create_index("ix_jobs_posted_at", "jobs", ["posted_at"], unique=False)
    op.create_index("ix_jobs_first_seen_at", "jobs", ["first_seen_at"], unique=False)
    op.create_index("ix_jobs_company_active", "jobs", ["company_id", "is_active"], unique=False)


def downgrade() -> None:
    op.drop_table("jobs")
    op.drop_table("career_sources")
    op.drop_table("companies")
