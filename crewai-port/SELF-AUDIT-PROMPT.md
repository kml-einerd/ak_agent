# SELF-AUDIT — Verificação de Completude

Você terminou o port CrewAI → PM-OS Go. Antes de entregar, **rode este audit contra seu próprio output**.

**Trabalhe em `/tmp/crewai-port-output/`**. Compare com `FILE-MAP.md` + `CHECKLIST.md` originais.

---

## PARTE 1 — Inventário de arquivos

Para CADA um dos 65 arquivos listados em `FILE-MAP.md`, responda:

```
[TIER A]
A1 fingerprint.go              → STATUS | LOC | TEST_FILE | TEST_PASS | COVERAGE%
A2 constants merged            → STATUS
A3 config.go                   → STATUS | LOC | TEST_FILE | TEST_PASS | COVERAGE%

[TIER B]
B1 types.go                    → STATUS | LOC | TEST_FILE | TEST_PASS | COVERAGE%
...
```

STATUS = `DONE` | `PARTIAL` | `SKIPPED` | `MISSING`

Para qualquer STATUS != DONE, explicar em 1 linha por quê.

---

## PARTE 2 — Rodar gates técnicos

Execute NA RAIZ de `/tmp/crewai-port-output/`:

```bash
# Gate 1 — compila
go mod tidy
go build ./... 2>&1 | tee build.log

# Gate 2 — vet
go vet ./... 2>&1 | tee vet.log

# Gate 3 — testa
go test ./... -count=1 2>&1 | tee test.log

# Gate 4 — race detector
go test ./... -race -count=1 -timeout 5m 2>&1 | tee race.log

# Gate 5 — coverage
go test ./... -cover -coverprofile=coverage.out 2>&1 | tee cover.log
go tool cover -func=coverage.out | tail -5
```

**Cole output resumido no audit** (não precisa full log — só erros + totais).

---

## PARTE 3 — Validar regras hard de RULES.md

Responda SIM/NÃO com evidência (grep/arquivo):

1. **Sem pydantic?** `grep -rn "BaseModel\|pydantic\|Field(\|PrivateAttr" pkg/` → 0 matches?
2. **Sem decorators Python?** `grep -rn "@\w\+(" pkg/ --include="*.go"` → 0 matches (exceto em strings/comments)?
3. **Sem asyncio/await?** `grep -rn "asyncio\|async def\|await " pkg/ --include="*.go"` → 0 matches?
4. **Sem `interface{}` preguiçoso?** `grep -rn "interface{}" pkg/` → quantos? (aceitável só em JSON boundaries)
5. **Context.Context primeiro param?** Grep funções com I/O — todas começam com `ctx context.Context`?
6. **Doc comments em exports?** `go doc ./pkg/...` não mostra `undocumented`?
7. **Deps permitidas?** Listar `go list -m all | grep -v indirect`. Só os listados em `RULES.md` seção 1?
8. **Error wrapping com %w?** `grep -rn "fmt.Errorf" pkg/ | grep -v "%w" | grep -v "_test.go"` → 0 matches non-test?
9. **`snake_case.go` nomes?** `find pkg/ -name "*.go" -not -name "*-*.go"` — zero arquivos com hífen?
10. **Package doc comments?** `grep -L "^// Package" pkg/*/*.go` → 0 arquivos sem doc (exceto `*_test.go`)?

---

## PARTE 4 — Validar semântica

Por Tier, responda SIM/NÃO + evidência:

### Tier A — Security
- [ ] `Fingerprint` tem UUID4 random
- [ ] `Fingerprint` tem UUID5 seed-based (mesmo seed → mesmo UUID) — **mostra teste**
- [ ] Metadata validator rejeita >10KB — **mostra teste**
- [ ] Metadata rejeita nesting >1 level — **mostra teste**

### Tier B — Hooks
- [ ] `LLMHook` interface tem `Before` + `After`
- [ ] `ToolHook` interface tem `Before` + `After`
- [ ] Registry é thread-safe — **mostra teste `-race`**
- [ ] Chain preserva ordem de registration — **mostra teste**

### Tier C — Events
- [ ] `EventBus` tem `Register` + `Emit` + `WithScope`
- [ ] Crew→Run renaming feito (grep `Crew` em events/types/ → 0 matches)
- [ ] Agent events NÃO portados (grep `Agent` em events/types/ → 0 matches)
- [ ] Handler dependency graph funciona (teste DAG topológico)

