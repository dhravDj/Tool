"""Integration tests for SQLAlchemy 2.0 database models and operations."""

import uuid

import pytest
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from app.domain.enums import BatchStatus, FileStatus, JobStatus
from app.infrastructure.database.models import (
    Batch,
    DocumentJob,
    FileRecord,
    User,
)


@pytest.mark.asyncio
async def test_create_and_query_user(db_session: AsyncSession):
    user = User(
        email="developer@documind.ai",
        password_hash="pbkdf2:sha256:310000$test$testhash",
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    assert isinstance(user.id, uuid.UUID)
    assert user.created_at is not None

    stmt = select(User).where(User.email == "developer@documind.ai")
    result = await db_session.execute(stmt)
    fetched = result.scalar_one()
    assert fetched.id == user.id


@pytest.mark.asyncio
async def test_file_and_batch_relational_hierarchy(db_session: AsyncSession):
    # 1. Create User
    user = User(email="analyst@documind.ai", password_hash="dummy")
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)

    # 2. Create File Record
    file_rec = FileRecord(
        owner_id=user.id,
        original_filename="financial_q4.pdf",
        stored_filename="uuid-q4.pdf",
        extension="pdf",
        detected_mime_type="application/pdf",
        file_size=204850,
        sha256="e3b0c44298fc1c149afbf4c8996fb92427ae41e4649b934ca495991b7852b855",
        storage_path="uploads/uuid-q4.pdf",
        status=FileStatus.STORED.value,
    )
    db_session.add(file_rec)

    # 3. Create Parent Batch
    batch = Batch(
        owner_id=user.id,
        name="Q4 Financial Reports Batch",
        total_files=1,
        queued_files=1,
        status=BatchStatus.QUEUED.value,
    )
    db_session.add(batch)
    await db_session.commit()
    await db_session.refresh(file_rec)
    await db_session.refresh(batch)

    # 4. Create Child Document Job
    job = DocumentJob(
        batch_id=batch.id,
        file_id=file_rec.id,
        status=JobStatus.QUEUED.value,
    )
    db_session.add(job)
    await db_session.commit()
    await db_session.refresh(job)

    assert isinstance(job.id, uuid.UUID)
    assert job.batch_id == batch.id
    assert job.file_id == file_rec.id

    # Verify query
    stmt = select(DocumentJob).where(DocumentJob.batch_id == batch.id)
    jobs = (await db_session.execute(stmt)).scalars().all()
    assert len(jobs) == 1
    assert jobs[0].status == JobStatus.QUEUED.value
