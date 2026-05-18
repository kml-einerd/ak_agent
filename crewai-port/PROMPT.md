# PROMPT MESTRE — Port CrewAI (Python) → PM-OS (Go)

**Public-alvo:** LLM especializada em tradução Python→Go (Claude Sonnet 4.6, GPT-4o, ou Cursor IDE com modelo equivalente).

**Objetivo:** Portar 60-65 arquivos selecionados do repo [crewAIInc/crewAI](https://github.com/crewAIInc/crewAI) para Go idiomático, prontos pra integrar no PM-OS (motor de orquestração em Go).

---

## ANTES DE COMEÇAR — leia estes 4 anexos

1. `PM-OS-CONTEXT.md` — arquitetura alvo. **OBRIGATÓRIO ler antes de portar qualquer linha.**
2. `FILE-MAP.md` — lista exata dos arquivos a portar, com path de origem e destino.
3. `RULES.md` — convenções Go PM-OS + restrições hard (o que NUNCA fazer).
4. `CHECKLIST.md` — critérios de aceitação por arquivo.

**Se qualquer anexo faltar, pare e avise.** Não adivinhe estrutura PM-OS.

---

## Tarefa

Para cada arquivo listado em `FILE-MAP.md`:

1. **Ler** o arquivo Python de origem (`lib/crewai/src/crewai/<path>.py`) no repositório CrewAI
2. **Mapear** dependências Python (imports) e resolver equivalentes Go
3. **Transcrever** pra Go idiomático seguindo `RULES.md`
4. **Criar** arquivo Go em `/tmp/crewai-port-output/pkg/<target>/<name>.go`
5. **Criar** teste unitário `/tmp/crewai-port-output/pkg/<target>/<name>_test.go` com cobertura mínima 70%
6. **Validar** com `go vet` e `go test -race` antes de marcar completo

## Método TDD obrigatório

Para cada arquivo:
1. **Escrever testes primeiro** (RED — testes falham)
2. **Implementar** (GREEN — testes passam)
3. **Refatorar** (mantém testes verdes)

Teste deve cobrir:
- Happy path (cenário normal)
- Edge cases (nil, empty, boundary)
- Error paths (inputs inválidos)
- Concorrência (`go test -race`) quando aplicável

## Regras hard (de `RULES.md`)

- **Go 1.25+ stdlib first.** Só importar lib externa se lista em `RULES.md` autorizar.
- **Sem pydantic.** Substituir por structs + validate funcs explícitas.
- **Sem decorators.** Substituir por registration funcs + interface methods.
- **Sem asyncio.** Substituir por goroutines + channels + `context.Context`.
- **Sem metaclass/__init_subclass__.** Substituir por interfaces + `init()` para registro global.
- **Sem `interface{}` preguiçoso.** Usar tipos concretos. `any` só em JSON unmarshaling.
- **Error handling:** `if err != nil { return fmt.Errorf("operation: %w", err) }`. Nunca panic em library code.
- **Context:** `func(ctx context.Context, ...)` como primeiro arg em qualquer I/O.
- **Naming:** PascalCase exportados, camelCase unexportados, snake_case APENAS em tags JSON que espelham DB Supabase.
- **Testes:** `_test.go` no mesmo package. `testify/assert` permitido (já no go.mod PM-OS).

## Output esperado

Estrutura final em `/tmp/crewai-port-output/`:

```
/tmp/crewai-port-output/
├── PORT-REPORT.md              # resumo do que foi portado + caveats
├── pkg/
│   ├── security/
│   │   ├── fingerprint.go
│   │   ├── fingerprint_test.go
│   │   └── config.go
│   ├── hooks/
│   │   ├── types.go
│   │   ├── registry.go
│   │   ├── llm_hooks.go
│   │   ├── tool_hooks.go
│   │   └── wrappers.go
│   ├── events/
│   │   ├── base.go
│   │   ├── bus.go
│   │   ├── context.go
│   │   ├── depends.go
│   │   ├── graph.go
│   │   ├── listener.go
│   │   └── types/
│   │       ├── task_events.go
│   │       ├── tool_events.go
│   │       ├── llm_events.go
│   │       ├── mcp_events.go
│   │       ├── guardrail_events.go
│   │       ├── logging_events.go
│   │       ├── system_events.go
│   │       └── bus_types.go
│   ├── quality/
│   │   ├── hallucination_guardrail.go
│   │   ├── llm_guardrail.go
│   │   ├── guardrail.go
│   │   └── guardrail_types.go
│   ├── hitl/
│   │   ├── feedback.go
│   │   ├── providers.go
│   │   ├── types.go
│   │   └── input_provider.go
│   ├── checkpoint/
│   │   ├── config.go
│   │   ├── listener.go
│   │   ├── event_record.go
│   │   ├── provider.go
│   │   ├── json_provider.go
│   │   ├── supabase_provider.go
│   │   ├── utils.go
│   │   └── runtime.go
│   ├── skills/
│   │   ├── loader.go
│   │   ├── models.go
│   │   ├── parser.go
│   │   └── validation.go
│   ├── memory/
│   │   ├── types.go
│   │   ├── scope.go
│   │   ├── unified.go
│   │   ├── encoding.go
│   │   ├── recall.go
│   │   ├── analyze.go
│   │   ├── utils.go
│   │   └── storage/
│   │       ├── backend.go
│   │       └── pgvector_storage.go   # substitui lancedb/qdrant
│   ├── mcp/
│   │   ├── client.go
│   │   ├── config.go
│   │   ├── filters.go
│   │   ├── resolver.go
│   │   └── transports/
│   │       ├── base.go
│   │       ├── http.go
│   │       ├── sse.go
│   │       └── stdio.go
│   ├── recipe/
│   │   └── task_output.go    # extende struct existente
│   ├── engine/
│   │   └── tools/
│   │       └── types.go      # extende struct existente
│   ├── ratelimit/
│   │   └── rpm.go
│   ├── types/
│   │   └── callback.go
│   └── errors/
│       ├── errors.go
│       └── context_window.go
└── tests/
    └── integration/
        └── events_bus_integration_test.go  # opcional
```

Cada arquivo `.go` deve:
- Começar com comment de package (`// Package X provides Y.`)
- Ter doc comments em TODOS os exports (types, funcs, métodos, constants)
- Citar a origem Python no comment do package (ex: `// Ported from crewai/security/fingerprint.py`)

## Entregue também `PORT-REPORT.md`

Conteúdo mínimo:
- **Feito:** lista de arquivos portados com LOC final
- **Desvios do CrewAI:** onde a semântica mudou e por quê (ex: "LanceDB substituído por pgvector — schema diferente, API similar")
- **TODOs pro Akita resolver:** imports que não resolvi, integrações com PM-OS que precisam decisão, funcionalidades que exigem design (não só tradução)
- **Dependências adicionadas:** se usou lib externa fora de `RULES.md`, justifique
- **Coverage report:** output de `go test -cover ./...`

## Como isso complementa o Akita

Eu (Akita, orquestrador PM-OS) vou:
1. **Não** reconverter o que você portou — seu output é input meu
2. **Revisar** os arquivos contra convenções do meu codebase específico
3. **Resolver conflitos** de naming com `pkg/` existentes (já tenho `pkg/engine/tools/registry.go`, `pkg/recipe/`, `pkg/store/`, `pkg/quality/`, `pkg/sensors/`, `pkg/git/`, `pkg/infra/`, `pkg/core/`, `pkg/api/`)
4. **Integrar** no `engine.go`, `schema.go`, `wave_executor.go`, `main.go` (arquivos que você NÃO deve tocar)
5. **Substituir** storage adapters (LanceDB/Qdrant → Supabase pgvector REST)
6. **Wire** eventos novos no sistema de narrator/metrics existente
7. **Rodar** full test suite, corrigir breaks, passar pelo Keel
8. **Deployar** em Cloud Run

Se você tentar fazer integração sozinho sem conhecer meu codebase, vai gerar conflito. **Foque em tradução idiomática + testes unitários isolados.**

## Fail fast — quando parar e perguntar

- Arquivo Python tem dependência que eu não listei em `RULES.md` → pare, pergunte
- Semântica do arquivo depende de comportamento Python não-determinístico (GIL, descriptor protocol) → pare, descreva o problema
- Existem 3+ maneiras idiomáticas Go de fazer a mesma coisa → liste as opções, me pergunte qual escolher
- Teste unitário exige mock de sistema externo (Supabase, Anthropic API, MCP server) → implemente mock interno no `_test.go`, não subprocess

## Referência opcional — gocrewai

Existe um projeto Go **parcialmente inspirado** em CrewAI: [github.com/Ecook14/gocrewwai](https://github.com/Ecook14/gocrewwai) (MIT, 29k LOC, single commit, 2 semanas).

**NÃO é port literal do CrewAI Python.** É reimplementação parcial com paradigma e APIs diferentes. **Qualidade mista** (4 testes falhando, deps pesadas, single-author).

**Use APENAS como referência secundária** quando:
- Você travar em decisão idiomática Go (ex: como mapear asyncio event bus → goroutines)
- Quiser ver exemplo de nomenclatura Go pra conceito CrewAI
- Precisar de spec MCP implementation (eles têm `pkg/protocols/mcp.go` 916 LOC funcional)

**NÃO faça:**
- Copy-paste do gocrewai (paradigma deles é agent-first, nosso é task-first)
- Assumir API deles é correta (não é port fiel)
- Usar as deps deles (Gin, Docker, Chrome driver — PM-OS é stdlib only)

**Seu job continua sendo port direto do CrewAI Python → PM-OS Go**. Gocrewai é só dicionário de consulta quando precisar.

## Aviso final

**Este é um port MECÂNICO + IDIOMÁTICO.** Não é refactor criativo. Não reinvente APIs. Não "melhore" a arquitetura do CrewAI. Traduza o que está lá pra Go idiomático mantendo semântica. Deixe decisões arquiteturais pro Akita resolver depois.

**Não invente funcionalidade que não existe no CrewAI.** Se um arquivo cita uma classe/função que você não encontra no source, pare e reporte.

**Formato de commit sugerido por arquivo:**
```
port(<pkg>): translate <file>.py to Go

- Source: lib/crewai/src/crewai/<path>.py (<LOC> LOC)
- Target: pkg/<target>/<name>.go
- TDD: <test_count> tests passing, <coverage>% coverage
- Deviations: <list or "none">
```

Começar pelo Tier A (security/fingerprint) e progredir em ordem de `FILE-MAP.md`.
