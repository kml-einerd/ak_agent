# Wave Orchestration System — Design

**Date:** 2026-03-02
**Status:** Approved
**Approach:** B — wave-server.js (Node.js) + vscode-terminals

---

## Problema

O fluxo atual exige que o usuário abra 6 instâncias do Claude Code manualmente, copie prompts, e gerencie a progressão entre ondas de trabalho. O objetivo é automatizar o dispatch e a injeção de prompts entre ondas, mantendo o usuário no controle dos gatilhos de avanço.

---

## Fluxo Completo

```
Sênior gera wave-N (7 arquivos) → curl POST /wave/launch?wave=N
  → Devs ativos (1-5, variável): injeta e executa imediatamente
  → Reviewer: injeta reviewer.md no input, aguarda "pode revisar" manual
  → Sênior já começa a escrever wave-N+1 em paralelo

Usuário acompanha os terminais
Usuário diz ao Sênior "onda N concluída"
  → Sênior revisa outputs (acesso ao mesmo projeto local)
  → Sênior ajusta wave-N+1 se necessário
  → Sênior pede confirmação do usuário

Usuário confirma → Sênior chama curl POST /wave/inject?wave=N+1
  → Prompts injetados nos terminais ativos da nova onda
```

---

## Arquitetura

```
┌─────────────────────────────────────────────────────┐
│            SÊNIOR (terminal principal)              │
│  Claude Code com Bash tool                          │
│  Gera arquivos de onda, chama wave-server via curl  │
│  Pode lançar sub-agentes próprios antes de avançar  │
└──────────────────┬──────────────────────────────────┘
                   │ curl POST /wave/launch
                   │ curl POST /wave/inject
                   ▼
┌─────────────────────────────────────────────────────┐
│         wave-server.js (Node.js, porta 9898)        │
│  - Lê meta.json para saber devs ativos por onda     │
│  - Injeta prompts via vscode-terminals API          │
│  - Log de ondas em wave-state.json                  │
└──────┬──────┬──────┬──────┬──────┬─────────────────┘
       │      │      │      │      │
   ┌───▼──┐ ┌─▼───┐ ┌▼────┐ ┌▼───┐ ┌▼───┐ ┌─▼──────┐
   │ Dev 1│ │Dev 2│ │Dev 3│ │Dev4│ │Dev5│ │Reviewer│
   │  🔵  │ │  🟢 │ │  🟡 │ │ 🟠 │ │ 🔴 │ │   🟣   │
   └──────┘ └─────┘ └─────┘ └────┘ └────┘ └────────┘
     Terminais fixos no Antgravity (vscode-terminals)
```

---

## Estrutura de Arquivos por Onda

```
wave-orchestrator/
  waves/
    wave-1/
      dev-1.md          # prompt de implementação (Dev 1)
      dev-2.md          # prompt de implementação (Dev 2)
      dev-3.md          # prompt de implementação (Dev 3)
      reviewer.md       # identidade + contexto + critérios desta onda
      meta.json         # { "wave": 1, "active_devs": [1, 2, 3] }
    wave-2/
      dev-1.md
      ...
      meta.json         # { "wave": 2, "active_devs": [1, 2, 3, 4, 5] }
  wave-server.js
  wave-state.json       # log append-only de todas as ondas
  .vscode/
    terminals.json      # configuração fixa dos 6 terminais
```

**Regras:**
- Número de devs ativos por onda é variável (1-5), definido pelo Sênior
- `meta.json` diz ao wave-server quais terminais recebem trabalho
- Devs inativos ficam abertos e ociosos — não recebem nada
- `reviewer.md` sempre existe — gerado pelo Sênior com contexto específico da onda

---

## Terminais — Configuração Fixa

| Terminal | Cor | Papel |
|----------|-----|-------|
| Dev 1 | 🔵 azul | Implementação |
| Dev 2 | 🟢 verde | Implementação |
| Dev 3 | 🟡 amarelo | Implementação |
| Dev 4 | 🟠 laranja | Implementação |
| Dev 5 | 🔴 vermelho | Implementação |
| Reviewer | 🟣 roxo | Revisão (disparo manual) |

---

## wave-server.js — Endpoints

| Endpoint | Ação |
|----------|------|
| `POST /wave/init` | Abre os 6 terminais via vscode-terminals (uma vez por sessão) |
| `POST /wave/launch?wave=N` | Lança onda N: devs ativos executam, reviewer aguarda input |
| `POST /wave/inject?wave=N` | Injeta onda N nos terminais já abertos (ondas 2+) |
| `GET /wave/status` | Onda atual, devs ativos, histórico |

---

## Como o Sênior Dispara (via Bash tool)

```bash
# Inicializar os 6 terminais (uma vez por sessão)
curl -X POST localhost:9898/wave/init

# Lançar onda 1
curl -X POST localhost:9898/wave/launch?wave=1

# Injetar onda 2 (após confirmação do usuário)
curl -X POST localhost:9898/wave/inject?wave=2
```

---

## Comportamento do Reviewer

1. No `/wave/launch`: recebe `reviewer.md` injetado no input — **não é enviado automaticamente**
2. Texto fica visível no campo de input aguardando
3. Usuário decide quando enviar manualmente
4. Reviewer tem acesso ao mesmo projeto local que os Devs

---

## Comportamento do Sênior entre Ondas

1. Dispara `/wave/launch` para onda N
2. Imediatamente começa a escrever `wave-(N+1)/` em paralelo
3. Pode lançar sub-agentes próprios via `claude` CLI para resolver bloqueios
4. Quando usuário confirma "onda N concluída": revisa outputs (arquivos locais)
5. Ajusta `wave-(N+1)/` se necessário
6. Pede confirmação do usuário → dispara `/wave/inject?wave=N+1`

---

## Stack

- **wave-server.js**: Node.js, CommonJS, sem novas dependências
- **Injeção de terminal**: vscode-terminals extension (`terminals.runTerminalByName`)
- **Estado**: `wave-state.json` (append-only)
- **Editor**: Antgravity (fork VSCode) — compatível com extensões VSCode

---

## O que Este Sistema NÃO faz

- Não monitora se os Devs terminaram — responsabilidade do usuário
- Não envia automaticamente para o Reviewer — sempre manual
- Não tem UI web — tudo via curl + terminais do editor
- Não requer Redis ou banco externo

---

## Próximos Passos

1. Instalar extensão vscode-terminals no Antgravity
2. Criar `.vscode/terminals.json` com os 6 terminais configurados
3. Criar `wave-server.js`
4. Testar init + launch com onda de exemplo
5. Adicionar instrução ao `akita-agent.xml` para o Sênior saber usar o wave-server
