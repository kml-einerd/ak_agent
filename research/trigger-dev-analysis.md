# Trigger.dev — Análise Para PM-OS

**Data:** 2026-04-23
**Contexto:** expansão de horizonte. Port CrewAI em andamento via LLM externa. Esta análise é input pra decisão futura — seguir estratégia "LLM externa escreve + Akita integra" ou "Sonnet converte arquivo a arquivo" depende do resultado do port CrewAI atual.

---

## 1. Stack realidade

| Dimensão | Trigger.dev | PM-OS |
|---|---|---|
| Lang | **TypeScript/Node.js** | **Go** |
| Runtime | Docker + Kubernetes | Cloud Run |
| DB | Postgres + **Prisma ORM** | Supabase PostgREST |
| Queue | **Redis + Lua scripts** (MARQS) | in-process + Supabase |
| Front | React Remix | stdlib |
| License | Apache 2.0 ✅ | — |
| LOC | 218k (webapp) + 52k (SDK) + 20k (run-engine) = **~290k LOC TS** | ~60k LOC Go |
| Commits | ativo (grande equipe) | solo |

**Port literal: impossível.** 290k TS → Go seria 400k+ LOC Go, 6 meses full-time.

**Estratégia "Sonnet converte e cola" NÃO se aplica aqui.** Escala errada, paradigma errado (ORM + Redis vs stdlib + PostgREST).

---

## 2. Features mapeadas

### Tier 1 — Conceitos transformadores (genuinamente novos vs CrewAI/PM-OS)

| Feature | Descrição mecânica | Fit PM-OS | Prioridade |
|---|---|---|---|
| **Waitpoints** | Step pausa, persiste state, libera worker. Resume via HTTP token. Zero poll, zero cron fake. | Task-first friendly | **🔥 HIGH** |
| **Execution Snapshots** | Serializar estado completo do run (allOutputs + wave/step pointer) em pontos críticos. Resume mid-wave, não restart wave. | Supera Tier F CrewAI | **🔥 HIGH** |
| **Durable cron até 1 ano** | Scheduler reconcilia, não esquece | OVERLAP (PM-OS tem cron básico) | BAIXA |
| **Long-running sem timeout** | Supervisor drena graceful, não mata em 15min | Cloud Run corta em 60min hoje | MÉDIA |
| **MARQS (Multi-tenant Aware Redis Queue System)** | Fair queue per-tenant. Previne noisy neighbor. Lua-script based. | PM-OS tem quota mas não fair queue | **HIGH** só em escala |
| **Heartbeats + zombie detection** | Task sem heartbeat 45s = stuck, requeue | PM-OS tem reconciler similar | BAIXA (overlap) |
| **Batch triggering + completion tracking** | Trigger 1000 tasks, wait todas, fan-in | PM-OS tem waves | MÉDIA (melhorar fan-in) |
| **Retries com backoff configurável** | Per-task retry policy, DLQ | PM-OS tem retry básico | MÉDIA |
| **Idempotency keys** | Request re-submit = dedupe 24h | PM-OS não tem formal | **HIGH** (fácil + valor) |
| **Build extensions** | User injeta Python/FFmpeg/browser no container | PM-OS não tem story pra binários custom | **HIGH** |
| **Preview branches** | Cada git branch = env isolado | PM-OS é single env | BAIXA (só escalar) |
| **Run metadata + tags** | Filter runs por tag em query | PM-OS tem slug mas não tag | MÉDIA (fácil) |
| **Realtime streaming LLM** | React hook `useRealtimeRun()` stream pra frontend | PM-OS tem SSE raw, sem SDK | MÉDIA (quando tiver front) |
| **Wait-for-token** | Pausa até token específico (agent↔human↔sistema) | Core HITL pattern | **HIGH** (parte de Waitpoints) |
| **Machines** (vCPU/GB config) | Escolher resource por task | Cloud Run faz auto | BAIXA |
| **Structured input/output schemas** | Zod schemas validation | OVERLAP (PM-OS valida recipe) | — |

