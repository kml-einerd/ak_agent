# Procedimento: Pensamento Invertido para Debug de Orquestração IA

> **Trigger:** Sistema de orquestração de agentes IA falha — tasks não completam, outputs errados, runs stuck, credentials expiram, deploys quebram.
>
> **Princípio:** Mapear tudo que pode dar errado. Eliminar cada caminho de falha. O único caminho que sobra é o que funciona.
>
> **Origem:** 14 bugs encontrados em sessão de 10h no PM-OS (2026-04-07). Cada bug foi encontrado pelo método invertido — perguntar "como isso falha?" em vez de "como isso funciona?"

---

## O Método

```
1. PARAR — não tente mais fixes
2. MAPEAR — liste todo o data flow de ponta a ponta
3. INVERTER — pra cada componente: "como ele falha?"
4. ELIMINAR — pra cada modo de falha: verificar se existe no código
5. O QUE SOBRA — é o caminho que funciona
```

**Regra de ouro:** Se o mesmo erro persiste após 2 fixes, o problema está numa camada que você não está olhando. PARAR e mapear ponta a ponta.

---

## Camada 1: Build e Artefato

### Como falha:
| Modo de falha | Sinal | Causa real |
|---------------|-------|-----------|
| "Binary not found" em runtime | Zelador/preflight bloqueia | Dockerfile errado no build. `gcloud builds submit --tag` usa root Dockerfile, não `deploy/Dockerfile.api` |
| Build SUCCESS mas binário antigo roda | Imagem com digest idêntico ao anterior | Docker cache. `--no-cache` ou mudar algo no layer |
| Build inclui binário mas sem dependências | Crash com "not found" ou "GLIBC not found" | Alpine (musl) vs Debian (glibc). free-code compilado com Bun precisa de glibc |
| Source code falta no build context | `FileNotFound` durante build | `.gitignore` exclui diretório que o Dockerfile COPY precisa. Fix: `.gcloudignore` |
| CMD roda binário errado | Fix "está lá" mas "não executa" | WORKDIR + CMD `./pm-api` resolve pro path errado. COPY pro path que CMD usa |

### Eliminação:
```bash
# Verificar QUAL Dockerfile o build usa:
grep -l "FROM" Dockerfile deploy/Dockerfile.api

# Verificar se binários existem no container:
docker run --rm [image] ls -la /usr/local/bin/picoclaw /usr/local/bin/free-code

# Verificar qual binário o CMD executa:
docker run --rm [image] which pm-api && docker run --rm [image] readlink -f ./pm-api
```

### O que sobra:
`.gcloudignore` override + `deploy/Dockerfile.api` explícito no `--config` + canary test (`docker run [image] [binary] --help`) ANTES de deploy.

---

## Camada 2: Credentials e Auth

### Como falha:
| Modo de falha | Sinal | Causa real |
|---------------|-------|-----------|
| "Not logged in" | free-code recusa executar | `~/.claude/.credentials.json` não existe ou não legível |
| Token expirado mas cache diz OK | Tasks falham com 401 após minutos | Cache bool (`credentialsSynced`) não valida expiresAt do token |
| Token refreshado mas stale persiste | Refresh funciona, próximo request usa stale | Push async pro Secret Manager — goroutine não completou antes do próximo read |
| Volume mount read-only | Write falha silenciosamente | Cloud Run monta secrets como read-only. Subprocess tenta escrever session files → falha sem erro |
| HOME aponta pro volume read-only | Tudo que escreve em $HOME falha | Subprocess herda HOME do container. Volume mount substitui o diretório |
| Token fresco no Secret Manager, stale no container | Instância antiga mantém volume antigo | Cloud Run não atualiza volumes em instâncias vivas. Precisa nova revisão + routing |

### Eliminação:
```bash
# Verificar token no Secret Manager:
gcloud secrets versions access latest --secret=claude-credentials | python3 -c "
import sys,json,time; d=json.load(sys.stdin)
remaining=(d['claudeAiOauth']['expiresAt']-time.time()*1000)/60000
print(f'{remaining:.0f} min remaining')"

# Verificar token no container:
docker run --rm -v $HOME/.claude/.credentials.json:/creds:ro [image] \
  python3 -c "import json; print(json.load(open('/creds'))['claudeAiOauth']['expiresAt'])"

# Testar auth end-to-end:
docker run --rm -v $HOME/.claude/.credentials.json:/tmp/creds:ro [image] sh -c "
  mkdir -p /tmp/home/.claude && cp /tmp/creds /tmp/home/.claude/.credentials.json
  HOME=/tmp/home /usr/local/bin/free-code -p 'say hello' --model sonnet"
```

