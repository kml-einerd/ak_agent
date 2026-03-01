# Modelo de Desenvolvimento Multi-Dev Orquestrado — Processo Oficial

> **ESTE E O PROCESSO OFICIAL** para implementacao paralela de features, fixes e refactors
> usando multiplos terminais Claude Code.
>
> Framework validado em producao:
> - PM Engine v5.1: 10 features, 3 waves, 5 devs, ~4h, 0 conflitos
> - PM Engine v5.2: 9 features, 3 waves, 5 devs, ~6h, 0 conflitos
> - PM Engine v5.4: 41 fixes, 4 waves, 4 devs, 0 conflitos
>
> Autor: Operador KML + Akita Agent | v2.0 — 2026-03-01

---

## TL;DR — Como Funciona

```
1. SENIOR planeja tudo (prompts com codigo concreto, orquestracao, quality gates)
2. OPERADOR cola comandos nos terminais dos devs (copy-paste, sem improvisar)
3. DEVS implementam em paralelo (cada um so toca SEUS arquivos, zero conflito)
4. REVIEWER valida localmente (diff, smoke tests) — NAO implementa
5. SENIOR valida remotamente (quality gates especificos) — NAO implementa
6. REVIEWER commita e pusha — UNICO que faz git operations
7. Proxima wave — repete ate terminar
```

**Tres regras absolutas:**
1. **NUNCA dois devs editam o mesmo arquivo na mesma wave**
2. **APENAS o reviewer faz git operations** (add, commit, push)
3. **Prompts tem codigo concreto** — snippets prontos, nao descricoes vagas

---

## Arquitetura: Quem Faz o Que

```
AGENTE SENIOR (Claude Code — maquina do operador)
│  Planeja, cria prompts, roda quality gates remotos, diagnostica falhas
│  NAO implementa codigo. NAO esta nos terminais do servidor.
│
OPERADOR (humano)
│  Coordena, copia comandos, decide quando avancar wave
│  NAO implementa. NAO decide tecnicamente.
│
├── Dev 1 (Claude Code — terminal servidor) ── implementa
├── Dev 2 (Claude Code — terminal servidor) ── implementa
├── Dev 3 (Claude Code — terminal servidor) ── implementa
├── Dev N (Claude Code — terminal servidor) ── implementa
└── Dev R (Claude Code — terminal servidor) ── REVIEWER: valida, commita, pusha
```

**Importante:** Cada terminal de dev e uma instancia Claude Code completa que pode
usar sub-agentes, teams, e ferramentas internas. A capacidade de implementacao
e massiva porque cada dev opera como um agente autonomo com multiplos workers internos.

**Diferencial:** O agente senior NAO esta nos terminais do servidor. Ele acessa
remotamente (SSH/Tailscale) para verificar estado, rodar testes, e validar
resultados. Isso cria uma **DUPLA CHECAGEM**: reviewer local + senior remoto.

---

## Verificacao em Duas Camadas

```
Dev termina implementacao e avisa "pronto"
         │
         ▼
   [Camada 1: REVIEWER LOCAL — Dev R]
   - git diff visual (ve o que mudou)
   - confirma que SO arquivos permitidos foram tocados
   - roda smoke tests
   - Se OK: reporta ao operador
         │
         ▼
   [Camada 2: SENIOR REMOTO]
   - Acessa servidor via SSH/Tailscale
   - Roda quality gates especificos (node -e "...")
   - Verifica exports, funcoes, assinaturas, tipos
   - Valida integridade ENTRE modulos (cross-check)
   - Se OK: manda reviewer commitar
         │
         ▼
   [COMMIT + PUSH pelo Reviewer]
```

Por que duas camadas:
- **Reviewer** pega problemas obvios: arquivo errado, syntax error, test fail
- **Senior** pega problemas sutis: funcao exportada com assinatura errada,
  tabela criada sem indice, integracao quebrada entre modulos
- Nenhum dos dois implementa — apenas validam

---