### Tier 2 — Overlap com PM-OS (já temos, não prioridade)

- Queues/Concurrency rules
- Observability OTel
- Auto retry básico
- Multi-env (DEV/STAGING/PROD)

### Tier 3 — NÃO fit

- JavaScript SDK (PM-OS é Go)
- React hooks (frontend específico)
- Docker/K8s provider (Cloud Run)
- Prisma schema (Supabase REST)
- CLI trigger dev

---

## 3. Achado chave — Waitpoints + Execution Snapshots

**Este é o genuine-novel primitive do trigger.dev que nenhum outro projeto (CrewAI, gocrewai, AMP) tem igual.**

### Mecânica Waitpoint

```
Task executing → encounters wait.forToken("user_approval_123")
              → task STATE serialized (V8 heap snapshot)
              → worker RELEASED (não segura container)
              → DB row: waitpoint{id, run_id, status: BLOCKED, resume_data}
              → user/system: POST /waitpoints/user_approval_123/complete { approved: true }
              → engine detects → picks new worker → RESUMES state
              → task continues AS IF never paused
```

**PM-OS hoje:** step `clarify` é blocking thread. Container segurado.

**Com Waitpoint:** task de 1 semana (aguarda cliente aprovar recipe) não segura goroutine nem container. Grava state + libera.

### Mecânica Execution Snapshot

- Snapshot completo do run em pontos críticos (não só per-step)
- Inclui: `allOutputs` map, wave/step index atual, acumuladores de métricas
- Tabela `run_snapshots (id, run_id, tenant_id, status, execution_state jsonb, created_at)`
- Retomada: carrega último snapshot, pula diretamente pro step atual

**PM-OS hoje:** falha mid-wave = restart wave. Com snapshot: resume exatamente onde parou.

---

## 4. Estratégia de absorção

### NÃO USE: "Sonnet converte arquivos"

**Motivo:** stack completamente diferente (TS/Prisma/Redis/Remix vs Go/Supabase/stdlib). Zero copy-paste funciona. Tentativa de tradução literal gera lixo.

### USE: "Conceito → Design Go original"

Processo por primitive:

1. **Identifica primitive** (ex: Waitpoint)
2. **Lê implementação TS** pra entender semântica (não API)
3. **Escreve design doc curto** (Go idiomático, Supabase storage, REST API)
4. **Implementa** (LLM externa ou Akita+Forge) com TDD
5. **Integra + Keel**

### Prompt template pra LLM externa (exemplo Waitpoints)

```
Read /tmp/trigger-eval/trigger.dev/internal-packages/run-engine/src/engine/systems/waitpointSystem.ts

Understand the Waitpoint mechanic. Then IGNORE the TypeScript implementation entirely.

Design a Go-idiomatic Waitpoint system for PM-OS with these constraints:
- Supabase PostgREST storage
- REST API: POST /api/v2/waitpoints/create, POST /api/v2/waitpoints/{token}/complete,
  GET /api/v2/waitpoints/{token}/status
- New step type "wait_for_token" in Recipe; engine releases worker when step hits waitpoint,
  resumes when token completed
- Timeout configurable, default 7 days
- HMAC-signed tokens (reuse primitive from CrewAI HITL port)

Produce:
- pkg/waitpoints/types.go (structs)
- pkg/waitpoints/store.go (Supabase REST client)
- pkg/waitpoints/api.go (HTTP handlers)
- pkg/waitpoints/types_test.go
- migrations/waitpoints.sql (table schema)

Don't port TS code. Design Go code inspired by the semantics.
```

---

## 5. Priorização final pra PM-OS

### AGORA — não mexer
- Port CrewAI (em andamento, LLM externa)
- Esperar resultado, integrar, validar qualidade

### DEPOIS — aproveitar LLM externa (já tem contexto PM-OS)

