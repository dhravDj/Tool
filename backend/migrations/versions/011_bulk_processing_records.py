"""Add Bulk Processing and Scalability Engine records for Phase 12.

Revision ID: 011_bulk_processing_records
Revises: 010_ai_intelligence_records
Create Date: 2026-11-06 23:45:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "011_bulk_processing_records"
down_revision: str | None = "010_ai_intelligence_records"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    json_variant = sa.JSON().with_variant(postgresql.JSONB, "postgresql")

    # 1. processing_batches
    op.create_table(
        "processing_batches",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("owner_id", sa.Uuid(), nullable=True),
        sa.Column("name", sa.String(length=255), nullable=False),
        sa.Column("total_files", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("accepted_files", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("rejected_files", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("queued_files", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("processing_files", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("completed_files", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("partially_completed_files", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("failed_files", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("cancelled_files", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_size_bytes", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="pending"),
        sa.Column("overall_progress", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("processing_policy", json_variant, nullable=False, server_default="{}"),
        sa.Column("error_summary", json_variant, nullable=False, server_default="{}"),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["owner_id"], ["users.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_processing_batches_owner_status", "processing_batches", ["owner_id", "status"])
    op.create_index("ix_processing_batches_created_at", "processing_batches", ["created_at"])
    op.create_index("ix_processing_batches_status", "processing_batches", ["status"])

    # 2. batch_files
    op.create_table(
        "batch_files",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("batch_id", sa.Uuid(), nullable=False),
        sa.Column("file_id", sa.Uuid(), nullable=True),
        sa.Column("filename", sa.String(length=255), nullable=False),
        sa.Column("file_size", sa.BigInteger(), nullable=False, server_default="0"),
        sa.Column("sha256", sa.String(length=64), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="accepted"),
        sa.Column("validation_error", sa.Text(), nullable=True),
        sa.Column("dedup_decision", sa.String(length=32), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["batch_id"], ["processing_batches.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["file_id"], ["files.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_batch_files_batch_status", "batch_files", ["batch_id", "status"])
    op.create_index("ix_batch_files_sha256", "batch_files", ["sha256"])
    op.create_index("ix_batch_files_file_id", "batch_files", ["file_id"])

    # 3. processing_jobs
    op.create_table(
        "processing_jobs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("batch_id", sa.Uuid(), nullable=True),
        sa.Column("batch_file_id", sa.Uuid(), nullable=True),
        sa.Column("file_id", sa.Uuid(), nullable=False),
        sa.Column("job_type", sa.String(length=64), nullable=False, server_default="pipeline_orchestration"),
        sa.Column("stage", sa.String(length=64), nullable=False, server_default="queued"),
        sa.Column("priority", sa.Integer(), nullable=False, server_default="50"),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="queued"),
        sa.Column("current_worker_id", sa.String(length=128), nullable=True),
        sa.Column("retry_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("max_retries", sa.Integer(), nullable=False, server_default="3"),
        sa.Column("progress", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("stage_progress", json_variant, nullable=False, server_default="{}"),
        sa.Column("idempotency_key", sa.String(length=128), nullable=False),
        sa.Column("error_code", sa.String(length=64), nullable=True),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("started_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("completed_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("heartbeat_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("expires_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["batch_id"], ["processing_batches.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["batch_file_id"], ["batch_files.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["file_id"], ["files.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("idempotency_key"),
    )
    op.create_index("ix_processing_jobs_batch_status", "processing_jobs", ["batch_id", "status"])
    op.create_index("ix_processing_jobs_priority_status", "processing_jobs", ["priority", "status"])
    op.create_index("ix_processing_jobs_file_stage", "processing_jobs", ["file_id", "stage"])
    op.create_index("ix_processing_jobs_status", "processing_jobs", ["status"])

    # 4. job_attempts
    op.create_table(
        "job_attempts",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("job_id", sa.Uuid(), nullable=False),
        sa.Column("attempt_number", sa.Integer(), nullable=False, server_default="1"),
        sa.Column("worker_id", sa.String(length=128), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("finished_at", sa.DateTime(timezone=True), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="running"),
        sa.Column("error_message", sa.Text(), nullable=True),
        sa.Column("duration_ms", sa.Float(), nullable=True),
        sa.Column("memory_peak_mb", sa.Float(), nullable=True),
        sa.ForeignKeyConstraint(["job_id"], ["processing_jobs.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_job_attempts_job_attempt", "job_attempts", ["job_id", "attempt_number"])

    # 5. worker_heartbeats
    op.create_table(
        "worker_heartbeats",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("worker_id", sa.String(length=128), nullable=False),
        sa.Column("hostname", sa.String(length=255), nullable=False),
        sa.Column("pid", sa.Integer(), nullable=False),
        sa.Column("worker_type", sa.String(length=64), nullable=False, server_default="generic"),
        sa.Column("current_job_id", sa.Uuid(), nullable=True),
        sa.Column("jobs_completed", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("jobs_failed", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("cpu_percent", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("memory_mb", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("gpu_utilization", sa.Float(), nullable=True),
        sa.Column("gpu_memory_used_mb", sa.Float(), nullable=True),
        sa.Column("status", sa.String(length=32), nullable=False, server_default="alive"),
        sa.Column("last_heartbeat", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("started_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("worker_id"),
    )
    op.create_index("ix_worker_heartbeats_status", "worker_heartbeats", ["status"])
    op.create_index("ix_worker_heartbeats_last_heartbeat", "worker_heartbeats", ["last_heartbeat"])


def downgrade() -> None:
    op.drop_table("worker_heartbeats")
    op.drop_table("job_attempts")
    op.drop_table("processing_jobs")
    op.drop_table("batch_files")
    op.drop_table("processing_batches")
