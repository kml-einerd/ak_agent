# [RASCUNHO — SERA REVISADO APOS RESULTADOS DE 01-03]
# PROMPT 05 — Callback do Trigger.dev + Streaming

> INSTRUCAO CRITICA: NAO implemente ainda. Primeiro, leia tudo, depois responda com:
> 1. O que voce entendeu que deve ser feito
> 2. Mudancas necessarias no PM Engine (novos endpoints)
> 3. Mudancas necessarias no Trigger.dev worker (pm-agents.ts / trigger-tasks)
> 4. Fluxo completo de dados: PM Engine → Trigger.dev → execucao → callback → PM Engine
> 5. Riscos que voce identifica
> Aguarde confirmacao antes de implementar.

## Pre-requisito

Prompts 01-04 COMPLETOS. O trigger-tasks deve estar copiado para dentro do repo pm-engine (pasta `trigger-tasks/`). Se nao esta, copie primeiro.

## Contexto

Gap #1 da auditoria: quando a execucao vai via Trigger.dev, o PM Engine perde visibilidade. Dispatch_log vazia, runs nao registrados, WebSocket mudo.

**Solucao:** Trigger.dev reporta de volta para o PM Engine via callback HTTP. O PM Engine registra tudo internamente.

Gap #7: WebSocket nao funciona via Trigger.dev.

**Solucao:** Trigger.dev envia eventos de progresso via streaming endpoint. PM Engine retransmite via WebSocket.

## O que deve ser feito

### 1. Novo endpoint: POST /internal/run-complete

Endpoint interno (nao exposto publicamente) que o Trigger.dev chama ao terminar uma execucao.

```javascript
// Em webhook-server.js
app.post('/internal/run-complete', async (req, res) => {
  const {
    pm_task_uuid,    // UUID interno da task
    run_id,          // ID do run no Trigger.dev
    status,          // 'completed' | 'failed'
    result,          // output do agente (texto)
    agent,           // qual agente executou
    model_used,      // qual modelo foi usado
    turns_used,      // quantos turns
    cost_usd,        // custo da execucao
    time_seconds,    // duracao
    error_type,      // se falhou: codigo do erro (da taxonomia)
    error_message,   // se falhou: mensagem
  } = req.body;

  // 1. Atualizar task no banco interno
  taskStore.updateTask(pm_task_uuid, {
    status: status === 'completed' ? 'completed' : 'failed',
    updated_at: new Date().toISOString()
  });

  // 2. Registrar metricas
  taskStore.recordMetrics({
    pmTaskUuid: pm_task_uuid,
    agent, modelUsed: model_used, turnsUsed: turns_used,
    costUsd: cost_usd, timeSeconds: time_seconds,
    errorType: error_type,
    auxVerdict: 'pending', // AUX roda apos este callback
    qualityScore: null,     // preenchido pelo AUX
  });

  // 3. Publicar evento
  if (status === 'completed') {
    await eventBus.publish('task.execution_completed', {
      pm_task_uuid, agent, result, run_id
    });
  } else {
    await eventBus.publish('task.failed', {
      pm_task_uuid, agent, error_type, error_message, run_id
    });
  }

  // 4. Registrar no audit_trail (tabela existente)
  db.addAuditEntry(pm_task_uuid, `run_${status}`, agent);

  res.json({ received: true });
});
```

### 2. Novo endpoint: POST /internal/run-stream

Endpoint para eventos de progresso durante a execucao.

```javascript
app.post('/internal/run-stream', (req, res) => {
  const { pm_task_uuid, event_type, data } = req.body;
  // event_type: 'started' | 'text' | 'tool_call' | 'turn_complete'

  // 1. Publicar evento
  eventBus.publish('task.progress', { pm_task_uuid, event_type, data });

  // 2. Retransmitir via WebSocket (reutilizar logica existente)
  broadcastToWs({
    type: `agent_${event_type}`,
    taskId: pm_task_uuid,
    data
  });

  res.json({ ok: true });
});
```

### 3. Refatorar o Trigger.dev worker

O worker no trigger-tasks precisa ser modificado para:

**A) Receber payload COMPLETO do PM Engine** (nao mais tomar decisoes):

Hoje o worker faz:
```
1. getTask(taskId) — busca task do ClickUp
2. buildBriefing() — monta briefing
3. selectAgent() — seleciona agente
4. buildPrompt() — constroi prompt
5. dispatch() — executa
```

