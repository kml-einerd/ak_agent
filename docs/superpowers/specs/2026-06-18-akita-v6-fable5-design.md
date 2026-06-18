# Akita Agent v6 — Assistente Geral com Núcleo Akita

> Design validado · 2026-06-18 · branch `feat/akita-v6-fable5`

## Contexto e motivação

O `ak_agent` (Akita Agent) é hoje um **motor de raciocínio read-only travado**: anti-assistente,
sem persona, sem opinião, recusa qualquer pergunta fora da knowledge base local (96 elements
extraídos de artigos do Fabio Akita / akitaonrails.com). O `CLAUDE.md` atual (25 linhas) só aponta
para `akita-agent.xml`, que carrega identidade, routing por domínio e constraints rastreadas aos elements.

O usuário quer evoluir esse agente trazendo a "programação de comportamento" do system prompt do
**Claude Fable 5** (`CLAUDE-FABLE-5.md`) — tom, epistemologia, segurança, formatação, honestidade.

**Decisões do usuário (travadas via AskUserQuestion):**

- **Escopo:** transformação completa — Akita vira assistente geral estilo Fable-5, **mantendo a
  knowledge base Akita como uma das fontes** (não a única). Objetivo declarado: *"manter a base e
  capacidade de lógica, arquitetura, padrões e código do Akita e evoluir o processo"*.
- **Destino:** "o mais adequado" — decisão de arquitetura delegada ao implementador.
- **Prioridade de fonte:** Akita primeiro, geral complementa. Quando a KB cobre o tema, ela é a
  fonte de verdade prioritária e os elements são citados; conhecimento geral preenche lacunas e
  adiciona contexto moderno.
- **Citação da KB:** só quando a KB é de fato usada. Conversa geral / código fora do escopo Akita
  não carrega o ritual de "declarei tais arquivos".

## Identidade nova (o pivô)

| | Antes (v5) | Depois (v6) |
|---|---|---|
| Natureza | Motor read-only, anti-assistente | Assistente de engenharia geral |
| Persona | Nenhuma | Warm, prose, honesto, epistemicamente humilde (estilo Fable-5) |
| Conhecimento geral | Proibido | Permitido, complementa a KB |
| Knowledge base | Única fonte (cárcere) | Núcleo de excelência priorizado (biblioteca) |
| Fora do escopo KB | Recusa + 1 pergunta | Responde como assistente normal |
| Declaração de carregamento | Sempre, ou resposta inválida | Só quando a KB é usada |

O **diferencial Akita sobrevive como qualidade**: os 96 elements, o routing por domínio, os formatos
PROCEDURE/PROTOCOL/ANTI-PATTERN/HEURISTIC/CONCEPT/REFERENCE, as never-rules/always-rules/escalation-rules.
Tudo isso permanece. O que muda é a **moldura**: deixa de ser prisão, vira biblioteca de referência
priorizada quando o tema bate com um domínio coberto.

## Arquitetura de arquivos (3 camadas)

```
CLAUDE.md          → ponto de entrada. Comportamento Fable-5 + nova identidade + inicialização condicional
akita-agent.xml    → routing/never-rules/always-rules/escalation/response-format MANTIDOS;
                     identity/setup/hard-rules/default-rule RE-SEMANTIZADOS pro novo modelo
base/INDEX.md      → corrigir vault-root (path Windows obsoleto → path Linux real)
base/*             → 96 elements INTOCADOS
```

Separação de concerns: **CLAUDE.md = como se comporta** (tom, segurança, epistemologia, formatação).
**XML = o que sabe e como roteia** (lógica Akita preservada). **base/ = o conhecimento em si**.

## Restrição crítica: a suite de testes codifica a identidade antiga

`tests/` (8 suites, ~1400 assertions) valida a **estrutura** do XML antigo. Quebrar essas estruturas
quebra a suite E perde a rastreabilidade que o usuário quer manter. Estratégia: **preservação
estrutural + re-semantização** — manter todas as tags e contadores que os tests verificam, mas
reescrever o conteúdo semântico delas.

Contrato que DEVE continuar válido (senão a suite falha):

- **Test 04/06/08 (routing):** todo `<route>` tem `<if>`/`<load>`/`<then>`; arquivos em `<load>`
  existem em disco e estão no INDEX; ≥10 rotas; cada rota 1–8 arquivos; `<then>` menciona o tipo
  primário; `<cross-domain-rule>` menciona 8 + "PROTOCOL > PROCEDURE"; `<default-rule>` carrega
  `INDEX.md` e faz "clarifying question"; domínios ai-/security-/frontend-/backend-/architecture-/
  database-|deployment-/testing- têm ≥1 rota cada.
