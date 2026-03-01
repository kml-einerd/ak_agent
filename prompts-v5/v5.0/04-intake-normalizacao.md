# [RASCUNHO — SERA REVISADO APOS RESULTADOS DE 01-03]
# PROMPT 04 — Intake Worker + Normalizacao de Entry Points

> INSTRUCAO CRITICA: NAO implemente ainda. Primeiro, leia tudo, depois responda com:
> 1. O que voce entendeu que deve ser feito
> 2. Quais entry points serao refatorados e como
> 3. Formato do canonical_task_event
> 4. Riscos que voce identifica (especialmente regressoes)
> Aguarde confirmacao antes de implementar.

## Pre-requisito

Prompts 01-03 COMPLETOS e testes passando.

## Contexto

Hoje existem 6 entry points com comportamentos diferentes (ver SYSTEM-AUDIT secao 4). O Gap #1 existe porque Trigger.dev bypassa o PM Engine. A solucao: toda execucao — independente de origem — passa pelo mesmo pipeline interno.

```
ClickUp webhook     -\
CLI pm-cli.sh       -|
API REST /trigger   -|-> intake.normalize() -> banco interno -> fluxo canonico
API REST /create    -|
API REST /plan      -|
Agendamento cron    -/
```

## O que deve ser feito

### 1. Criar `src/intake.js`

Funcao central de normalizacao. Todo entry point chama `normalize()` que produz um `canonical_task_event` padronizado.

```javascript
// src/intake.js
const taskStore = require('./task-store');
const eventBus = require('./event-bus');
const { createError } = require('./errors');

/**
 * Normaliza qualquer entrada para o formato canonico interno.
 * Cria registro no banco e publica evento.
 *
 * @param {object} input
 * @param {string} input.source - 'clickup' | 'cli' | 'api' | 'inject' | 'cron'
 * @param {string} [input.clickup_id] - ID do ClickUp (se origem for ClickUp)
 * @param {string} input.name - nome da task
 * @param {string} [input.description] - descricao
 * @param {string} [input.action] - 'execute' | 'plan' | 'create'
 * @param {string} [input.agent] - agente forcado (opcional)
 * @param {string} [input.project_id] - projeto
 * @param {string} [input.squad_id] - squad
 * @param {number} [input.priority] - 1-4
 * @param {string} [input.task_type] - 'task' | 'plan'
 * @param {string} [input.parent_task_id] - se faz parte de um plano
 * @param {string} [input.plan_goal] - objetivo do plano
 * @param {array}  [input.subtasks] - subtasks para planos
 * @param {string} [input.scheduled_at] - ISO 8601
 * @param {object} [input.metadata] - dados extras
 * @returns {object} canonical_task_event
 */
async function normalize(input) {
  // 1. Validar campos obrigatorios
  // 2. Se clickup_id fornecido, verificar se ja existe no identity_map
  //    - Se existe: retornar o pm_task_uuid existente (idempotencia)
  //    - Se nao existe: criar nova identity
  // 3. Criar task no banco interno (taskStore.createTask)
  // 4. Se task_type='plan' e subtasks fornecidas: criar tasks filhas
  // 5. Publicar evento: eventBus.publish('task.received', canonicalEvent)
  // 6. Retornar canonical_task_event
}

module.exports = { normalize };
```

**Formato do canonical_task_event:**

```javascript
{
  pm_task_uuid: 'uuid-v4',
  clickup_id: '86abc123' || null,
  source: 'clickup',
  name: 'Implementar login OAuth',
  description: '...',
  action: 'execute',
  task_type: 'task',
  parent_task_id: null,
  plan_goal: null,
  assigned_agent: null,  // ou 'dex' se forcado
  project_id: 'nowork',
  squad_id: 'nowork',
  priority: 3,
  scheduled_at: null,
  depends_on: [],
  metadata: {},
  created_at: '2026-03-01T...'
}
```

### 2. Refatorar entry points em `webhook-server.js`

Cada entry point atual deve ser modificado para chamar `intake.normalize()` ANTES de qualquer processamento. O fluxo muda de:

**ANTES:** Entry point → router.routeEvent() → dispatcher → Trigger.dev
**DEPOIS:** Entry point → intake.normalize() → banco interno → router.routeEvent() → dispatcher → Trigger.dev

