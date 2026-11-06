"""Add code_analysis_records and structured_data_analysis_records tables

Revision ID: 008_code_structured_data_records
Revises: 007_video_analysis_records
Create Date: 2026-11-06 21:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "008_code_structured_data_records"
down_revision: str | None = "007_video_analysis_records"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    json_variant = sa.JSON().with_variant(postgresql.JSONB, "postgresql")

    # 1. code_analysis_records
    op.create_table(
        "code_analysis_records",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("file_id", sa.Uuid(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="completed"),
        sa.Column("language", sa.String(length=32), nullable=False),
        sa.Column("total_lines", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("code_lines", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("comment_lines", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("blank_lines", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("symbol_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("function_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("class_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("import_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("diagnostic_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("has_syntax_errors", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("cyclomatic_complexity", sa.Float(), nullable=False, server_default="1.0"),
        sa.Column("model_name", sa.String(length=64), nullable=False, server_default="documind-code-v1"),
        sa.Column("engine_name", sa.String(length=64), nullable=False, server_default="documind-code"),
        sa.Column("confidence", sa.Float(), nullable=False, server_default="1.0"),
        sa.Column("processing_duration", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("artifacts", json_variant, nullable=False, server_default="{}"),
        sa.Column("code_metadata", json_variant, nullable=False, server_default="{}"),
        sa.Column("warnings", json_variant, nullable=False, server_default="[]"),
        sa.Column("error_details", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["file_id"], ["files.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_code_analysis_records_file_id"),
        "code_analysis_records",
        ["file_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_code_analysis_records_status"),
        "code_analysis_records",
        ["status"],
        unique=False,
    )
    op.create_index(
        op.f("ix_code_analysis_records_language"),
        "code_analysis_records",
        ["language"],
        unique=False,
    )

    # 2. structured_data_analysis_records
    op.create_table(
        "structured_data_analysis_records",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("file_id", sa.Uuid(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="completed"),
        sa.Column("format", sa.String(length=32), nullable=False),
        sa.Column("root_type", sa.String(length=32), nullable=False, server_default="object"),
        sa.Column("record_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("field_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("max_depth", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("is_valid", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("compression", sa.String(length=32), nullable=False, server_default="none"),
        sa.Column("model_name", sa.String(length=64), nullable=False, server_default="documind-structured-v1"),
        sa.Column("engine_name", sa.String(length=64), nullable=False, server_default="documind-structured"),
        sa.Column("confidence", sa.Float(), nullable=False, server_default="1.0"),
        sa.Column("processing_duration", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("artifacts", json_variant, nullable=False, server_default="{}"),
        sa.Column("schema_definition", json_variant, nullable=False, server_default="{}"),
        sa.Column("profile_data", json_variant, nullable=False, server_default="{}"),
        sa.Column("warnings", json_variant, nullable=False, server_default="[]"),
        sa.Column("error_details", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["file_id"], ["files.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_structured_data_analysis_records_file_id"),
        "structured_data_analysis_records",
        ["file_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_structured_data_analysis_records_status"),
        "structured_data_analysis_records",
        ["status"],
        unique=False,
    )
    op.create_index(
        op.f("ix_structured_data_analysis_records_format"),
        "structured_data_analysis_records",
        ["format"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_structured_data_analysis_records_format"), table_name="structured_data_analysis_records")
    op.drop_index(op.f("ix_structured_data_analysis_records_status"), table_name="structured_data_analysis_records")
    op.drop_index(op.f("ix_structured_data_analysis_records_file_id"), table_name="structured_data_analysis_records")
    op.drop_table("structured_data_analysis_records")

    op.drop_index(op.f("ix_code_analysis_records_language"), table_name="code_analysis_records")
    op.drop_index(op.f("ix_code_analysis_records_status"), table_name="code_analysis_records")
    op.drop_index(op.f("ix_code_analysis_records_file_id"), table_name="code_analysis_records")
    op.drop_table("code_analysis_records")
