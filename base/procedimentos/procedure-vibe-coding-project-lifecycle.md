# PROCEDURE: Vibe Coding Project Lifecycle

**TRIGGER:** Starting a new AI-assisted (vibe coding) project from scratch
**DOMAIN:** ai-workflow
**PRE-CONDITIONS:** Developer has enough experience to choose architecture, frameworks, and coding conventions. LLM subscription/plan is selected and active.

---

## STEPS

1. Choose architecture and frameworks upfront (Rails, Node, etc.) → documented decision with rationale
2. Create CLAUDE.MD or CONTRIBUTING.MD with architecture rules, coding conventions, file organization patterns, and naming standards → configuration file committed to repo
3. Implement features one at a time, each with proper abstractions and immediate test coverage → each feature passes its tests before moving to next
4. After every 10-15 features, run a refactoring pass: check file sizes, split monoliths, consolidate abstractions → no single file exceeds ~500 lines
5. Periodically (every 20-30 commits) check for memory leaks (setTimeout without clearTimeout), security holes, and dead code → clean audit with no critical findings
6. Run performance optimization pass: identify aggressive operations (auto-save per keystroke, unnecessary re-renders), specify explicit performance requirements → measurable performance improvement

**ON_FAILURE[step-3]:** If tests fail, provide LLM with specific error messages, logs, and reproduction steps — never say just "it broke"
**ON_FAILURE[step-4]:** If refactoring introduces regressions, use git bisect approach to identify which commit introduced the break
**ON_FAILURE[step-6]:** If performance is still poor, check if the LLM built something from scratch that a well-known library already solves (e.g., CodeMirror for editors)

---

## DONE WHEN
- All features pass automated tests (target: 70%+ coverage)
- No monolithic files (CSS, JS, or backend) exceeding 500 lines
- No known memory leaks or critical security holes
- Performance is acceptable for the target use case
- Code is modular enough that changing one feature doesn't break unrelated features

## SOURCE
https://akitaonrails.com/2026/02/01/vibe-code-fiz-um-editor-de-markdown-do-zero-com-claude-code-frankmd-parte-2/
