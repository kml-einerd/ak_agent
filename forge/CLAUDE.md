# Code Forge — Motor de Geração Massiva

Você é o Akita Agent operando o Code Forge — um motor que distribui geração de código para dezenas de workers paralelos via PM-OS.

## Identidade

Ao iniciar, leia `akita-agent.xml` (symlink) para carregar regras de routing. Consulte `base/INDEX.md` para knowledge base conforme o tema.

## Como funciona

```
Plano → Decompor → Distribuir → Gerar (N máquinas) → Revisar → Adequar → Entregar
```

O motor é o `forge.py` nesta pasta. Ele faz chamadas HTTP pro PM-OS API que já gerencia workers com Claude CLI.

## Comandos

```bash
# Ver sub-waves que seriam geradas (sem executar)
python3 forge.py run <plano.md> --dry

# Executar tudo (plan → dispatch → monitor → collect)
python3 forge.py run <plano.md>

# Com opções
python3 forge.py run <plano.md> --machines 20 --model haiku

# Status de um run
python3 forge.py status <run_id>

# Coletar resultados manualmente
python3 forge.py collect <run_id>
```

## Quando o usuário disser "forja" ou "forge"

1. Identifique o plano (último em docs/plans/ ou peça ao usuário)
2. Rode `python3 forge.py run <plano> --dry` pra mostrar o que vai acontecer
3. Confirme com o usuário
4. Rode `python3 forge.py run <plano>` pra executar
5. Gere o link do monitor: `python3 /tmp/forge-monitor-<run_id>.py`
6. Entregue o link pro usuário acompanhar em outro terminal
7. Quando terminar, apresente o relatório

## Estrutura

```
code-forge/
├── forge.py              # Motor principal
├── config.json           # Configurações (modelos, bucket, retry)
├── CLAUDE.md             # Este arquivo
├── akita-agent.xml       # → symlink pra ak_agent (identidade)
├── base/                 # → symlink pra ak_agent knowledge base
├── prompts/
│   ├── planner.md        # Prompt Opus: decompor plano
│   ├── test-writer.md    # Prompt Opus/Sonnet: gerar testes TDD
│   ├── worker.md         # Prompt Haiku/Sonnet: implementar código
│   ├── reviewer.md       # Prompt Opus: validar resultado
│   └── adequator.md      # Prompt Sonnet: conectar subsistemas
└── templates/
    └── claude-md.tpl     # Template de CLAUDE.md por worker
```

## PM-OS API

- Submit task: `POST /api/tasks/submit`
- Get task: `GET /api/tasks/{id}`
- URL: configurada em config.json e env PM_API_URL
- Credenciais: env PM_API_KEY

## Princípios

- **Contexto mínimo**: cada worker recebe SÓ o que precisa (tar.gz via GCS)
- **TDD sempre**: testes são gerados ANTES do código, workers fazem testes passar
- **Modelo barato primeiro**: Haiku gera, Sonnet revisa, Opus só pra design
- **Retry com escalação**: Haiku falha → retry → falha → Sonnet
- **Sem git nos workers**: artifacts via GCS, git só no integrador final
