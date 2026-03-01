# AKITA VAULT — ENRICHMENT LOG

**Date:** 2026-02-28
**Pipeline:** 02-enrichment.md (Multi-Agent Enrichment Pass)
**Input:** 63 elements from extraction pass
**Output:** 18 elements enriched (14 constraint, 2 rationale, 2 reclassification)

---

## RULE 1 — Limitation to Constraint (14 elements)

Each element below received an OPERATIONAL CONSTRAINTS block (NEVER/ALWAYS/GATE) inserted before the SOURCE section.

| # | Element | Gate Condition |
|---|---------|---------------|
| 1 | antipattern-llm-unsupervised-coding | Developer is actively monitoring the session (not multitasking). If false, commit and pause. |
| 2 | antipattern-no-architecture-rules-upfront | CLAUDE.MD (or equivalent) exists and contains at minimum: architecture rules + file organization + naming conventions. If false, create it before proceeding. |
| 3 | antipattern-reinventing-wheel-llm | The feature being built has no well-known library solving the same problem, OR the library doesn't cover the specific domain need. If false, use the library. |
| 4 | antipattern-funciona-ja-accumulation | Last consolidation cycle was fewer than 5 features ago. If false, consolidate before adding the next feature. |
| 5 | antipattern-vibe-coding-without-expertise | Developer can independently choose and justify an architecture for the project type AND diagnose bugs by reading error messages. If false, pair with an experienced developer. |
| 6 | antipattern-frontend-equals-framework | Project has genuine client-side state management needs (dashboards, editors, real-time collaboration). If false, use static generator + utility CSS. |
| 7 | antipattern-catch-all-error-retry | Every `retry_on` call specifies a named exception class (not StandardError/Exception). If false, refactor retry logic. |
| 8 | antipattern-one-shot-prompt | Current approach is iterative pair programming (not spec-in, code-out). If false, restructure approach. |
| 9 | antipattern-multi-task-mega-prompt | Current prompt contains exactly one task type. If false, split into sequential prompts. |
| 10 | heuristic-scope-inflation-vibe-coding | Written scope boundary exists and was reviewed within last 5 features. If false, stop adding features and review scope against original definition. |
| 11 | heuristic-bigger-newer-not-better | Latency and cost are relevant constraints. If false, larger model may be justified for marginal quality gains. |
| 12 | heuristic-match-model-to-harness | Task is complex/agentic (multi-step tool use, file editing, iterative debugging). If false, harness mismatch is negligible. |
| 13 | heuristic-agent-skills-token-cost | Using per-token billing AND context window is limited (<200K tokens). If false, token overhead may be acceptable. |
| 14 | heuristic-rag-vs-lora-knowledge | *(superseded by Rule 4 reclassification — see below)* |

---

## RULE 2 — Rationale Reconstruction (2 elements)

Each element below had its RATIONALE replaced with a multi-step reasoning chain.

| # | Element | Steps | Derivation |
|---|---------|-------|------------|
| 15 | heuristic-i18n-delegated-to-llm | 2-step chain | [partial — derived from existing rationale + source article] |
| 16 | protocol-layered-rate-limiting | 3-step chain | Steps 1,3 [explicit], step 2 [derived] |

**Note:** heuristic-i18n-delegated-to-llm required revision during validation — original step 1 used general LLM knowledge not derivable from source. Revised to 2-step chain starting from derivable content.

---

## RULE 3 — REFERENCE to PROTOCOL Reclassification (1 element)

| # | Old Path | New Path | Reason |
|---|----------|----------|--------|
| 17 | base/referencias/reference-llm-sampling-agent-loops.md | base/protocolos/protocol-llm-sampling-agent-loops.md | Contains signal→diagnose→intervene pattern (4-row EVALUATION table), model-specific settings table, TRADE-OFFS, and ESCALATE WHEN — qualifies as PROTOCOL, not REFERENCE |

---

## RULE 4 — HEURISTIC to PROTOCOL Reclassification (1 element)

| # | Old Path | New Path | Reason |
|---|----------|----------|--------|
| 18 | base/heuristicas/heuristic-rag-vs-lora-knowledge.md | base/protocolos/protocol-rag-vs-lora-knowledge.md | Requires multi-criteria evaluation (knowledge change frequency x corpus size x context window x cost model x session count) — exceeds HEURISTIC's "deterministic guidance without situational judgment" criterion |

---

## VALIDATION SUMMARY

- 18 enrichments submitted to Validator
- 17/18 approved immediately
- 1/18 revised (heuristic-i18n-delegated-to-llm: derivability violation in step 1)
- 18/18 approved after revision
- 0 Council cases
- 0 disputes

---

## POST-ENRICHMENT ELEMENT COUNTS

| Type | Before | After | Delta |
|------|--------|-------|-------|
| Procedures | 12 | 12 | 0 |
| Protocols | 10 | 12 | +2 |
| Anti-Patterns | 9 | 9 | 0 |
| Concepts | 7 | 7 | 0 |
| Heuristics | 22 | 21 | -1 |
| References | 3 | 2 | -1 |
| **Total** | **63** | **63** | **0** |
