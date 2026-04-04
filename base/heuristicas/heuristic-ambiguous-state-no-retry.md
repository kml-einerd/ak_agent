# HEURISTIC: Ambiguous State Never Auto-Retry

**DOMAIN:** backend / email / async-jobs
**RULE:** Operations in an ambiguous state (may or may not have completed) must never be automatically retried. Mark them for manual review instead.
**APPLIES WHEN:** Any operation where duplication has negative consequences (sending emails, processing payments, publishing content, calling external APIs with side effects) and the process was interrupted between "started" and "confirmed."
**RATIONALE:**
1. When a server dies between sending an email and recording that it was sent, the operation is in an ambiguous state — the email may or may not have been delivered, and auto-retrying risks sending it twice. [explicit]
2. Duplicate consequences scale with severity: annoying for emails (newsletter twice), financially damaging for payments, and unpredictable for API calls with side effects. [derived]
3. The correct approach is to mark the operation as "unknown" after a timeout and require human review before retrying, because the cost of one missed delivery is always lower than the cost of one duplicate. [explicit]
**COUNTER-INDICATION:** Idempotent operations (checking a status, reading data, cache warming) can safely be retried even in ambiguous states, because running them twice produces the same result.

## SOURCE
https://akitaonrails.com/2026/02/19/jobs-asssincronos-que-sobrevivem-ao-caos-bastidores-do-the-m-akita-chronicles/
