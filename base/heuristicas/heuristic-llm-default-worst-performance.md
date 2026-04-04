# HEURISTIC: LLMs Default to Worst Performance

**DOMAIN:** ai-workflow
**RULE:** Always explicitly specify performance requirements in prompts. LLMs default to the most conservative (slowest but "safest") implementation for any feature.
**APPLIES WHEN:** Requesting any feature that involves repeated operations: auto-save, input handling, real-time updates, search, filtering, or any operation triggered by user interaction.
**RATIONALE:**
1. LLMs optimize for correctness, not performance — when asked to implement "auto-save" they save on every keystroke, "word count statistics" recalculates on every character, "preview update" re-renders even when the panel is hidden. [explicit]
2. The simplest correct implementation IS the most aggressive one — debouncing, throttling, and conditional execution require explicit performance awareness that LLMs don't apply by default. [derived]
3. Performance is always a trade-off with correctness, security, and maintainability — only an experienced developer knows which trade-off is appropriate for each case. [derived]
**COUNTER-INDICATION:** One-time operations (file save on button click, form submission) where performance optimization would add unnecessary complexity.

## SOURCE
https://akitaonrails.com/2026/02/01/vibe-code-fiz-um-editor-de-markdown-do-zero-com-claude-code-frankmd-parte-2/
