# HEURISTIC: Agent Skills Token Cost

**DOMAIN:** ai-workflow
**RULE:** Every installed AI agent skill/plugin adds 80-250 tokens to the system prompt per session, even when unused — be selective about what you install and regularly audit your active skills.
**APPLIES WHEN:** Using any AI coding agent that supports skills/plugins (Claude Code, Cursor, Crush, OpenCode). The cost compounds: 50 installed skills = 4,000 to 12,500 tokens consumed before you type your first prompt.
**RATIONALE:**
1. Agent skills inject their metadata (name, description, script paths, XML formatting) into the system prompt at session start — the model has no persistent tool awareness, so skills must be re-declared every time, consuming tokens regardless of usage. [explicit]
2. A developer who installs every available marketplace plugin pays a significant token tax on every session, making interactions more expensive and potentially pushing useful context out of the context window. [derived]
3. Skills are genuinely useful, but the cost is invisible unless you track it — awareness requires deliberate auditing. [explicit]
**COUNTER-INDICATION:** If you're on a flat-rate subscription (unlimited tokens per month) and your context window is large enough (200K+ tokens), the token cost is irrelevant. Also, for frequently-used skills that save significant manual work, the token overhead is justified by the productivity gain.

## OPERATIONAL CONSTRAINTS
**FOR efficient token usage in AI agent sessions TO SUCCEED:**

NEVER:
- Install agent skills/plugins without considering the per-session token cost [explicit — RULE]
- Keep unused skills installed across sessions [explicit — RULE: "regularly audit your active skills"]

ALWAYS:
- Be selective about installed skills — each adds 80-250 tokens to every session [explicit — RULE]
- Regularly audit active skills and remove unused ones [explicit — RULE]
- Track the total token overhead from installed skills [derived — RATIONALE: "cost is invisible unless you track it"]

GATE: Using per-token billing AND context window is limited (<200K tokens). If false, token overhead may be acceptable.

## SOURCE
https://akitaonrails.com/2026/01/24/ai-agents-qual-e-o-melhor-opencode-crush-claude-code-gpt-codex-gopilot-cursor-windsurf-antigravity/
