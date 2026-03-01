# CONCEPT: Pareto 90/10 in Software

**DOMAIN:** ai-workflow
**DEFINITION:** The observation that in real software development, approximately 10% of the total effort produces a "working" prototype, while the remaining 90% of effort goes into making that prototype production-ready: security hardening, error handling, configuration management, refactoring, testing, input validation, deployment automation, i18n, and edge case handling. This is the Pareto principle applied to software, but empirically closer to 90/10 than the theoretical 80/20. In Akita's TV Clipboard project: 1 hour (10%) produced a functioning app; 11+ additional hours (90%) were spent on the 14 categories of hardening that separate a toy from production software.
**NOT:** Not the claim that 90% of work is unnecessary — every one of those hardening steps exists because a real failure mode demands it. Not an argument against prototyping — the 10% "make it work" phase is essential for validating the idea. Not a suggestion to skip the 90% — skipping it is exactly what produces insecure, brittle software. The concept names the gap between "works on my machine" and "works in production" so it can be planned for, not discovered after deadline.
**RATIONALE:** Without this concept named explicitly, teams and individuals consistently underestimate the work remaining after a prototype "works." With AI coding agents, the 10% phase shrinks further (an LLM can produce a working prototype in minutes), making the gap even more deceptive. The prototype arrives so fast that it feels "almost done" when it's actually 10% done. Naming the 90/10 ratio calibrates expectations and prevents premature declarations of completion.

---

## REFERENCED BY

- base/conceitos/concept-funciona-ja.md
- base/anti-patterns/antipattern-vibe-coding-without-expertise.md
- base/heuristicas/heuristic-scope-inflation-vibe-coding.md

## SOURCE
https://akitaonrails.com/2026/01/28/vibe-code-eu-fiz-um-appzinho-100-com-glm-4-7-tv-clipboard/