Refatorar estes endpoints:

**POST /webhook/clickup:**
```javascript
// ANTES: routeEvent({ event, task_id, ... })
// DEPOIS:
const task = await clickupClient.getTask(taskId);  // ja faz isso hoje
const canonical = await intake.normalize({
  source: 'clickup',
  clickup_id: taskId,
  name: task.name,
  description: task.description,
  action: resolveActionFromStatus(task.status),  // 'executando' -> 'execute'
  project_id: resolveProject(task),
  squad_id: resolveSquad(task),
  priority: task.priority,
  metadata: { clickup_status: task.status, clickup_tags: task.tags }
});
// Depois: routeEvent com canonical (nao mais com dados brutos do ClickUp)
```

**POST /trigger:**
```javascript
// ANTES: routeEvent({ event: 'taskStatusUpdated', task_id })
// DEPOIS:
const canonical = await intake.normalize({
  source: 'api',
  clickup_id: req.body.task_id,  // pode ser clickup_id
  name: taskName,  // buscar do ClickUp se necessario
  action: req.body.action || 'execute',
  agent: req.body.agent,
  metadata: { dry_run: req.body.dry_run }
});
```

**POST /create:**
```javascript
// ANTES: cria direto no ClickUp
// DEPOIS:
const canonical = await intake.normalize({
  source: 'api',
  name: req.body.name,
  description: req.body.description,
  action: req.body.execute ? 'execute' : 'create',
  project_id: req.body.project,
  priority: req.body.priority,
  metadata: { tags: req.body.tags }
});
// ClickUp e atualizado via evento (futuro: worker de escrita)
// Por ora: manter a criacao no ClickUp tambem (transicao gradual)
```

**POST /plan:**
```javascript
const canonical = await intake.normalize({
  source: 'api',
  name: req.body.name,
  description: req.body.description,
  task_type: 'plan',
  plan_goal: req.body.description,
  subtasks: req.body.subtasks,  // array de { name, description }
  action: 'create',
});
```

### 3. Transicao Gradual

IMPORTANTE: Nesta fase, o fluxo ATUAL continua funcionando normalmente. O `normalize()` adiciona o registro interno SEM interferir no fluxo existente. O router continua recebendo os mesmos dados de antes — apenas agora o banco interno tambem e populado.

Nao quebrar nada. Adicionar, nao substituir.

### 4. Endpoint de consulta

Adicionar endpoint GET para consultar tasks internas:

```
GET /tasks?status=pending&limit=20  → lista tasks internas
GET /tasks/:id                      → detalhe de task interna (com artefatos se houver)
GET /plans                          → lista planos com progresso
GET /plans/:id                      → detalhe do plano com subtasks e artefatos
```

### 5. Teste

Verificar que cada entry point agora cria registro interno:

```bash
# Via API
curl -X POST localhost:9897/trigger -d '{"task_id":"86abc123"}' -H "Content-Type: application/json"
# Verificar: registro criado em tasks + task_identity_map
curl localhost:9897/tasks | jq .

# Via webhook simulado
curl -X POST localhost:9897/webhook/clickup -d '{"event":"taskStatusUpdated","task_id":"86test01"}' -H "Content-Type: application/json"
# Verificar: mesmo registro
```

## O que NAO fazer

- NAO remover o fluxo atual (routeEvent, dispatcher, etc.) — adicionar o normalize() ANTES
- NAO quebrar a integracao com ClickUp
- NAO mudar como o router processa eventos (isso vem em prompts futuros)
- NAO implementar os workers de ClickUp ainda (prompt 06)

## Quality Gate

- [ ] `src/intake.js` criado com normalize()
- [ ] Todos os 4 POST endpoints refatorados para chamar normalize()
- [ ] Registro interno criado para cada entry point
- [ ] task_identity_map populado corretamente (clickup_id quando aplicavel)
- [ ] POST /plan cria plano com subtasks filhas no banco interno
- [ ] Novos endpoints GET /tasks e GET /plans funcionam
- [ ] Fluxo existente NAO foi quebrado (14 smoke tests passam)
- [ ] Idempotencia: mesma task recebida 2x nao cria duplicata
