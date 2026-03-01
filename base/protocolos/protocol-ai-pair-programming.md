# PROTOCOL: AI Pair Programming

**DOMAIN:** ai-workflow
**APPLIES TO:** Any sustained coding session using an AI agent (Claude Code, Cursor, etc.) where the goal is production-quality software, not a throwaway prototype
**RATIONALE:** Using an AI agent as a code generator (spec in → code out) produces plausible code that solves the wrong problem, over-engineers solutions, and accumulates technical debt. Using it as a pair programming partner — where the human navigates and the agent pilots — leverages the agent's speed at writing code while keeping the human's judgment on architecture, domain knowledge, and quality. The dynamic mirrors traditional pair programming: when the human pilots (dictating exact code), results worsen. When the human navigates (defining direction, questioning decisions, correcting course), results improve dramatically.

---

## EVALUATION

| SIGNAL | DIAGNOSE | INTERVENE |
|--------|----------|-----------|
| Agent proposes a solution with 8 states, retry queues, and dead letter handling for a simple problem | Over-engineering — agent defaults to enterprise-grade complexity | Interrupt: "Simplifica. Quatro estados: pending, sending, sent, unknown." Provide the minimal viable design. |
| Agent uses HTTParty for a site that blocks non-browser clients | Missing domain knowledge (TLS fingerprinting, bot detection) | Provide context: "This site does TLS fingerprinting. Use headless Chromium with stealth patches." This knowledge comes from experience, not documentation. |
| Agent's generated text (prompts, personalities) sounds generic and bland | LLM suaviza opiniões por default | Be explicit in prompt instructions: "Akita never says 'maybe'. Marvin uses 'well...' and 'anyway'. The LLM will soften opinions if you're not explicit." |
| Agent implements a feature server-side that was previously done client-side (or vice versa) | Inconsistency from lack of persistent architectural memory | Interrupt and redirect. Document the pattern in CLAUDE.MD to prevent recurrence. |
| Agent implements anything you ask with equal enthusiasm, including bad ideas | Agent never says "no" — this is a bug, not a feature | You are the brake. You are the code review. You are the adult in the room. Question every decision: "Is this necessary? Is there a simpler way?" |

**TRADE-OFFS:** Pair programming with an agent requires constant attention — you cannot multitask. But the productivity gain (34 commits/day vs 11 commits/day) justifies the focus investment. The alternative (letting the agent work unsupervised) produces code that requires 6+ emergency refactoring sessions.

**ESCALATE WHEN:** The agent enters a loop (making and undoing changes) or the problem requires domain expertise the agent clearly lacks. At that point, solve the specific sub-problem yourself and give the agent the solution as context.

## SOURCE
https://akitaonrails.com/2026/02/20/do-zero-a-pos-producao-em-1-semana-como-usar-ia-em-projetos-de-verdade-bastidores-do-the-m-akita-chronicles/
