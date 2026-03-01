# CONCEPT: Funciona Já

**DOMAIN:** ai-workflow
**DEFINITION:** The deceptive state where code produces the correct visible output when tested manually, but has accumulated structural problems: monolithic files, zero test coverage, inconsistent patterns, dead code, memory leaks, and hidden coupling between components. The code "functions" in the sense that the user sees the expected behavior, but it is fragile — changing one thing breaks multiple others unpredictably. In AI-assisted coding, this state is reached much faster than in traditional development because LLMs deliver features 6-7x faster, compressing the technical debt cycle from months to hours.
**NOT:** Not the same as a working prototype or MVP. A prototype explicitly acknowledges its throwaway nature. "Funciona Já" is code that the developer believes is production-ready because every feature visually works, unaware of the structural debt beneath. Also not the same as "good enough" — a conscious decision to accept trade-offs is engineering, while "Funciona Já" is unconscious debt accumulation.
**RATIONALE:** This concept needs explicit naming because it is the central failure mode in vibe coding. Without the label, developers describe the same phenomenon in vague terms ("it got messy", "things started breaking") without recognizing the systemic pattern. Other elements in this knowledge base (ANTI-PATTERN: "Funciona Já" Accumulation, PROTOCOL: Code Growth Quality Gate, PROCEDURE: Vibe Coding Project Lifecycle) all reference this concept as the state they exist to prevent or correct.

---

## REFERENCED BY

- base/anti-patterns/antipattern-funciona-ja-accumulation.md
- base/protocolos/protocol-code-growth-quality-gate.md
- base/procedimentos/procedure-vibe-coding-project-lifecycle.md
- base/anti-patterns/antipattern-llm-unsupervised-coding.md
- base/anti-patterns/antipattern-vibe-coding-without-expertise.md

## SOURCE
https://akitaonrails.com/2026/02/01/vibe-code-fiz-um-editor-de-markdown-do-zero-com-claude-code-frankmd-part-1/
https://akitaonrails.com/2026/02/01/vibe-code-fiz-um-editor-de-markdown-do-zero-com-claude-code-frankmd-parte-2/
