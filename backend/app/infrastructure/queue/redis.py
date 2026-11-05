"""Redis client, connection lifecycle, and resilient task queue utilities."""

import asyncio
import json
import time
import uuid
from dataclasses import asdict, dataclass, field
from datetime import UTC, datetime
from typing import Any

import redis.asyncio as aioredis

from app.core.config import settings
from app.core.logging import logger


@dataclass
class TaskMessage:
    """Represents an asynchronous task item in the distributed queue."""

    task_id: str
    task_name: str
    payload: dict[str, Any]
    queue_name: str = "default"
    retry_count: int = 0
    max_retries: int = 3
    created_at: str = field(default_factory=lambda: datetime.now(UTC).isoformat())
    error_history: list[str] = field(default_factory=list)

    def to_json(self) -> str:
        return json.dumps(asdict(self))

    @classmethod
    def from_json(cls, raw: str | bytes) -> "TaskMessage":
        if isinstance(raw, bytes):
            raw = raw.decode("utf-8")
        data = json.loads(raw)
        return cls(**data)


class RedisManager:
    """Manages asynchronous Redis connections for caching and message queuing."""

    def __init__(self) -> None:
        self._client: aioredis.Redis | None = None

    async def get_client(self) -> aioredis.Redis:
        if self._client is None:
            self._client = aioredis.from_url(
                settings.redis_uri,
                encoding="utf-8",
                decode_responses=True,
                socket_connect_timeout=2.0,
                socket_timeout=2.0,
            )
        return self._client

    async def close(self) -> None:
        if self._client:
            await self._client.aclose()
            self._client = None

    async def check_connectivity(self) -> tuple[bool, float, str]:
        """Ping Redis and return (is_healthy, latency_ms, message)."""
        start = time.perf_counter()
        try:
            client = await self.get_client()
            pong = await client.ping()
            latency = (time.perf_counter() - start) * 1000
            if pong:
                return True, round(latency, 2), "Redis cache/queue responsive."
            return False, round(latency, 2), "Unexpected response from Redis ping."
        except Exception as e:
            latency = (time.perf_counter() - start) * 1000
            logger.info(f"Redis not reachable at {settings.REDIS_HOST}:{settings.REDIS_PORT} ({e})")
            return False, round(latency, 2), f"Redis unavailable: {e}"