### O que sobra:
`CredentialCache` com `isTokenFreshOnDisk()` + copy read-only → writable + HOME override + push síncrono pro Secret Manager + zelador check ANTES de cada run.

---

## Camada 3: Executor e Wiring

### Como falha:
| Modo de falha | Sinal | Causa real |
|---------------|-------|-----------|
| Tasks vão pro worker HTTP em vez de PicoClaw local | Worker health OK mas tasks falham | `FallbackExecutor(workerURL)` no main.go. Se workerURL != "", usa HTTP |
| Executor de tasks trocado mas review não | Task 1 OK, review FAIL | `llmCaller` tem fallback separado do task executor. Trocar um não troca o outro |
| Subprocess não encontra config | PicoClaw init falha | `PICOCLAW_CONFIG` env var não propagada ao subprocess |
| HOME override clobra outras env vars | PicoClaw perde config path | Override de HOME substitui PICOCLAW_HOME. Fix: override SOMENTE HOME |
| Modelo não encontrado | "model not found in config" | Nome do modelo com hífen vs ponto: `claude-sonnet-4-6` vs `claude-sonnet-4.6` |

### Eliminação:
```bash
# Verificar qual executor está wired:
grep -n "WithExecutor\|WithQualityLayer\|llmCaller" cmd/pm-api/main.go

# Verificar que TODAS as referências ao worker foram removidas:
grep -n "WorkerLLMCaller\|FallbackExecutor\|workerURL" cmd/pm-api/main.go

# Verificar env vars do subprocess:
# TDD: TestPicoClawExecutor_HomeOverridePreservesEnv
```

### O que sobra:
PicoClaw local pra TUDO (tasks + reviews + spot-checks). `WithCredentials()` pra HOME writable. Zero referências ao worker no path de execução.

---

## Camada 4: Dados e Persistência

### Como falha:
| Modo de falha | Sinal | Causa real |
|---------------|-------|-----------|
| Timestamps ghost (70ms pra run que levou minutos) | `done_at - started_at` impossível | Upsert sobrescreve StartedAt com time.Now() pós-planning |
| Plan JSON perdido no run | `total_tasks: 0` | `UpdateRun(status)` só atualiza status, não salva plan |
| Zero-time leak no upsert | `created_at: "0001-01-01T00:00:00Z"` | `time.Time` struct com omitempty não omite zero value. Precisa `*time.Time` + custom MarshalJSON |
| Duplicate CreateRun | Run status flipando entre planning/running | Engine chama CreateRun (upsert) que sobrescreve campos do handler |
| `seen` map cresce infinito | Memory leak em deploys longos | `realtime.go` nunca faz pruning do map de IDs já vistos |
| Catalog data race | Panic sob carga | `map[string]*Recipe` sem `sync.RWMutex`. Concurrent Save+Get = crash |

### Eliminação:
```go
// TDD: TestRun_MarshalJSON_ZeroTimePtrOmitted
// TDD: TestRun_MarshalJSON_NilTimestampsOmitted
// TDD: TestRun_MarshalJSON_RealTimestampsPreserved

// Grep: zero-time values
grep -rn "time.Time{}" pkg/store/ --include="*.go" | grep -v test

// Race detector:
go test -race ./pkg/recipe/...
```

### O que sobra:
`*time.Time` com custom `MarshalJSON` que nulifica zero pointers + `runPreCreated` flag que faz UpdateRun em vez de CreateRun duplicado + `sync.RWMutex` no Catalog.

---

## Camada 5: Observabilidade

### Como falha:
| Modo de falha | Sinal | Causa real |
|---------------|-------|-----------|
| Logs visíveis localmente, invisíveis no Cloud Run | Linhas em branco no Cloud Logging | Logger usa `{"level":"info"}`. Cloud Run precisa `{"severity":"INFO"}` |
| Health handler diz "ok" com checks falhando | Worker "healthy" com token expirado | `healthHandler` retorna status hardcoded, ignora checks registrados |
| Review parser aceita "NOT APPROVED" como APPROVED | Run APPROVED com output ruim | `strings.Contains("NOT APPROVED", "APPROVED")` = true |
| Erro de credential copy silencioso | Task falha sem explicação | `os.ReadFile` erro ignorado com `if err == nil` sem else-log |

