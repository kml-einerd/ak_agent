# HEURISTIC: LLMs Default to Worst Performance

**DOMAIN:** ai-workflow
**RULE:** Always explicitly specify performance requirements in prompts. LLMs default to the most conservative (slowest but "safest") implementation for any feature.
**APPLIES WHEN:** Requesting any feature that involves repeated operations: auto-save, input handling, real-time updates, search, filtering, or any operation triggered by user interaction.
**RATIONALE:** LLMs optimize for correctness, not performance. When asked to implement "auto-save", they will save on every keystroke. When asked for "word count statistics", they will recalculate on every character typed. When asked for "preview update", they will re-render even when the preview panel is hidden. This is because the simplest correct implementation IS the most aggressive one — debouncing, throttling, and conditional execution require explicit performance awareness that LLMs don't apply by default. Performance is always a trade-off with correctness, security, and maintainability — only an experienced developer knows which trade-off is appropriate for each case.
**COUNTER-INDICATION:** One-time operations (file save on button click, form submission) where performance optimization would add unnecessary complexity.

## SOURCE
https://akitaonrails.com/2026/02/01/vibe-code-fiz-um-editor-de-markdown-do-zero-com-claude-code-frankmd-parte-2/
