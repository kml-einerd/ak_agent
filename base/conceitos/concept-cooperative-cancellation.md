# CONCEPT: Cooperative Cancellation

**DOMAIN:** architecture
**DEFINITION:** A design pattern for responsive task cancellation in concurrent systems using a shared flag (e.g., AtomicBool) between the task thread and the control thread. The task periodically checks the flag at multiple strategic points in its processing loop — before each unit of work, during expensive operations, and after expensive operations — to bound the maximum cancellation latency to the time of one processing unit, not the time of the entire task. The flag is checked cooperatively (the task voluntarily inspects it) rather than forcefully (the task is killed externally).
**NOT:** Not process termination (kill -9), which can leave data in inconsistent state. Not thread interruption (Thread.interrupt), which can fire at arbitrary points causing partial writes. Not timeout-based cancellation, which doesn't respond to user intent. The key distinction is that cooperative cancellation lets the task reach a safe checkpoint before stopping, preserving data integrity.
**RATIONALE:** Long-running tasks (scanning 500K files, batch classification, data migration) must be cancellable without data corruption. Killing the process mid-write corrupts files or databases. Cooperative cancellation ensures the task stops at a safe boundary (after completing the current file, after committing the current transaction). Without multiple check points, cancellation of a 500K-file scan could take minutes waiting for the current batch to finish. With checks before each file, before each classification, and after each classification, the maximum wait is bounded to ~1 second (the time of one LLM call).

---

## REFERENCED BY

- base/protocolos/protocol-graceful-degradation-external-deps.md

## SOURCE
https://akitaonrails.com/2026/02/23/vibe-code-fiz-um-indexador-inteligente-de-imagens-com-ia-em-2-dias/
