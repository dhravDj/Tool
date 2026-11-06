"""Asynchronous background worker executing decoupled pipeline jobs from the task queue.

Supports graceful shutdown, bounded hardware concurrency via HardwareGovernor,
and dead-letter queue routing upon fatal failure.
"""

import asyncio
import logging
from collections.abc import Callable, Coroutine
from typing import Any

from app.core.hardware import hardware_governor
from app.infrastructure.queue.redis import TaskMessage, task_queue

logger = logging.getLogger(__name__)

TaskHandler = Callable[[dict[str, Any]], Coroutine[Any, Any, dict[str, Any]]]


class TaskWorker:
    """Async background worker consuming tasks from Redis or memory queues."""

    def __init__(self, queue_name: str = "default", poll_interval: float = 1.0) -> None:
        self.queue_name = queue_name
        self.poll_interval = poll_interval
        self._running = False
        self._handlers: dict[str, TaskHandler] = {}
        self._stop_event = asyncio.Event()

    def register_handler(self, task_name: str, handler: TaskHandler) -> None:
        """Register a handler coroutine for a specific task_name."""
        self._handlers[task_name] = handler
        logger.debug(f"Registered task worker handler for '{task_name}'")

    async def start(self) -> None:
        """Start the worker execution loop."""
        self._running = True
        self._stop_event.clear()
        logger.info(
            f"TaskWorker started on queue '{self.queue_name}' with {len(self._handlers)} handlers."
        )

        while self._running:
            try:
                task = await task_queue.dequeue(self.queue_name, timeout=self.poll_interval)
                if task is None:
                    continue

                await self._process_task(task)
            except asyncio.CancelledError:
                logger.info("TaskWorker received cancellation signal.")
                break
            except Exception as exc:
                logger.error(f"Unexpected error in TaskWorker loop: {exc}")
                await asyncio.sleep(self.poll_interval)

        self._running = False
        logger.info("TaskWorker stopped.")

    async def stop(self) -> None:
        """Signal the worker to gracefully shut down after finishing current task."""
        self._running = False
        self._stop_event.set()

    async def _process_task(self, task: TaskMessage) -> None:
        """Dispatch task to its handler under hardware governor limits."""
        handler = self._handlers.get(task.task_name)
        if not handler:
            err_msg = f"No handler registered for task type '{task.task_name}'"
            logger.error(err_msg)
            await task_queue.fail_task(task, error=err_msg, retry=False)
            return

        try:
            # Govern CPU concurrency for background processing
            async with hardware_governor.cpu_bound_slot():
                result = await handler(task.payload)
                await task_queue.complete_task(task.task_id, result=result)
                logger.info(f"Task {task.task_id} ({task.task_name}) completed successfully.")
        except Exception as exc:
            err_msg = f"Task {task.task_id} failed: {exc}"
            logger.warning(err_msg)
            await task_queue.fail_task(task, error=err_msg, retry=True)


# Global task worker instance
task_worker = TaskWorker()
