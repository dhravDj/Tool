"""Hardware resource governor and concurrency throttle for DocuMind AI.

Optimized for AMD Ryzen 7 5800H (8 physical cores / 16 threads) and
NVIDIA GeForce RTX 3050 Laptop GPU (4GB VRAM).

Enforces:
1. Bounded CPU worker concurrency (MAX_PARALLEL_WORKERS = 4) to prevent CPU starvation.
2. Strict GPU mutex (GPU_MAX_CONCURRENT_INFERENCE = 1) to eliminate CUDA out-of-memory (OOM) faults.
3. Memory and system resource inspection with graceful CPU fallback.
"""

import asyncio
import logging
import os
import shutil
import subprocess
from collections.abc import AsyncGenerator
from contextlib import asynccontextmanager
from typing import Any

from app.core.config import settings

logger = logging.getLogger(__name__)


class HardwareGovernor:
    """Controls and bounds resource utilization across CPU-intensive and GPU-bound tasks."""

    def __init__(
        self,
        max_cpu_workers: int | None = None,
        max_gpu_slots: int | None = None,
    ) -> None:
        self.max_cpu_workers = max_cpu_workers or settings.MAX_PARALLEL_WORKERS
        self.max_gpu_slots = max_gpu_slots or settings.GPU_MAX_CONCURRENT_INFERENCE

        self._cpu_semaphore: asyncio.Semaphore | None = None
        self._gpu_semaphore: asyncio.Semaphore | None = None
        self._gpu_detected: bool | None = None
        self._gpu_device_name: str = "None"
        self._gpu_vram_mb: int = 0

    def _init_semaphores(self) -> None:
        """Lazy-initialize asyncio semaphores on the active event loop."""
        if self._cpu_semaphore is None:
            self._cpu_semaphore = asyncio.Semaphore(self.max_cpu_workers)
        if self._gpu_semaphore is None:
            self._gpu_semaphore = asyncio.Semaphore(self.max_gpu_slots)

    @asynccontextmanager
    async def cpu_bound_slot(self) -> AsyncGenerator[None, None]:
        """Acquire a concurrency slot for CPU-intensive extraction, OCR or detection."""
        self._init_semaphores()
        assert self._cpu_semaphore is not None
        await self._cpu_semaphore.acquire()
        try:
            yield
        finally:
            self._cpu_semaphore.release()

    @asynccontextmanager
    async def gpu_bound_slot(self) -> AsyncGenerator[None, None]:
        """Acquire an exclusive or bounded mutex slot for GPU/VRAM inference."""
        self._init_semaphores()
        assert self._gpu_semaphore is not None
        await self._gpu_semaphore.acquire()
        try:
            yield
        finally:
            self._gpu_semaphore.release()

    def detect_hardware(self) -> dict[str, Any]:
        """Inspect host CPU, memory, and accelerator availability."""
        logical_cpus = os.cpu_count() or 1
        # Memory metrics
        total_ram_mb = 0
        free_ram_mb = 0
        try:
            with open("/proc/meminfo", encoding="utf-8") as f:
                mem_data = f.read()
            for line in mem_data.splitlines():
                if line.startswith("MemTotal:"):
                    total_ram_mb = int(line.split()[1]) // 1024
                elif line.startswith("MemAvailable:"):
                    free_ram_mb = int(line.split()[1]) // 1024
        except Exception:
            # Fallback for non-Linux or sandboxed environments
            total_ram_mb = 16384
            free_ram_mb = 8192

        # GPU / CUDA detection
        if not self._gpu_detected:
            self._check_gpu_presence()

        return {
            "cpu": {
                "logical_cores": logical_cpus,
                "recommended_workers": self.max_cpu_workers,
                "active_workers_limit": self.max_cpu_workers,
            },
            "memory": {
                "total_ram_mb": total_ram_mb,
                "free_ram_mb": free_ram_mb,
            },
            "accelerator": {
                "gpu_detected": self._gpu_detected,
                "device_name": self._gpu_device_name,
                "vram_mb": self._gpu_vram_mb,
                "gpu_concurrency_limit": self.max_gpu_slots,
                "execution_target": settings.VISION_DEVICE,
            },
        }

    def _check_gpu_presence(self) -> None:
        """Inspect GPU without throwing exceptions if PyTorch or nvidia-smi is unavailable."""
        # 1. Try PyTorch CUDA if installed
        try:
            import torch  # type: ignore[import-untyped,import-not-found]

            if torch.cuda.is_available():
                self._gpu_detected = True
                self._gpu_device_name = torch.cuda.get_device_name(0)
                props = torch.cuda.get_device_properties(0)
                self._gpu_vram_mb = getattr(props, "total_memory", 0) // (1024 * 1024)
                logger.info(
                    f"CUDA accelerator identified: {self._gpu_device_name} ({self._gpu_vram_mb} MB VRAM)"
                )
                return
        except Exception:
            pass

        # 2. Try nvidia-smi subprocess
        smi = shutil.which("nvidia-smi")
        if smi:
            try:
                res = subprocess.run(
                    [smi, "--query-gpu=name,memory.total", "--format=csv,noheader,nounits"],
                    capture_output=True,
                    text=True,
                    timeout=2,
                    check=False,
                )
                if res.returncode == 0 and res.stdout.strip():
                    parts = res.stdout.strip().split("\n")[0].split(",")
                    self._gpu_detected = True
                    self._gpu_device_name = parts[0].strip()
                    self._gpu_vram_mb = int(parts[1].strip()) if len(parts) > 1 else 4096
                    logger.info(f"NVIDIA GPU detected via nvidia-smi: {self._gpu_device_name}")
                    return
            except Exception:
                pass

        self._gpu_detected = False
        self._gpu_device_name = "None"
        self._gpu_vram_mb = 0


# Global hardware governor singleton
hardware_governor = HardwareGovernor()
