# HEURISTIC: Fail-Fast Production Config

**DOMAIN:** deployment
**RULE:** Production configuration must crash at boot when required values are missing — never use fallback defaults for secrets, encryption keys, or critical service URLs (`ENV.fetch("KEY")` without a second argument, not `ENV.fetch("KEY", "test-key")`).
**APPLIES WHEN:** Any configuration value that, if wrong, would silently degrade security or correctness: encryption keys (hardcoded fallback means anyone reading source code can decrypt), API keys (fallback to test key means data goes nowhere), database URLs (fallback to SQLite in a PostgreSQL app means data is silently lost).
**RATIONALE:**
1. `ENV.fetch("KEY", "test-primary-key")` means the app runs happily in production with the hardcoded key — anyone who reads the source code can decrypt all OTP secrets, session tokens, or encrypted fields, while the app appears to work with no errors or warnings. [explicit]
2. `ENV.fetch("KEY")` without fallback raises `KeyError` on boot, which is the correct behavior: the app refuses to start in an insecure state rather than running silently compromised. [explicit]
3. Fail-fast at boot is infinitely better than fail-silently in production — the cost of a failed deployment is a restart, the cost of a silent compromise is a breach. [derived]
**COUNTER-INDICATION:** Development and test environments legitimately need defaults to avoid requiring every developer to configure every variable. Use environment-conditional logic: `if Rails.env.production? then ENV.fetch("KEY") else "test-key" end`. The rule is specifically about production — never about development convenience.

## SOURCE
https://akitaonrails.com/2026/02/21/vibe-code-fiz-um-clone-do-mega-em-rails-em-1-dia-pro-meu-home-server/
