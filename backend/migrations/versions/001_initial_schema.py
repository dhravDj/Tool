"""Initial schema for DocuMind AI

Revision ID: 001_initial_schema
Revises: None
Create Date: 2026-11-06 00:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "001_initial_schema"
down_revision: str | None = None
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    # 1. users table
    op.create_table(
        "users",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column("email", sa.String(length=255), nullable=False),
        sa.Column("password_hash", sa.String(length=255), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_index("ix_users_email", "users", ["email"], unique=True)

    # 2. files table
    op.create_table(
        "files",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column(
            "owner_id",
            sa.Uuid(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("original_filename", sa.String(length=255), nullable=False),
        sa.Column("stored_filename", sa.String(length=255), nullable=False),
        sa.Column("extension", sa.String(length=32), nullable=False),
        sa.Column("detected_mime_type", sa.String(length=128), nullable=True),
        sa.Column("file_size", sa.BigInteger(), nullable=False),
        sa.Column("sha256", sa.String(length=64), nullable=False),
        sa.Column("storage_path", sa.String(length=512), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_index("ix_files_owner_id", "files", ["owner_id"])
    op.create_index("ix_files_extension", "files", ["extension"])
    op.create_index("ix_files_detected_mime_type", "files", ["detected_mime_type"])
    op.create_index("ix_files_sha256", "files", ["sha256"])
    op.create_index("ix_files_status", "files", ["status"])
    op.create_index("ix_files_owner_status", "files", ["owner_id", "status"])
    op.create_index("ix_files_sha256_size", "files", ["sha256", "file_size"])

    # 3. batches table
    op.create_table(
        "batches",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column(
            "owner_id",
            sa.Uuid(as_uuid=True),
            sa.ForeignKey("users.id", ondelete="SET NULL"),
            nullable=True,
        ),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("total_files", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("queued_files", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("processing_files", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("completed_files", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("failed_files", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("cancelled_files", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_index("ix_batches_owner_id", "batches", ["owner_id"])
    op.create_index("ix_batches_status", "batches", ["status"])
    op.create_index("ix_batches_owner_status", "batches", ["owner_id", "status"])

    # 4. document_jobs table
    op.create_table(
        "document_jobs",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column(
            "batch_id",
            sa.Uuid(as_uuid=True),
            sa.ForeignKey("batches.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column(
            "file_id",
            sa.Uuid(as_uuid=True),
            sa.ForeignKey("files.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("status", sa.String(length=32), nullable=False),
        sa.Column("retry_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("error_code", sa.String(length=64), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_index("ix_document_jobs_batch_id", "document_jobs", ["batch_id"])
    op.create_index("ix_document_jobs_file_id", "document_jobs", ["file_id"])
    op.create_index("ix_document_jobs_status", "document_jobs", ["status"])
    op.create_index("ix_document_jobs_batch_status", "document_jobs", ["batch_id", "status"])
    op.create_index("ix_document_jobs_file_status", "document_jobs", ["file_id", "status"])

    # 5. extraction_records table
    json_variant = sa.JSON().with_variant(postgresql.JSONB, "postgresql")
    op.create_table(
        "extraction_records",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column(
            "file_id",
            sa.Uuid(as_uuid=True),
            sa.ForeignKey("files.id", ondelete="CASCADE"),
            nullable=False,
        ),
        sa.Column("engine", sa.String(length=64), nullable=False),
        sa.Column("output_format", sa.String(length=32), nullable=False),
        sa.Column("output_path", sa.String(length=512), nullable=False),
        sa.Column("metadata", json_variant, nullable=False),
        sa.Column(
            "created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_index("ix_extraction_records_file_id", "extraction_records", ["file_id"])
    op.create_index("ix_extraction_records_engine", "extraction_records", ["engine"])

    # 6. system_settings table
    op.create_table(
        "system_settings",
        sa.Column("id", sa.Uuid(as_uuid=True), primary_key=True),
        sa.Column("setting_key", sa.String(length=128), nullable=False),
        sa.Column("setting_value", json_variant, nullable=False),
        sa.Column(
            "updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False
        ),
    )
    op.create_index(
        "ix_system_settings_setting_key", "system_settings", ["setting_key"], unique=True
    )


def downgrade() -> None:
    op.drop_table("system_settings")
    op.drop_table("extraction_records")
    op.drop_table("document_jobs")
    op.drop_table("batches")
    op.drop_table("files")
    op.drop_table("users")
