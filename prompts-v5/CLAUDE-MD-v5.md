# PM Engine v5 — CLAUDE.MD

> Este arquivo substitui o CLAUDE.md atual do projeto.
> Coloque na raiz do repositorio pm-engine.

---

# PM Engine v5 — Sistema de Orquestracao de Agentes

## Identidade

PM Engine e o kernel de orquestracao de agentes IA. Ele decide TUDO (qual agente, qual contexto, qual modelo, qual temperatura, quais credenciais). Trigger.dev APENAS executa o que o PM Engine manda. ClickUp e um canal de input/output do usuario — nao e motor.

## Arquitetura

```
PM Engine (kernel)  →  decide tudo, registra tudo, valida tudo
Trigger.dev         →  executa com durabilidade, reporta resultado via callback
ClickUp             →  canal do usuario (input via webhook, output via workers)
Agentes CLI         →  processos isolados que fazem o trabalho real
```

## Regras Absolutas de Implementacao

### Estrutura
- Nenhum arquivo deve exceder 500 linhas. Se exceder, divida em modulos logicos
- Todo novo modulo em `src/` — nao criar subpastas novas sem necessidade
- Module system: CommonJS (`require`/`module.exports`) — nao usar ESM
- Manter as 5 dependencias atuais (better-sqlite3, bullmq, ioredis, js-yaml, ws). Nova dependencia so com justificativa explicita

### Banco de Dados
- SQLite WAL mode (mantido). Nao migrar para PostgreSQL
- Novas tabelas criadas via migration functions em `db.js` (mesmo padrao atual)
- Toda mudanca de estado persiste no banco ANTES de publicar evento

### Event Bus
- Implementado sobre BullMQ (ja no stack). NAO usar Redis pub/sub direto
- Eventos criticos persistidos antes de publicar (at-least-once delivery via BullMQ)
- Dead letter queue para eventos nao processados

### Agentes e ClickUp
- Agentes NUNCA chamam ClickUp diretamente — toda interacao via PM Engine
- Workers de sincronizacao ClickUp sao assincrono — falha no ClickUp nao bloqueia execucao
- Toda task tem dual identity: pm_task_uuid (interno) + clickup_id (externo, pode ser null)

### Qualidade
- Toda execucao passa por AUX deterministico antes de ser marcada como concluida
- AUX conceitual (com LLM) so no v5.1+ — por ora, apenas checks objetivos
- Modelo para AUX: claude-haiku (custo minimo)

### Paralelismo
- Tasks executam UMA POR VEZ (evitar rate limit)
- DENTRO de um plano, steps sem depends_on entre si executam em PARALELO
- Concorrencia maxima de steps paralelos: 3

### Testes
- Apos cada mudanca, rodar smoke tests (14 testes da SYSTEM-AUDIT)
- Quality gate a cada 3 features: revisar file sizes, extrair patterns
- Nenhum endpoint existente pode parar de funcionar

### Proibido
- NAO adicionar features que nao estao no prompt atual
- NAO refatorar codigo que nao esta no escopo do prompt
- NAO mudar convencoes de nomenclatura existentes sem instrucao explicita
- NAO criar arquivos de documentacao sem instrucao explicita
- NAO usar ESM (import/export) — manter CommonJS
- NAO instalar novas dependencias npm sem justificativa

## Contexto do Sistema (7 camadas)

| Camada | Nome | Condicao |
|--------|------|----------|
| 1 | meta-frame | Sempre |
| 2 | squad | Se task tem squad |
| 3 | profile | Se score >= 3 |
| 4 | process | Sempre |
| 5 | task | Sempre |
| 6 | project_memory | Se projeto tem memoria (v5.1+) |
| 7 | plan_context | Se task tem parent_task_id |

## Contrato de Output dos Agentes

Todo agente deve produzir output neste formato:

```
## RESULTADO
[Texto livre com o resultado do trabalho]

## ARTEFATOS
### [artifact_key]
[Conteudo do artefato]

## STATUS
COMPLETO | PARCIAL | FALHA

## NOTAS
[Observacoes, decisoes, riscos]
```

O PM Engine faz parsing deste formato para persistir em `task_artifacts` e injetar como contexto nos steps dependentes.

## Limites

| Parametro | Valor |
|-----------|-------|
| Max prompt | 48.000 chars |
| Max description | 8.000 chars |
| Max context | 2.000 chars |
| Max project context | 4.000 chars |
| Max subtasks no prompt | 20 |
| Max turns (Claude) | 50 |
| Timeout Claude | 2h |
| Max concurrent steps | 3 |
| Max arquivo | 500 linhas |

## Agents

| Agente | Role | Provider |
|--------|------|----------|
| dex | Developer | claude |
| quinn | QA | claude |
| aria | Architect | claude |
| atlas | Analyst | claude |
| sage | Content Writer | claude |
| morgan | PM | claude |
| pixel | SEO/Marketing | claude |
| uma | UX/Design | claude |
| gage | DevOps | claude |
| prism | Prompt Engineer | claude |
