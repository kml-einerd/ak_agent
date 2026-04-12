# Forge — Fork Notes

Este diretório é um **fork intencional** do `pm-os/tools/forge/`, clonado em
2026-04-11 e adaptado pra falar com o pm-api local em `cmd/pm-api/` deste repo.

## Divergências em relação ao upstream

- `akita-agent.xml` e `base/` são symlinks pros equivalentes do ak_agent,
  não cópias físicas
- `forge.py` configurado por default pro endpoint `http://localhost:8080/api/v2/run`
  (vs Cloud Run no upstream)
- `config.json` usa `pmos_test_key_2024` como default (fallback local)

## Sincronização

Manual. Se o upstream (`pm-os/tools/forge/`) receber fixes relevantes, mergir
manualmente. Este fork NÃO é atualizado automaticamente — por design.

## Quando usar qual

- **Este fork** (ak_agent/forge/): desenvolvimento local, testes contra pm-api local
- **Upstream** (pm-os/tools/forge/): produção, Cloud Run

Ver `CLAUDE.md:143` (Modo 3) pro fluxo operacional completo.
