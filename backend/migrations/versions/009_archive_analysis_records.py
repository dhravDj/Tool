"""Add archive_analysis_records, archive_entry_records, and archive_relationship_records tables

Revision ID: 009_archive_analysis_records
Revises: 008_code_structured_data_records
Create Date: 2026-11-06 22:30:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "009_archive_analysis_records"
down_revision: str | None = "008_code_structured_data_records"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    json_variant = sa.JSON().with_variant(postgresql.JSONB, "postgresql")

    # 1. archive_analysis_records
    op.create_table(
        "archive_analysis_records",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("file_id", sa.Uuid(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="completed"),
        sa.Column("archive_format", sa.String(length=32), nullable=False),
        sa.Column("processing_mode", sa.String(length=32), nullable=False, server_default="inspect_only"),
        sa.Column("entry_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("file_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("directory_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("nested_archive_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_uncompressed_size", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("extracted_size", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("compression_ratio", sa.Float(), nullable=False, server_default="1.0"),
        sa.Column("nesting_depth", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("is_encrypted", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("is_corrupted", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("archive_comment", sa.Text(), nullable=True),
        sa.Column("model_name", sa.String(length=64), nullable=False, server_default="documind-archive-v1"),
        sa.Column("engine_name", sa.String(length=64), nullable=False, server_default="documind-archive"),
        sa.Column("confidence", sa.Float(), nullable=False, server_default="1.0"),
        sa.Column("processing_duration", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("safety_report", json_variant, nullable=False, server_default="{}"),
        sa.Column("artifacts", json_variant, nullable=False, server_default="{}"),
        sa.Column("archive_metadata", json_variant, nullable=False, server_default="{}"),
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
        op.f("ix_archive_analysis_records_file_id"),
        "archive_analysis_records",
        ["file_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_archive_analysis_records_status"),
        "archive_analysis_records",
        ["status"],
        unique=False,
    )
    op.create_index(
        op.f("ix_archive_analysis_records_archive_format"),
        "archive_analysis_records",
        ["archive_format"],
        unique=False,
    )

    # 2. archive_entry_records
    op.create_table(
        "archive_entry_records",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("archive_analysis_id", sa.Uuid(), nullable=False),
        sa.Column("entry_id", sa.String(length=128), nullable=False),
        sa.Column("original_path", sa.Text(), nullable=False),
        sa.Column("normalized_path", sa.Text(), nullable=False),
        sa.Column("filename", sa.String(length=512), nullable=False),
        sa.Column("extension", sa.String(length=64), nullable=False, server_default=""),
        sa.Column("entry_type", sa.String(length=32), nullable=False, server_default="file"),
        sa.Column("compressed_size", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("uncompressed_size", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("compression_method", sa.String(length=64), nullable=False, server_default=""),
        sa.Column("checksum", sa.String(length=64), nullable=True),
        sa.Column("encrypted", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("is_directory", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("is_symlink", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("is_nested_archive", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("detection_result", json_variant, nullable=False, server_default="{}"),
        sa.Column("extracted_file_id", sa.Uuid(), nullable=True),
        sa.Column("processing_status", sa.String(length=32), nullable=False, server_default="inspected"),
        sa.Column("error", sa.Text(), nullable=True),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["archive_analysis_id"], ["archive_analysis_records.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["extracted_file_id"], ["files.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_archive_entry_records_archive_analysis_id"),
        "archive_entry_records",
        ["archive_analysis_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_archive_entry_records_entry_id"),
        "archive_entry_records",
        ["entry_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_archive_entry_records_extracted_file_id"),
        "archive_entry_records",
        ["extracted_file_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_archive_entry_records_processing_status"),
        "archive_entry_records",
        ["processing_status"],
        unique=False,
    )

    # 3. archive_relationship_records
    op.create_table(
        "archive_relationship_records",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("parent_file_id", sa.Uuid(), nullable=False),
        sa.Column("parent_archive_id", sa.Uuid(), nullable=False),
        sa.Column("parent_entry_id", sa.String(length=128), nullable=False),
        sa.Column("child_file_id", sa.Uuid(), nullable=False),
        sa.Column("root_archive_id", sa.Uuid(), nullable=False),
        sa.Column("nesting_depth", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("original_path", sa.Text(), nullable=False),
        sa.Column("extracted_storage_reference", sa.Text(), nullable=True),
        sa.Column("sha256", sa.String(length=64), nullable=True),
        sa.Column("detection_result", json_variant, nullable=False, server_default="{}"),
        sa.Column("processing_status", sa.String(length=32), nullable=False, server_default="extracted"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["parent_file_id"], ["files.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["parent_archive_id"], ["archive_analysis_records.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["child_file_id"], ["files.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["root_archive_id"], ["archive_analysis_records.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index(
        op.f("ix_archive_relationship_records_parent_file_id"),
        "archive_relationship_records",
        ["parent_file_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_archive_relationship_records_parent_archive_id"),
        "archive_relationship_records",
        ["parent_archive_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_archive_relationship_records_child_file_id"),
        "archive_relationship_records",
        ["child_file_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_archive_relationship_records_root_archive_id"),
        "archive_relationship_records",
        ["root_archive_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_archive_relationship_records_sha256"),
        "archive_relationship_records",
        ["sha256"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_archive_relationship_records_sha256"), table_name="archive_relationship_records")
    op.drop_index(op.f("ix_archive_relationship_records_root_archive_id"), table_name="archive_relationship_records")
    op.drop_index(op.f("ix_archive_relationship_records_child_file_id"), table_name="archive_relationship_records")
    op.drop_index(op.f("ix_archive_relationship_records_parent_archive_id"), table_name="archive_relationship_records")
    op.drop_index(op.f("ix_archive_relationship_records_parent_file_id"), table_name="archive_relationship_records")
    op.drop_table("archive_relationship_records")

    op.drop_index(op.f("ix_archive_entry_records_processing_status"), table_name="archive_entry_records")
    op.drop_index(op.f("ix_archive_entry_records_extracted_file_id"), table_name="archive_entry_records")
    op.drop_index(op.f("ix_archive_entry_records_entry_id"), table_name="archive_entry_records")
    op.drop_index(op.f("ix_archive_entry_records_archive_analysis_id"), table_name="archive_entry_records")
    op.drop_table("archive_entry_records")

    op.drop_index(op.f("ix_archive_analysis_records_archive_format"), table_name="archive_analysis_records")
    op.drop_index(op.f("ix_archive_analysis_records_status"), table_name="archive_analysis_records")
    op.drop_index(op.f("ix_archive_analysis_records_file_id"), table_name="archive_analysis_records")
    op.drop_table("archive_analysis_records")
