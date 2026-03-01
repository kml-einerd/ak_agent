# ANTI-PATTERN: LLM Unsupervised Coding

**DOMAIN:** ai-workflow
**APPEARS AS:** "The LLM is processing, I can watch YouTube / do other things while it works. I'll check the result when it's done." Seems reasonable because the LLM reports success and the feature visually works when tested.
**ROOT CAUSE:** LLMs do not proactively apply engineering best practices. They solve the immediate request via the path of least resistance: appending code to existing files, skipping refactoring, ignoring separation of concerns. Without continuous human oversight, code quality degrades silently while features appear to work.
**RATIONALE:** The visible output (feature works) masks the invisible problem (code structure degrades). Each unsupervised feature adds to a monolith. By the time the developer checks, the codebase has accumulated thousands of lines in single files, duplicated logic, and inconsistent patterns. The refactoring cost grows exponentially with the amount of unsupervised work.

---

## SYMPTOMS

- Single CSS file exceeds 1000+ lines after a session of inattention
- Single JavaScript file exceeds 5000+ lines with all logic interleaved
- LLM switches between server-side and client-side approaches inconsistently
- Dead code accumulates from refactorings the LLM did without cleanup
- setTimeout calls without corresponding clearTimeout (memory leaks)

## CORRECTION

Monitor LLM output continuously during coding sessions. After every 3-5 features, pause to inspect:
1. File sizes — any file growing beyond ~500 lines needs splitting
2. Code organization — is new code going to the right module?
3. Consistency — is the LLM following the same patterns as before?

If you must step away, commit the current state first. Review the diff when you return before allowing the LLM to continue.

**NOT TO CONFUSE WITH:** Batching simple, repetitive tasks (e.g., "add these 5 similar test cases") where the output is predictable and the risk of structural degradation is low.

## OPERATIONAL CONSTRAINTS
**FOR production-quality AI-assisted code TO SUCCEED:**

NEVER:
- Leave the LLM generating code while doing another activity [explicit — ROOT CAUSE]
- Allow more than 5 features without a file size and structure inspection [explicit — CORRECTION step 1]
- Let the LLM continue after returning from an absence without reviewing the diff [explicit — CORRECTION]

ALWAYS:
- Monitor LLM output continuously during active coding sessions [explicit — CORRECTION]
- Commit current state before stepping away [explicit — CORRECTION]
- Inspect file sizes, code organization, and pattern consistency after every 3-5 features [explicit — CORRECTION]

GATE: Developer is actively monitoring the session (not multitasking). If false, commit and pause.

## SOURCE
https://akitaonrails.com/2026/02/01/vibe-code-fiz-um-editor-de-markdown-do-zero-com-claude-code-frankmd-parte-2/
