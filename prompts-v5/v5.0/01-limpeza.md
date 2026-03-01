# PROMPT 01 — Limpeza de Codigo Morto + Taxonomia de Erros

> INSTRUCAO CRITICA: NAO implemente ainda. Primeiro, leia tudo, depois responda com:
> 1. O que voce entendeu que deve ser feito
> 2. Quais arquivos serao modificados/criados/deletados
> 3. Riscos que voce identifica
> Aguarde confirmacao antes de implementar.

## Contexto

Estamos iniciando a refatoracao do PM Engine para v5. Este e o Passo 1: limpar codigo morto antes de construir. Construir sobre codigo morto acumula divida tecnica.

Leia o CLAUDE.md na raiz do projeto (ele foi atualizado para v5 — siga as regras dele).

## O que deve ser feito

### 1. Remover `state.js`

O arquivo `src/state.js` (19 linhas) e um wrapper legacy — todas as chamadas ja vao direto ao `db.js`. Deve ser:
- Deletado completamente
- Todos os imports/requires de `state.js` em outros arquivos devem ser atualizados para usar `db.js` diretamente
- Verificar com `grep -r "state" src/` se ha referencias remanescentes (ignorar variaveis chamadas "state" que nao sao o modulo)

### 2. Remover providers mortos

Os providers `gemini.js`, `kimi.js` e `openclaw.js` nunca sao executados (todos os agentes usam claude). Deve ser:
- Deletar os 3 arquivos de `src/providers/`
- Manter `src/providers/base.js` (interface de abstracao) e `src/providers/index.js` (registry)
- Em `src/providers/index.js`: remover os imports e registros dos providers mortos, mas manter a estrutura de registry para futuros providers
- Adicionar comentario no index.js: `// Para adicionar novo provider: criar arquivo que estende base.js e registrar aqui`
- Manter `openrouter.js` (pode ser ativado com API key, tem tracking de custo)

### 3. Mover arquivos de referencia

Os arquivos abaixo existem no `config/` mas nao sao lidos pelo codigo:
- `config/nowork-clickup-tasks.json`
- `config/nowork-drive-structure.json`
- `config/credentials.json`
- `config/arsenal.md`

Deve ser:
- Criar pasta `docs/reference/` se nao existir
- Mover esses 4 arquivos para `docs/reference/`
- Verificar com `grep -r` que nenhum codigo os referencia (se referenciar, ajustar o path)

### 4. Deprecar tabela `dispatch_log`

A tabela `dispatch_log` nunca e preenchida quando a execucao vai via Trigger.dev (que e o fluxo principal). Na v5, o tracking migra para a tabela `runs` (existente) e as novas tabelas. Deve ser:
- Em `db.js`: comentar a criacao da tabela `dispatch_log` com nota: `// DEPRECATED v5: tracking migrado para runs + execution_metrics`
- Em todos os modulos que escrevem em `dispatch_log`: remover as escritas (mas manter leituras para o endpoint `/dispatches` funcionar com dados historicos)
- No endpoint GET `/dispatches` em `webhook-server.js`: adicionar nota no response: `{ "deprecated": "dispatch_log sera removido na proxima versao. Use /runs." }`

### 5. Criar taxonomia de erros padronizada

Criar `src/errors.js` com classes de erro que todo o sistema usara:

```javascript
// src/errors.js — Taxonomia de erros do PM Engine v5
class PMError extends Error {
  constructor(code, message, context = {}) {
    super(message);
    this.code = code;
    this.context = context;
    this.timestamp = new Date().toISOString();
  }
}

// Categorias
const ERROR_CODES = {
  // Agente
  AGENT_TIMEOUT: 'Agente excedeu o tempo limite',
  AGENT_QUALITY_FAIL: 'AUX reprovou o output',
  AGENT_INVALID_OUTPUT: 'Output nao esta no formato esperado',
  AGENT_SELECTION_FAIL: 'Nenhum agente adequado encontrado',

  // ClickUp
  CLICKUP_API_ERROR: 'Falha na chamada a API do ClickUp',
  CLICKUP_RATE_LIMIT: 'Rate limit atingido',

  // Trigger.dev
  TRIGGER_UNREACHABLE: 'Trigger.dev nao responde',
  TRIGGER_RUN_FAILED: 'Run no Trigger.dev encerrou com erro',

  // Contexto
  CONTEXT_BUILD_FAIL: 'Falha ao construir contexto',

  // Fila
  QUEUE_OVERFLOW: 'Fila excedeu capacidade configurada',

  // Validacao
  VALIDATION_FAIL: 'Validacao de input falhou',
};

function createError(code, extraContext = {}) {
  const message = ERROR_CODES[code] || `Erro desconhecido: ${code}`;
  return new PMError(code, message, extraContext);
}

module.exports = { PMError, ERROR_CODES, createError };
```

### 6. Smoke Test

Apos todas as mudancas, verificar que TODOS estes endpoints continuam funcionando:

```bash
# Health e status
curl -s http://localhost:9897/health | jq .status
curl -s http://localhost:9897/status | jq .
curl -s http://localhost:9897/metrics | jq .

# Dados
curl -s http://localhost:9897/providers | jq .
curl -s http://localhost:9897/projects | jq .
curl -s http://localhost:9897/squads | jq .
curl -s http://localhost:9897/profiles | jq .
curl -s http://localhost:9897/queue | jq .
curl -s http://localhost:9897/queue-jobs | jq .
curl -s http://localhost:9897/runs | jq .
curl -s http://localhost:9897/audit | jq .
curl -s http://localhost:9897/dispatches | jq .

# Trigger com validacao
curl -s -X POST http://localhost:9897/trigger -H "Content-Type: application/json" -d '{}' | jq .error
```

Se o PM Engine estiver parado, inicie-o antes de testar: `node src/index.js`

## O que NAO fazer

- NAO refatorar outros arquivos alem dos listados
- NAO adicionar novas funcionalidades
- NAO mudar a logica de nenhum modulo — apenas remover mortos e mover referencia
- NAO alterar o `process-prompt.md`

## Quality Gate

Este passo esta COMPLETO quando:
- [ ] `state.js` deletado, zero imports remanescentes
- [ ] `gemini.js`, `kimi.js`, `openclaw.js` deletados
- [ ] `providers/index.js` atualizado sem os providers mortos
- [ ] 4 arquivos de referencia movidos para `docs/reference/`
- [ ] `dispatch_log` deprecada (nao removida, deprecada)
- [ ] `src/errors.js` criado com taxonomia completa
- [ ] Todos os 14 smoke tests passam
- [ ] Nenhum `require` apontando para arquivo deletado
