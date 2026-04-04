# HEURISTIC: Cron as Safety Net

**DOMAIN:** backend / async-jobs
**RULE:** Never trust a single execution chain for critical jobs. Always have a scheduled cron job as a fallback that checks if work was completed and does it if not.
**APPLIES WHEN:** Any critical background job that runs on a schedule or is triggered by an event (webhook, user action, upstream job). Especially important for jobs that form chains where one failure can block the entire sequence.
**RATIONALE:**
1. In a chain like PublishAndSendJob → PublishToBlogJob → SendNewsletterJob, if the first job fails catastrophically (process killed, server crash, unhandled exception), the entire chain stops with no recovery mechanism. [explicit]
2. A cron job scheduled slightly later acts as a safety net: it checks the expected outcome (was the newsletter sent?) and triggers the relevant job if not. [explicit]
3. Because the job is idempotent (running it when work is already done is a no-op), the cron is always safe to execute — it either does the work or returns immediately. [derived]
**COUNTER-INDICATION:** Jobs that are NOT idempotent should never be put on a cron safety net — running them twice would produce incorrect results. Also, do NOT create jobs that reschedule themselves infinitely when there's no work to do — use the cron for scheduling, let the job be a one-shot execution.

## SOURCE
https://akitaonrails.com/2026/02/19/jobs-asssincronos-que-sobrevivem-ao-caos-bastidores-do-the-m-akita-chronicles/
