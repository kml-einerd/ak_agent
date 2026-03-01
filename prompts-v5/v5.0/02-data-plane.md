# PROMPT 02 — Data Plane: Novas Tabelas + Modulos de Acesso

> INSTRUCAO CRITICA: NAO implemente ainda. Primeiro, leia tudo, depois responda com:
> 1. O que voce entendeu que deve ser feito
> 2. Schema SQL completo que sera criado
> 3. API publica dos modulos (funcoes exportadas)
> 4. Riscos que voce identifica
> Aguarde confirmacao antes de implementar.

## Pre-requisito

Prompt 01 (Limpeza) COMPLETO e smoke tests passando.

## Contexto

O PM Engine v5 precisa de um banco de dados interno como fonte de verdade. Hoje o ClickUp e a fonte de verdade das tasks. Na v5, o banco interno e a fonte de verdade e o ClickUp e um espelho.

O banco continua sendo SQLite WAL mode (via better-sqlite3, ja no stack). As novas tabelas sao ADICIONADAS ao `db.js` existente — nao substituem as tabelas atuais.

## O que deve ser feito

### 1. Adicionar novas tabelas em `db.js`

Adicionar na funcao de inicializacao do banco (onde as tabelas atuais sao criadas) as seguintes tabelas:

```sql
-- Mapeamento de identidade: todo ID externo mapeia para um UUID interno
CREATE TABLE IF NOT EXISTS task_identity_map (
  pm_task_uuid  TEXT PRIMARY KEY,  -- UUID v4 gerado pelo sistema
  clickup_id    TEXT UNIQUE,       -- nulo para tasks criadas internamente
  source        TEXT NOT NULL,     -- 'clickup' | 'inject' | 'internal' | 'api' | 'cli'
  created_at    TEXT DEFAULT (datetime('now'))
);

-- Tasks internas: fonte de verdade do sistema
CREATE TABLE IF NOT EXISTS tasks (
  id              TEXT PRIMARY KEY,  -- referencia task_identity_map.pm_task_uuid
  name            TEXT NOT NULL,
  description     TEXT,
  status          TEXT NOT NULL DEFAULT 'pending',
  -- Status validos: pending, queued, dispatched, executing, completed, failed, cancelled, blocked
  task_type       TEXT NOT NULL DEFAULT 'task',
  -- 'task' = unidade atomica | 'plan' = container de subtasks
  parent_task_id  TEXT,             -- referencia tasks.id (para hierarquia de planos)
  plan_goal       TEXT,             -- objetivo do plano (apenas para task_type='plan')
  project_id      TEXT,
  squad_id        TEXT,
  assigned_agent  TEXT,
  priority        INTEGER DEFAULT 3,  -- 1=urgent, 2=high, 3=normal, 4=low
  scheduled_at    TEXT,               -- ISO 8601, nulo = imediata
  depends_on      TEXT,               -- JSON array de task IDs que devem completar antes
  metadata        TEXT DEFAULT '{}',  -- JSON livre
  created_at      TEXT DEFAULT (datetime('now')),
  updated_at      TEXT DEFAULT (datetime('now'))
);

-- Artefatos: outputs nomeados produzidos por tasks
CREATE TABLE IF NOT EXISTS task_artifacts (
  id           TEXT PRIMARY KEY,  -- UUID v4
  task_id      TEXT NOT NULL,     -- referencia tasks.id
  artifact_key TEXT NOT NULL,     -- nome do artefato ('research_findings', 'architecture_doc')
  content      TEXT,              -- conteudo (truncado se > 8KB)
  full_path    TEXT,              -- path no filesystem se conteudo for grande
  created_at   TEXT DEFAULT (datetime('now'))
);

-- Metricas de execucao: registra cada run
CREATE TABLE IF NOT EXISTS execution_metrics (
  id              TEXT PRIMARY KEY,  -- UUID v4
  pm_task_uuid    TEXT,              -- referencia tasks.id
  agent           TEXT,
  task_type_inferred TEXT,           -- 'dev', 'content', 'research', 'ops', etc.
  project_id      TEXT,
  quality_score   REAL,              -- 0-100, do AUX
  aux_verdict     TEXT,              -- 'pass' | 'fail' | 'skipped'
  turns_used      INTEGER,
  cost_usd        REAL,
  time_seconds    INTEGER,
  retries_needed  INTEGER DEFAULT 0,
  model_used      TEXT,
  error_type      TEXT,              -- da taxonomia de erros (errors.js)
  is_sandbox      INTEGER DEFAULT 0,
  created_at      TEXT DEFAULT (datetime('now'))
);

-- Registry: entidades configuraveis e versionadas
CREATE TABLE IF NOT EXISTS registry (
  id              TEXT PRIMARY KEY,  -- UUID v4
  entity_type     TEXT NOT NULL,
  -- Tipos: agent_prompt, agent_config, agent_selection_rule,
  --        workflow_template, skill_definition, routing_rule,
  --        temperature_profile, model_routing, planning_checklist
  entity_id       TEXT NOT NULL,     -- slug: 'dex', 'implement-feature', etc.
  version         INTEGER NOT NULL DEFAULT 1,
  config          TEXT NOT NULL,     -- JSON com o conteudo da entidade
  is_active       INTEGER DEFAULT 0,
  created_by      TEXT,              -- 'user' | 'system'
  created_at      TEXT DEFAULT (datetime('now')),
  notes           TEXT
);

-- Indices
CREATE INDEX IF NOT EXISTS idx_tasks_status ON tasks(status);
CREATE INDEX IF NOT EXISTS idx_tasks_parent ON tasks(parent_task_id);
CREATE INDEX IF NOT EXISTS idx_tasks_project ON tasks(project_id);
CREATE INDEX IF NOT EXISTS idx_artifacts_task ON task_artifacts(task_id);
CREATE INDEX IF NOT EXISTS idx_metrics_task ON execution_metrics(pm_task_uuid);
CREATE INDEX IF NOT EXISTS idx_metrics_agent ON execution_metrics(agent);
CREATE INDEX IF NOT EXISTS idx_registry_entity ON registry(entity_type, entity_id);
CREATE UNIQUE INDEX IF NOT EXISTS idx_registry_active
  ON registry(entity_type, entity_id) WHERE is_active = 1;
```

