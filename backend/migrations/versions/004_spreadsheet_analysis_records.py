"""Add spreadsheet_analysis_records table

Revision ID: 004_spreadsheet_analysis_records
Revises: 003_image_analysis_records
Create Date: 2026-11-06 11:15:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "004_spreadsheet_analysis_records"
down_revision: str | None = "003_image_analysis_records"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    json_variant = sa.JSON().with_variant(postgresql.JSONB, "postgresql")

    op.create_table(
        "spreadsheet_analysis_records",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("file_id", sa.Uuid(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="completed"),
        sa.Column("format", sa.String(length=32), nullable=False),
        sa.Column("sheet_count", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("total_rows", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_columns", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_cells", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("formula_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("has_charts", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("has_tables", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("has_merged_cells", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("has_hidden_sheets", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("artifacts", json_variant, nullable=False, server_default="{}"),
        sa.Column("workbook_metadata", json_variant, nullable=False, server_default="{}"),
        sa.Column("profiling_summary", json_variant, nullable=False, server_default="{}"),
        sa.Column("warnings", json_variant, nullable=False, server_default="[]"),
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
        "ix_spreadsheet_analysis_records_file_id",
        "spreadsheet_analysis_records",
        ["file_id"],
    )
    op.create_index(
        "ix_spreadsheet_analysis_records_status",
        "spreadsheet_analysis_records",
        ["status"],
    )
    op.create_index(
        "ix_spreadsheet_analysis_records_format",
        "spreadsheet_analysis_records",
        ["format"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_spreadsheet_analysis_records_format",
        table_name="spreadsheet_analysis_records",
    )
    op.drop_index(
        "ix_spreadsheet_analysis_records_status",
        table_name="spreadsheet_analysis_records",
    )
    op.drop_index(
        "ix_spreadsheet_analysis_records_file_id",
        table_name="spreadsheet_analysis_records",
    )
    op.drop_table("spreadsheet_analysis_records")
