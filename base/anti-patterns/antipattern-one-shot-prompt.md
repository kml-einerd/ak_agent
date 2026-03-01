# ANTI-PATTERN: One-Shot Prompt

**DOMAIN:** ai-workflow
**APPEARS AS:** "Write a detailed spec, give it to the AI agent, and it delivers the complete system." Reinforced by demo videos showing "I built a SaaS in 10 minutes with Cursor." The output looks impressive: a working prototype with UI, routes, and basic functionality — all from a single prompt.
**ROOT CAUSE:** The delivered output is a prototype without tests, security, error handling, or deployment. In Akita's 274-commit project, only 37% of commits were new features. The remaining 63% was: bug fixes (16%), refactoring/hardening (10%), security (8%), deploy/infra (11%), tests/CI (16%), documentation (10%). A one-shot prompt produces only the 37% — the visible part — and misses the 63% that makes software survive contact with real users. Many critical features (ContentPreflight, RecoverStaleDeliveriesJob, StealthBrowser) only emerged from iteration, not from any spec.
**RATIONALE:** Real software emerges from iteration, not specification. Edge cases, failure modes, and security requirements are discovered during development, not predicted before it. The one-shot approach assumes complete knowledge upfront — which is impossible for any non-trivial system. The correct approach is iterative pair programming with the AI agent, with continuous testing, refactoring, and hardening at every step.

---

## SYMPTOMS

- Demo projects have zero tests
- Generated code has no error handling or graceful degradation
- No security measures (SSRF protection, rate limiting, input validation)
- No deployment configuration
- The project "works" in a demo but fails on first contact with real users or real data
- Developer shows a video of 10 minutes of work but doesn't show the 10 hours of fixing that followed

## CORRECTION

Treat AI-assisted coding as pair programming, not code generation:
1. Build features incrementally (small releases), not all-at-once
2. Write tests for each feature immediately (TDD preferred)
3. Refactor continuously — don't let code accumulate
4. Run CI on every commit (linting, security scanning, tests)
5. Deploy frequently and validate with real data
6. Accept that 63% of the work is invisible: fixes, hardening, security, testing, documentation

The correct metric is not "how fast can I generate features" but "how fast can I reach a production-ready system."

**NOT TO CONFUSE WITH:** Using a detailed spec/prompt for a SINGLE well-defined task (e.g., "implement this specific API endpoint with these tests"). One-shot works for individual tasks within a disciplined process. The anti-pattern is using one-shot for an entire project.

## OPERATIONAL CONSTRAINTS
**FOR production-quality AI-assisted software TO SUCCEED:**

NEVER:
- Expect a single prompt to produce a production-ready system [explicit — ROOT CAUSE]
- Evaluate AI-assisted coding by feature generation speed alone [explicit — CORRECTION: "correct metric is not how fast can I generate features"]
- Ship AI-generated code without tests, security measures, and error handling [explicit — SYMPTOMS]

ALWAYS:
- Treat AI-assisted coding as iterative pair programming, not code generation [explicit — CORRECTION]
- Build features incrementally with tests for each feature [explicit — CORRECTION steps 1-2]
- Account for the invisible 63%: fixes, hardening, security, testing, documentation [explicit — ROOT CAUSE, CORRECTION step 6]

GATE: Current approach is iterative pair programming (not spec-in, code-out). If false, restructure approach.

## SOURCE
https://akitaonrails.com/2026/02/20/do-zero-a-pos-producao-em-1-semana-como-usar-ia-em-projetos-de-verdade-bastidores-do-the-m-akita-chronicles/
