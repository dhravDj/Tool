"""Add AI Intelligence records for Phase 11.

Revision ID: 010_ai_intelligence_records
Revises: 009_archive_analysis_records
Create Date: 2026-11-06 23:15:00.000000

"""

from collections.abc import Sequence

import sqlalchemy as sa
from alembic import op
from sqlalchemy.dialects import postgresql

revision: str = "010_ai_intelligence_records"
down_revision: str | None = "009_archive_analysis_records"
branch_labels: str | Sequence[str] | None = None
depends_on: str | Sequence[str] | None = None


def upgrade() -> None:
    json_variant = sa.JSON().with_variant(postgresql.JSONB, "postgresql")

    # 1. knowledge_documents
    op.create_table(
        "knowledge_documents",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("file_id", sa.Uuid(), nullable=False),
        sa.Column("knowledge_document_id", sa.String(length=64), nullable=False),
        sa.Column("source_type", sa.String(length=32), nullable=False),
        sa.Column("content_type", sa.String(length=64), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False),
        sa.Column("content_hash", sa.String(length=64), nullable=False),
        sa.Column("extraction_status", sa.String(length=32), nullable=False, server_default="completed"),
        sa.Column("language", sa.String(length=16), nullable=False, server_default="en"),
        sa.Column("total_blocks", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("raw_metadata", json_variant, nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["file_id"], ["files.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("knowledge_document_id"),
    )
    op.create_index("ix_knowledge_documents_file_id", "knowledge_documents", ["file_id"])
    op.create_index("ix_knowledge_documents_id_str", "knowledge_documents", ["knowledge_document_id"])
    op.create_index("ix_knowledge_documents_source_type", "knowledge_documents", ["source_type"])
    op.create_index("ix_knowledge_documents_content_hash", "knowledge_documents", ["content_hash"])

    # 2. knowledge_chunks
    op.create_table(
        "knowledge_chunks",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("knowledge_document_id", sa.Uuid(), nullable=False),
        sa.Column("file_id", sa.Uuid(), nullable=False),
        sa.Column("chunk_id", sa.String(length=64), nullable=False),
        sa.Column("chunk_index", sa.Integer(), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("token_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("source_type", sa.String(length=32), nullable=False),
        sa.Column("source_reference", json_variant, nullable=False, server_default="{}"),
        sa.Column("content_hash", sa.String(length=64), nullable=False),
        sa.Column("embedding_status", sa.String(length=32), nullable=False, server_default="pending"),
        sa.Column("metadata_payload", json_variant, nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["knowledge_document_id"], ["knowledge_documents.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["file_id"], ["files.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("chunk_id"),
    )
    op.create_index("ix_knowledge_chunks_kdoc_id", "knowledge_chunks", ["knowledge_document_id"])
    op.create_index("ix_knowledge_chunks_file_id", "knowledge_chunks", ["file_id"])
    op.create_index("ix_knowledge_chunks_chunk_id", "knowledge_chunks", ["chunk_id"])
    op.create_index("ix_knowledge_chunks_chunk_index", "knowledge_chunks", ["chunk_index"])
    op.create_index("ix_knowledge_chunks_source_type", "knowledge_chunks", ["source_type"])
    op.create_index("ix_knowledge_chunks_content_hash", "knowledge_chunks", ["content_hash"])
    op.create_index("ix_knowledge_chunks_emb_status", "knowledge_chunks", ["embedding_status"])
    op.create_index("ix_chunks_file_index", "knowledge_chunks", ["file_id", "chunk_index"])
    op.create_index("ix_chunks_doc_index", "knowledge_chunks", ["knowledge_document_id", "chunk_index"])

    # 3. embedding_records
    op.create_table(
        "embedding_records",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("chunk_id", sa.Uuid(), nullable=False),
        sa.Column("provider", sa.String(length=32), nullable=False),
        sa.Column("model_name", sa.String(length=64), nullable=False),
        sa.Column("dimension", sa.Integer(), nullable=False),
        sa.Column("vector_data", json_variant, nullable=False),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["chunk_id"], ["knowledge_chunks.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("chunk_id"),
    )
    op.create_index("ix_embedding_records_chunk_id", "embedding_records", ["chunk_id"])
    op.create_index("ix_embedding_records_provider", "embedding_records", ["provider"])
    op.create_index("ix_embedding_records_model_name", "embedding_records", ["model_name"])

    # 4. retrieval_records
    op.create_table(
        "retrieval_records",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("query", sa.Text(), nullable=False),
        sa.Column("search_mode", sa.String(length=32), nullable=False, server_default="hybrid"),
        sa.Column("top_k", sa.Integer(), nullable=False, server_default="10"),
        sa.Column("filter_payload", json_variant, nullable=False, server_default="{}"),
        sa.Column("hits_payload", json_variant, nullable=False, server_default="[]"),
        sa.Column("duration_ms", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )

    # 5. ai_conversations
    op.create_table(
        "ai_conversations",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("title", sa.String(length=255), nullable=False, server_default="New Conversation"),
        sa.Column("provider", sa.String(length=32), nullable=False, server_default="sovereign"),
        sa.Column("model_name", sa.String(length=64), nullable=False, server_default="documind-sovereign-llm-v1"),
        sa.Column("file_id", sa.Uuid(), nullable=True),
        sa.Column("context_mode", sa.String(length=32), nullable=False, server_default="single_file"),
        sa.Column("system_prompt", sa.Text(), nullable=True),
        sa.Column("metadata_payload", json_variant, nullable=False, server_default="{}"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["file_id"], ["files.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_ai_conversations_file_id", "ai_conversations", ["file_id"])

    # 6. ai_messages
    op.create_table(
        "ai_messages",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("conversation_id", sa.Uuid(), nullable=False),
        sa.Column("role", sa.String(length=32), nullable=False),
        sa.Column("content", sa.Text(), nullable=False),
        sa.Column("thought_process", sa.Text(), nullable=True),
        sa.Column("citations", json_variant, nullable=False, server_default="[]"),
        sa.Column("retrieval_id", sa.Uuid(), nullable=True),
        sa.Column("token_count", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("latency_ms", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["conversation_id"], ["ai_conversations.id"], ondelete="CASCADE"),
        sa.ForeignKeyConstraint(["retrieval_id"], ["retrieval_records.id"], ondelete="SET NULL"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_ai_messages_conversation_id", "ai_messages", ["conversation_id"])

    # 7. ai_provider_configs
    op.create_table(
        "ai_provider_configs",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("provider_name", sa.String(length=32), nullable=False),
        sa.Column("is_enabled", sa.Boolean(), nullable=False, server_default=sa.true()),
        sa.Column("api_key_encrypted", sa.Text(), nullable=True),
        sa.Column("base_url", sa.String(length=255), nullable=True),
        sa.Column("default_model", sa.String(length=64), nullable=False),
        sa.Column("user_consent_granted", sa.Boolean(), nullable=False, server_default=sa.false()),
        sa.Column("settings_payload", json_variant, nullable=False, server_default="{}"),
        sa.Column("updated_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
        sa.UniqueConstraint("provider_name"),
    )
    op.create_index("ix_ai_provider_configs_name", "ai_provider_configs", ["provider_name"])

    # 8. ai_usage_records
    op.create_table(
        "ai_usage_records",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("provider", sa.String(length=32), nullable=False),
        sa.Column("model_name", sa.String(length=64), nullable=False),
        sa.Column("operation_type", sa.String(length=32), nullable=False),
        sa.Column("prompt_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("completion_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("total_tokens", sa.Integer(), nullable=False, server_default="0"),
        sa.Column("duration_ms", sa.Float(), nullable=False, server_default="0.0"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_ai_usage_records_provider", "ai_usage_records", ["provider"])
    op.create_index("ix_ai_usage_records_op_type", "ai_usage_records", ["operation_type"])

    # 9. summary_records
    op.create_table(
        "summary_records",
        sa.Column("id", sa.Uuid(), nullable=False),
        sa.Column("file_id", sa.Uuid(), nullable=False),
        sa.Column("summary_type", sa.String(length=32), nullable=False),
        sa.Column("provider", sa.String(length=32), nullable=False),
        sa.Column("model_name", sa.String(length=64), nullable=False),
        sa.Column("summary_text", sa.Text(), nullable=False),
        sa.Column("key_findings", json_variant, nullable=False, server_default="[]"),
        sa.Column("citations", json_variant, nullable=False, server_default="[]"),
        sa.Column("created_at", sa.DateTime(timezone=True), server_default=sa.func.now(), nullable=False),
        sa.ForeignKeyConstraint(["file_id"], ["files.id"], ondelete="CASCADE"),
        sa.PrimaryKeyConstraint("id"),
    )
    op.create_index("ix_summary_records_file_id", "summary_records", ["file_id"])
    op.create_index("ix_summary_records_type", "summary_records", ["summary_type"])
    op.create_index("ix_summaries_file_type", "summary_records", ["file_id", "summary_type"])


def downgrade() -> None:
    op.drop_table("summary_records")
    op.drop_table("ai_usage_records")
    op.drop_table("ai_provider_configs")
    op.drop_table("ai_messages")
    op.drop_table("ai_conversations")
    op.drop_table("retrieval_records")
    op.drop_table("embedding_records")
    op.drop_table("knowledge_chunks")
    op.drop_table("knowledge_documents")
