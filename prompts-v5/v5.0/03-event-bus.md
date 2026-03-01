# PROMPT 03 — Event Bus sobre BullMQ

> INSTRUCAO CRITICA: NAO implemente ainda. Primeiro, leia tudo, depois responda com:
> 1. O que voce entendeu que deve ser feito
> 2. Quais filas BullMQ serao criadas
> 3. Catalogo de eventos com publishers e subscribers
> 4. Riscos que voce identifica
> Aguarde confirmacao antes de implementar.

## Pre-requisito

Prompt 02 (Data Plane) COMPLETO e testes passando.

## Contexto

O PM Engine v5 precisa de um mecanismo de pub/sub interno para desacoplar componentes. Hoje, modulos chamam uns aos outros diretamente (router chama dispatcher, dispatcher chama checkout, etc.). No v5, transicoes de estado publicam eventos e componentes se inscrevem no que precisam.

**Implementacao: BullMQ** (ja no stack). NAO usar Redis pub/sub direto — ele e fire-and-forget e perde eventos se o subscriber nao esta online. BullMQ garante persistencia, retry e dead letter queue.

## O que deve ser feito

### 1. Criar `src/event-bus.js`

Wrapper fino sobre BullMQ. Maximo 150 linhas.

```javascript
// src/event-bus.js
const { Queue, Worker, QueueEvents } = require('bullmq');
const config = require('./config');

// Conexao Redis (reutiliza a mesma do queue.js existente)
const connection = { host: '127.0.0.1', port: 6379 };

// Filas por dominio (separadas para controle de concorrencia e prioridade)
const DOMAINS = {
  task: 'pm-events-task',
  plan: 'pm-events-plan',
  clickup: 'pm-events-clickup',
  system: 'pm-events-system',
};

// Catalogo de eventos (documentacao + validacao)
const EVENT_CATALOG = {
  // Task lifecycle
  'task.received': { domain: 'task', description: 'Task normalizada e persistida internamente' },
  'task.agent_selected': { domain: 'task', description: 'Agente definido para a task' },
  'task.context_built': { domain: 'task', description: 'Prompt completo montado' },
  'task.dispatched': { domain: 'task', description: 'Enviado ao Trigger.dev' },
  'task.execution_started': { domain: 'task', description: 'Trigger.dev confirmou inicio' },
  'task.progress': { domain: 'task', description: 'Evento de streaming (turns, tool calls)' },
  'task.execution_completed': { domain: 'task', description: 'Trigger.dev retornou resultado' },
  'task.quality_check_passed': { domain: 'task', description: 'AUX aprovou' },
  'task.quality_check_failed': { domain: 'task', description: 'AUX reprovou' },
  'task.completed': { domain: 'task', description: 'Task finalizada com sucesso' },
  'task.failed': { domain: 'task', description: 'Task encerrada com falha' },
  'task.retrying': { domain: 'task', description: 'Sendo reexecutada' },

  // Plan lifecycle
  'plan.created': { domain: 'plan', description: 'Plano criado com N subtasks' },
  'plan.step_completed': { domain: 'plan', description: 'Subtask do plano concluiu' },
  'plan.step_unblocked': { domain: 'plan', description: 'Task filha desbloqueada' },
  'plan.completed': { domain: 'plan', description: 'Todas subtasks concluidas' },
  'plan.failed': { domain: 'plan', description: 'Subtask falhou sem recovery' },

  // ClickUp sync
  'clickup.sync_required': { domain: 'clickup', description: 'Dado precisa ser refletido no ClickUp' },
  'clickup.task_created': { domain: 'clickup', description: 'Webhook: nova task no ClickUp' },
  'clickup.status_changed': { domain: 'clickup', description: 'Webhook: status mudou no ClickUp' },

  // System health
  'system.health_degraded': { domain: 'system', description: 'Metrica abaixo do threshold' },
  'system.agent_stuck': { domain: 'system', description: 'Execucao travada alem do timeout' },
};

module.exports = {
  // Publicar evento
  async publish(eventName, payload) { ... },
  // - Valida que eventName existe no EVENT_CATALOG
  // - Resolve o dominio automaticamente
  // - Adiciona timestamp ao payload
  // - Publica na fila BullMQ do dominio
  // - Log: logger.info(`[event-bus] published ${eventName}`)

  // Registrar handler para eventos de um dominio
  subscribe(domain, handler) { ... },
  // - Cria Worker BullMQ para a fila do dominio
  // - handler recebe (eventName, payload)
  // - Retry automatico 3x com backoff exponencial
  // - Apos 3 falhas: move para dead letter queue

  // Registrar handler para evento especifico (filtro no subscriber)
  on(eventName, handler) { ... },
  // - Atalho: subscribe no dominio do evento, filtra por eventName

  // Utilitarios
  getEventCatalog() { ... },  // retorna EVENT_CATALOG
  async getDeadLetterCount() { ... },  // quantos eventos na DLQ
  async shutdown() { ... },  // fecha todas as filas e workers
};
```

