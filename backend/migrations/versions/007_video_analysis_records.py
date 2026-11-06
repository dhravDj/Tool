"""Add video_analysis_records table

Revision ID: 007_video_analysis_records
Revises: 006_audio_analysis_records
Create Date: 2026-11-06 14:00:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "007_video_analysis_records"
down_revision: str | None = "006_audio_analysis_records"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    json_variant = sa.JSON().with_variant(postgresql.JSONB, "postgresql")

    op.create_table(
        "video_analysis_records",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("file_id", sa.Uuid(), nullable=False),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="completed"),
        sa.Column("format", sa.String(length=32), nullable=False),
        sa.Column("duration_seconds", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("width", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("height", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("fps", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("video_codec", sa.String(length=32), nullable=False, server_default="unknown"),
        sa.Column("audio_codec", sa.String(length=32), nullable=False, server_default="none"),
        sa.Column("scene_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("keyframe_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("detection_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("track_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("has_audio", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("has_transcript", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("full_transcript", sa.Text(), nullable=False, server_default=""),
        sa.Column("model_name", sa.String(length=64), nullable=False, server_default="documind-video-v1"),
        sa.Column("engine_name", sa.String(length=64), nullable=False, server_default="documind-video"),
        sa.Column("confidence", sa.Float(), nullable=False, server_default="1.0"),
        sa.Column("processing_duration", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("artifacts", json_variant, nullable=False, server_default="{}"),
        sa.Column("video_metadata", json_variant, nullable=False, server_default="{}"),
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
        op.f("ix_video_analysis_records_file_id"),
        "video_analysis_records",
        ["file_id"],
        unique=False,
    )
    op.create_index(
        op.f("ix_video_analysis_records_status"),
        "video_analysis_records",
        ["status"],
        unique=False,
    )
    op.create_index(
        op.f("ix_video_analysis_records_format"),
        "video_analysis_records",
        ["format"],
        unique=False,
    )


def downgrade() -> None:
    op.drop_index(op.f("ix_video_analysis_records_format"), table_name="video_analysis_records")
    op.drop_index(op.f("ix_video_analysis_records_status"), table_name="video_analysis_records")
    op.drop_index(op.f("ix_video_analysis_records_file_id"), table_name="video_analysis_records")
    op.drop_table("video_analysis_records")
