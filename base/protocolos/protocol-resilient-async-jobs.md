# PROTOCOL: Resilient Async Jobs

**DOMAIN:** backend / architecture
**APPLIES TO:** Any background job system processing important operations (email sending, content publishing, API calls, data processing) that must survive failures, restarts, and concurrent execution
**RATIONALE:** Background jobs are inherently fragile: APIs timeout, servers restart, processes crash. Treating jobs as disposable scripts ("coloca num Sidekiq e tá bom") guarantees failure in production. The correct approach is designing jobs to recover from any failure state without human intervention. Six patterns compose a resilient job architecture: specific retries, distributed locks, atomic claiming, job orchestration, cron safety nets, and status notifications. Together they create a system that handles chaos gracefully.

---

## EVALUATION

| SIGNAL | DIAGNOSE | INTERVENE |
|--------|----------|-----------|
| Job fails and retries indiscriminately | Using `retry_on StandardError` — catches everything, fixes nothing | Create specific exception classes for transient states (e.g., `PodcastNotReady`). Use `retry_on` with specific exceptions, explicit wait intervals, and attempt limits. |
| Same job runs multiple times in parallel | Multiple triggers (cron, manual, API) without coordination | Implement distributed lock with TTL: acquire lock before execution, release in `ensure` block. Lock with automatic expiry prevents deadlock if process dies. |
| Server restart causes duplicate processing | No tracking of partially completed work | Use atomic claiming: create records per item, lock→claim→process→confirm. Items in ambiguous state ("sending") are never auto-retried. |
| Single job does too many things, fails unpredictably | Monolithic job with multiple responsibilities | Split into orchestrator job + specialized jobs. Orchestrator coordinates sequence. Each specialized job can be re-executed independently. |
| Job fails silently, nobody notices for hours | No observability on job status | Add status notifications (Discord, Slack, email) at start, completion, and failure. Every long-running job should communicate its progress. |
| Entire job chain fails, no fallback | Single execution path, no safety net | Add cron-based safety nets: a scheduled job that checks if work was completed and does it if not. Jobs must be idempotent — running twice produces same result. |

**TRADE-OFFS:** Each resilience pattern adds code complexity. For simple, non-critical jobs (cache warming, log cleanup), full resilience is overkill. Apply proportionally to the criticality of the operation.

**ESCALATE WHEN:** The failure mode is in the job queue infrastructure itself (SolidQueue/Sidekiq corrupted, database unavailable). At that point, the resilience patterns can't help — infrastructure recovery is needed.

## SOURCE
https://akitaonrails.com/2026/02/19/jobs-asssincronos-que-sobrevivem-ao-caos-bastidores-do-the-m-akita-chronicles/
