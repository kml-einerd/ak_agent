# HEURISTIC: Dead Code After Refactoring

**DOMAIN:** ai-workflow
**RULE:** After every LLM-assisted refactoring pass, explicitly scan for and remove dead code. LLMs always leave orphaned code behind.
**APPLIES WHEN:** Any refactoring has moved, renamed, or consolidated code across files during an AI-assisted coding session.
**RATIONALE:**
1. LLMs operate within a context window that cannot encompass all project files simultaneously — when moving code from file A to file B, they reliably update file B but frequently forget to remove the original code from file A. [explicit]
2. This dead code causes no immediate bugs (it's simply unused), making it invisible during testing and undetectable by standard CI checks. [derived]
3. Over multiple refactorings, dead code accumulates and creates confusion about which version of a function is actually active. [derived]
**COUNTER-INDICATION:** In early prototyping phases where the code is expected to be thrown away entirely, dead code cleanup is waste. Only applies when the codebase is intended to be maintained.

## SOURCE
https://akitaonrails.com/2026/02/01/vibe-code-fiz-um-editor-de-markdown-do-zero-com-claude-code-frankmd-parte-2/
