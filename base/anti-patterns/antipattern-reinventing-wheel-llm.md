# ANTI-PATTERN: Reinventing Wheel with LLM

**DOMAIN:** ai-workflow
**APPEARS AS:** "The LLM can build anything from scratch, so I don't need external libraries." Since LLMs produce working code quickly, it feels faster to let the LLM implement a custom solution than to integrate an existing library. The custom solution works for simple cases initially.
**ROOT CAUSE:** Complex, well-known problems (text editors, syntax highlighting, rich text editing, date handling, etc.) have thousands of edge cases discovered over years of development. An LLM will produce a solution that handles the common cases but misses the long tail of edge cases. Established open-source libraries have already encountered and solved these edge cases.
**RATIONALE:** Akita's custom textarea with syntax highlighting worked initially but broke on: line wrapping alignment, scroll synchronization, cursor positioning with formatted text, and several other edge cases. Switching to CodeMirror (an established library) required ~6000 lines of changes across 5+ commits and 3+ hours of stabilization. Had CodeMirror been used from the start, those 3+ hours and 6000 lines would have been unnecessary.

---

## SYMPTOMS

- Increasing number of "edge case" bugs for a feature that seemed simple
- LLM spending multiple commits fixing alignment, positioning, or synchronization issues
- The custom implementation requires a "hidden layer" (e.g., a background div synced with a foreground div)
- You find yourself saying "this should be simpler" after the third fix for the same feature area

## CORRECTION

Before letting the LLM build a complex feature from scratch, ask:
1. "Is there a well-known open-source library that solves this?" (CodeMirror, Monaco, Quill for editors; Day.js for dates; etc.)
2. If yes, instruct the LLM to integrate the library instead of building from scratch.
3. If the library doesn't cover your specific needs, use it as a base and extend — don't start from zero.

Rule of thumb: if the feature you're building has its own Wikipedia article, use a library.

**NOT TO CONFUSE WITH:** Building simple, project-specific utilities that no library covers (e.g., a custom frontMatter generator for your specific Hugo setup). Libraries solve generic problems; custom code solves domain-specific ones.

## OPERATIONAL CONSTRAINTS
**FOR avoiding unnecessary custom implementations TO SUCCEED:**

NEVER:
- Let the LLM build a complex feature from scratch without first checking for existing libraries [explicit — CORRECTION]
- Accept a custom implementation for a problem with its own Wikipedia article [explicit — CORRECTION rule of thumb]

ALWAYS:
- Ask "Is there a well-known open-source library for this?" before building complex features [explicit — CORRECTION step 1]
- When a library exists, instruct the LLM to integrate it rather than build from scratch [explicit — CORRECTION step 2]

GATE: The feature being built has no well-known library solving the same problem, OR the library doesn't cover the specific domain need. If false, use the library.

## SOURCE
https://akitaonrails.com/2026/02/01/vibe-code-fiz-um-editor-de-markdown-do-zero-com-claude-code-frankmd-parte-2/