### Tier D — Guardrails
- [ ] `HallucinationGuardrail` detecta sem grounding — **mostra teste**
- [ ] `LLMGuardrail` tem threshold + retry bounded
- [ ] Output format enum tem RAW + JSON (sem PYDANTIC)

### Tier E — HITL
- [ ] `Provider` interface pluggable
- [ ] Signed resume token usa HMAC-SHA256 — **mostra código**
- [ ] Token expiry ≤ 7 days
- [ ] Emit routing (approved/rejected) funciona

### Tier F — Checkpoint
- [ ] `Provider` interface implementada por JSON + Supabase
- [ ] `SupabaseProvider` usa REST PostgREST (não Postgres direto)
- [ ] Fork/branch support (runtime state)

### Tier G — Skills
- [ ] Parse YAML frontmatter funciona
- [ ] Parse markdown body funciona
- [ ] Loader walk filesystem

### Tier H — Utilities
- [ ] `ratelimit/rpm.go` token bucket funciona — **mostra teste concorrência**
- [ ] `types/callback.go` dotted path resolver funciona

### Tier I — Tools concepts
- [ ] `types.go` novo NÃO conflita com `registry.go` do PM-OS
- [ ] Campos `result_as_answer` + `max_usage_count` documentados em `PORT-REPORT.md` como merge candidates

### Tier J — MCP
- [ ] stdio transport testado contra servidor mock
- [ ] SSE transport testado
- [ ] HTTP transport testado
- [ ] Tool description sanitization implementada (anti prompt-injection)
- [ ] Reconnection funciona

### Tier K — Memory
- [ ] `Episode` struct compatível com schema pgvector
- [ ] `Scope` hierarchy funciona
- [ ] `PgvectorStorage` implementa Backend interface
- [ ] `Backend` interface cumprida pelos providers
- [ ] Recall ordering: recency + semantic + importance

---

## PARTE 5 — Arquivos que NÃO deveriam existir

Rode e reporte count:

```bash
# gocrewai vendor leaks?
grep -rn "Ecook14/gocrewwai" pkg/ | wc -l    # deve ser 0

# agent/crew paradigm leaks?
grep -rn "AgentConfig\|CrewConfig\|NewAgent\|NewCrew" pkg/ | wc -l    # deve ser 0

# LLM provider zoo leaks?
find pkg/llm -type f 2>/dev/null | wc -l    # deve ser 0 (PM-OS tem AnthropicDirect próprio)

# Decorator attempt files?
grep -rn "reflect.TypeOf.*Func\|// decorator" pkg/ | wc -l    # review se > 0

# Panic calls?
grep -rn "panic(" pkg/ --include="*.go" | grep -v "_test.go" | wc -l    # deve ser ~0
```

---

## PARTE 6 — Output final

Gera arquivo `/tmp/crewai-port-output/AUDIT-REPORT.md` com TODAS as respostas acima estruturadas:

```markdown
# Audit Report — CrewAI → PM-OS Port

## Summary
- Files DONE: X / 65
- Files PARTIAL: Y
- Files SKIPPED: Z
- Files MISSING: W
- Build status: PASS|FAIL
- Test pass rate: X/Y
- Coverage: X%

## Part 1 — File inventory
<tabela completa>

## Part 2 — Technical gates
<output resumido dos 5 comandos>

## Part 3 — Hard rules
<10 SIM/NÃO + evidence>

## Part 4 — Semantic validation
<per-tier checkboxes + test file paths>

## Part 5 — Leak check
<counts dos 5 greps>

## Known gaps
<lista explícita de TODOs que deixou pro Akita>

## Confidence score
<dê um score 0-100 de quão pronto está o output pra review do Akita, com justificativa>
```

---

## Regra de ouro do audit

**Seja brutalmente honesto.** Se algo está incompleto ou bugado, declare. Melhor reportar gap claro que vender trabalho incompleto — o Akita vai rodar os mesmos comandos e pegar a diferença.

**Se você identificar gap, NÃO tente consertar agora.** Lista em "Known gaps" e entrega o AUDIT-REPORT.md. Akita decide se conserta ele mesmo ou manda de volta.

**Se passou em todos os gates, declare com confiança.** O trabalho é fluido pra Akita integrar.

Output final: **1 arquivo `/tmp/crewai-port-output/AUDIT-REPORT.md`** + confirmação explícita que os 5 comandos do Gate técnico foram executados.
