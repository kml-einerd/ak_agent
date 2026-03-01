# ANTI-PATTERN: "Funciona Já" Accumulation

**DOMAIN:** ai-workflow
**APPEARS AS:** Add feature → test → it works → move to next feature. Repeat 30-50 times. The rapid visible success of each feature creates a strong positive feedback loop that discourages stopping to refactor. "Why fix what isn't broken?"
**ROOT CAUSE:** In AI-assisted coding, features arrive 6-7x faster than manual coding. This velocity compresses the technical debt accumulation cycle: what would normally take months of neglect happens in hours. Each feature adds code to existing files without restructuring, creating monolithic modules, inconsistent patterns, and hidden coupling. The code "works" (see CONCEPT: Funciona Já) but is a fragile castle of cards.
**RATIONALE:** Akita's FrankMD project accumulated a 1000+ line CSS file, a 5000+ line JavaScript file, and zero tests — all while every feature demonstrably "worked." The refactoring to fix this consumed more time than building the features in the first place. The ratio of feature development to refactoring/testing was roughly 1:1 — half the total project time was spent cleaning up accumulated debt.

---

## SYMPTOMS

- Every feature works when tested individually, but changing one breaks others
- Single files growing rapidly because new features are appended, never reorganized
- Zero or near-zero test coverage despite many "working" features
- Developer feels productive (many features done!) but code is increasingly fragile
- The phrase "it works" is used frequently to justify moving forward

## CORRECTION

Adopt a strict rhythm: for every 3-5 features, force a consolidation cycle:
1. Review file sizes — split anything exceeding ~500 lines
2. Extract repeated patterns into shared modules
3. Write tests for the features just added (aim for 70%+ coverage)
4. Run the full test suite to catch regressions
5. Only then proceed to the next batch of features

The consolidation cycle should be non-negotiable, not "when I feel like it."

**NOT TO CONFUSE WITH:** Legitimate rapid prototyping where the goal IS a throwaway prototype. If you plan to keep the code, you need the consolidation cycle.

## OPERATIONAL CONSTRAINTS
**FOR sustainable code quality during AI-assisted development TO SUCCEED:**

NEVER:
- Add more than 5 features without a consolidation cycle [explicit — CORRECTION]
- Treat "it works" as evidence the code is ready [explicit — SYMPTOMS, ROOT CAUSE]
- Skip consolidation because "we're on a roll" [implied — CORRECTION: "non-negotiable"]

ALWAYS:
- After every 3-5 features: review file sizes, extract repeated patterns, write tests, run full suite [explicit — CORRECTION steps 1-4]
- Maintain minimum 70% test coverage [explicit — CORRECTION step 3]

GATE: Last consolidation cycle was fewer than 5 features ago. If false, consolidate before adding the next feature.

## SOURCE
https://akitaonrails.com/2026/02/01/vibe-code-fiz-um-editor-de-markdown-do-zero-com-claude-code-frankmd-parte-2/