### Eliminação:
```bash
# Verificar severity no logger:
grep -n "severity" pkg/infra/logger.go

# Verificar health handler lê checks:
grep -n "checks\|degraded" pkg/health/server.go

# Verificar word boundary no parser:
grep -n "matchWord\|boundary" pkg/quality/opus_review.go
```

### O que sobra:
Logger com `severity` field + health handler que reflete check state + `matchWord()` com regex boundaries + negation check ("NOT") + credential copy com log explícito de erro.

---

## Camada 6: LLM e Structured Output

### Como falha:
| Modo de falha | Sinal | Causa real |
|---------------|-------|-----------|
| LLM ignora restrições do prompt | `type: "development"` em vez de `"llm"` | Prompt define intenção, não enforcement. Sem enum no schema |
| Recipe com 3 tasks pra intent complexo | Output correto mas inútil | Granularidade depende de quão enfático o prompt é. Gemini gera menos que Claude |
| JSON válido mas semanticamente errado | `version: "1.0.0"` em vez de `"2.0"` | Schema valida estrutura mas não valores sem enum constraints |
| Planning demora 3-5 min | Worker timeout, cold start | Morgan via worker HTTP. Cada request = cold start + token check |

### Eliminação:
```bash
# Verificar enum constraints no schema:
grep -n "enum" pkg/engine/adapters/gemini_planner.go

# Testar com curl:
curl -s -X POST "https://generativelanguage.googleapis.com/v1beta/models/gemini-3.1-pro-preview:generateContent?key=$KEY" \
  -d '{"contents":[...],"generationConfig":{"responseMimeType":"application/json","responseSchema":{...enum...}}}'
```

### O que sobra:
Gemini REST direto (sem worker) + `responseSchema` com enum constraints em `type`, `provider`, `version`, `mode` + `recipeSchema()` como single source of truth.

---

## Protocolo de Debug (o atalho)

Quando algo falha num sistema de orquestração IA:

```
1. QUAL ARTEFATO está rodando?
   → docker run [image] which [binary]
   → Se binário não existe: problema é BUILD (Camada 1)

2. QUAL TOKEN está sendo usado?
   → gcloud secrets versions access latest --secret=[name]
   → Se expirado: problema é CREDENTIALS (Camada 2)

3. QUAL EXECUTOR está wired?
   → grep "WithExecutor\|LLMCaller" cmd/*/main.go
   → Se aponta pro worker: problema é WIRING (Camada 3)

4. O QUE o banco mostra?
   → curl GET /api/runs/{id} → check timestamps, tasks, status
   → Se timestamps impossíveis: problema é DADOS (Camada 4)

5. O QUE os logs dizem?
   → gcloud logging read ... --format=json
   → Se linhas em branco: problema é LOGGING (Camada 5)

6. O QUE o LLM gerou?
   → Check recipe JSON no run.plan
   → Se valores errados: problema é SCHEMA (Camada 6)
```

**Cada camada tem <30s de diagnóstico.** Se seguir na ordem, o problema é encontrado em <3 minutos, não em 3 horas.

---

## Regra Final: O Caminho que Funciona

Quando TODOS os modos de falha são eliminados, o único caminho que resta é:

```
Intent
  → Gemini 3.1 Pro (REST direto, enum schema, 15s)
  → Zelador (binários + credentials + supabase, <1s)
  → PicoClaw local (free-code, HOME writable, credentials copiados)
  → Quality gates (matchWord boundaries, fail-closed, determinísticos)
  → Opus review (PicoClaw local, síncrono, blocking)
  → GCS upload (collector, tar.gz)
  → Supabase (custom MarshalJSON, no zero-time leak)
  → Done (timestamps reais, plan preservado, status correto)
```

Este é o caminho que funciona. Qualquer desvio cai num modo de falha documentado acima.

---

*Extraído de: sessão PM-OS 2026-04-07 (14 bugs, 10h, Keel verificador)*
*Cross-ref: keel-lessons.md (14 lições), SESSION-20260407.md (7 patterns, 7 anti-patterns)*
*Aplicável a: qualquer sistema de orquestração com LLM + subprocess + Cloud Run + Supabase*