| Ordem | Primitive | Tempo estimado | Dependência |
|---|---|---|---|
| 1 | **Waitpoints** | 1-2 semanas (LLM + integração) | Port CrewAI completo (HMAC + HITL base) |
| 2 | **Execution Snapshots** | 1 semana | Waitpoints (reuso schema) |
| 3 | **Idempotency keys** | 2-3 dias | — |
| 4 | **Run tags/metadata** | 1 dia | — |
| 5 | **Realtime SDK TS** | 1 semana | SSE PM-OS atual |
| 6 | **Build extensions** | 1 semana | — |
| 7 | **MARQS fair queue** | 1-2 semanas | ≥5 tenants competindo compute |

### NUNCA (salvo inversão de escala)

- Preview branches (single dev env)
- Machine presets (Cloud Run autoescala)
- Port dos SDKs TS/React (fora de escopo)

---

## 6. Decisão estratégica — escrita vs conversão

Critério pra escolher estratégia futura (depois do CrewAI port voltar):

### Se port CrewAI voltar BOM (cobertura ≥90%, gates passam)

**Estratégia "LLM externa converte arquivo a arquivo"** funciona pra:
- Projetos com paradigma similar ao Go (ex: CrewAI — OOP → struct, mecânico)
- Primitives pequenos e bem isolados

**NÃO funciona** pra trigger.dev. Paradigma distante (Remix/Prisma/Redis) + volume (290k LOC).

### Se port CrewAI voltar RUIM (bugs, não compila)

**Estratégia "Sonnet converte" tem limites claros.** Vale recuar pra:
- Conceitos → design Go original (workflow aplicável a trigger.dev)
- Eu (Akita) dirige design, LLM externa gera seguindo spec clara

### Regra final

- **Trigger.dev ≠ port literal. Conceito apenas.**
- Usar LLM externa pra GERAR Go original quando tiver spec Akita-written clara
- Reservar estratégia "port mecânico" pra projetos Python/OOP simples (CrewAI)

---

## 7. Resumo executivo

**Perguntas principais respondidas:**

**1. Tem coisa interessante pro PM-OS no trigger.dev?**
SIM. 2 primitives transformadores (Waitpoints, Execution Snapshots) + 5 melhorias importantes (Idempotency, Tags, Build Extensions, Realtime SDK, MARQS).

**2. Podemos usar estratégia "LLM externa converte e cola"?**
NÃO para trigger.dev. Stack incompatível, paradigma distante, volume inviável.

**3. Como absorver então?**
Conceito apenas. Ler TS pra entender semântica, escrever design Go original, LLM externa implementa Go idiomático seguindo spec nossa.

**4. Quando?**
Só depois do CrewAI port validar viabilidade do workflow "LLM externa + Akita integra". Trigger.dev expande horizonte, não é prioridade imediata.

**5. Onde vai primeiro?**
Waitpoints (genuine-novel primitive) > Execution Snapshots > Idempotency keys. Total: ~4 semanas pra ganhos concretos multi-tenant.

---

## 8. Backlog de primitives pra avaliar depois

Lista para revisitar quando CrewAI port estiver integrado:

- [ ] **Waitpoints** — design doc + implementação
- [ ] **Execution Snapshots** — design doc + implementação
- [ ] **Idempotency keys** — middleware + dedupe table
- [ ] **Run tags/metadata** — schema extension + query API
- [ ] **Build extensions** — pattern pra Cloud Run image layer
- [ ] **Realtime streaming SDK TS** — consumer do SSE atual
- [ ] **MARQS fair queue** — avaliação pós-escala real
- [ ] **Retry policy config per-step** — expandir básico atual
- [ ] **Machine presets** — se tiver múltiplos pools Cloud Run

---

## 9. Origem da análise

- Clonado repositório: `/tmp/trigger-eval/trigger.dev` (branch main, Apache 2.0)
- Inspecionado: apps/webapp/app/v3/, internal-packages/run-engine/, packages/core/src/v3/
- Arquivo chave referência semântica: `internal-packages/run-engine/src/engine/systems/waitpointSystem.ts`

Repo local removível após uso — análise conceitual gravada aqui.
