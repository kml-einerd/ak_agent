# PROTOCOL: Integration Testing Hierarchy

**DOMAIN:** testing
**APPLIES TO:** Projects with multiple applications or services sharing data via filesystem, APIs, or implicit contracts — especially when LLM-generated content is part of the pipeline
**RATIONALE:** Each testing layer catches a fundamentally different class of bug. Unit tests prove pieces work in isolation but miss integration failures (parser A writes format X, parser B expects format Y). CI proves code health but uses mocked data. Integration with real data catches the edge cases that mocked data is too clean to contain (Japanese titles breaking slugify, API rate limits not present in mocks, nil values in old records). Visual preview catches rendering bugs no automated test can detect. Skipping any layer creates a blind spot.

---

## EVALUATION

| SIGNAL | DIAGNOSE | INTERVENE |
|--------|----------|-----------|
| Tests pass but deployed system produces wrong output | Unit tests mock too aggressively; real integration never tested | Add integration layer: rsync production data, run full pipeline with real APIs, validate output structure |
| Integration pipeline is too expensive to run frequently (API costs) | LLM calls not cached in dev/integration environment | Implement DevCache: file-based cache per namespace+key, active only in integration env, TTL 1 day, FORCE=1 to bust |
| Pipeline runs without exception but output is incomplete (2 items instead of 10) | "No exception ≠ correct" — structural validation missing | Add preflight checks: validate file existence, minimum item counts, required markers, data-specific constraints |
| Format change in one app silently breaks another app that reads its output | Implicit contract between apps not verified | Cross-app integration test: run producer, then consumer, in same pipeline; verify end-to-end output |
| Prompt change increases API cost 3x without anyone noticing | No billing visibility in test pipeline | Add billing summary to every pipeline run: tokens in/out per provider, cost per job, total cost |
| CI is green but newsletter/report has visual rendering bugs | Automated tests cannot catch visual issues | Add visual preview step: render final output as HTML (light/dark), manual browser inspection |

**TRADE-OFFS:** Full integration testing costs money (~$0.40 per run in API calls), takes longer (~3 minutes vs 7 seconds for unit tests), and requires production data access. But it catches bugs that unit tests fundamentally cannot detect. Run integration before deploys or after prompt changes, not on every commit.

**ESCALATE WHEN:** Integration data is too sensitive to copy locally (PII, financial data). In that case, run integration tests on a secured environment with production-equivalent data, or implement data anonymization before rsync.

## SOURCE
https://akitaonrails.com/2026/02/20/testes-de-integracao-em-monorepo-bastidores-do-the-m-akita-chronicles/