### 2. Configuracao das filas BullMQ

Cada fila (dominio) tem configuracao especifica:

| Fila | Concorrencia | Retry | Backoff | DLQ apos |
|------|-------------|-------|---------|----------|
| pm-events-task | 5 | 3x | exponencial 1s/2s/4s | 3 falhas |
| pm-events-plan | 3 | 3x | exponencial 1s/2s/4s | 3 falhas |
| pm-events-clickup | 2 | 5x | exponencial 2s/4s/8s/16s/32s | 5 falhas (API instavel) |
| pm-events-system | 1 | 2x | fixo 5s | 2 falhas |

### 3. Integrar no index.js

Na inicializacao do sistema (`src/index.js`), inicializar o event bus:

```javascript
const eventBus = require('./event-bus');
// Event bus inicializa automaticamente ao ser importado
// Shutdown no SIGTERM/SIGINT:
process.on('SIGTERM', async () => {
  await eventBus.shutdown();
  process.exit(0);
});
```

### 4. NAO conectar subscribers ainda

Neste prompt, criamos apenas a infraestrutura (publish + subscribe). Os subscribers reais serao conectados nos prompts seguintes (04-08) conforme cada componente for refatorado.

Para validar, criar um subscriber de teste que apenas loga:

```javascript
// Temporario: loga todos os eventos (remover quando subscribers reais existirem)
eventBus.subscribe('task', (event, payload) => {
  logger.info(`[event-bus-debug] ${event}`, { taskId: payload.pm_task_uuid });
});
```

### 5. Teste

Criar `tests/test-event-bus.js`:

```javascript
// Testa:
// 1. publish de evento valido → subscriber recebe
// 2. publish de evento invalido → erro
// 3. handler que falha → retry 3x → DLQ
// 4. filtro por eventName funciona (on())
// 5. shutdown fecha tudo limpo
```

## O que NAO fazer

- NAO usar Redis pub/sub (`redis.publish`/`redis.subscribe`) — usar BullMQ
- NAO criar nova conexao Redis — reutilizar a configuracao existente
- NAO conectar o event bus ao fluxo de execucao atual (isso vem nos proximos prompts)
- NAO adicionar mais de 150 linhas ao event-bus.js

## Quality Gate

- [ ] `src/event-bus.js` criado com publish, subscribe, on, shutdown
- [ ] 4 filas BullMQ criadas com configuracoes especificas
- [ ] EVENT_CATALOG com todos os eventos documentados
- [ ] Teste de publish → subscribe funciona
- [ ] Teste de falha → retry → DLQ funciona
- [ ] Shutdown limpo (sem conexoes pendentes)
- [ ] Smoke tests dos 14 endpoints continuam passando
- [ ] event-bus.js tem no maximo 150 linhas
