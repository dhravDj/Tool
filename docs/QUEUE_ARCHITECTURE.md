# Priority Task Queue Architecture (Phase 12)

## 1. Overview & Tiered Design

The DocuMind AI Priority Queue subsystem (`PriorityTaskQueue`) manages workload scheduling across 4 distinct priority tiers with built-in anti-starvation mechanisms, Redis backing, and automatic memory fallback.

```
       Task Ingestion (POST /api/v1/jobs/submit or Batch Manager)
                                  │
                                  ▼
      ┌────────────────────────────────────────────────────────┐
      │             Priority & Idempotency Filter              │
      │   - Checks idempotency_key (Redis / in-memory set)     │
      │   - Maps priority (0..100) to queue tier               │
      └───────────────────────────┬────────────────────────────┘
                                  │
      ┌───────────────────────────┼────────────────────────────┬───────────────────────────┐
      │ (priority >= 80)          │ (priority >= 50)           │ (priority >= 20)          │ (priority < 20)
      ▼                           ▼                            ▼                           ▼
┌──────────────┐            ┌──────────────┐             ┌──────────────┐            ┌──────────────┐
│ Interactive  │            │    Normal    │             │     Bulk     │            │ Maintenance  │
│  Queue (80+) │            │ Queue(50..79)│             │ Queue(20..49)│            │ Queue (0..19)│
└──────┬───────┘            └──────┬───────┘             └──────┬───────┘            └──────┬───────┘
       │                           │                            │                           │
       └───────────────────────────┴─────────────┬──────────────┴───────────────────────────┘
                                                 │
                                                 ▼
                                ┌──────────────────────────────────┐
                                │   Fair Scheduling Dequeue Loop   │
                                │   - Anti-starvation counter      │
                                │   - Checks cancellation registry │
                                │   - Leases Hardware slots        │
                                └──────────────────────────────────┘
```

---

## 2. Queue Tiers & SLA Guarantees

| Tier | Priority Range | Weight / Ratio | Target SLA | Intended Workload |
|---|---|---|---|---|
| **Interactive** | $80 - 100$ | $8 \times$ | $< 2.0\text{ s}$ | User-initiated single file extractions, live UI queries |
| **Normal** | $50 - 79$ | $4 \times$ | $< 15.0\text{ s}$ | Standard batch processing, asynchronous webhook jobs |
| **Bulk** | $20 - 49$ | $2 \times$ | Best effort | Massive uploads ($1,000+$ to $10,000+$ files) |
| **Maintenance** | $0 - 19$ | $1 \times$ | Idle only | Index compaction, vector pruning, temporary cleanup |

### Anti-Starvation Scheduling
To avoid bulk or maintenance queues starving when high-priority tasks arrive continuously:
- For every 8 tasks popped from `interactive`, at least 1 task from `normal` is guaranteed.
- For every 4 tasks popped from `normal`, at least 1 task from `bulk` is guaranteed.
- Starvation tick counters reset periodically to prevent queue stagnation.

---

## 3. Resilience, Exponential Backoff & Dead Letter Queue (DLQ)

When task execution encounters transient errors (network hiccups, momentary rate limits, database lock timeouts):
1. **Exponential Backoff with Full Jitter:**
   $$\text{Delay} = \min\left(\text{max\_delay}, \text{base\_delay} \times 2^{\text{attempt}-1}\right) \times \text{Uniform}(0.5, 1.5)$$
2. **Retry Ceiling:** Tasks have a configurable retry limit (default: 3 attempts).
3. **Dead Letter Queue (DLQ):** After exhausting retries, tasks are routed to the DLQ (`queue:dead_letter`) with the root error trace and attempt history preserved in `job_attempts`.

---

## 4. Idempotency & Task Revocation

- **Idempotency Registry:** Every task submission can specify an `idempotency_key`. The queue maintains a TTL cache of active/completed keys. Duplicate submissions within the window return the existing `task_id` without re-queueing.
- **Dynamic Revocation:** Tasks can be cancelled by `task_id` or `batch_id`. The queue marks cancellation in a fast Redis set, and dequeue loops discard revoked tasks transparently.
