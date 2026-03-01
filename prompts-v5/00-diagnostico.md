# PROMPT 00 — Diagnostico Pre-Refatoracao

> INSTRUCAO: NAO implemente nada. Apenas colete informacoes e retorne o relatorio estruturado abaixo.

## Contexto

Vamos iniciar a refatoracao do PM Engine para v5. Antes de qualquer codigo, preciso de um retrato preciso do estado atual do sistema.

## O que voce deve fazer

1. **Verificar ambiente de runtime:**
   - Versao do Node.js (`node --version`)
   - Versao do Redis (`redis-cli info server | grep redis_version`)
   - Versao do SQLite (`node -e "console.log(require('better-sqlite3')(':memory:').pragma('compile_options'))"`)
   - Status do PM Engine (esta rodando? PID? porta?)
   - Status do Trigger.dev (esta rodando? porta? Docker?)

2. **Mapear o projeto trigger-tasks:**
   - Onde esta o codigo do Trigger.dev worker (pm-agents.ts)?
   - Qual a estrutura de arquivos? Liste todos os arquivos com linhas
   - Qual o package.json do trigger-tasks?
   - Como o worker e iniciado? (Docker? npm start? trigger dev?)
   - Copie o projeto trigger-tasks completo para dentro do repo pm-engine na pasta `trigger-tasks/` para facilitar a refatoracao. Se ja estiver la, apenas confirme.

3. **Verificar estado atual do PM Engine:**
   - Houve alguma mudanca nos arquivos desde o SYSTEM-AUDIT.md de 2026-02-28?
   - Listar todos os arquivos em `src/` com contagem de linhas (`wc -l src/*.js src/providers/*.js`)
   - Ha algum processo rodando? (`ps aux | grep pm-engine`)
   - Estado do banco SQLite: quantos registros em cada tabela?
   - BullMQ: ha jobs pendentes/ativos/falhados?

4. **Verificar integracao ClickUp:**
   - Webhook esta ativo? (`curl` para verificar)
   - Token esta valido?

5. **Verificar dependencias:**
   - `cat package.json` (completo)
   - `node_modules` esta instalado e atualizado?

## Formato da resposta

Retorne EXATAMENTE neste formato:

```
## DIAGNOSTICO PM ENGINE — [DATA]

### Ambiente
- Node.js: [versao]
- Redis: [versao]
- SQLite: [versao]
- PM Engine: [rodando/parado] PID [X] porta [Y]
- Trigger.dev: [rodando/parado] porta [Y] tipo [Docker/local]

### Trigger-Tasks
- Path: [caminho completo]
- Arquivos: [lista com linhas]
- Copiado para pm-engine/trigger-tasks/: [sim/nao]
- Package.json: [conteudo]

### PM Engine — Arquivos Fonte
[lista de todos os arquivos src/ com linhas]

### PM Engine — Banco de Dados
[contagem de registros por tabela]

### PM Engine — BullMQ
[status das filas]

### ClickUp
- Webhook: [ativo/inativo]
- Token: [valido/invalido]

### Mudancas desde SYSTEM-AUDIT
[lista de mudancas ou "nenhuma"]

### Dependencias (package.json)
[conteudo completo]
```