- **Test 07 (constraints):** `<hard-rules>` contém as strings `INDEX.md`, `element files were loaded`,
  `general LLM knowledge`, `element type`; `<mandatory-read>` tem exatamente 5 `<step>`; `<load-scope>`
  menciona `8` e `PROTOCOL`; `<identity>` tem `<what-it-is>`/`<what-it-is-not>`/`<operational-objective>`/
  `<quality-standard>`; never≥10, always≥8, escal≥5; response-format dos 6 tipos; coverage-gaps≥4 com
  `CI/CD` e `authentication`.
- **Test 03 (index):** paths do INDEX existem no fs e usam forward-slash; sem duplicatas; todo arquivo
  do fs está no INDEX.

**Como a re-semantização satisfaz isso:** as strings exigidas continuam presentes, mas como cláusulas
**condicionais** ("Quando a resposta usa a knowledge base, é inválida se não declarar quais element
files were loaded…") em vez de absolutas. A semântica muda; o token que o teste procura permanece.

## CLAUDE.md — camadas portadas do Fable-5 (adaptadas, não copiadas)

1. **Identidade & inicialização condicional** — quem é o agente; quando carregar a KB vs responder
   como assistente geral; ambíguo → pergunta no fluxo (não trava).
2. **Tom e formatação** — warm; prose sobre bullets; formatação mínima necessária; nunca bullets ao
   recusar; máx 1 pergunta por resposta; não psicanalisar; assume adulto capaz.
3. **Epistemologia & busca** — humildade calibrada; nunca inventar atribuição; declarar incerteza em
   vez de confabular; buscar quando o tema muda rápido / pode ter mudado pós-cutoff; não buscar fato
   estável; crer em resultados com ceticismo apropriado.
4. **Segurança** — child-safety; user-wellbeing (sem diagnóstico, sem reforçar self-talk negativo,
   sem métodos de self-harm); harmful content (sem malware/armas/synthesis); refusal gracioso.
5. **Honestidade sobre erros** — owns mistakes sem auto-flagelo; mantém self-respect.
6. **Evenhandedness** — apresentar o melhor caso de posições contestadas como "o caso que outros
   fariam", não como opinião própria; cauteloso com política partidária.
7. **Legal/financeiro** — informação factual pra decisão informada, não recomendação confiante;
   "não sou advogado/consultor".
8. **Copyright** — quotes sob ~15 palavras, 1 por fonte; nunca regurgitar; nunca letras/poemas.
9. **Núcleo Akita (prioridade de fonte)** — quando a pergunta bate um domínio coberto, a KB é fonte
   prioritária; aplicar o formato do element type; citar os elements; conhecimento geral complementa
   lacunas e é sinalizado quando a KB é rasa (coverage-gaps).

**Explicitamente NÃO portado** (infra do harness consumer da Anthropic, irrelevante pro CLI):
artifacts storage API, MCP app suggestions, places/recipe/weather/sports tools, Claudeception,
computer_use `/mnt` paths, citation tags `{cite}`, network/filesystem config, image_search.

## Inicialização condicional (substitui a trava absoluta)

- Pergunta toca domínio Akita (detectável pelo routing do XML)? → carrega INDEX + elements relevantes,
  responde aplicando o formato do element type, **cita os elements**.
- Pergunta geral / código fora do escopo? → responde como assistente, **sem** ritual de carregamento.
- Ambíguo? → faz uma pergunta de clarificação no fluxo (estilo Fable-5), não trava.

`<load-scope>` (máx 8 elements, prioridade PROTOCOL>PROCEDURE>...) e os response-formats por tipo
permanecem para o caminho KB.

## O que sobrevive intacto do Akita

Routing completo · never-rules/always-rules (viram "princípios de engenharia" do agente) ·
escalation-rules · response-format por element type · coverage-gaps (vira "onde a KB é rasa,
complemento com geral e sinalizo") · os 96 elements e o INDEX.

## Plano de implementação (ordem)

1. **CLAUDE.md** — reescrita completa com as 9 camadas acima.
2. **akita-agent.xml** — re-semantizar `<identity>`, `<setup>`/`<hard-rules>`/`<mandatory-read>`,
   `<default-rule>`, `<coverage-gaps>`; preservar routing/constraints/response-format e as strings
   que os tests exigem.
3. **base/INDEX.md** — corrigir vault-root para `/home/agdev/ak_agent/`.
4. **Validação** — `node tests/run-all.js` deve passar verde (8 suites). Reconciliar discrepância
   pré-existente 94 vs 96 elements (test 03 exige fs ⊆ INDEX) se aparecer.
5. **Commit** na branch `feat/akita-v6-fable5`.

## Critérios de sucesso

- `node tests/run-all.js` → todas as 8 suites passam.
- CLAUDE.md carrega as 9 camadas de comportamento; identidade nova clara.
- XML re-semantizado: trava absoluta → rigor condicional; routing/constraints preservados.
- Knowledge base e os 96 elements intocados; INDEX com path correto.
- Agente responde perguntas gerais sem recusar; aplica e cita a KB quando o tema bate um domínio.
