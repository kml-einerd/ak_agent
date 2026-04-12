# Code Forge

Motor de geração massiva de código. Distribui trabalho para dezenas de workers paralelos via PM-OS.

## Como usar

```bash
cd /home/agdis/pm-os-gcp/code-forge
claude
```

Pronto. O Claude Code carrega o CLAUDE.md desta pasta e vira o operador do forge.

Dentro do Claude Code:

```
Você: "forja o plano do bodycam"
Akita: mostra preview (sub-waves, custo, tempo) e pede confirmação
Você: "vai"
Akita: executa, gera link do monitor
Você: abre outro terminal e roda o monitor pra acompanhar
```

## Fluxo completo

```
1. Abra o Claude Code nesta pasta
2. Diga o que quer construir (ou passe um plano pronto)
3. Diga "forja"
4. O Akita mostra o preview:
   - Quantas sub-waves
   - Quantas máquinas
   - Custo estimado
   - Tempo estimado
5. Confirme
6. O Akita executa e entrega um link de monitor:
   python3 /tmp/forge-monitor-<run_id>.py
7. Abra outro terminal e rode o monitor pra ver o dashboard:

   ╔══════════════════════════════════════════════════════════╗
   ║  CODE FORGE — forge-20260324-053417                     ║
   ║  ████████████░░░░ 72.2%                                 ║
   ║  Done: 13  Running: 4  Failed: 0  Total: 18            ║
   ║  Cost: $8.40                               14:32:15     ║
   ╠══════════════════════════════════════════════════════════╣
   ║  ✅ sw-01    Portal Client types       haiku   2s $0.30 ║
   ║  ✅ sw-02    Portal Client methods     haiku   3s $0.35 ║
   ║  ⏳ sw-06    OTel setup                sonnet       ... ║
   ║  ⬚  sw-15    Agent service             [blocked]        ║
   ╚══════════════════════════════════════════════════════════╝

8. Quando terminar, o Akita apresenta o resultado
9. Revise o código gerado e integre
```

## Comandos diretos (sem Claude Code)

```bash
# Preview sem executar
python3 forge.py run <plano.md> --dry

# Executar
python3 forge.py run <plano.md>

# Com opções
python3 forge.py run <plano.md> --machines 30 --model sonnet

# Ver status de um run
python3 forge.py status <run_id>

# Coletar resultados manualmente
python3 forge.py collect <run_id>
```

## O que acontece por baixo

```
Seu plano
    │
    ▼
Opus decompõe em sub-waves independentes
    │
    ▼
Opus gera macro tests (contratos entre subsistemas)
    │
    ▼
Sonnet gera unit tests por sub-wave
    │
    ├──► Worker 1 (Haiku) → faz testes passarem → resultado
    ├──► Worker 2 (Haiku) → faz testes passarem → resultado
    ├──► Worker 3 (Haiku) → faz testes passarem → resultado
    ├──► ...
    └──► Worker N (Haiku) → faz testes passarem → resultado
              │
              ▼
         Sonnet adequadores conectam os pedaços
              │
              ▼
         Opus reviewer valida tudo
              │
              ▼
         Código pronto na sua máquina
```

## Custo

| Escala | Sub-waves | Tempo | Custo |
|--------|-----------|-------|-------|
| Pequeno (5 componentes) | ~8 | ~10 min | ~$5 |
| Médio (20 componentes) | ~25 | ~15 min | ~$15 |
| Grande (80 componentes) | ~80 | ~30 min | ~$50 |
