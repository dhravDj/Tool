# Scalable Autonomous Worker & Concurrency Architecture (Phase 12)

## 1. Overview & Worker Topology

DocuMind AI scales processing through autonomous worker processes (`ScalableWorker`) that self-register, lease computational slots from `HardwareGovernor`, report periodic heartbeats, and autonomously reclaim orphaned jobs.

```
┌─────────────────────────────────────────────────────────────────────────────┐
│                             Autonomous Worker                               │
│                                                                             │
│  ┌───────────────────────┐            ┌──────────────────────────────────┐  │
│  │   Heartbeat Thread    │            │        Task Execution Loop       │  │
│  │ - 15s interval        │            │ 1. Lease HardwareGovernor slot   │  │
│  │ - Reports CPU/RAM/VRAM│            │ 2. Dequeue from Priority Queue   │  │
│  │ - Refreshes status    │            │ 3. Execute Pipeline Orchestrator │  │
│  └───────────┬───────────┘            │ 4. Release slot & complete task  │  │
│              │                        └─────────────────┬────────────────┘  │
└──────────────┼──────────────────────────────────────────┼───────────────────┘
               │ (UPSERT worker_heartbeats)               │ (Task status)
               ▼                                          ▼
   [PostgreSQL / Redis]                       [Priority Task Queue]
               ▲
               │ (Periodic Sweep > 90s)
   ┌───────────┴───────────┐
   │   Stale Job Reaper    │
   │ - Marks dead workers  │
   │ - Requeues jobs       │
   └───────────────────────┘
```

---

## 2. Dynamic Hardware Governor Slot Integration

To prevent catastrophic system thrashing, workers never spawn unconstrained threads or allocate unbounded GPU buffers. All task steps lease capacity from `HardwareGovernor`:

```python
async with hardware_governor.lease_slot(requires_gpu=task.requires_gpu):
    # Safe execution within guaranteed resource limits
    result = await execute_pipeline_stage(task)
```

- **CPU Worker Allocation:** Fixed pool of 4 parallel CPU worker slots on commodity 8–16 core hosts.
- **GPU Slots:** Strictly single-slot serialization (1 slot) for AI embedding/inference workloads to avoid CUDA out-of-memory errors.

---

## 3. Worker Heartbeats & Stale Job Recovery

### Worker Heartbeat Contract
Workers write telemetry to `worker_heartbeats` every 15 seconds:
- `worker_id`: Unique identifier (e.g. `worker-hostname-pid-uuid`)
- `status`: `idle` | `busy` | `paused` | `shutting_down`
- `current_task_id`: Identifier of active job
- `cpu_percent`, `ram_usage_mb`: Current process footprint
- `processed_count`, `failed_count`: Lifetime throughput stats

### Stale Job Reaper
A supervisory routine monitors `worker_heartbeats`:
1. Any worker with `last_heartbeat < now - 90s` is transitioned to `dead`.
2. Any in-flight jobs (`processing`) assigned to the dead worker are re-queued with attempt count incremented.
3. If attempts exceed `max_retries`, the job is moved to `failed` and logged in the dead letter ledger.
