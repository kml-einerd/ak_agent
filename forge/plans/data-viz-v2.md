# PM-OS Data Visualization System v2 — Forge Plan

**Goal:** Dashboard completo + sync pipeline para PM-OS. Tabelas Supabase já existem.

**Supabase URL:** https://yppmptpcpffuubvpiveu.supabase.co
**Supabase Anon Key:** `${SUPABASE_ANON_KEY}` <!-- redacted - see reference_credentials memory -->

**Tabelas existentes:** forge_runs, forge_events, device_fleet, bodycam_events, system_health, github_commits, github_builds, github_languages, cloud_run_services, cloud_run_revisions, cost_events, agent_performance, failure_log, capacity_snapshots

**Views existentes:** pipeline_status, fleet_summary, cost_daily, agent_metrics

**PM-OS API:** https://pm-api-852176378633.us-central1.run.app

**Repo:** github.com/kml-einerd/pm-os-gcp

**Stack frontend:** HTML puro + CSS variables + vanilla JS + Supabase JS client (CDN). Sem frameworks. Dark theme (#0d1117 bg, #c9d1d9 text, #238636 green, #da3633 red, #1f6feb blue, #e3b341 yellow).

---

### Task 4.2: Design tokens + components CSS

Criar `d-ui/design.css` com design system completo:

CSS variables:
- --bg-primary: #0d1117, --bg-secondary: #161b22, --bg-tertiary: #21262d
- --text-primary: #c9d1d9, --text-secondary: #8b949e, --text-accent: #58a6ff
- --green: #238636, --red: #da3633, --blue: #1f6feb, --yellow: #e3b341, --purple: #8957e5
- --radius: 6px, --shadow: 0 1px 3px rgba(0,0,0,.3)
- --font: -apple-system, BlinkMacSystemFont, 'Segoe UI', sans-serif
- --font-mono: 'SF Mono', 'Fira Code', monospace

Components (classes CSS reutilizáveis):
- `.card` — bg-secondary, radius, padding 16px, shadow
- `.badge` — inline pill com cor de status (green/red/yellow/blue)
- `.stat-number` — font-size 2.5rem, font-weight 700, monospace
- `.stat-label` — text-secondary, font-size 0.85rem, uppercase
- `.progress-bar` — height 8px, rounded, animated fill
- `.timeline-item` — left border + dot + content
- `.table` — striped rows, hover highlight
- `.chart-bar` — flexbox horizontal bars com width via CSS var
- `.heatmap-cell` — grid cell com opacity baseado no valor
- `.pill-group` — row de filter pills clicáveis
- `.pulse` — @keyframes pulse animation (para status "running")
- `.fade-in` — @keyframes fadeIn animation (para novos dados)
- `.slide-in` — @keyframes slideIn (para transições de view)

Responsivo: breakpoints em 768px e 1200px.

Run: `echo "CSS design system created"`

### Task 2.1: GitHub sync script

Criar `scripts/sync/github_sync.py`:

```python
#!/usr/bin/env python3
"""Sync GitHub data → Supabase."""
```

Funcionalidade:
- Usa subprocess para chamar `gh api` (GitHub CLI já instalado)
- Busca últimos 50 commits de kml-einerd/pm-os-gcp
- Busca linguagens do repo
- Busca últimos 20 Cloud Build runs (via `gcloud builds list --format=json`)
- Upsert em github_commits, github_languages, github_builds via Supabase REST API
- Supabase URL e key lidos de env vars (SUPABASE_URL, SUPABASE_KEY) ou hardcoded com os valores acima
- `--test` flag faz dry run mostrando o que insertaria
- Usa `requests` ou `urllib` pra REST calls

Run: `python3 scripts/sync/github_sync.py --test`

### Task 2.2: GCP sync script

Criar `scripts/sync/gcp_sync.py`:

```python
#!/usr/bin/env python3
"""Sync GCP Cloud Run + PM-OS data → Supabase."""
```

Funcionalidade:
- `gcloud run services list --format=json` → cloud_run_services
- `gcloud run revisions list --format=json` → cloud_run_revisions
- Chama PM-OS API GET /api/workers → capacity_snapshots
- Chama PM-OS API GET /api/tasks?limit=100 → cost_events + agent_performance
- Calcula failure patterns (agrupa error messages similares)
- Upsert tudo no Supabase via REST API
- PM-OS API URL hardcoded: https://pm-api-852176378633.us-central1.run.app
- `--test` flag pra dry run

Run: `python3 scripts/sync/gcp_sync.py --test`

### Task 2.3: PM-OS sync script

Criar `scripts/sync/pmos_sync.py`:

```python
#!/usr/bin/env python3
"""Sync PM-OS task/run data → Supabase analytics tables."""
```

Funcionalidade:
- GET /api/tasks → itera tasks, extrai cost, duration, status
- Agrupa por agent → agent_performance (upsert)
- Tasks com status "failed" → failure_log
- GET /api/system/status → system_health (upsert por componente)
- Snapshot atual → capacity_snapshots (insert)
- `--test` flag
- Usa urllib (sem deps externas)

Run: `python3 scripts/sync/pmos_sync.py --test`

### Task 2.4: Systemd timers

Criar `scripts/sync/install-timers.sh`:

- Cria 3 systemd timer units:
  - pm-sync-github.timer (5 min) → pm-sync-github.service (python3 github_sync.py)
  - pm-sync-gcp.timer (2 min) → pm-sync-gcp.service (python3 gcp_sync.py)
  - pm-sync-pmos.timer (30s) → pm-sync-pmos.service (python3 pmos_sync.py)
- Cada service: WorkingDirectory=/home/agdis/pm-os-gcp, User=agdis
- Environment com SUPABASE_URL e SUPABASE_KEY
- Script instala, enable e start todos

Run: `bash scripts/sync/install-timers.sh`

### Task 3.1: Pipeline Flow — DAG visual

Criar `d-ui/views/pipeline.html`:

HTML standalone que:
- Inclui design.css via `<link rel="stylesheet" href="../design.css">`
- Inclui supabase-js via CDN: `<script src="https://cdn.jsdelivr.net/npm/@supabase/supabase-js@2/dist/umd/supabase.min.js"></script>`
- Conecta ao Supabase Realtime (URL e key inline)
- Visualiza forge runs como fluxograma vertical:
  - Cada run como card com: ID, status badge, progresso bar (completed/total), custo, duração
  - Dentro do run: sub-waves como nós de um DAG
  - Nós coloridos por status: verde=done, amarelo=running (com pulse), vermelho=failed, cinza=pending
  - Setas SVG de dependência entre nós
- Subscription no Supabase Realtime para forge_events → atualiza nós em tempo real
- Query inicial: SELECT * FROM pipeline_status ORDER BY created_at DESC LIMIT 10

Run: `echo "Pipeline view created"`

### Task 3.2: Forge Waterfall — Gantt chart

Criar `d-ui/views/forge.html`:

HTML standalone com design.css e supabase-js CDN.
- Gantt chart horizontal puro CSS/JS:
  - Eixo X = tempo (minutos desde início do run)
  - Eixo Y = sub-waves (cada uma é uma barra)
  - Barra colorida: azul=running, verde=done, vermelho=failed, cinza=pending
  - Barras posicionadas por start_time e width por duração
  - Marcadores 🔀 quando push_event detectado (branch pushed)
  - Overlapping mostra paralelismo real
- Click na barra: modal com detalhes (output, branch, cost, duration)
- Supabase Realtime subscription em forge_events
- Dropdown pra selecionar run_id

Run: `echo "Forge waterfall created"`

### Task 3.3: Agent Timeline

Criar `d-ui/views/timeline.html`:

HTML standalone com design.css e supabase-js CDN.
- Timeline vertical de eventos:
  - Cada evento como `.timeline-item` com: timestamp, icon, tipo, preview
  - Icons por tipo: 📁 file_read, ✏️ file_write, 🧪 test_run, 💻 command, 🤖 llm_call, ❌ error
  - Click expande: JSON completo do evento
  - Auto-scroll com botão pause/resume
- Filtros: por task_id, por tipo de evento, por agent
- Fonte de dados: bodycam_events + forge_events
- Supabase Realtime subscription em bodycam_events

Run: `echo "Timeline view created"`

### Task 3.4: Cost Analytics

Criar `d-ui/views/cost.html`:

HTML standalone com design.css e supabase-js CDN.
- Números grandes no topo:
  - Custo hoje, custo semana, custo mês, projeção mensal (extrapolada)
  - Usando `.stat-number` e `.stat-label`
- Heatmap de custo: grid 7×24 (dias da semana × horas), cor = custo via opacity
  - Usa `.heatmap-cell` com --value CSS var controlando opacity
- Breakdown por modelo: barras horizontais (haiku, sonnet, opus) com % e valor
- Breakdown por agente: barras horizontais com % e valor
- Top 10 runs mais caros: tabela com run_id, custo, sub-waves, duração
- Dados via cost_daily view + cost_events table

Run: `echo "Cost analytics created"`

### Task 3.5: Device Cockpit

Criar `d-ui/views/devices.html`:

HTML standalone com design.css e supabase-js CDN.
- Grid de cards (CSS grid, auto-fill, minmax 280px):
  - Cada device: nome, IP, status dot (🟢 online / 🔴 offline), última ação, capabilities list
  - Badge com tipo: "android", "server", etc
  - Última ação com timestamp relativo (2min ago, etc)
- Click no card expande: últimas 10 ações do device (via bodycam_events WHERE device_id=X)
- Botão "Ping" que faz GET /health no device
- Supabase Realtime em device_fleet

Run: `echo "Device cockpit created"`

### Task 3.6: System Health Matrix

Criar `d-ui/views/health.html`:

HTML standalone com design.css e supabase-js CDN.
- Grid de tiles (componentes do sistema):
  - pm-api, pm-worker, android-agent, supabase, forge, github, cloud-run, pub-sub
  - Cada tile: nome, status dot, uptime % (últimas 24h), último check, latência ms
  - Cores: verde >99%, amarelo >95%, vermelho <95%
- Mini timeline em cada tile: 24 barrinhas (1 por hora) mostrando status naquela hora
- Alertas: se status="error" por >1min, borda vermelha pulsante
- Supabase Realtime em system_health
- Query: SELECT * FROM system_health ORDER BY timestamp DESC

Run: `echo "Health matrix created"`

### Task 3.7: GitHub + Deploy View

Criar `d-ui/views/repo.html`:

HTML standalone com design.css e supabase-js CDN.
- Commit feed: últimos 20 commits em lista vertical
  - Cada commit: SHA (link), message, author, date relativa, badge +N/-N
- Language breakdown: barras horizontais coloridas por linguagem
  - Cores padrão GitHub: Go=#00ADD8, Python=#3572A5, JS=#f1e05a, HTML=#e34c26, CSS=#563d7c
- Build history: últimos 10 builds em timeline horizontal
  - Cada build: status badge (success/failure/running), duração, trigger
- Deploy timeline: Cloud Run revisions com traffic split
  - Cada revision: nome, created_at, traffic_pct como barra
- Dados via github_commits, github_builds, github_languages, cloud_run_services, cloud_run_revisions

Run: `echo "Repo view created"`

### Task 3.8: Knowledge Brain Explorer

Criar `d-ui/views/brains.html`:

HTML standalone com design.css.
- Grid de cards (brains):
  - Usa fetch para GET https://pm-api-852176378633.us-central1.run.app/api/knowledge/brains
  - Cada brain como card: nome, synapses count, vetos count, episodes count
  - Click expande: lista de synapses (text items), vetos, top 5 episodes
- Search input no topo: filtra brains por nome em tempo real (client-side)
- Empty state quando API retorna erro ou sem dados

Run: `echo "Brains explorer created"`

### Task 3.9: Bodycam Live Stream

Criar `d-ui/views/bodycam.html`:

HTML standalone com design.css e supabase-js CDN.
- Stream vertical de eventos em tempo real:
  - 5 toggle filters no topo: Visual, Network, Server, Browser, Audio
  - Cada evento: timestamp, icon por layer, type badge, preview dos dados
  - Dados vindo de Supabase Realtime (bodycam_events)
  - Click expande: JSON completo formatado
- Auto-scroll com botão 📌 pin/unpin no canto
- Volume indicator: events/sec no header
- Cores por layer: visual=#8957e5, network=#1f6feb, server=#238636, browser=#e3b341, audio=#da3633

Run: `echo "Bodycam stream created"`

### Task 3.10: Failure Analytics

Criar `d-ui/views/failures.html`:

HTML standalone com design.css e supabase-js CDN.
- Top 10 erros mais comuns: tabela com error_category, count, último occurrence
  - Agrupados por error_category
- Failure rate por modelo: barras comparativas haiku vs sonnet vs opus
- Failure rate por agente: barras comparativas
- Timeline de falhas: últimas 24h, cada falha como dot no eixo temporal
  - Permite identificar padrões ("falhas sempre às 3am" = OAuth token expirando)
- Dados via failure_log table
- Supabase Realtime em failure_log para novos erros

Run: `echo "Failure analytics created"`

### Task 4.1: Main navigation shell

Criar `d-ui/layout.html` — shell que carrega views:

- Sidebar esquerda fixa (width 220px, collapsible em mobile):
  - Logo "PM-OS" no topo
  - Nav items com icons (emoji): 📊 Overview, 🔄 Pipeline, ⚒️ Forge, ⏱️ Timeline, 💰 Cost, 📱 Devices, 🏥 Health, 🗃️ Repo, 🧠 Brains, 📹 Bodycam, ❌ Failures
  - Active state: bg-tertiary + left border accent
  - Collapse button (☰) que esconde labels mantendo icons
- Main content area: div#view-container
- View loading: click no nav → fetch(`views/${name}.html`) → inject no container
- Hash routing: `#pipeline`, `#forge`, etc → carrega view correspondente
- Default view: pipeline
- Footer: "PM-OS Dashboard v2 — Powered by Code Forge"
- Inclui design.css

Run: `echo "Navigation shell created"`

### Task 4.3: Landing page overview

Criar `d-ui/views/overview.html`:

HTML standalone com design.css e supabase-js CDN.
- 4 stat cards no topo:
  - Total Tasks (via count de forge_events), Active Workers (via capacity_snapshots), Devices Online (via device_fleet), Cost Today (via cost_daily)
- System health ribbon: 8 dots inline (um por componente), cor por status
- Recent forge runs: últimos 5 runs como mini cards com progresso
- Recent commits: últimos 5 commits em lista compacta
- Quick links: grid de botões pra cada view
- Tudo via Supabase queries + Realtime subscriptions

Run: `echo "Overview page created"`