## Pre-requisitos

### Infraestrutura
1. **Servidor** com N+1 terminais Claude Code (mesma maquina, mesmo repositorio)
2. **Repositorio git** com branch principal limpa (sem mudancas uncommitted)
3. **Acesso remoto** para o senior (SSH, Tailscale, ou similar)
4. **Sistema rodando** se quality gates testam codigo vivo (health check, API)

### Roles necessarios
| Role | Onde roda | Quantidade |
|------|-----------|-----------|
| Operador (humano) | Qualquer lugar | 1 |
| Agente Senior (Claude Code) | Maquina do operador | 1 |
| Devs (Claude Code) | Servidor | N (tipicamente 3-5) |
| Reviewer (Claude Code) | Servidor | 1 |

### Antes de comecar
1. **Tag de retorno seguro** criada: `git tag vX.Y-pre-fixes && git push origin --tags`
2. **Smoke tests funcionando** — se nao existirem, senior cria na Fase 0

---

## Smoke Tests

Smoke tests NAO sao nativos de nenhum framework. Sao testes basicos criados
para o projeto que verificam: "o sistema ainda funciona?"

### O que cobrir:
- Todos os modulos carregam sem erro (`require('./src/modulo')`)
- Funcoes principais existem e tem o tipo certo
- Banco de dados inicializa corretamente
- Servidor responde no health check
- Nenhuma dependencia faltando

### Template:

```javascript
// tests/smoke-test.js
'use strict';
let passed = 0, failed = 0;

function test(name, fn) {
  try { fn(); passed++; }
  catch (err) { console.error(`FAIL: ${name} — ${err.message}`); failed++; }
}

// Modulos carregam sem erro
test('config loads', () => { require('./src/config'); });
test('db loads', () => { require('./src/db'); });
test('router loads', () => { require('./src/router'); });

// Funcoes criticas existem
test('db.getUser is function', () => {
  if (typeof require('./src/db').getUser !== 'function') throw new Error('missing');
});

console.log(`SMOKE: ${passed}/${passed + failed} passed`);
if (failed > 0) process.exit(1);
```

O senior cria/atualiza smoke tests na Fase 0. A cada wave, adicionar entries
para novos modulos. Smoke tests sao um **contrato crescente**: cada wave so
pode ADD, nunca BREAK.

---

## Fase 0: Planejamento (Senior)

O senior faz TUDO antes de envolver os devs.
**Esta e a fase mais importante** — erros aqui causam retrabalho em cascata.

### 0.1 — Leitura do Codebase

1. Ler TODOS os arquivos fonte (ou os principais)
2. Mapear: arquivo → exports → dependencias → linhas
3. Entender arquitetura e convencoes (CommonJS vs ESM, tabs vs spaces, etc.)

### 0.2 — Inventario de Trabalho

Listar TUDO que precisa ser implementado:

```markdown
| # | Item | Descricao | Edita | Cria | Depende de | Complexidade |
|---|------|-----------|-------|------|-----------|-------------|
| 1 | Auth | JWT auth | routes.js, db.js | auth.js | — | Media |
| 2 | Cache | Redis layer | config.js | cache.js | — | Baixa |
```

### 0.3 — Matriz de Conflito

Para CADA par de items, verificar overlap de arquivos:

```
Item 1 edita: routes.js, db.js
Item 2 edita: config.js
Item 3 edita: routes.js
  → 1 e 2: ZERO conflito ✓ (mesma wave OK)
  → 1 e 3: CONFLITO em routes.js ✗ (waves diferentes)
  → 2 e 3: ZERO conflito ✓ (mesma wave OK)
```

**Regra absoluta: NUNCA dois devs editam o mesmo arquivo na mesma wave.**

### 0.4 — Design de Waves

Agrupar em waves respeitando:
1. Zero conflito de arquivo por wave
2. Dependencias entre items (X antes de Y)
3. Maximizar paralelismo (mais devs ativos = mais rapido)
4. Items que tocam MUITOS arquivos vao para wave solo (ultima)

