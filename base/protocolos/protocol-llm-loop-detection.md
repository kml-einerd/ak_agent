# PROTOCOL: LLM Loop Detection

**DOMAIN:** ai-workflow
**APPLIES TO:** Situations where an LLM is stuck in trial-and-error during a coding session, making and undoing changes without converging on a solution
**RATIONALE:** LLMs operate within a context window and may lack critical environmental information (e.g., .gitignore rules, build tool configurations, OS-specific behaviors). When stuck, they will attempt increasingly random modifications rather than questioning their assumptions. Human intervention to investigate root causes outside the code is the only way to break the loop.

---

## EVALUATION

| SIGNAL | DIAGNOSE | INTERVENE |
|--------|----------|-----------|
| LLM makes a change, tests, reverts, tries different change in same area — 2+ cycles | Missing critical context that isn't in the codebase (environment config, build tool behavior, OS quirk) | Stop the LLM. Investigate environment: check .gitignore, build configs, dependency versions, OS-specific behavior. Provide the missing context explicitly. |
| LLM adds increasingly complex workarounds for what should be a simple fix | Root cause is elsewhere — LLM is treating a symptom, not the disease | Ask the LLM to stop fixing and instead explain its theory of what's wrong. Then verify the theory manually before allowing more changes. |
| LLM generates code that works in tests but fails in browser/runtime | Disconnect between test environment and real environment | Check for differences: build pipeline, asset compilation, caching, runtime-specific behavior. Report exact differences to LLM. |

**TRADE-OFFS:** Stopping the LLM mid-flow costs time and breaks momentum, but letting it loop can waste hours (Akita lost 2 hours to a .gitignore issue the LLM couldn't see)

**ESCALATE WHEN:** Root cause is in infrastructure, deployment, or third-party service behavior that the LLM cannot inspect or test.

## SOURCE
https://akitaonrails.com/2026/02/01/vibe-code-fiz-um-editor-de-markdown-do-zero-com-claude-code-frankmd-parte-2/
