"""Add presentation_analysis_records table

Revision ID: 005_presentation_analysis_records
Revises: 004_spreadsheet_analysis_records
Create Date: 2026-11-06 12:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "005_presentation_analysis"
down_revision: str | None = "004_spreadsheet_analysis_records"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    json_variant = sa.JSON().with_variant(postgresql.JSONB, "postgresql")

    op.create_table(
        "presentation_analysis_records",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("file_id", sa.Uuid(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="completed"),
        sa.Column("format", sa.String(length=32), nullable=False),
        sa.Column("slide_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("hidden_slide_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_elements", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("has_notes", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("has_tables", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("has_charts", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("has_diagrams", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("has_images", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("artifacts", json_variant, nullable=False, server_default="{}"),
        sa.Column("presentation_metadata", json_variant, nullable=False, server_default="{}"),
        sa.Column("warnings", json_variant, nullable=False, server_default="[]"),
        sa.Column("engine_version", sa.String(length=32), nullable=False, server_default="6.0.0"),
        sa.Column("confidence", sa.Float(), nullable=False, server_default="1.0"),
        sa.Column("processing_duration", sa.Float(), nullable=False, server_default="0.0"),
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
        "ix_presentation_analysis_records_file_id",
        "presentation_analysis_records",
        ["file_id"],
    )
    op.create_index(
        "ix_presentation_analysis_records_status",
        "presentation_analysis_records",
        ["status"],
    )
    op.create_index(
        "ix_presentation_analysis_records_format",
        "presentation_analysis_records",
        ["format"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_presentation_analysis_records_format",
        table_name="presentation_analysis_records",
    )
    op.drop_index(
        "ix_presentation_analysis_records_status",
        table_name="presentation_analysis_records",
    )
    op.drop_index(
        "ix_presentation_analysis_records_file_id",
        table_name="presentation_analysis_records",
    )
    op.drop_table("presentation_analysis_records")