```
Wave 1: Max paralelo (independentes, arquivos distintos)
Wave 2: Dependem da Wave 1 (core pipeline)
Wave 3: Features avancadas
Wave N: Item(s) complexo(s) que toca(m) muitos arquivos (solo)
```

### 0.5 — Identificar Bottlenecks

Arquivo editado por N items = bottleneck com N waves minimas:

```
db.js editado por items 1, 5, 9
  → Item 1: Wave 1 (dono de db.js)
  → Item 5: Wave 2 (dono de db.js)
  → Item 9: Wave 3 (dono de db.js)
```

**Strategies para bottlenecks:**
- **Combinar:** 2 items no mesmo arquivo + mesma tematica → prompt unico
- **Mover:** Item A e B precisam de routes.js → mova parte de routes.js do B pro dev de A
- **Adiar:** Item cria modulo sem schema. Na wave seguinte, quem owns db adiciona a tabela

### 0.6 — Criar Prompts Individuais

**Cada item vira um prompt .md.** Template:

```markdown
# Prompt XX — Nome do Item

> Wave N | Dev N | Paralelizavel: SIM/NAO
> Arquivos que VOCE edita: `src/x.js`, `src/y.js`
> Arquivos que VOCE cria: `src/z.js`
> Arquivos que VOCE NAO TOCA: a.js, b.js, c.js

---

## Contexto
[Estado atual do codigo. Quantas linhas o arquivo tem. O que existe. O que falta.]

## Task 1: [titulo]
[CODIGO CONCRETO: snippets prontos para o dev inserir/adaptar]

## Task 2: [titulo]
[Mais codigo concreto]

## Quality Gate
```bash
node -e "const m = require('./src/modulo'); console.log(typeof m.funcao)"
# Deve retornar 'function'
```

## O que NAO fazer
- NAO alterar [arquivo X]
- NAO adicionar dependencias npm
- NAO remover funcionalidade existente
```

**Principios dos prompts:**
- **Codigo concreto** — snippets prontos, NAO descricoes vagas
- **Restricoes explicitas** — lista de arquivos PROIBIDOS
- **Quality gates automatizaveis** — comandos que retornam pass/fail
- **Contexto completo** — NAO assumir que o dev conhece o projeto
- **Estado atual** — dizer quantas linhas o arquivo tem, que funcoes exporta

### 0.7 — Criar Documento de Orquestracao

Um unico .md com TUDO que o operador precisa:
- Mapa de waves (quem faz o que)
- Matriz de conflito (prova de zero conflito)
- Comandos EXATOS para enviar a cada dev em cada wave
- Quality gates por wave (comandos copy-paste)
- Comandos de commit/push para o reviewer
- Instrucoes de rollback

### 0.8 — Smoke Tests

Se nao existem: criar agora.
Se ja existem: adicionar entries para novos modulos.

---

## Fase 1: Entendimento (Opcional)

Cada dev le o prompt e escreve o que entendeu ANTES de implementar.

### Comando para cada Dev:
```
Faca git pull. Leia [path do prompt]
NAO implemente nada ainda. Escreva o que entendeu em
[path da resposta] e aguarde confirmacao.
```

### Senior valida cada entendimento:
1. Verifica que o dev compreendeu: quais arquivos, o que fazer, o que NAO fazer
2. Se OK: operador manda implementar
3. Se errado: senior escreve correcao, operador envia

### Quando pular:
- Mudancas simples (< 30 linhas)
- Waves 2+ quando devs ja demonstraram competencia
- Pressao de tempo (aceitar risco de retrabalho)

---

## Fase 2: Implementacao

### Contexto dos Terminais

Cada terminal Claude Code no servidor e uma instancia NOVA, sem contexto.
A **primeira mensagem** de cada wave precisa alinhar o terminal com:
1. **Quem ele e** — dev executor ou reviewer
2. **Qual projeto** — nome e diretorio
3. **Regras do role** — o que faz e o que NAO faz
4. **Sinal de conclusao** — "diga pronto quando terminar"

