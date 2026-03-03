# Wave Orchestrator v3 — Plano de Rearquitetura

## Problemas Criticos no v2

### 1. Launch SEQUENCIAL (mata o proposito)
`wave-server.py` usa `subprocess.run()` — bloqueante. 8 devs a 2h cada = 16h serial.
O sistema inteiro foi construido para paralelismo mas executa em serie.

### 2. Zero monitoramento em tempo real
Depois que um dev lanca, ninguem sabe se terminou, se travou, se falhou.
Sem polling, sem watcher, sem callback.

### 3. Review manual
Usuario precisa ir no terminal do Reviewer e falar "pode revisar".
Nao tem gatilho automatico.

### 4. Sem checagem do Senior pos-review
O fluxo para no Reviewer. Senior nunca valida o resultado final.

### 5. Arquivos mortos
3 pares de duplicatas (hifen vs underscore). Os com hifen sao inuteis.

### 6. Max 7 devs (config), usuario quer 8

---

## Solucao v3

### Arquitetura de execucao

```
Senior (CLAUDE.md)
  |
  | escreve inventory.json
  | roda: py wave-cli.py go PROJECT
  |
  v
wave-cli.py go (comando unico)
  |
  |-- 1. plan (gera prompts)
  |-- 2. launch (paralelo via Popen)
  |-- 3. watch (polling loop)
  |       |-- dev terminou? -> auto-gate
  |       |-- todos passaram? -> auto-review
  |       |-- review passou? -> auto-senior-check
  |-- 4. report (resultado final)
  |
  v
Senior recebe report e apresenta ao usuario
```

### O que cada papel faz

| Papel | Quem | O que faz |
|-------|------|-----------|
| Senior | Claude Code no terminal | Conversa, levanta, escreve inventory, roda `go`, apresenta resultado |
| Dev 1-8 | `claude -p` headless | Recebe prompt, implementa, reporta PRONTO |
| Reviewer | `claude -p` headless | Valida escopo, sintaxe, imports — dispara automatico |
| Senior Check | Script Python | Valida report do reviewer + gates — nao precisa de LLM |

---

## Mudancas por arquivo

### 1. wave-server.py — Reescrever launch para paralelo

**O que muda:**
- `run_claude_headless()` → `launch_claude_async()` usando `subprocess.Popen`
- Novo: `_dev_procs = {}` — dict de dev_id → {proc, start_time, output_file, status}
- Novo: `watcher_thread()` — thread daemon que polls `proc.poll()` a cada 5s
- Quando dev termina: captura output, roda gates automatico, salva em report.json
- Quando todos passam: lanca reviewer automatico em headless
- Novo endpoint: `GET /wave/watch` — retorna status em tempo real de cada dev
- Novo endpoint: `POST /wave/go` — faz tudo (plan + launch + watch em background)

**Funcao chave — launch paralelo:**
```python
def launch_devs_parallel(wave_dir, project, active_devs):
    for dev_num in active_devs:
        prompt = read dev-{dev_num}.md
        output_file = wave_dir / f"dev-{dev_num}-output.txt"
        proc = subprocess.Popen(
            [CLAUDE_BIN, "--dangerously-skip-permissions", "-p", prompt,
             "--output-format", "json", "--max-turns", "50"],
            cwd=project, stdout=open(output_file, "w"), stderr=subprocess.STDOUT,
            env=clean_env
        )
        _dev_procs[f"dev-{dev_num}"] = {
            "proc": proc, "status": "running",
            "start": time.time(), "output_file": output_file
        }
    # Inicia watcher em background
    threading.Thread(target=watcher_loop, args=(wave_dir, project), daemon=True).start()
```

**Funcao chave — watcher:**
```python
def watcher_loop(wave_dir, project):
    while any(d["status"] == "running" for d in _dev_procs.values()):
        for dev_id, info in _dev_procs.items():
            if info["status"] != "running":
                continue
            if info["proc"].poll() is not None:
                # Dev terminou
                info["status"] = "finished"
                # Auto-gate
                result = gate_enforcer.run(str(wave_dir / f"{dev_id}.md"), project)
                info["gates"] = result
                info["status"] = "pass" if result["all_pass"] else "fail"
                save_report(wave_dir, dev_id, info)
        # Checa se todos terminaram e passaram
        if all(d["status"] == "pass" for d in _dev_procs.values()):
            launch_reviewer_auto(wave_dir, project)
            break
        time.sleep(5)
```

### 2. wave-cli.py — Novo comando `go`

**O que muda:**
- Novo comando `go` que faz tudo:
  1. Roda `plan` diretamente
  2. Inicia servidor se nao estiver rodando (em background thread)
  3. Roda `launch` via API
  4. Entra em loop de `watch` mostrando status no terminal
  5. Quando termina, mostra report

```
py wave-cli.py go PROJECT_PATH [--session SLUG]
```

O Senior roda esse unico comando. Tudo acontece sozinho.

**Watch display (atualiza a cada 5s):**
```
Wave 1 — 3/3 devs rodando
  Dev 1: [RODANDO]  42min  context-engine.js
  Dev 2: [PASS]     18min  logger.js — gates 3/3
  Dev 3: [RODANDO]  42min  dispatcher.js
```

### 3. config.json — Atualizar devs para 8

```json
"grade": {
    "devs": 8,
    "terminal_names": ["Dev 1","Dev 2","Dev 3","Dev 4","Dev 5","Dev 6","Dev 7","Dev 8","Reviewer","Senior"]
}
```

### 4. CLAUDE.md — Simplificar Senior

O Senior nao precisa mais saber de todos os comandos intermediarios.
Fluxo:
1. Modo Levantamento: conversa, identifica problemas, reformula
2. Modo Execucao: escreve inventory.json, roda `py wave-cli.py go PROJECT`
3. Recebe report automatico no stdout
4. Apresenta resultado ao usuario

### 5. Limpeza

- Deletar: `codebase-scanner.py` (hifen — dead code)
- Deletar: `gate-enforcer.py` (hifen — dead code)
- Deletar: `senior-prompter.py` (hifen — dead code)
- Deletar: `templates/` (vazio)
- Deletar: `tests/` (vazio)

### 6. senior_prompter.py — Gates por linguagem

Detectar linguagem do projeto via conventions e gerar gates adequados:
- JS/TS: `node -c`, `node -e "require(...)"`
- Python: `python -c "import ..."`, `python -m py_compile`
- Generico: sintaxe do arquivo + smoke test

---

## Ordem de implementacao

1. Limpeza (deletar duplicatas e pastas vazias)
2. config.json (8 devs)
3. wave-server.py (launch paralelo + watcher + auto-gate + auto-review)
4. wave-cli.py (comando `go` + watch display)
5. CLAUDE.md (simplificar para Senior)
6. senior_prompter.py (gates por linguagem)
7. Testar fluxo completo: init → inventario → go → report

---

## O que NAO muda

- codebase_scanner.py — funciona bem
- gate_enforcer.py — funciona bem
- senior_prompter.py — apenas ajuste nos gates (item 6)
- Estrutura de .wave/ — mantida
- Formato do inventory.json — mantido
- Formato dos prompts gerados — mantido