Na v5, o worker faz:
```
1. Recebe payload completo do PM Engine (agente, prompt, modelo ja definidos)
2. Executa o agente CLI com o payload recebido
3. Envia eventos de progresso via POST /internal/run-stream
4. Ao terminar, chama POST /internal/run-complete com resultado
```

**B) Modificar o payload enviado pelo PM Engine:**

Em `src/trigger-bridge.js`, mudar o payload:

```javascript
// ANTES:
const payload = { taskId, taskName, source: 'pm-engine-bridge' };

// DEPOIS:
const payload = {
  pm_task_uuid,          // UUID interno
  clickup_id: taskId,    // ID do ClickUp (para compatibilidade)
  agent: selectedAgent,  // agente ja selecionado pelo PM Engine
  prompt: fullPrompt,    // prompt COMPLETO (7 camadas) ja construido
  model: selectedModel,  // modelo ja definido
  timeout: 7200000,      // 2h em ms
  callback_url: `http://localhost:${config.PM_PORT}/internal/run-complete`,
  streaming_url: `http://localhost:${config.PM_PORT}/internal/run-stream`,
};
```

**C) Modificar o worker para usar o novo payload:**

```typescript
// No pm-agents.ts (trigger-tasks):
// ANTES: getTask, buildBriefing, selectAgent, buildPrompt — tudo no worker
// DEPOIS:
export const pmDispatch = task({
  id: 'pm-dispatch',
  run: async (payload) => {
    const { pm_task_uuid, agent, prompt, model, callback_url, streaming_url } = payload;

    // Notificar inicio
    await fetch(streaming_url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({ pm_task_uuid, event_type: 'started', data: { agent } })
    });

    // Executar o agente
    const startTime = Date.now();
    const result = await spawnClaude(prompt, { model, timeout: payload.timeout });

    // Reportar resultado via callback
    await fetch(callback_url, {
      method: 'POST',
      headers: { 'Content-Type': 'application/json' },
      body: JSON.stringify({
        pm_task_uuid,
        run_id: ctx.run.id,
        status: result.success ? 'completed' : 'failed',
        result: result.output,
        agent,
        model_used: model,
        turns_used: result.turns || 0,
        cost_usd: result.cost || 0,
        time_seconds: Math.round((Date.now() - startTime) / 1000),
        error_type: result.error?.code || null,
        error_message: result.error?.message || null,
      })
    });

    return { success: result.success };
  }
});
```

### 4. Mover a inteligencia para o PM Engine

Refatorar `src/router.js` e `src/dispatcher.js` para que TODA a inteligencia rode ANTES de enviar ao Trigger.dev:

```javascript
// Em router.js → handleExecute():
// 1. intake.normalize() ja foi chamado (prompt 04)
// 2. Agora: selectAgent, buildContext, buildPrompt — tudo aqui
// 3. Montar payload completo
// 4. triggerBridge.dispatch(payloadCompleto)
// 5. Atualizar task: status = 'dispatched'
// 6. eventBus.publish('task.dispatched', ...)
```

### 5. Fallback para dispatch local

Se Trigger.dev estiver offline, o PM Engine faz dispatch local (como funciona hoje). Manter esse fallback:

```javascript
if (!triggerBridge.isEnabled() || !(await triggerBridge.healthCheck())) {
  logger.warn('[router] Trigger.dev offline — executando localmente');
  // Dispatch local (fluxo atual mantido)
  // MAS: ao terminar, registrar no banco interno e publicar eventos
  // (simular o que o callback faria)
}
```

## O que NAO fazer

- NAO remover as tasks per-agent no Trigger.dev (pm-agent-dex, etc.) — manter por compatibilidade
- NAO alterar o ClickUp client neste prompt
- NAO implementar AUX ainda (prompt 07)
- NAO quebrar o fluxo de fallback local

## Quality Gate

- [ ] POST /internal/run-complete criado e funcional
- [ ] POST /internal/run-stream criado e funcional
- [ ] trigger-bridge.js envia payload completo (agente, prompt, modelo, callbacks)
- [ ] Worker do Trigger.dev usa payload recebido (nao toma decisoes proprias)
- [ ] Worker chama callback com resultado ao terminar
- [ ] Worker envia eventos de progresso durante execucao
- [ ] WebSocket recebe eventos de execucoes via Trigger.dev (Gap #7 resolvido)
- [ ] Banco interno registra TODAS as execucoes (Gap #1 resolvido)
- [ ] Fallback local continua funcionando se Trigger.dev estiver offline
- [ ] 14 smoke tests passam