A partir da **segunda mensagem** (wave 2+), o terminal ja sabe quem e.
Basta mandar o comando direto (git pull + leia prompt + implemente).

### Primeira mensagem (Wave 1 — terminais novos):

**Template Dev:**
```
Voce e um dev executor no projeto [NOME] ([diretorio atual]).
Seu trabalho: implementar fixes conforme um prompt. Voce NAO faz git operations (add/commit/push).
Quando terminar, diga "pronto".

Faca git pull. Leia [path do prompt] e implemente TUDO que esta la.
Edite APENAS: [lista de arquivos]
NAO toque em nenhum outro arquivo. NAO faca git add/commit/push.
```

**Template Reviewer:**
```
Voce e o REVIEWER do projeto [NOME] ([diretorio atual]).
Voce NAO implementa codigo. Seu trabalho:
1. Verificar que os devs so tocaram nos arquivos permitidos (git diff)
2. Rodar quality gates (comandos especificos)
3. Fazer git add/commit/push quando tudo passar

Faca git pull. Leia [path da orquestracao] para entender o plano completo.
Aguarde ate que todos os devs reportem "pronto". Entao execute os quality gates
da Wave atual. Reporte o resultado.
```

### Waves seguintes (terminais ja alinhados — comando direto):
```
Faca git pull. Leia [path do prompt] e implemente.
Edite APENAS: [lista de arquivos]
NAO faca git add/commit/push.
```

### Regras dos Devs:
1. **NAO fazem git operations** (add, commit, push, pull, stash) — NUNCA
2. **NAO editam arquivos fora do escopo** do prompt
3. **NAO instalam dependencias** (npm install, pip install)
4. **Avisam "pronto" quando terminam**
5. Se travarem: operador pressiona Esc, mata o processo, reenvia

### Regras do Operador:
1. Enviar comandos para TODOS os devs da wave AO MESMO TEMPO
2. NAO interferir enquanto devs trabalham
3. Se um dev demorar muito (>20min alem dos outros): verificar se travou
4. Esperar TODOS terminarem antes de acionar review

### Paralelismo:
- Todos os devs iniciam simultaneamente
- Cada dev trabalha 100% independente (zero comunicacao entre devs)
- Cada dev pode usar sub-agentes e teams internamente
- Devs terminam em tempos diferentes — normal
- Operador espera TODOS antes de prosseguir

---

## Fase 3: Review e Quality Gate

### 3.1 — Reviewer Local (Dev R)

```
Verifique os arquivos modificados com git diff.
Confirme que apenas os arquivos permitidos foram tocados.
Rode: [comando smoke test]
Reporte o resultado.
```

### 3.2 — Senior Remoto

```bash
# Estado do repo
git status --short src/

# Smoke tests
node tests/smoke-test.js

# Quality gates especificos (do prompt de cada item)
node -e "const m = require('./src/novo-modulo'); console.log('export:', typeof m.funcao)"

# Cross-check (modulos se integram?)
node -e "const a = require('./src/a'); const b = require('./src/b'); console.log('OK')"
```

### 3.3 — Tabela de Decisao

| Reviewer | Senior | Acao |
|----------|--------|------|
| PASS | PASS | **Reviewer commita e pusha** |
| PASS | FAIL | Senior identifica qual dev falhou, manda correcao |
| FAIL | — | Reviewer identifica problema, dev corrige |
| — | FAIL (smoke) | Senior faz git diff por arquivo para achar culpado |

### 3.4 — Se um Gate Falha

1. Identificar QUAL dev causou (pelo arquivo modificado)
2. Ler o diff do arquivo com problema
3. Formular instrucao de correcao especifica
4. Operador envia correcao para o dev
5. Dev corrige, avisa "pronto"
6. Senior re-roda APENAS o gate que falhou

### 3.5 — Commit pelo Reviewer

