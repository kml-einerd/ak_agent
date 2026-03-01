# HEURISTIC: LLM Billing as Engineering Metric

**DOMAIN:** ai-workflow
**RULE:** Track LLM API costs per pipeline run (tokens in/out per provider, cost per job, total cost) as an engineering metric — a prompt change that costs 3x more is a performance bug, not just a billing concern.
**APPLIES WHEN:** Any production system that makes LLM API calls, especially pipelines with multiple LLM steps where cost can compound (content generation, classification, summarization, enrichment).
**RATIONALE:** Without billing visibility in the test pipeline, a "refactored" prompt that increases output tokens by 3x goes unnoticed until the monthly bill arrives. By treating cost as a visible metric in every pipeline run — displayed alongside duration, success rate, and item counts — cost regressions are caught during development, not in production. Akita's integration pipeline prints a billing summary table (input tokens, output tokens, cost per provider) after every run. This also enables informed trade-offs: "this prompt produces better results but costs 2x more per run" is a decision with data, not a surprise.
**COUNTER-INDICATION:** For low-volume applications where total LLM cost is negligible (< $10/month), the overhead of tracking per-run costs may exceed the savings. Also not applicable when using fixed-cost LLM subscriptions (unlimited tokens per month) where per-call cost is irrelevant.

## SOURCE
https://akitaonrails.com/2026/02/20/testes-de-integracao-em-monorepo-bastidores-do-the-m-akita-chronicles/
