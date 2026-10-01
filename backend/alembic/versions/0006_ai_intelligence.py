"""0006_ai_intelligence

Revision ID: 0006_ai_intelligence
Revises: 0005_matching_engine
Create Date: 2026-10-01 07:00:00.000000

"""
from typing import Sequence, Union

from alembic import op
import sqlalchemy as sa
from pgvector.sqlalchemy import Vector
from app.models.base import GUID

# revision identifiers, used by Alembic.
revision: str = "0006_ai_intelligence"
down_revision: Union[str, None] = "0005_matching_engine"
branch_labels: Union[str, Sequence[str], None] = None
depends_on: Union[str, Sequence[str], None] = None


def upgrade() -> None:
    # 0. Enable pgvector extension on PostgreSQL
    bind = op.get_bind()
    if bind and bind.dialect.name == "postgresql":
        op.execute(sa.text("CREATE EXTENSION IF NOT EXISTS vector;"))

    # 1. ai_job_extractions table
    op.create_table(
        "ai_job_extractions",
        sa.Column("id", GUID(), nullable=False),
        sa.Column("job_id", GUID(), nullable=False),
        sa.Column("input_hash", sa.String(length=64), nullable=False),
        sa.Column("model", sa.String(length=64), nullable=False),
        sa.Column("prompt_version", sa.String(length=32), nullable=False, server_default="v1"),
        sa.Column("extraction_version", sa.String(length=32), nullable=False, server_default="v1"),
        sa.Column("structured_requirements", sa.JSON(), nullable=False),
        sa.Column("is_success", sa.Boolean(), nullable=False, server_default=sa.text("true")),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("tokens_used", sa.Integer(), nullable=True),
        sa.Column("duration_ms", sa.Float(), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["job_id"], ["jobs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "job_id",
            "input_hash",
            "model",
            "prompt_version",
            name="uq_ai_job_extractions_cache",
        ),
    )
    op.create_index("ix_ai_job_extractions_job_id", "ai_job_extractions", ["job_id"], unique=False)
    op.create_index("ix_ai_job_extractions_input_hash", "ai_job_extractions", ["input_hash"], unique=False)

    # 2. job_embeddings table
    op.create_table(
        "job_embeddings",
        sa.Column("id", GUID(), nullable=False),
        sa.Column("job_id", GUID(), nullable=False),
        sa.Column("content_hash", sa.String(length=64), nullable=False),
        sa.Column("model", sa.String(length=64), nullable=False),
        sa.Column("dimensions", sa.Integer(), nullable=False, server_default="1536"),
        sa.Column("embedding_version", sa.String(length=32), nullable=False, server_default="v1"),
        sa.Column("embedding", Vector(1536), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["job_id"], ["jobs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "job_id",
            "content_hash",
            "model",
            "embedding_version",
            name="uq_job_embeddings_cache",
        ),
    )
    op.create_index("ix_job_embeddings_job_id", "job_embeddings", ["job_id"], unique=False)
    op.create_index("ix_job_embeddings_content_hash", "job_embeddings", ["content_hash"], unique=False)

    # 3. candidate_embeddings table
    op.create_table(
        "candidate_embeddings",
        sa.Column("id", GUID(), nullable=False),
        sa.Column("profile_id", GUID(), nullable=False),
        sa.Column("content_hash", sa.String(length=64), nullable=False),
        sa.Column("model", sa.String(length=64), nullable=False),
        sa.Column("dimensions", sa.Integer(), nullable=False, server_default="1536"),
        sa.Column("embedding_version", sa.String(length=32), nullable=False, server_default="v1"),
        sa.Column("embedding", Vector(1536), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["profile_id"], ["candidate_profiles.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "profile_id",
            "content_hash",
            "model",
            "embedding_version",
            name="uq_candidate_embeddings_cache",
        ),
    )
    op.create_index("ix_candidate_embeddings_profile_id", "candidate_embeddings", ["profile_id"], unique=False)
    op.create_index("ix_candidate_embeddings_content_hash", "candidate_embeddings", ["content_hash"], unique=False)

    # 4. ai_explanations table
    op.create_table(
        "ai_explanations",
        sa.Column("id", GUID(), nullable=False),
        sa.Column("profile_id", GUID(), nullable=False),
        sa.Column("job_id", GUID(), nullable=False),
        sa.Column("input_hash", sa.String(length=64), nullable=False),
        sa.Column("model", sa.String(length=64), nullable=False),
        sa.Column("prompt_version", sa.String(length=32), nullable=False, server_default="v1"),
        sa.Column("explanation_version", sa.String(length=32), nullable=False, server_default="v1"),
        sa.Column("summary", sa.Text(), nullable=False),
        sa.Column("strengths", sa.JSON(), nullable=False),
        sa.Column("gaps", sa.JSON(), nullable=False),
        sa.Column("recommendation", sa.Text(), nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["profile_id"], ["candidate_profiles.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["job_id"], ["jobs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint(
            "profile_id",
            "job_id",
            "input_hash",
            "model",
            "prompt_version",
            name="uq_ai_explanations_cache",
        ),
    )
    op.create_index("ix_ai_explanations_profile_id", "ai_explanations", ["profile_id"], unique=False)
    op.create_index("ix_ai_explanations_job_id", "ai_explanations", ["job_id"], unique=False)
    op.create_index("ix_ai_explanations_input_hash", "ai_explanations", ["input_hash"], unique=False)


def downgrade() -> None:
    op.drop_index("ix_ai_explanations_input_hash", table_name="ai_explanations")
    op.drop_index("ix_ai_explanations_job_id", table_name="ai_explanations")
    op.drop_index("ix_ai_explanations_profile_id", table_name="ai_explanations")
    op.drop_table("ai_explanations")

    op.drop_index("ix_candidate_embeddings_content_hash", table_name="candidate_embeddings")
    op.drop_index("ix_candidate_embeddings_profile_id", table_name="candidate_embeddings")
    op.drop_table("candidate_embeddings")

    op.drop_index("ix_job_embeddings_content_hash", table_name="job_embeddings")
    op.drop_index("ix_job_embeddings_job_id", table_name="job_embeddings")
    op.drop_table("job_embeddings")

    op.drop_index("ix_ai_job_extractions_input_hash", table_name="ai_job_extractions")
    op.drop_index("ix_ai_job_extractions_job_id", table_name="ai_job_extractions")
    op.drop_table("ai_job_extractions")