```bash
git add [lista EXPLICITA de arquivos — NUNCA git add .]
git commit -m "feat(vX.Y): Wave N — descricao

- #XX Item A: descricao curta
- #XX Item B: descricao curta

Quality gate: [N/N] smoke tests + all specific gates PASS"
git push
```

**NUNCA `git add .` ou `git add -A`** — sempre listar arquivos para evitar
commitar lixo (.claude/, logs, db files).

---

## Fase 4: Proxima Wave

1. Operador anuncia: "Wave N completa"
2. Senior confirma push e verifica log
3. Operador manda devs da proxima wave fazerem `git pull`
4. Repete Fase 2 (ou Fase 1 se quiser entendimento)

**Ao terminar a ULTIMA wave:**
1. Senior roda ALL quality gates de TODAS as waves (regressao completa)
2. Se tudo passa: reviewer cria tag `vX.Y-consolidada`
3. Operador anuncia conclusao

---

## Patterns que Funcionam

### 1. Combinar items tematicamente
2 items no mesmo arquivo + tematica similar = prompt unico.
```
Exemplo: Degraded Mode + Sandbox Mode → prompt combinado
Ambos tocam dispatcher.js, ambos sao "resiliencia"
```

### 2. Dono de arquivo por wave
Cada arquivo tem no maximo 1 "dono" por wave. O dono e responsavel por
TODAS as mudancas naquele arquivo naquela wave.
```
Exemplo: Dev 2 e dono de routes.js na Wave 2
Qualquer mudanca de routes.js vai pro prompt do Dev 2
```

### 3. Mover responsabilidades
Se Item A e B precisam de routes.js, mova a parte de routes.js
do B para o dev de A.
```
Instrucao pro dev de B: "NAO toque em routes.js — outro dev ja fez."
```

### 4. Adiar schema changes
Feature precisa de tabela no banco MAS outro dev owns db:
- Wave N: cria modulos SEM a tabela
- Wave N+1: quem owns db adiciona tabela e conecta

### 5. Feature complexa sempre solo
Item que edita 4+ arquivos compartilhados: ultima wave, sozinho.

### 6. Smoke test como contrato crescente
Antes de cada wave: smoke cobre modulos existentes.
Depois de cada wave: adicionar novos modulos.
Contrato: cada wave so pode ADD, nunca BREAK.

---

## Anti-patterns — O que NAO Fazer

| Anti-pattern | Por que falha | Solucao |
|-------------|--------------|---------|
| Dois devs no mesmo arquivo | Ultimo save sobrescreve o primeiro | Matriz de conflito |
| Dev faz git push | Outros devs dessincronizam | Apenas reviewer faz git |
| Prompt vago sem codigo | Dev interpreta diferente | Snippets concretos |
| Gate manual/subjetivo | Inconsistente, falsos positivos | Comandos automatizaveis |
| Pular entendimento (wave 1) | Dev implementa errado | Pelo menos na 1a wave |
| Wave com >5 items | Dificil achar qual dev quebrou | Max 5 items/wave |
| Feature complexa em paralelo | Conflita com tudo | Solo na ultima wave |
| `git add .` no commit | Commita lixo | Listar arquivos |
| Sem tag de retorno | Sem rollback possivel | Tag ANTES de iniciar |
| Senior no terminal do dev | Conflito de papel | Senior em maquina separada |
| Senior implementa codigo | Perde neutralidade de validacao | Senior so planeja e valida |

---

## Comunicacao

### Operador → Devs
```
[Comando copy-paste EXATO do doc de orquestracao]
```
Sempre copiar do documento. NUNCA improvisar.

### Devs → Operador
```
"pronto" ou "travei em [descricao]"
```

### Operador → Senior
```
"todos terminaram" ou "dev X travou" ou "dev X reportou erro"
```

### Senior → Operador
```
"gates passaram, mande reviewer commitar" ou
"dev X precisa corrigir: [instrucao especifica]"
```

### Operador → Reviewer
```
[Comando de commit do doc de orquestracao]
```

