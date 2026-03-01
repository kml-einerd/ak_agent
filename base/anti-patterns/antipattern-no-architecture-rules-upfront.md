# ANTI-PATTERN: No Architecture Rules Upfront

**DOMAIN:** ai-workflow
**APPEARS AS:** "I'll start coding right away and figure out conventions later. The LLM probably knows best practices already." Starting a vibe coding session without a CLAUDE.MD or equivalent configuration file seems faster because you skip planning and jump straight to features.
**ROOT CAUSE:** LLMs default to the most generic, junior-level patterns for any given framework. Without explicit rules, a Rails project won't use RESTful resources idiomatically, code won't follow the project's naming conventions, and architecture decisions will be inconsistent across sessions. The LLM treats each prompt independently and has no persistent memory of "how we do things here."
**RATIONALE:** The cost of writing a CLAUDE.MD file is ~30 minutes. The cost of refactoring an entire codebase after 50+ commits without conventions is 3-5 hours minimum. Akita's FrankMD project required a massive "Refactor to Restful Architecture" commit (~1000 lines) specifically because no architecture rules were set at the beginning. This refactoring would have been unnecessary with a single paragraph in CLAUDE.MD.

---

## SYMPTOMS

- LLM creates manual routes instead of using framework resource conventions
- Service objects or modules have inconsistent naming
- Code style varies between commits (sometimes server-side, sometimes client-side for same type of task)
- No clear domain separation — everything in a few large files
- First major refactoring commit is larger than all feature commits combined

## CORRECTION

Before the first feature commit, create a CLAUDE.MD (or CONTRIBUTING.MD, or .cursorrules) containing at minimum:
1. Framework-specific architecture rules (e.g., "use RESTful resources for all routes")
2. File organization standards (e.g., "no file should exceed 500 lines")
3. Naming conventions (e.g., "controllers in plural, models in singular")
4. Testing requirements (e.g., "every feature must have at least one integration test")
5. Performance defaults (e.g., "use debouncing for any input-triggered operations")

**NOT TO CONFUSE WITH:** Over-planning before writing any code. The CLAUDE.MD should contain architectural constraints, not a full design document. 30 minutes is sufficient.

## OPERATIONAL CONSTRAINTS
**FOR consistent AI-generated code quality TO SUCCEED:**

NEVER:
- Start coding with an AI agent before creating CLAUDE.MD or equivalent [explicit — CORRECTION]
- Let the LLM choose framework conventions by default [implied — ROOT CAUSE: "defaults to most generic, junior-level patterns"]

ALWAYS:
- Create CLAUDE.MD with architecture rules, file organization, naming conventions, testing requirements, and performance defaults before the first feature commit [explicit — CORRECTION]
- Limit initial CLAUDE.MD creation to ~30 minutes — constraints, not design document [explicit — NOT TO CONFUSE WITH]

GATE: CLAUDE.MD (or equivalent) exists and contains at minimum: architecture rules + file organization + naming conventions. If false, create it before proceeding.

## SOURCE
https://akitaonrails.com/2026/02/01/vibe-code-fiz-um-editor-de-markdown-do-zero-com-claude-code-frankmd-parte-2/
