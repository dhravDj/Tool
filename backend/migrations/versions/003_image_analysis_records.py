"""Add image_analysis_records table

Revision ID: 003_image_analysis_records
Revises: 002_file_detection_fields
Create Date: 2026-11-06 03:20:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "003_image_analysis_records"
down_revision: str | None = "002_file_detection_fields"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    json_variant = sa.JSON().with_variant(postgresql.JSONB, "postgresql")

    op.create_table(
        "image_analysis_records",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("file_id", sa.Uuid(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="completed"),
        sa.Column("format", sa.String(length=32), nullable=False),
        sa.Column("width", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("height", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("color_mode", sa.String(length=32), nullable=False, server_default="RGB"),
        sa.Column("has_transparency", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("is_animated", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("ocr_word_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("ocr_text", sa.Text(), nullable=True),
        sa.Column("detected_objects_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("caption", sa.Text(), nullable=True),
        sa.Column("has_charts", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("has_diagrams", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("artifacts", json_variant, nullable=False, server_default="{}"),
        sa.Column("metadata", json_variant, nullable=False, server_default="{}"),
        sa.Column(
            "created_at",
            sa.DateTime(timezone=True),
            server_default=sa.text("now()"),
            nullable=False,
        ),
        sa.ForeignKeyConstraint(["file_id"], ["files.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )

    op.create_index("ix_image_analysis_records_file_id", "image_analysis_records", ["file_id"])
    op.create_index("ix_image_analysis_records_status", "image_analysis_records", ["status"])
    op.create_index("ix_image_analysis_records_format", "image_analysis_records", ["format"])


def downgrade() -> None:
    op.drop_index("ix_image_analysis_records_format", table_name="image_analysis_records")
    op.drop_index("ix_image_analysis_records_status", table_name="image_analysis_records")
    op.drop_index("ix_image_analysis_records_file_id", table_name="image_analysis_records")
    op.drop_table("image_analysis_records")