class TaskQueue:
    """Resilient task queue with exponential retries, dead-letter routing, and in-memory fallback."""

    def __init__(self, manager: RedisManager | None = None) -> None:
        self.manager = manager or redis_manager
        # In-memory queues for fallback when Redis is absent or offline
        self._memory_queues: dict[str, asyncio.Queue[str]] = {}
        self._memory_tasks: dict[str, dict[str, Any]] = {}

    def _get_mem_queue(self, queue_name: str) -> asyncio.Queue[str]:
        if queue_name not in self._memory_queues:
            self._memory_queues[queue_name] = asyncio.Queue()
        return self._memory_queues[queue_name]

    async def enqueue(
        self,
        task_name: str,
        payload: dict[str, Any],
        queue_name: str = "default",
        max_retries: int = 3,
    ) -> str:
        """Enqueue a new task and return its task_id."""
        task_id = uuid.uuid4().hex
        msg = TaskMessage(
            task_id=task_id,
            task_name=task_name,
            payload=payload,
            queue_name=queue_name,
            max_retries=max_retries,
        )
        raw_msg = msg.to_json()

        try:
            client = await self.manager.get_client()
            await client.rpush(f"queue:{queue_name}", raw_msg)
            await client.set(f"task:{task_id}:status", "queued", ex=86400)
            logger.debug(f"Enqueued task {task_id} ({task_name}) to Redis queue:{queue_name}")
            return task_id
        except Exception as exc:
            logger.debug(f"Redis enqueue failed ({exc}), falling back to in-memory queue.")
            q = self._get_mem_queue(queue_name)
            await q.put(raw_msg)
            self._memory_tasks[task_id] = {"status": "queued", "task": msg}
            return task_id

    async def dequeue(self, queue_name: str = "default", timeout: float = 1.0) -> TaskMessage | None:
        """Dequeue the next available task, blocking up to timeout seconds."""
        try:
            client = await self.manager.get_client()
            # blpop with integer timeout in seconds
            res = await client.blpop(f"queue:{queue_name}", timeout=max(1, int(timeout)))
            if res:
                _key, raw_msg = res
                msg = TaskMessage.from_json(raw_msg)
                await client.set(f"task:{msg.task_id}:status", "processing", ex=86400)
                return msg
            return None
        except Exception as exc:
            logger.debug(f"Redis dequeue failed ({exc}), reading from in-memory queue.")
            q = self._get_mem_queue(queue_name)
            try:
                raw_msg = await asyncio.wait_for(q.get(), timeout=timeout)
                msg = TaskMessage.from_json(raw_msg)
                if msg.task_id in self._memory_tasks:
                    self._memory_tasks[msg.task_id]["status"] = "processing"
                return msg
            except TimeoutError:
                return None

    async def complete_task(self, task_id: str, result: dict[str, Any] | None = None) -> None:
        """Mark a task as completed."""
        try:
            client = await self.manager.get_client()
            await client.set(f"task:{task_id}:status", "completed", ex=86400)
            if result:
                await client.set(f"task:{task_id}:result", json.dumps(result), ex=86400)
        except Exception:
            if task_id in self._memory_tasks:
                self._memory_tasks[task_id]["status"] = "completed"
                self._memory_tasks[task_id]["result"] = result

    async def fail_task(
        self,
        task: TaskMessage,
        error: str,
        retry: bool = True,
    ) -> None:
        """Handle task failure with retry or dead-letter queue routing."""
        task.retry_count += 1
        task.error_history.append(f"[{datetime.now(UTC).isoformat()}] {error}")

        if retry and task.retry_count <= task.max_retries:
            logger.warning(
                f"Retrying task {task.task_id} ({task.task_name}) - attempt {task.retry_count}/{task.max_retries}"
            )
            raw_msg = task.to_json()
            try:
                client = await self.manager.get_client()
                await client.rpush(f"queue:{task.queue_name}", raw_msg)
                await client.set(f"task:{task.task_id}:status", "retrying", ex=86400)
            except Exception:
                q = self._get_mem_queue(task.queue_name)
                await q.put(raw_msg)
                if task.task_id in self._memory_tasks:
                    self._memory_tasks[task.task_id]["status"] = "retrying"
        else:
            # Route to dead-letter queue (DLQ)
            logger.error(f"Task {task.task_id} ({task.task_name}) permanently failed. Routing to DLQ.")
            raw_msg = task.to_json()
            try:
                client = await self.manager.get_client()
                await client.rpush(f"dlq:{task.queue_name}", raw_msg)
                await client.set(f"task:{task.task_id}:status", "failed", ex=86400)
                await client.set(f"task:{task.task_id}:error", error, ex=86400)
            except Exception:
                dlq = self._get_mem_queue(f"dlq:{task.queue_name}")
                await dlq.put(raw_msg)
                if task.task_id in self._memory_tasks:
                    self._memory_tasks[task.task_id]["status"] = "failed"
                    self._memory_tasks[task.task_id]["error"] = error

    async def get_task_status(self, task_id: str) -> dict[str, Any]:
        """Fetch current task execution status."""
        try:
            client = await self.manager.get_client()
            status = await client.get(f"task:{task_id}:status")
            if status:
                result_raw = await client.get(f"task:{task_id}:result")
                error_raw = await client.get(f"task:{task_id}:error")
                return {
                    "task_id": task_id,
                    "status": status,
                    "result": json.loads(result_raw) if result_raw else None,
                    "error": error_raw,
                }
        except Exception:
            pass

        if task_id in self._memory_tasks:
            info = self._memory_tasks[task_id]
            return {
                "task_id": task_id,
                "status": info.get("status", "unknown"),
                "result": info.get("result"),
                "error": info.get("error"),
            }
        return {"task_id": task_id, "status": "unknown"}


redis_manager = RedisManager()
task_queue = TaskQueue(redis_manager)
