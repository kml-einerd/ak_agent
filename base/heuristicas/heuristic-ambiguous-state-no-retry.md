# HEURISTIC: Ambiguous State Never Auto-Retry

**DOMAIN:** backend / email / async-jobs
**RULE:** Operations in an ambiguous state (may or may not have completed) must never be automatically retried. Mark them for manual review instead.
**APPLIES WHEN:** Any operation where duplication has negative consequences (sending emails, processing payments, publishing content, calling external APIs with side effects) and the process was interrupted between "started" and "confirmed."
**RATIONALE:** When a server dies between sending an email and recording that it was sent, the email may or may not have been delivered. Auto-retrying would risk sending it twice. For emails, this is annoying (user gets newsletter twice). For payments, it's a financial error. For API calls, it may trigger duplicate side effects. The correct approach is to mark the operation as "unknown" after a timeout and require human review before retrying. The cost of one missed delivery is always lower than the cost of one duplicate.
**COUNTER-INDICATION:** Idempotent operations (checking a status, reading data, cache warming) can safely be retried even in ambiguous states, because running them twice produces the same result.

## SOURCE
https://akitaonrails.com/2026/02/19/jobs-asssincronos-que-sobrevivem-ao-caos-bastidores-do-the-m-akita-chronicles/
