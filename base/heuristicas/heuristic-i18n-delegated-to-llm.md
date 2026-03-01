# HEURISTIC: I18n Delegated to LLM

**DOMAIN:** ai-workflow
**RULE:** Always delegate internationalization and translation tasks to LLMs. They are orders of magnitude better than traditional approaches (Google Translate + manual native speaker correction).
**APPLIES WHEN:** A project needs multi-language support (extracting strings, translating UI text, localizing content) in any web or software application.
**RATIONALE:** [partial — derived from: existing rationale + source article LLM i18n workflow]
1. LLMs process text with cross-language semantic understanding, meaning they translate technical jargon in context (e.g., "commit" in git vs "commit" in database) and adapt register/formality per target language — something rule-based translation tools cannot do [derived from existing: "understand context, technical jargon, and cultural nuances"]
2. Therefore, delegating i18n to LLMs produces higher-quality translations with less human correction, and allows string extraction + translation + i18n framework setup in a single pass rather than requiring a developer + translator per language [derived from existing: "extracted all English strings, translated to Portuguese, and added Japanese... in a single refactoring pass"]
**COUNTER-INDICATION:** Legal or medical translations where certified human translators are required by regulation. Also, translations into languages with very low representation in LLM training data may have quality issues.

## SOURCE
https://akitaonrails.com/2026/02/01/vibe-code-fiz-um-editor-de-markdown-do-zero-com-claude-code-frankmd-parte-2/
