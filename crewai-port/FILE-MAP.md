# FILE-MAP — Python → Go arquivo por arquivo

**Base source:** `lib/crewai/src/crewai/` no repo [crewAIInc/crewAI](https://github.com/crewAIInc/crewAI)

**Base target:** `/tmp/crewai-port-output/pkg/`

**Ordem execução recomendada:** A → B → C → D → E → F → G → H → I → J → K. Cada tier depende do anterior (events precisa types, memory precisa storage backend, etc).

**Convenção:** `LOC` é tamanho Python aproximado — Go final geralmente 20-40% maior por verbosidade de tipos/erros. Cada arquivo DEVE ter `*_test.go` ao lado.

---

## Tier A — Security (base, zero deps)

| # | Python source | LOC | Go target | Notas |
|---|---|---|---|---|
| A1 | `security/fingerprint.py` | 163 | `pkg/security/fingerprint.go` | Core deliverable. UUID4 random + UUID5 seed-based + metadata validator. Exportar `Fingerprint` struct, `NewFingerprint()`, `GenerateFromSeed(seed, metadata)`. **Usa `github.com/google/uuid`.** |
| A2 | `security/constants.py` | ~10 | merge → `pkg/security/fingerprint.go` | Só constante `CREW_AI_NAMESPACE` — renomeie pra `PMOSNamespace` com novo UUID. |
| A3 | `security/security_config.py` | ~80 | `pkg/security/config.go` | Agrega `Fingerprint` + version. Struct `SecurityConfig`. |

---

## Tier B — Hooks (primitives, depende de Tier A)

| # | Python source | LOC | Go target | Notas |
|---|---|---|---|---|
| B1 | `hooks/types.py` | ~50 | `pkg/hooks/types.go` | Tipos base: `HookPhase` enum, `HookContext`, `HookResult`. |
| B2 | `hooks/decorators.py` | ~200 | `pkg/hooks/registry.go` | Decorator `@hook_llm_call` vira `Registry.RegisterLLMHook(fn)`. Converter decorator → registration API. |
| B3 | `hooks/llm_hooks.py` | ~150 | `pkg/hooks/llm_hooks.go` | Pre/post LLM call hooks. Interface `LLMHook { Before(ctx, req); After(ctx, req, resp) }`. |
| B4 | `hooks/tool_hooks.py` | ~150 | `pkg/hooks/tool_hooks.go` | Pre/post tool call. Interface `ToolHook { Before(ctx, call); After(ctx, call, result) }`. |
| B5 | `hooks/wrappers.py` | ~100 | `pkg/hooks/wrappers.go` | Chain composition, middleware pattern. |

---

## Tier C — Events (infra, usado por tudo)

### C1 — Core do event bus

| # | Python source | LOC | Go target | Notas |
|---|---|---|---|---|
| C1 | `events/base_events.py` | ~100 | `pkg/events/base.go` | `BaseEvent` interface + `Timestamp`, `ID`, `Type`. Exportar `Event` interface. |
| C2 | `events/depends.py` | ~80 | `pkg/events/depends.go` | Dependency injection marker. Adaptar pra DI Go-style. |
| C3 | `events/event_context.py` | ~150 | `pkg/events/context.go` | Context scoping. Usar `context.Context` com value keys. **CRÍTICO:** contextvars → context.Context. |
| C4 | `events/handler_graph.py` | ~200 | `pkg/events/graph.go` | Execution plan com dependency order. DAG topológico. |
| C5 | `events/event_bus.py` | 794 | `pkg/events/bus.go` | **MAIOR ARQUIVO DO PORT.** Singleton `CrewAIEventsBus` → `EventBus`. Async handlers (asyncio → goroutines). ThreadPool → sync.Pool/goroutines. `scoped_handlers` context manager → `WithScope()` method. |
| C6 | `events/base_event_listener.py` | ~100 | `pkg/events/listener.go` | Interface `EventListener` + base impl. |
| C7 | `events/utils/handlers.py` | ~100 | `pkg/events/handler_utils.go` | Utils: `is_async_handler` desnecessário em Go (tudo sync ou goroutine). Manter `_get_param_count` → reflection para validar assinatura. |

### C2 — Event types (selective)

**Renomeação global:** `Crew` → `Run`, `Agent` → omit, `Flow` → `Recipe` onde apropriado.

| # | Python source | LOC | Go target | Notas |
|---|---|---|---|---|
| C8 | `events/types/event_bus_types.py` | ~100 | `pkg/events/types/bus_types.go` | `Handler`, `AsyncHandler`, `ExecutionPlan` types. |
| C9 | `events/types/task_events.py` | ~120 | `pkg/events/types/task_events.go` | `TaskStartedEvent`, `TaskCompletedEvent`, `TaskFailedEvent`. |
| C10 | `events/types/tool_usage_events.py` | ~100 | `pkg/events/types/tool_events.go` | `ToolUsageStartedEvent`, `ToolUsageFinishedEvent`, `ToolUsageErrorEvent`, `ToolSelectionErrorEvent`, `ToolValidateInputErrorEvent`. |
| C11 | `events/types/llm_events.py` | ~100 | `pkg/events/types/llm_events.go` | `LLMCallStartedEvent`, `LLMCallCompletedEvent`, `LLMStreamChunkEvent`. |
| C12 | `events/types/mcp_events.py` | ~80 | `pkg/events/types/mcp_events.go` | MCP tool events. |
| C13 | `events/types/llm_guardrail_events.py` | ~60 | `pkg/events/types/guardrail_events.go` | Guardrail fired/passed events. |
| C14 | `events/types/logging_events.py` | ~40 | `pkg/events/types/logging_events.go` | Logger level events. |
| C15 | `events/types/system_events.py` | ~60 | `pkg/events/types/system_events.go` | Lifecycle: startup/shutdown/error. |
| C16 | `events/types/crew_events.py` | ~120 | `pkg/events/types/run_events.go` | **RENOMEAR:** Crew→Run. `CrewStartedEvent` → `RunStartedEvent`, etc. |

**NÃO portar:** `agent_events.py`, `flow_events.py`, `knowledge_events.py`, `memory_events.py`, `env_events.py`, `observation_events.py`, `reasoning_events.py`, `skill_events.py`, `a2a_events.py` — fora do escopo atual.

---

## Tier D — Guardrails

| # | Python source | LOC | Go target | Notas |
|---|---|---|---|---|
| D1 | `utilities/guardrail_types.py` | ~80 | `pkg/quality/guardrail_types.go` | `GuardrailResult`, `GuardrailInput`, enums. |
| D2 | `utilities/guardrail.py` | ~150 | `pkg/quality/guardrail.go` | Base guardrail interface + retry logic. |
| D3 | `tasks/hallucination_guardrail.py` | ~250 | `pkg/quality/hallucination_guardrail.go` | LLM-based hallucination detector. Usa `AnthropicDirectExecutor` do PM-OS (não recrie LLM client). |
| D4 | `tasks/llm_guardrail.py` | ~200 | `pkg/quality/llm_guardrail.go` | Generic LLM-based grader. Struct `LLMGuardrail { Description, Threshold, Retries }`. |
| D5 | `tasks/output_format.py` | ~30 | merge → `pkg/recipe/task_output.go` | Enum `OutputFormat { RAW, JSON, PYDANTIC }`. Descartar `PYDANTIC`, manter `RAW` + `JSON` + novo `STRUCTURED`. |
| D6 | `tasks/task_output.py` | ~150 | `pkg/recipe/task_output.go` | Struct `TaskOutput` com description, raw, json_dict, agent, output_format. Se PM-OS já tiver tipo com mesmo nome, use `CrewTaskOutput` prefix. |

---

## Tier E — HITL (Human-in-the-Loop)

| # | Python source | LOC | Go target | Notas |
|---|---|---|---|---|
| E1 | `flow/async_feedback/types.py` | ~100 | `pkg/hitl/types.go` | `HumanFeedbackContext`, `HumanFeedbackResult`, `HumanFeedbackPending` error. |
| E2 | `flow/async_feedback/providers.py` | ~150 | `pkg/hitl/providers.go` | Interface `Provider { RequestFeedback(ctx, fctx) (Result, error) }`. Implementações base: `CLIProvider`, `NoopProvider`. |
| E3 | `flow/human_feedback.py` | 674 | `pkg/hitl/feedback.go` | **GRANDE ARQUIVO.** Decorator `@human_feedback` NÃO portar diretamente. Em vez disso, criar struct `HumanFeedbackRequest` + método `Execute(ctx, stepCtx) (FeedbackResult, error)`. Emitir eventos. Signed token para resume (usar `crypto/hmac` + `crypto/sha256`). |
| E4 | `flow/input_provider.py` | 151 | `pkg/hitl/input_provider.go` | Interface + CLI default impl. |
| E5 | `core/providers/human_input.py` | ~100 | merge → `pkg/hitl/input_provider.go` | Merge conteúdo. |

---

## Tier F — State & Checkpointing

| # | Python source | LOC | Go target | Notas |
|---|---|---|---|---|
| F1 | `state/checkpoint_config.py` | ~80 | `pkg/checkpoint/config.go` | `CheckpointConfig { Enabled, Interval, Backend }`. |
| F2 | `state/event_record.py` | ~100 | `pkg/checkpoint/event_record.go` | `EventRecord` struct persistível. |
| F3 | `state/checkpoint_listener.py` | ~150 | `pkg/checkpoint/listener.go` | Listener no event bus que grava checkpoints. Usa `pkg/events`. |
| F4 | `state/provider/core.py` | ~100 | `pkg/checkpoint/provider.go` | Interface `Provider { Save(ctx, cp), Load(ctx, id), List(ctx, runID) }`. |
| F5 | `state/provider/json_provider.py` | ~150 | `pkg/checkpoint/json_provider.go` | File-based (útil pra test). |
| F6 | `state/provider/sqlite_provider.py` | ~200 | `pkg/checkpoint/supabase_provider.go` | **REESCREVER PRA SUPABASE.** Não portar SQLite. Tabela `checkpoints (id, run_id, tenant_id, state_json, created_at)`. Use `pkg/store/client.go` pattern. |
| F7 | `state/provider/utils.py` | ~80 | `pkg/checkpoint/utils.go` | Helpers: serialização, hashing. |
| F8 | `state/runtime.py` | ~200 | `pkg/checkpoint/runtime.go` | `RuntimeState` struct + fork/branch support. |

---

## Tier G — Skills (pequeno, isolado)

| # | Python source | LOC | Go target | Notas |
|---|---|---|---|---|
| G1 | `skills/models.py` | ~100 | `pkg/skills/models.go` | `SkillMetadata`, `Skill` structs. |
| G2 | `skills/parser.py` | ~150 | `pkg/skills/parser.go` | Parse YAML frontmatter + markdown body. **Use `gopkg.in/yaml.v3`** (adicionar a `go.mod`, justificar em `PORT-REPORT.md`). |
| G3 | `skills/validation.py` | ~80 | `pkg/skills/validation.go` | Validate skill frontmatter. |
| G4 | `skills/loader.py` | ~120 | `pkg/skills/loader.go` | Load skills from filesystem. Use `os` + `filepath.Walk`. |

---

## Tier H — Utilities & Types (pequenos, úteis)

| # | Python source | LOC | Go target | Notas |
|---|---|---|---|---|
| H1 | `types/callback.py` | ~80 | `pkg/types/callback.go` | Serializable callable references. Em Go: registry de named funcs + dotted path resolver. |
| H2 | `utilities/rpm_controller.py` | ~150 | `pkg/ratelimit/rpm.go` | Token bucket per-minute. Use `sync.Mutex` + `time.Ticker`. |
| H3 | `utilities/errors.py` | ~100 | `pkg/errors/errors.go` | Domain errors tipados. |
| H4 | `utilities/exceptions/context_window_exceeding_exception.py` | ~50 | `pkg/errors/context_window.go` | Specific error type. |
| H5 | `utilities/rw_lock.py` | ~80 | **PULAR** | Go tem `sync.RWMutex` nativo. |

---

## Tier I — Tools concepts (estende registry existente)

| # | Python source | LOC | Go target | Notas |
|---|---|---|---|---|
| I1 | `tools/tool_types.py` | ~60 | `pkg/engine/tools/types.go` | **NOVO ARQUIVO** no package existente. Tipos: `ToolCategory`, `ToolMetadata`. |
| I2 | `tools/base_tool.py` | 714 | **NÃO PORTAR INTEIRO.** Extrair só campos | Extrair campos `result_as_answer`, `max_usage_count`, `current_usage_count`, `cache_function` → documentar em `PORT-REPORT.md` como "merge candidate" que Akita integra no `registry.go` existente. |

---

## Tier J — MCP Client (independent subsystem)

| # | Python source | LOC | Go target | Notas |
|---|---|---|---|---|
| J1 | `mcp/config.py` | ~120 | `pkg/mcp/config.go` | `ServerConfig { URL, Transport, AuthToken, Allowlist }`. |
| J2 | `mcp/filters.py` | ~100 | `pkg/mcp/filters.go` | Tool filtering (allowlist, denylist). |
| J3 | `mcp/transports/base.py` | ~80 | `pkg/mcp/transports/base.go` | Interface `Transport { Call(ctx, method, params) (result, error); Close() }`. |
| J4 | `mcp/transports/stdio.py` | ~200 | `pkg/mcp/transports/stdio.go` | Subprocess + NDJSON stdin/stdout. Use `os/exec`. |
| J5 | `mcp/transports/sse.py` | ~250 | `pkg/mcp/transports/sse.go` | SSE client. Use `net/http` stdlib. |
| J6 | `mcp/transports/http.py` | ~200 | `pkg/mcp/transports/http.go` | Streamable HTTP POST+SSE. |
| J7 | `mcp/client.py` | ~400 | `pkg/mcp/client.go` | Orchestrator. Handle reconnection, session mgmt. |
| J8 | `mcp/tool_resolver.py` | ~150 | `pkg/mcp/resolver.go` | Resolve MCP tool → PM-OS Registry Tool. Wire pro `pkg/engine/tools/registry.go`. |

**Restrição crítica:** sanitize tool descriptions (prompt injection). Documente em code comment + `PORT-REPORT.md`.

---

## Tier K — Memory (REDESIGN, não port literal)

**IMPORTANTE:** LanceDB e Qdrant clients NÃO existem pra Go estável. Redesign para **Supabase pgvector** REST. Esta tier é mais trabalho que tradução — é adaptação pra stack PM-OS.

| # | Python source | LOC | Go target | Notas |
|---|---|---|---|---|
| K1 | `memory/types.py` | ~120 | `pkg/memory/types.go` | `Episode`, `Synapse`, `MemoryEntry` structs. |
| K2 | `memory/memory_scope.py` | ~150 | `pkg/memory/scope.go` | Scope tree `/tenant/<id>/recipe/<slug>/step/<id>`. Hierarchical lookup. |
| K3 | `memory/utils.py` | 110 | `pkg/memory/utils.go` | Helpers: scoring (recency + semantic + importance). |
| K4 | `memory/analyze.py` | ~200 | `pkg/memory/analyze.go` | Analysis pass sobre episodes. |
| K5 | `memory/encoding_flow.py` | 547 | `pkg/memory/encoding.go` | Encode → embedding → store. **Simplificar:** use Anthropic embedding API direta (PM-OS config). |
| K6 | `memory/recall_flow.py` | ~300 | `pkg/memory/recall.go` | Query → embedding → cosine similarity → rank → filter by scope → return top-K. |
| K7 | `memory/unified_memory.py` | 1062 | `pkg/memory/unified.go` | Fachada sobre encoding + recall + scope. |
| K8 | `memory/storage/backend.py` | ~180 | `pkg/memory/storage/backend.go` | Interface `Storage { Insert(ctx, entry) error; Query(ctx, scope, embedding, topK) ([]Entry, error) }`. |
| K9 | **NOVO** | — | `pkg/memory/storage/pgvector_storage.go` | Implementação Supabase REST. Schema definido em `PM-OS-CONTEXT.md`. **Não portar** `lancedb_storage.py` nem `qdrant_edge_storage.py` — substituir completamente. |

---

## Resumo (totalizado)

| Tier | Arquivos | LOC Python aprox | Complexidade |
|---|---|---|---|
| A — Security | 3 | 250 | Baixa |
| B — Hooks | 5 | 650 | Média |
| C — Events | 15 | 2100 | **Alta** (event_bus.py 794 LOC) |
| D — Guardrails | 6 | 860 | Média |
| E — HITL | 5 | 1100 | Média |
| F — Checkpoint | 8 | 1000 | Média (storage redesign) |
| G — Skills | 4 | 450 | Baixa |
| H — Utilities | 4 | 400 | Baixa |
| I — Tools concepts | 2 | 60+ (parcial) | **Extract only** |
| J — MCP client | 8 | 1500 | **Alta** (spec MCP) |
| K — Memory | 9 | 2670 | **Alta + redesign** |

**Total: ~65 arquivos, ~11k LOC Python estimado, ~15k LOC Go final.**

**Tempo estimado LLM externa (Sonnet):** 4-8h de trabalho contínuo se for sequencial. Se paralelizar (ex: 3 instâncias simultâneas dividindo tiers independentes), cai pra 2-3h.

**Paralelização recomendada:**
- Instância 1: Tier A + B + H (isolados)
- Instância 2: Tier C + D (events precedem guardrail events)
- Instância 3: Tier E + F + G (HITL, state, skills — isolados)
- Depois sequencial: Tier I (depende de conhecer registry existente), J (MCP spec), K (redesign pgvector)

---

## Arquivos do CrewAI que você NÃO PORTARÁ (lista explícita)

- `agent/**` (core.py 1884 LOC + utils 418 + planning_config + internal/meta) — agent-first paradigm
- `agents/**` (agent_adapters, agent_builder, cache, crew_agent_executor, parser, planner_observer, step_executor, tools_handler) — mesmo motivo
- `crew.py` (2298 LOC) — crew paradigm
- `crews/**` — mesmo
- `task.py` (1422 LOC) — PM-OS tem `Step` em `pkg/recipe`
- `tasks/conditional_task.py` — concept só, Akita adiciona campo `When` ao Step
- `llm.py` (2558 LOC) + `llms/**` — PM-OS tem `AnthropicDirectExecutor`, não porta provider zoo
- `flow/flow.py` (3465 LOC) + `flow_wrappers.py` + `flow_serializer.py` + `visualization/**` + `utils.py` + `flow_trackable.py` + `flow_config.py` + `flow_context.py` + `types.py` + `persistence/**` — decorator-driven, overlap com recipes
- `knowledge/**` (~1200 LOC) — adiar, Akita redesign depois
- `rag/**` (provider zoo de embeddings — 30+ arquivos) — adiar, use Anthropic embedding API direto
- `telemetry/**` — PM-OS tem narrator/metrics
- `tools/agent_tools/**` — agent delegation
- `tools/cache_tools/**` — Go tem cache nativo
- `tools/structured_tool.py` — pydantic-specific
- `tools/tool_usage.py` (1042) + `tool_calling.py` — concept pro `llm_with_tools` do PM-OS, Akita integra
- `tools/mcp_native_tool.py` + `mcp_tool_wrapper.py` — espere Tier J completo, então Akita wire
- `tools/memory_tools.py` — espere Tier K
- `experimental/**` — não-estável
- `lite_agent.py` + `lite_agent_output.py` — agent paradigm
- `process.py` (10 LOC enum) — Akita inline se precisar
- `context.py` — contextvars Python-specific
- `utilities/**` exceto os listados em Tier H — logger (PM-OS tem), printer, i18n, pydantic_schema_utils, serialization via pickle (impossível Go), internal_instructor, planning_handler, reasoning_handler, training_*, converter, file_handler/store, formatter, import_utils, llm_utils, paths, prompts, step_execution_context, streaming, string_utils, token_counter_callback, tool_utils, types, version
- `types/crew_chat.py`, `streaming.py`, `usage_metrics.py`, `utils.py` — fora do escopo
- `mypy.py` — static analysis helper
- `core/providers/content_processor.py` — Python-specific
- `hooks/decorators.py` — **PORTAR como `pkg/hooks/registry.go`** (já está em Tier B — adaptar)

**Total não-portado: ~240 arquivos.** Se LLM externa achar que algo dessa lista DEVE ser portado, ela para e pergunta.
