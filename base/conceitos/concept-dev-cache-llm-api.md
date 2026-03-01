# CONCEPT: DevCache for LLM API

**DOMAIN:** ai-workflow
**DEFINITION:** A file-based caching layer that intercepts LLM API calls during development and integration testing, storing responses as JSON files keyed by namespace and content hash. Active only in non-production environments (integration, development). First execution calls the real API and saves the result; subsequent executions return the cached response at zero cost. Includes cache-busting mechanism (FORCE=1) for when prompts change and fresh responses are needed. TTL of 1 day prevents serving stale data across sessions while allowing unlimited iteration within a session.
**NOT:** Not a production cache (never active in production — LLM responses must be fresh for real users). Not a mock (actual API responses are cached, not fabricated data). Not prompt caching (which is an API-level feature that reduces input token costs). DevCache operates at the application level, caching complete responses to avoid re-executing entire API calls. Not a replacement for testing with real responses — it caches real responses, it doesn't simulate them.
**RATIONALE:** Without DevCache, iterating on an LLM-powered pipeline that makes 8+ API calls per run costs $0.40+ per iteration. Over a day of active development (10+ iterations), costs reach $4+ with no code benefit — the same prompts producing similar outputs repeatedly. DevCache converts the cost model from per-iteration to per-change: you only pay when you actually modify a prompt and bust its cache. This makes intensive iteration financially viable and removes the psychological barrier of "this run will cost money."

---

## REFERENCED BY

- base/protocolos/protocol-integration-testing-hierarchy.md

## SOURCE
https://akitaonrails.com/2026/02/20/testes-de-integracao-em-monorepo-bastidores-do-the-m-akita-chronicles/
