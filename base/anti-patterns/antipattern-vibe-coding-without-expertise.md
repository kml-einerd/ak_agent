# ANTI-PATTERN: Vibe Coding Without Expertise

**DOMAIN:** ai-workflow
**APPEARS AS:** "AI can code for me — I don't need to know programming. I'll just describe what I want in natural language and the LLM will build it." This belief is reinforced by impressive demos of simple apps built with a few prompts. The surface appearance is compelling because LLMs genuinely DO produce working code for simple cases.
**ROOT CAUSE:** LLMs replicate patterns from their training data, defaulting to junior-level implementations. They produce code that "works" in the "Funciona Já" sense but with poor architecture, no tests, monolithic files, and hidden technical debt. Only a developer with senior-level experience can: (1) choose the right architecture, (2) detect when the LLM is building a house of cards, (3) instruct proper refactoring, (4) diagnose complex bugs, (5) evaluate performance trade-offs.
**RATIONALE:** Akita explicitly states: "nunca vai sair um app como este com poucos prompts e sem saber exatamente os componentes e técnicas pra usar por baixo." His FrankMD project required knowing Rails RESTful conventions, CodeMirror integration, S3 upload patterns, Docker deployment, i18n best practices, and dozens of other technical decisions an LLM cannot make correctly without expert guidance. The LLM provided 6-7x speed boost, but only because Akita already knew WHAT to ask for.

---

## SYMPTOMS

- User describes features in vague, non-technical terms ("make it faster", "it broke")
- No CLAUDE.MD or architectural constraints defined at project start
- Generated project has zero tests
- All code in 1-2 monolithic files
- User unable to diagnose why a fix didn't work or why a feature has edge cases

## CORRECTION

Before using LLMs for coding, acquire sufficient experience to:
1. Choose and justify an architecture for the project type
2. Write a CLAUDE.MD with framework-specific conventions
3. Review generated code for quality (not just "does it work?")
4. Diagnose bugs by reading error messages and logs
5. Know when to use existing libraries vs building from scratch

The LLM is a force multiplier, not a replacement. "Finalmente eu sinto que chegamos ao elusivo Developer 10x. Basta que você seja sênior primeiro."

**NOT TO CONFUSE WITH:** Using LLMs to learn programming. LLMs are excellent tutors. The anti-pattern is expecting production-quality output without programming knowledge, not using LLMs as learning aids.

## OPERATIONAL CONSTRAINTS
**FOR production-quality output from AI-assisted coding TO SUCCEED:**

NEVER:
- Expect production-quality software from LLM-only coding without programming knowledge [explicit — ROOT CAUSE]
- Deploy AI-generated code without review from an experienced developer [implied — CORRECTION: "precisa passar por revisão de um programador experiente"]

ALWAYS:
- Have the developer provide architecture decisions, framework conventions, and quality review [explicit — CORRECTION]
- Verify the developer can: choose architecture, write CLAUDE.MD, review code quality, diagnose bugs, evaluate library vs custom [explicit — CORRECTION steps 1-5]

GATE: Developer can independently choose and justify an architecture for the project type AND diagnose bugs by reading error messages. If false, pair with an experienced developer.

## SOURCE
https://akitaonrails.com/2026/02/01/vibe-code-fiz-um-editor-de-markdown-do-zero-com-claude-code-frankmd-part-1/
https://akitaonrails.com/2026/02/01/vibe-code-fiz-um-editor-de-markdown-do-zero-com-claude-code-frankmd-parte-2/
