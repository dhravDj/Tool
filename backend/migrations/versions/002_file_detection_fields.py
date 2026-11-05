"""Add file detection fields to files table

Revision ID: 002_file_detection_fields
Revises: 001_initial_schema
Create Date: 2026-11-06 02:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "002_file_detection_fields"
down_revision: str | None = "001_initial_schema"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    json_variant = sa.JSON().with_variant(postgresql.JSONB, "postgresql")

    op.add_column("files", sa.Column("detection_format_id", sa.String(length=64), nullable=True))
    op.add_column("files", sa.Column("claimed_extension", sa.String(length=32), nullable=True))
    op.add_column("files", sa.Column("actual_extension", sa.String(length=32), nullable=True))
    op.add_column("files", sa.Column("format_category", sa.String(length=32), nullable=True))
    op.add_column("files", sa.Column("confidence_level", sa.String(length=16), nullable=True))
    op.add_column("files", sa.Column("confidence_score", sa.Float(), nullable=True))
    op.add_column("files", sa.Column("support_status", sa.String(length=32), nullable=True))
    op.add_column(
        "files", sa.Column("is_valid", sa.Boolean(), server_default=sa.true(), nullable=False)
    )
    op.add_column(
        "files", sa.Column("is_mismatch", sa.Boolean(), server_default=sa.false(), nullable=False)
    )
    op.add_column(
        "files", sa.Column("is_corrupted", sa.Boolean(), server_default=sa.false(), nullable=False)
    )
    op.add_column(
        "files", sa.Column("is_suspicious", sa.Boolean(), server_default=sa.false(), nullable=False)
    )
    op.add_column(
        "files", sa.Column("detection_evidence", json_variant, server_default="{}", nullable=False)
    )
    op.add_column(
        "files", sa.Column("detection_warnings", json_variant, server_default="[]", nullable=False)
    )
    op.add_column(
        "files", sa.Column("file_metadata", json_variant, server_default="{}", nullable=False)
    )
    op.add_column(
        "files",
        sa.Column(
            "detection_engine_version", sa.String(length=32), server_default="2.0.0", nullable=True
        ),
    )
    op.add_column("files", sa.Column("detected_at", sa.DateTime(timezone=True), nullable=True))

    op.create_index("ix_files_detection_format_id", "files", ["detection_format_id"])
    op.create_index("ix_files_format_category", "files", ["format_category"])
    op.create_index("ix_files_support_status", "files", ["support_status"])


def downgrade() -> None:
    op.drop_index("ix_files_support_status", table_name="files")
    op.drop_index("ix_files_format_category", table_name="files")
    op.drop_index("ix_files_detection_format_id", table_name="files")

    op.drop_column("files", "detected_at")
    op.drop_column("files", "detection_engine_version")
    op.drop_column("files", "file_metadata")
    op.drop_column("files", "detection_warnings")
    op.drop_column("files", "detection_evidence")
    op.drop_column("files", "is_suspicious")
    op.drop_column("files", "is_corrupted")
    op.drop_column("files", "is_mismatch")
    op.drop_column("files", "is_valid")
    op.drop_column("files", "support_status")
    op.drop_column("files", "confidence_score")
    op.drop_column("files", "confidence_level")
    op.drop_column("files", "format_category")
    op.drop_column("files", "actual_extension")
    op.drop_column("files", "claimed_extension")
    op.drop_column("files", "detection_format_id")
