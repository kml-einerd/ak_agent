# Prompts v5 — Guia de Uso

## Protocolo de Execucao

Cada prompt segue este fluxo:

```
1. Voce envia o prompt para a IA dev
2. A IA dev responde com: O QUE ENTENDEU + O QUE VAI FAZER (sem implementar)
3. Voce envia essa resposta para o Akita Agent
4. Akita Agent confirma OU gera prompt de ajuste
5. Somente apos confirmacao, a IA dev implementa
```

**A IA dev NUNCA implementa no primeiro envio.** Sempre explica primeiro.

## Sequencia

1. Coloque o `CLAUDE-MD-v5.md` no projeto (substitui o CLAUDE.md atual)
2. Envie `00-diagnostico.md` e me mande a resposta
3. Siga os prompts de `v5.0/` na ordem numerica (01, 02, 03...)
4. Cada prompt tem um QUALITY GATE — so avance quando o gate passar
5. Apos `09-validacao-final.md`, o v5.0 esta completo
6. Prompts de v5.1+ serao criados apos v5.0 estabilizar

## Decisoes Tecnicas Tomadas

| Decisao | Escolha | Justificativa |
|---------|---------|---------------|
| Banco de dados | SQLite (mantido) | Volume atual (5-15/semana) nao justifica PostgreSQL |
| Event bus | BullMQ (ja no stack) | Persistencia, DLQ, retry nativos — sem nova dependencia |
| Vault | credentials.yaml simples | Single-user, sem necessidade de ACLs complexos |
| AUX no v5.0 | Deterministico apenas | Controle de custo, 80% dos checks sao objetivos |
| Modelos AUX | haiku (det.) / sonnet (conceitual futuro) | Custo minimo para verificacao |
| Conselho de Agentes | Nao no v5.0 | Custo alto, volume baixo — escalacao para humano |
| Auto-evolucao v5.0 | Apenas coleta de sinal | Volume insuficiente para loop completo |
| Paralelismo | Dentro de planos (multi-agent steps) | Tasks sequenciais, steps paralelos |