---

## Template de Orquestracao

Copie e adapte para cada projeto:

```markdown
# Orquestracao [Projeto] — N Devs + 1 Reviewer

> Tag de retorno: `[tag]`
> Total: X items em Y waves

## Roles
| Terminal | Papel | Foco |
|----------|-------|------|
| Dev 1 | Executor | [area] |
| Dev R | Reviewer | git ops |

## Wave 1 (N devs paralelos — ZERO conflito)
| Dev | # | Item | Edita | Cria | Conflito |
|-----|---|------|-------|------|----------|
| Dev 1 | | | | | NINGUEM |
| Dev 2 | | | | | NINGUEM |

## Quality Gates
### Gate Wave 1:
```bash
node tests/smoke-test.js
node -e "const m = require('./src/modulo'); console.log(typeof m.funcao)"
```

## Comandos para Devs
### Wave 1 (primeira mensagem — terminais novos):
**Dev 1:**
```
Voce e um dev executor no projeto [NOME] ([diretorio]).
Seu trabalho: implementar fixes conforme um prompt. Voce NAO faz git operations (add/commit/push).
Quando terminar, diga "pronto".

Faca git pull. Leia [path] e implemente TUDO que esta la.
Edite APENAS: [arquivos]
NAO toque em nenhum outro arquivo. NAO faca git add/commit/push.
```

**Dev R:**
```
Voce e o REVIEWER do projeto [NOME] ([diretorio]).
Voce NAO implementa codigo. Seu trabalho:
1. Verificar que os devs so tocaram nos arquivos permitidos (git diff)
2. Rodar quality gates (comandos especificos)
3. Fazer git add/commit/push quando tudo passar

Faca git pull. Leia [path orquestracao] para entender o plano.
Aguarde todos os devs reportarem "pronto". Execute quality gates. Reporte resultado.
```

### Wave 2+ (terminais ja alinhados):
**Dev N:**
```
Faca git pull. Leia [path] e implemente.
Edite APENAS: [arquivos]
NAO faca git add/commit/push.
```

## Commits (Reviewer)
### Wave 1:
```bash
git add [arquivos explicitos]
git commit -m "[mensagem]"
git push
```
```

---

## Metricas de Referencia

| Metrica | v5.1 (Grupo A) | v5.2 (Grupo B) | v5.4 (41 Fixes) |
|---------|---------------|---------------|----------------|
| Items implementados | 10 | 9 | 41 |
| Waves | 3 | 3 | 4 |
| Devs paralelos | 5 + 1 reviewer | 5 + 1 reviewer | 4 + 1 reviewer |
| Prompts criados | 10 + orquestracao | 9 + orquestracao | 16 + orquestracao |
| Conflitos de arquivo | 0 | 0 | 0 |
| Smoke tests quebrados | 0 | 0 | — |
| Re-trabalho | 1 caso | 0 | — |
| Taxa sucesso gates | 95% | 100% | — |

---

## Checklist para Iniciar

### Senior preparou:
- [ ] Leitura completa do codebase
- [ ] Inventario de items (tabela com arquivos e dependencias)
- [ ] Matriz de conflito (zero conflito por wave PROVADO)
- [ ] Waves desenhadas e justificadas
- [ ] Prompts individuais (codigo concreto + restricoes + gates)
- [ ] Documento de orquestracao completo
- [ ] Smoke tests existem e passam
- [ ] Acesso remoto ao servidor funcionando

### Operador preparou:
- [ ] Repositorio limpo (sem mudancas uncommitted)
- [ ] Tag de retorno criada e pushada
- [ ] Sistema rodando (se necessario para gates)
- [ ] N+1 terminais Claude Code abertos no servidor
- [ ] Prompts disponiveis no servidor (git push ou copia manual)

### Pronto:
- [ ] Senior confirma: "planejamento completo, pode iniciar Wave 1"
- [ ] Operador envia comandos para todos os devs simultaneamente
