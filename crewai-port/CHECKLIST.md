# CHECKLIST — Critérios de aceitação por arquivo

**Cada arquivo portado DEVE passar em TODOS os gates abaixo antes de ser considerado completo.**

---

## Gate 1 — Compila

- [ ] `go build ./pkg/<target>/...` passa sem erro
- [ ] `go vet ./pkg/<target>/...` sem warnings
- [ ] Imports todos resolvem (nenhum path quebrado)

## Gate 2 — Testa

- [ ] Arquivo `*_test.go` existe no mesmo package
- [ ] `go test ./pkg/<target>/...` passa
- [ ] `go test -race ./pkg/<target>/...` passa (se arquivo tem state concorrente)
- [ ] Cobertura `go test -cover ./pkg/<target>/...` ≥ 70%

## Gate 3 — Semântica preservada

- [ ] Output Go produz mesmo resultado que Python para inputs equivalentes (documentado em teste)
- [ ] Desvios semânticos anotados em comment inline + `PORT-REPORT.md`
- [ ] Validações equivalentes (exemplo: se Python valida `metadata size ≤ 10KB`, Go também)

## Gate 4 — Idiomático

- [ ] Naming segue `RULES.md` seção 5
- [ ] Error handling segue `RULES.md` seção 3 (wrapping com `%w`)
- [ ] Context.Context é 1º parâmetro em I/O
- [ ] Doc comments em todos os exports
- [ ] Sem `interface{}` preguiçoso (apenas `any` em JSON boundaries)

## Gate 5 — Sem side effects proibidos

- [ ] Sem `init()` que altera estado global (exceto registration explícita documentada)
- [ ] Sem `panic()` em library code
- [ ] Sem `time.Sleep()` em testes
- [ ] Sem shared mutable global sem mutex

---

## Checklist específico por Tier

### Tier A — Security

| Item | Fingerprint | Config |
|---|---|---|
| UUID4 random funciona | ✅ | — |
| UUID5 seed determinístico (mesmo seed → mesmo UUID) | ✅ | — |
| Validação metadata (string keys, max 10KB, max 1 level nested) | ✅ | — |
| `to_dict()` / `from_dict()` serialização | ✅ | — |
| Equality por UUID | ✅ | — |
| Hashable | ✅ | — |
| SecurityConfig agrega Fingerprint + version | — | ✅ |

### Tier B — Hooks

- [ ] `LLMHook` interface com `Before`/`After`
- [ ] `ToolHook` interface com `Before`/`After`
- [ ] Chain composition (`wrappers.go`)
- [ ] Registry thread-safe
- [ ] Ordered execution (registration order preserved)
- [ ] Error from hook aborts pipeline

### Tier C — Events

- [ ] `Event` interface portada
- [ ] `EventBus` com `Register()` + `Emit()` thread-safe
- [ ] Handler dependency graph (DAG topológico)
- [ ] Scoped handlers (`WithScope()` method)
- [ ] Event types implementam interface
- [ ] Crew→Run renaming em todos os eventos
- [ ] Context scoping funciona (event_id, parent_id propagam via context.Context)
- [ ] Emission sequence number monotônico
- [ ] Shutdown drena handlers pendentes (graceful)

### Tier D — Guardrails

- [ ] `Guardrail` interface genérica
- [ ] `LLMGuardrail` usa AnthropicDirectExecutor existente (ou mocka em teste)
- [ ] `HallucinationGuardrail` detecta claim sem grounding
- [ ] Retry loop com threshold bounded
- [ ] Emite eventos `guardrail_events`

### Tier E — HITL

- [ ] Provider interface pluggable
- [ ] CLI default provider
- [ ] Signed resume token (HMAC-SHA256, expiry ≤ 7 days)
- [ ] Emit routing (approved/rejected/custom)
- [ ] `HumanFeedbackPending` error para async flow
- [ ] Sync + async modes

### Tier F — Checkpoint

- [ ] `Provider` interface
- [ ] `JSONProvider` para dev/test (file-based)
- [ ] `SupabaseProvider` implementa Provider via PostgREST REST
- [ ] Fork/branch support (runtime state)
- [ ] Resume from checkpoint byID
- [ ] Checkpoint listener wire no event bus

### Tier G — Skills

- [ ] Parse YAML frontmatter
- [ ] Parse markdown body
- [ ] Validate required fields
- [ ] Loader walk filesystem
- [ ] Return SkillMetadata para discovery

### Tier H — Utilities

