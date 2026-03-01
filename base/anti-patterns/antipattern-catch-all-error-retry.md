# ANTI-PATTERN: Catch-All Error Retry

**DOMAIN:** backend / async-jobs
**APPEARS AS:** `retry_on StandardError, wait: 5.seconds, attempts: 3` — retry any error 3 times with a short wait. Seems like a reasonable safety net: "if anything goes wrong, try again." It appears pragmatic and covers all cases.
**ROOT CAUSE:** This pattern conflates transient errors (API timeout, resource temporarily unavailable) with permanent errors (invalid data, missing configuration, logic bugs). Retrying a logic bug 3 times just wastes 15 seconds before the same inevitable failure. Retrying a resource that takes 4 hours to become available with 3 attempts at 5-second intervals will always fail. The retry strategy must match the error type.
**RATIONALE:** Effective retry requires: (1) specific exception classes for specific transient states, (2) wait intervals matched to the expected resolution time (15 minutes for a podcast being processed, not 5 seconds), (3) attempt counts that cover the realistic window (16 attempts × 15 minutes = 4 hours for a podcast). Generic retry catches everything and handles nothing correctly.

---

## SYMPTOMS

- Jobs fail after 3 retries and nobody investigates — "it just doesn't work sometimes"
- Transient failures (API timeouts) are treated the same as permanent failures (invalid input)
- Jobs that depend on external resources (file processing, third-party APIs) always fail because the retry window (15 seconds total) is far too short
- Error logs show the same error 3 times followed by silent failure — no graceful degradation

## CORRECTION

1. Identify every distinct failure mode the job can encounter
2. Create a specific exception class for each transient failure mode (e.g., `PodcastNotReady`, `ApiRateLimited`, `ServiceUnavailable`)
3. Configure `retry_on` per exception with appropriate intervals and attempt limits:
   - `retry_on PodcastNotReady, wait: 15.minutes, attempts: 16` (polls for up to 4 hours)
   - `retry_on ApiRateLimited, wait: 60.seconds, attempts: 5` (waits for rate limit reset)
4. Handle the exhaustion case explicitly: when max attempts are reached, degrade gracefully (publish without podcast, notify team) instead of silently failing
5. Let permanent errors (StandardError, logic bugs) crash immediately with full stack trace for debugging — don't mask them with retries

**NOT TO CONFUSE WITH:** Using `retry_on` with a single specific exception for a well-understood transient condition. That's correct usage. The anti-pattern is catching StandardError (everything) with a one-size-fits-all retry strategy.

## OPERATIONAL CONSTRAINTS
**FOR reliable error handling in async jobs TO SUCCEED:**

NEVER:
- Use `retry_on StandardError` or equivalent catch-all retry [explicit — ROOT CAUSE, NOT TO CONFUSE WITH]
- Apply a single retry interval to all error types [explicit — ROOT CAUSE: "retry strategy must match the error type"]
- Silently fail when max attempts are reached [explicit — CORRECTION step 4]

ALWAYS:
- Create specific exception classes for each transient failure mode [explicit — CORRECTION step 2]
- Configure retry intervals matched to expected resolution time per exception [explicit — CORRECTION step 3]
- Handle exhaustion explicitly with graceful degradation [explicit — CORRECTION step 4]
- Let permanent errors crash immediately with full stack trace [explicit — CORRECTION step 5]

GATE: Every `retry_on` call specifies a named exception class (not StandardError/Exception). If false, refactor retry logic.

## SOURCE
https://akitaonrails.com/2026/02/19/jobs-asssincronos-que-sobrevivem-ao-caos-bastidores-do-the-m-akita-chronicles/
