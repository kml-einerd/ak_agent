# CONCEPT: Implicit Convention LLM Friction

**DOMAIN:** ai-workflow
**DEFINITION:** The phenomenon where programming language features designed to help humans (convention over configuration, DRY via metaprogramming, syntactic sugar, implicit conversions, operator overloading, progressive disclosure) actively hinder LLM reasoning because the model must simulate hidden behavior that isn't visible in the source code. Rails' convention-based approach — where `has_many :comments` implies a comments table, a foreign key, validation, eager loading, dependent destruction, and 20+ methods — requires the LLM to know all implicit behaviors to reason correctly about changes. In contrast, explicit, verbose code with inline metadata (annotations, type declarations, effect tracking) gives the LLM everything it needs in the visible text.
**NOT:** Not an argument against frameworks or conventions for human developers — these conventions exist because they genuinely reduce human cognitive load. Not a recommendation to write verbose code in all cases. The concept names the TENSION: features that reduce human friction increase LLM friction, and vice versa. As AI agents become primary code editors, this tension becomes a design consideration for languages and frameworks.
**RATIONALE:** LLMs process code as token sequences. When behavior is hidden (Rails' `before_action`, Ruby's `method_missing`, Python's `__getattr__`, JavaScript's prototype chain), the LLM must either recall the framework's behavior from training data (unreliable for edge cases and version-specific behavior) or ask for clarification (breaks flow). The ideal code for an LLM has a 3:1 metadata-to-logic ratio — the inverse of human-optimized code. Every function carries its effects, invariants, provenance, and dependency graph inline. This explains why LLMs often perform better with explicit, "boring" languages (Go, Rust) than with "magical" ones (Rails, Django).

---

## REFERENCED BY

- base/heuristicas/heuristic-llm-default-worst-performance.md

## SOURCE
https://akitaonrails.com/2026/02/09/ai-agents-qual-seria-a-melhor-linguagem-de-programacao-para-llms/