**IMPORTANTE:** Usar TEXT para UUIDs (SQLite nao tem tipo UUID nativo). Usar INTEGER para booleans (0/1). Usar TEXT com datetime() para timestamps.

### 2. Criar `src/task-store.js`

Modulo de acesso as tabelas de tasks. Funcoes exportadas:

```javascript
module.exports = {
  // Identity map
  createIdentity(source, clickupId = null),  // retorna pm_task_uuid
  resolveByClickupId(clickupId),             // retorna pm_task_uuid ou null
  resolveByUuid(pmTaskUuid),                 // retorna { pm_task_uuid, clickup_id, source }

  // Tasks CRUD
  createTask({ name, description, taskType, parentTaskId, planGoal, projectId, squadId, assignedAgent, priority, scheduledAt, dependsOn, metadata }),
  getTask(taskId),
  updateTask(taskId, updates),               // updates = objeto parcial
  getTasksByStatus(status, limit = 50),
  getTasksByParent(parentTaskId),            // subtasks de um plano
  getPlanProgress(planTaskId),               // { total, completed, failed, executing, pending }

  // Artifacts
  createArtifact(taskId, artifactKey, content, fullPath = null),
  getArtifacts(taskId),                      // todos os artefatos de uma task
  getArtifactsByPlan(planTaskId),            // artefatos de todas as subtasks de um plano

  // Metricas
  recordMetrics({ pmTaskUuid, agent, taskTypeInferred, projectId, qualityScore, auxVerdict, turnsUsed, costUsd, timeSeconds, retriesNeeded, modelUsed, errorType, isSandbox }),
  getMetricsByAgent(agent, limit = 50),
  getMetricsSummary(agent),                  // { avgQuality, avgCost, avgTime, successRate }
};
```

**Implementacao:** Cada funcao e uma query SQLite usando `better-sqlite3` (prepared statements). Gerar UUIDs com `crypto.randomUUID()` (Node 19+) ou fallback simples.

### 3. Criar `src/registry.js`

Modulo de acesso ao registry. Funcoes exportadas:

```javascript
module.exports = {
  // CRUD
  register(entityType, entityId, config, createdBy = 'user', notes = null),
  getActive(entityType, entityId),           // retorna a versao ativa ou null
  getVersion(entityType, entityId, version), // retorna versao especifica
  listVersions(entityType, entityId),        // todas as versoes
  listEntities(entityType),                  // todas as entidades de um tipo
  activate(entityType, entityId, version),   // desativa anterior, ativa nova
  deactivate(entityType, entityId),          // desativa versao ativa

  // Seed: carrega configuracao inicial dos arquivos existentes
  seedFromConfig(),
  // Le agents.json → registra como agent_config
  // Le squads/*.yaml → registra como squad_config (futuro)
  // Le profiles/*.md → registra como profile_config (futuro)
  // Por ora, seed apenas agents.json (v5.0)
};
```

### 4. Seed inicial do Registry

Na inicializacao do sistema (`src/index.js`), apos criar as tabelas, verificar se o registry esta vazio. Se sim, chamar `registry.seedFromConfig()` para popular com os dados dos arquivos de config atuais.

Para v5.0, fazer seed apenas de `agents.json` → `agent_config`. Cada agente vira uma entrada no registry:

```javascript
// Exemplo de seed para o agente dex
registry.register('agent_config', 'dex', {
  name: 'dex',
  role: 'Developer',
  provider: 'claude',
  tags: ['dev', 'code', 'feature', 'bug', 'fix'],
  keywords: { implement: 5, develop: 4, code: 4, build: 3, fix: 5, bug: 5 },
  isDefault: true
}, 'system', 'Seed from agents.json');
```

### 5. Testes

Criar `tests/test-data-plane.js` (script simples, sem framework):

```javascript
// Testes basicos: criar identity, criar task, criar plano com filhas,
// criar artefatos, registrar metricas, CRUD do registry
// Rodar: node tests/test-data-plane.js
// Output: linha por teste com PASS/FAIL
```

## O que NAO fazer

- NAO alterar as tabelas existentes (agents, own_actions, audit_trail, etc.)
- NAO migrar dados das tabelas antigas para as novas
- NAO criar endpoints HTTP ainda (isso vem no prompt 04)
- NAO modificar o fluxo de execucao atual

## Quality Gate

- [ ] 5 novas tabelas criadas no SQLite com indices
- [ ] `task-store.js` com todas as funcoes listadas
- [ ] `registry.js` com CRUD + seed
- [ ] Seed de agents.json funciona na inicializacao
- [ ] `tests/test-data-plane.js` passa (CRUD basico funciona)
- [ ] Smoke tests dos 14 endpoints continuam passando
- [ ] Nenhum arquivo excede 500 linhas
