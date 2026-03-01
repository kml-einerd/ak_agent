# HEURISTIC: TOCTOU Use Atomic Operations

**DOMAIN:** backend
**RULE:** Never use read-modify-write in application code (e.g., Ruby `increment!`, Python `+= 1`) for shared counters or state transitions under concurrency — always use atomic SQL (`UPDATE table SET counter = counter + 1 WHERE id = X AND counter < max`).
**APPLIES WHEN:** Any operation that checks a value and then updates it based on the check, especially: download counters, inventory decrements, seat reservations, vote counts, rate limit counters, or any resource with a maximum that must be enforced.
**RATIONALE:** `increment!` does three things: (1) reads the current value, (2) adds 1 in the application language, (3) writes back. Two simultaneous requests both read 4, both write 5, and the user gets two downloads when they should get one. This is the classic TOCTOU (Time of Check, Time of Use) bug. It never appears in development with a single browser but always appears in production with concurrent requests. An atomic SQL `UPDATE WHERE` performs the check and update in a single database operation — the database guarantees only one request wins. The `== 1` return value confirms success/failure without a separate query.
**COUNTER-INDICATION:** If the application is guaranteed single-threaded with no concurrent access (e.g., CLI tool, batch script), read-modify-write is safe. Also unnecessary when using database-level serializable transactions that already prevent concurrent reads of the same row.

## SOURCE
https://akitaonrails.com/2026/02/21/vibe-code-fiz-um-clone-do-mega-em-rails-em-1-dia-pro-meu-home-server/
