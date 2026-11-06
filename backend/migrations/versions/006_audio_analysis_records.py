"""Add audio_analysis_records table

Revision ID: 006_audio_analysis_records
Revises: 005_presentation_analysis
Create Date: 2026-11-06 13:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "006_audio_analysis_records"
down_revision: str | None = "005_presentation_analysis"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    json_variant = sa.JSON().with_variant(postgresql.JSONB, "postgresql")

    op.create_table(
        "audio_analysis_records",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("file_id", sa.Uuid(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="completed"),
        sa.Column("format", sa.String(length=32), nullable=False),
        sa.Column("duration_seconds", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("sample_rate", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("channels", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("codec", sa.String(length=32), nullable=False, server_default="unknown"),
        sa.Column("detected_language", sa.String(length=32), nullable=True),
        sa.Column("language_confidence", sa.Float(), nullable=True),
        sa.Column("full_transcript", sa.Text(), nullable=False, server_default=""),
        sa.Column("speaker_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("segment_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("event_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("has_diarization", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("has_word_timestamps", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("has_events", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("model_name", sa.String(length=64), nullable=False, server_default="documind-acoustic-v1"),
        sa.Column("engine_name", sa.String(length=64), nullable=False, server_default="documind-acoustic"),
        sa.Column("confidence", sa.Float(), nullable=False, server_default="1.0"),
        sa.Column("processing_duration", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("artifacts", json_variant, nullable=False, server_default="{}"),
        sa.Column("audio_metadata", json_variant, nullable=False, server_default="{}"),
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
        "ix_audio_analysis_records_file_id",
        "audio_analysis_records",
        ["file_id"],
    )
    op.create_index(
        "ix_audio_analysis_records_status",
        "audio_analysis_records",
        ["status"],
    )
    op.create_index(
        "ix_audio_analysis_records_format",
        "audio_analysis_records",
        ["format"],
    )


def downgrade() -> None:
    op.drop_index(
        "ix_audio_analysis_records_format",
        table_name="audio_analysis_records",
    )
    op.drop_index(
        "ix_audio_analysis_records_status",
        table_name="audio_analysis_records",
    )
    op.drop_index(
        "ix_audio_analysis_records_file_id",
        table_name="audio_analysis_records",
    )
    op.drop_table("audio_analysis_records")
