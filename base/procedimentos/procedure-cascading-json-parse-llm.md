# PROCEDURE: Cascading JSON Parse for LLM

**TRIGGER:** Parsing structured JSON output from an LLM response where the format is not guaranteed
**DOMAIN:** ai-workflow
**PRE-CONDITIONS:** LLM has been prompted to return JSON; expected fields are known; fallback behavior for partial data is defined

---

## STEPS

1. Attempt direct parse (json.loads / JSON.parse on raw response) → succeeds in ~70% of cases when LLM returns clean JSON
2. If direct parse fails, extract by brace balancing: find the first `{`, count open/close braces to find the matching `}`, parse the extracted substring → catches ~20% of cases where LLM wraps JSON in markdown fences or adds text before/after
3. If brace balancing fails, use regex field salvage: extract individual fields with patterns like `"type"\s*:\s*"([^"]*)"`, `"description"\s*:\s*"([^"]*)"` and construct a partial object → salvages the last ~10% where JSON is structurally broken but field values are readable
4. If all three levels fail, log the raw response for debugging and return a structured error/default object → no silent data loss; failure is visible and recoverable

**ON_FAILURE[step-2]:** If nested JSON with many levels, the brace balancing may match wrong closing brace — add depth tracking or limit to first-level object
**ON_FAILURE[step-3]:** Regex salvage produces partial data — mark the result with a confidence flag (e.g., `"parse_method": "regex_salvage"`) so downstream consumers know it's degraded

---

## DONE WHEN
- Every LLM response produces either a fully parsed JSON object or a clearly marked partial/error result (verified by checking that no response returns null/undefined without an error flag)
- Zero responses are silently dropped (verified by comparing input count to output count)
- The cascade is tested with known-bad inputs: markdown fences, trailing text, truncated JSON, and missing braces all produce a result or structured error

## SOURCE
https://akitaonrails.com/2026/02/23/vibe-code-fiz-um-indexador-inteligente-de-imagens-com-ia-em-2-dias/
