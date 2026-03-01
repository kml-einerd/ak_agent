# PROCEDURE: Security Audit AI Code

**TRIGGER:** AI coding agent has generated or significantly modified application code, especially authentication, file handling, or user-facing endpoints
**DOMAIN:** security
**PRE-CONDITIONS:** Application compiles and basic tests pass; developer has security domain knowledge to evaluate findings

---

## STEPS

1. Request targeted audit from AI agent with specific categories (crypto keys, authentication, race conditions, input validation, redirects, CSP) → list of issues classified by severity (CRITICAL, HIGH, MEDIUM)
2. Audit crypto key management: verify no hardcoded fallback keys in production config (ENV.fetch without defaults that silently degrade security) → all secrets fail-fast if missing in production
3. Audit authentication flows: check for replay attacks in TOTP (track last_otp_at), session fixation, open redirects after login (validate redirect URLs against request.host) → auth flows resist known attack vectors
4. Audit concurrent operations: identify read-modify-write patterns (Ruby increment!) and replace with atomic SQL (UPDATE WHERE) to prevent TOCTOU race conditions → all shared counters and state transitions are atomic
5. Audit input validation: verify server-side MIME detection (Marcel, not Content-Type header), file size from tempfile (not Content-Length header), filename sanitization → no client-supplied values trusted without server verification
6. Audit CSP and nonces: verify nonce is random per request (SecureRandom.base64), not derived from session ID → CSP nonces are unpredictable
7. Run full test suite before and after applying fixes → test count increases (Akita: 73 → 109 tests after security commit), zero regressions

**ON_FAILURE[step-1]:** If AI agent misses categories, provide explicit checklist: OWASP Top 10, framework-specific pitfalls, concurrency issues
**ON_FAILURE[step-4]:** If unsure about race conditions, use database-level constraints and transactions as default safe approach

---

## DONE WHEN
All identified issues are classified, fixed, tested, and the test suite grows to cover each security fix explicitly. No CRITICAL or HIGH issues remain open.

## SOURCE
https://akitaonrails.com/2026/02/21/vibe-code-fiz-um-clone-do-mega-em-rails-em-1-dia-pro-meu-home-server/