- [ ] `types/callback.go` dotted path resolver
- [ ] `ratelimit/rpm.go` token bucket
- [ ] `errors/errors.go` domain errors tipados
- [ ] `errors/context_window.go` typed

### Tier I — Tools concepts

- [ ] `types.go` novo arquivo não conflita com registry existente
- [ ] Documentação clara em `PORT-REPORT.md` de quais campos de `base_tool.py` Akita deve merge

### Tier J — MCP

- [ ] stdio transport funciona contra servidor MCP simples (teste com `everything` reference server)
- [ ] SSE transport conecta e recebe events
- [ ] HTTP transport POST + resposta stream
- [ ] Reconnection em caso de drop
- [ ] Tool allowlist funciona
- [ ] Tool description sanitization (anti prompt-injection)
- [ ] Resolver converte MCP tool spec → PM-OS Tool struct
- [ ] Config permite per-tenant allowlist

### Tier K — Memory

- [ ] `Episode`/`Entry` struct compatível com schema pgvector
- [ ] `Scope` path hierarchy funciona (`/tenant/X/recipe/Y`)
- [ ] `Backend` interface cumprida
- [ ] `PgvectorStorage` implementa Backend via Supabase PostgREST REST
- [ ] Embedding via Anthropic API (stub em teste)
- [ ] Recall ordering: recency + semantic + importance (weighted sum)
- [ ] Top-K filter por scope

---

## PORT-REPORT.md — template obrigatório

Arquivo `/tmp/crewai-port-output/PORT-REPORT.md` deve conter:

```markdown
# Port Report — CrewAI → PM-OS

## Summary

- **Files ported:** X / 65
- **Total LOC Python input:** ~11,000
- **Total LOC Go output:** ~Y (medir com `find pkg/ -name '*.go' | xargs wc -l`)
- **Test coverage average:** Z%
- **External deps added:** lista (ou "none beyond allowed")

## Per-tier status

### Tier A — Security
- [x] A1 fingerprint.go (188 LOC, 15 tests, 92% coverage)
- [x] A2 merged
- [x] A3 config.go (95 LOC, 5 tests, 88% coverage)

... (repetir pra todos tiers)

## Deviations (semantic changes)

### security/fingerprint.py → pkg/security/fingerprint.go
- CREW_AI_NAMESPACE replaced with PMOSNamespace (new UUID generated)
- Equality check uses UUID comparison (Python __eq__ equivalent)
- from_dict returns error instead of raising

### state/provider/sqlite_provider.py → pkg/checkpoint/supabase_provider.go
- COMPLETE REWRITE: SQLite dropped in favor of Supabase PostgREST REST
- Schema: table `checkpoints (id, run_id, tenant_id, state_json, created_at)`
- API identical to Provider interface but backend completely different

... (repetir por arquivo com desvio)

## TODOs for Akita

### High priority
- [ ] Wire `pkg/events.GlobalBus` into `pkg/engine/engine.go` RunRecipe
- [ ] Register new event types emitted by ported code
- [ ] Merge concepts from `tools/base_tool.py` (result_as_answer, max_usage_count) into existing `pkg/engine/tools/registry.go`
- [ ] Add pgvector extension SQL migration for `memory_episodes` table
- [ ] Decide if `pkg/skills` needs to integrate with existing `base/` knowledge system

### Medium priority
- [ ] Consolidate logger usage — some ported files use local log.Printf, standardize on pkg/infra/logger
- [ ] Review if ratelimit/rpm.go duplicates existing rate limiter in middleware_quota.go

### Questions for Akita
- Should `RunStartedEvent` replace or complement existing narrator/metrics?
- HITL provider — default to CLI or Telegram (PM-OS has Telegram bot)?
- Memory scope — should `/tenant/X/recipe/Y` also include `/step/Z`?

## External dependencies added

| Dep | Version | Reason | File that needs it |
|---|---|---|---|
| gopkg.in/yaml.v3 | v3.0.1 | skills YAML frontmatter | pkg/skills/parser.go |

## Test execution

```
go test -race -cover ./pkg/...
```

Full output:

<paste full `go test -v` output here>

## Known issues

### Cannot reproduce Python behavior X
- File: `events/event_bus.py:L234`
- Python: uses `contextvars.Token` for nested scope restoration
- Go: simulated with context.Context chain; edge case when scopes overlap asymmetrically may differ
- Workaround: test case `TestEventBus_Scope_Nested` documents expected Go behavior
```

## Regra de ouro

**Se QUALQUER gate do checklist falhar, o arquivo não está pronto. Não marque como feito em PORT-REPORT.md até todos os gates passarem.**
