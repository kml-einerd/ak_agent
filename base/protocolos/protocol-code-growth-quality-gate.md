# PROTOCOL: Code Growth Quality Gate

**DOMAIN:** ai-workflow
**APPLIES TO:** Any AI-assisted coding session where features are being added incrementally, especially when the developer is not reviewing every line the LLM produces
**RATIONALE:** LLMs do not proactively refactor code. They add new functionality to existing files following the path of least resistance, exactly like an unsupervised junior developer. Without explicit file size and structure monitoring, a project will accumulate monolithic files (1000+ line CSS, 5000+ line JS) that become increasingly fragile and hard to debug. The developer must impose structure because the LLM will not.

---

## EVALUATION

| SIGNAL | DIAGNOSE | INTERVENE |
|--------|----------|-----------|
| Any single source file exceeds ~500 lines | LLM has been accumulating code without splitting | Instruct LLM to break the file into logically separated modules. Verify each module works independently. |
| All CSS is in one file (application.css, styles.css) | No style organization was specified | Instruct LLM to split by component/feature area. Include theme files separately. |
| All JavaScript logic in a single controller/file | No modular architecture was specified in CLAUDE.MD | Instruct LLM to extract into separate controllers/modules by domain. |
| Routes are manually defined instead of using framework conventions (e.g., RESTful resources in Rails) | LLM defaulted to manual approach instead of framework idioms | Instruct LLM to refactor to framework-idiomatic patterns. |

**TRADE-OFFS:** Frequent refactoring slows feature velocity but prevents the "castle of cards" where changing one thing breaks ten others.

**ESCALATE WHEN:** Refactoring would require redesigning the core architecture — at that point, evaluate whether to continue or restart with proper CLAUDE.MD conventions.

## SOURCE
https://akitaonrails.com/2026/02/01/vibe-code-fiz-um-editor-de-markdown-do-zero-com-claude-code-frankmd-parte-2/
