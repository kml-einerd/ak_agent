# HEURISTIC: Preflight Structural Validation

**DOMAIN:** testing
**RULE:** After any LLM-powered generation pipeline runs, validate the output structure (file existence, item counts, required markers, data constraints) before consuming the output — never trust "ran without exception" as proof of correctness.
**APPLIES WHEN:** Any pipeline where LLM generates structured output that downstream systems consume: newsletter sections, content generation, report building, data enrichment, batch classification.
**RATIONALE:**
1. LLMs fail in "creative" ways that don't raise exceptions: truncated responses that parse as valid JSON with fewer items, missing sections that leave no trace, format changes that produce valid but wrong structures. [explicit]
2. A generation job can return success (exit code 0) while producing a Markdown file with 2 items instead of 10, or missing required markers like [COMMENTARY] that downstream assembly depends on — "ran without exception" is not proof of correctness. [explicit]
3. Preflight checks (file exists? item count >= minimum? required markers present? data constraints met?) catch these silent failures before they propagate, producing a per-section status (pass, degraded, fail, skip) that gates downstream processing. [derived]
**COUNTER-INDICATION:** For one-off exploratory generation where output quality is manually reviewed anyway, preflight adds overhead without benefit. The heuristic applies to automated pipelines where output feeds into the next stage without human inspection.

## SOURCE
https://akitaonrails.com/2026/02/20/testes-de-integracao-em-monorepo-bastidores-do-the-m-akita-chronicles/
