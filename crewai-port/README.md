# CrewAI → PM-OS Port Package

Package de instruções para LLM externa portar seletivamente arquivos do CrewAI (Python) para PM-OS (Go).

## Arquivos deste pacote

| Arquivo | Propósito | Uso |
|---|---|---|
| `PROMPT.md` | Instrução mestre pra LLM externa | **cole isso primeiro** |
| `PM-OS-CONTEXT.md` | Briefing da arquitetura PM-OS | **anexe como contexto** |
| `FILE-MAP.md` | Mapa Python→Go arquivo por arquivo | **anexe como referência** |
| `RULES.md` | Regras Go idiomáticas + restrições | **anexe como regra** |
| `CHECKLIST.md` | Critérios de aceitação por feature | **anexe como gate de qualidade** |

## Como usar (fluxo recomendado)

1. Clonar CrewAI localmente: `git clone --depth 1 https://github.com/crewAIInc/crewAI`
2. Mandar `PROMPT.md` pra LLM externa (Claude/GPT-4) + anexar os 4 docs auxiliares
3. LLM externa gera arquivos Go em `/tmp/crewai-port-output/pkg/...` seguindo `FILE-MAP.md`
4. LLM externa **também** gera `*_test.go` por arquivo (TDD obrigatório)
5. Dis envia pasta de saída pra Akita (eu) no próximo turno
6. Akita revisa, ajusta imports, resolve conflicts, integra no PM-OS, roda `go test -race`

## Escopo

**Portam: 60-65 arquivos** distribuídos em:
- Security (3)
- Hooks (5)
- Events (15)
- Guardrails (6)
- HITL (5)
- State/Checkpoint (8)
- Skills (4)
- Memory (9) — redesign pra Supabase pgvector
- MCP client (8)
- Tools concepts (2)
- Utilities (5)

**Não portam: ~240 arquivos** (agents, crews, flow decorators, RAG providers, LLM providers, telemetria, experimental, agent_tools, visualização).

## O que Akita faz depois

- Merge com branch `feat/llm-with-tools` atual
- Resolver conflitos de naming com `pkg/` existente
- Integrar com `engine.go`, `pkg/recipe/schema.go`, `cmd/pm-api/main.go`
- Wire eventos no `pkg/events` novo + hooks existentes
- Substituir `lancedb/qdrant` storage por `Supabase pgvector`
- Rodar `go test -race -count=1 ./...` até verde
- Passar pelo Keel
