# PM-OS Data Visualization System — Implementation Plan

**Goal:** Sistema completo de visualização, analytics e monitoramento para orquestração de agentes IA. Dados de GitHub, Google Cloud, PM-OS, Supabase, Android Fleet e Bodycam unificados num dashboard ao vivo.

---

## SUB-SISTEMA 1: Data Layer (Supabase)

### Task 1.1: Views materializadas + RPC functions

Criar no Supabase via SQL:
- pipeline_status: aggregated run view com sub-waves
- fleet_summary: device count by status
- bodycam_by_layer: events agrupados por layer/hora
- cost_daily: custo por dia/modelo/agente
- agent_metrics: tasks/success_rate/avg_duration por agente
- commit_activity: commits por dia/autor (sync do GitHub)

Run: `Execute SQL via Supabase Management API`

### Task 1.2: Tabelas de sync GitHub

Criar tabelas:
- github_commits (sha, message, author, date, additions, deletions)
- github_builds (id, status, duration, created_at, source)
- github_languages (language, bytes, percentage)
- cloud_run_services (name, url, revision, status, last_deployed)
- cloud_run_revisions (service, revision, created, traffic_pct)

Run: `Execute SQL via Management API`

### Task 1.3: Tabelas de analytics

Criar tabelas:
- cost_events (timestamp, model, agent, tokens_in, tokens_out, cost_usd, task_id, run_id)
- agent_performance (agent, task_type, total, success, failed, avg_duration, avg_cost)
- failure_log (task_id, error_message, error_category, model, agent, created_at)
- capacity_snapshots (timestamp, workers_total, workers_active, queue_depth, tasks_running)

Run: `Execute SQL via Management API`

### Task 1.4: Edge Function — GitHub Sync

Criar Supabase Edge Function que:
- Chama GitHub API (commits, languages, builds)
- Insere/atualiza nas tabelas github_*
- Roda via cron a cada 5 min

Run: `Deploy via Supabase CLI ou Management API`

### Task 1.5: Edge Function — GCP Sync

Criar Edge Function que:
- Chama PM-OS API (/api/tasks, /api/workers, /api/analytics/cost)
- Transforma e insere em cost_events, agent_performance, capacity_snapshots
- Chama gcloud API pra Cloud Run services status
- Roda via cron a cada 1 min

Run: `Deploy via Management API`

### Task 1.6: Edge Function — Log Parser

Criar Edge Function que:
- Recebe raw log line (POST)
- Parseia: tool_use, file_write, test_run, error, decision
- Insere em bodycam_events com layer=server, type=parsed_action
- Detecta patterns: "FORGE_COMPLETE", "TASK_NOTES", errors

Run: `Deploy via Management API`

## SUB-SISTEMA 2: Sync Pipeline (Python na agdis)

### Task 2.1: GitHub sync script

Criar scripts/sync/github_sync.py:
- gh api calls pra commits, languages, builds, branches
- Upsert no Supabase via REST API
- Roda a cada 5 min via systemd timer

Run: `python3 scripts/sync/github_sync.py --test`

### Task 2.2: GCP sync script

Criar scripts/sync/gcp_sync.py:
- gcloud calls pra Cloud Run services, revisions, builds
- gcloud billing pra custo
- Upsert no Supabase
- Roda a cada 2 min via systemd timer

Run: `python3 scripts/sync/gcp_sync.py --test`

### Task 2.3: PM-OS sync script

Criar scripts/sync/pmos_sync.py:
- Chama PM-OS API: tasks, runs, workers, analytics
- Transforma em cost_events, agent_performance
- Calcula failure patterns (clustering de error messages)
- Upsert no Supabase
- Roda a cada 30s via systemd timer

Run: `python3 scripts/sync/pmos_sync.py --test`

### Task 2.4: Systemd timers pra todos os syncs

Criar scripts/sync/install-timers.sh:
- pm-sync-github.timer (5 min)
- pm-sync-gcp.timer (2 min)
- pm-sync-pmos.timer (30s)
- Instala e ativa todos

Run: `bash scripts/sync/install-timers.sh`

## SUB-SISTEMA 3: Dashboard Views (d-ui/)

### Task 3.1: Pipeline Flow — DAG visual

Criar d-ui/views/pipeline.html:
- Visualiza run como fluxograma: Morgan → Raven → Waves → Tasks → Gates → Done
- Cada nó: círculo colorido por status (verde/amarelo/vermelho/cinza)
- Arrows de dependência entre tasks
- Nós pulsam quando running
- CSS animations, sem lib externa
- Dados via Supabase Realtime (pipeline_status view)

Run: `Open in browser`

### Task 3.2: Forge Waterfall — Gantt chart

Criar d-ui/views/forge.html:
- Timeline horizontal: cada sub-wave como barra
- Eixo X = tempo, Eixo Y = sub-waves
- Cores: azul=running, verde=done, vermelho=failed, cinza=pending
- Markers 🔀 quando push detectado
- Barras overlapping mostram paralelismo real
- Auto-update via Supabase Realtime forge_events
- Click na barra mostra detalhes (output, branch, cost)

Run: `Open in browser`

### Task 3.3: Agent Timeline

Criar d-ui/views/timeline.html:
- Timeline vertical por task: cada ação do agente como card
- Cards: "Leu arquivo X", "Escreveu Y", "Rodou test", "Commit"
- Icons por tipo de ação
- Duração de cada ação
- Expandir card mostra output completo
- Dados via bodycam_events + task events

Run: `Open in browser`

### Task 3.4: Cost Analytics

Criar d-ui/views/cost.html:
- Números grandes: custo hoje, semana, mês, projeção
- Heatmap: grid dias×horas, cor=custo (CSS grid + gradients)
- Breakdown por modelo (pie chart CSS)
- Breakdown por agente (bar chart CSS)
- Top 10 runs mais caros
- Cost per task trend line
- Dados via cost_daily view + cost_events

Run: `Open in browser`

### Task 3.5: Device Cockpit

Criar d-ui/views/devices.html:
- Grid de cards, 1 por device
- Cada card: nome, IP, status dot (🟢/🔴), última ação, capabilities
- Click abre: últimas 10 ações, screenshot (se disponível)
- Botão "Send Command" com dropdown de ações
- Supabase Realtime device_fleet
- Auto-update status a cada 30s

Run: `Open in browser`

### Task 3.6: System Health Matrix

Criar d-ui/views/health.html:
- Grid: componentes como tiles
- Cada tile: nome, status bar (uptime %), último check, latência
- Componentes: pm-api, pm-worker, android-agent, supabase, forge, github, cloud-run, pub/sub
- Histórico de saúde (timeline das últimas 24h por componente)
- Alertas: se componente fica offline >1min, destaque vermelho
- Supabase Realtime system_health

Run: `Open in browser`

### Task 3.7: GitHub + Deploy View

Criar d-ui/views/repo.html:
- Commit feed: últimos 20 commits com message, author, date, +/-
- Language breakdown (bar chart horizontal, cores por linguagem)
- Build history: últimos 10 builds com status, duration
- Deploy timeline: revisions do Cloud Run com traffic split
- Branch list com last commit
- Dados via github_commits, github_builds, cloud_run_revisions

Run: `Open in browser`

### Task 3.8: Knowledge Brain Explorer

Criar d-ui/views/brains.html:
- 19 brains como cards em grid
- Cada card: nome, synapses count, vetos count, episodes count
- Click abre: lista de synapses, vetos, top episodes
- Search/filter por keyword
- Dados via /api/knowledge/brains + /api/knowledge/synapses

Run: `Open in browser`

### Task 3.9: Bodycam Live Stream

Criar d-ui/views/bodycam.html:
- Stream vertical de eventos em tempo real
- 5 colunas filtráveis: Visual, Network, Server, Browser, Audio
- Cada evento: timestamp, icon por layer, type, preview dos dados
- Click expande: JSON completo
- Auto-scroll com botão pause/resume
- Volume indicator (events/sec)
- Supabase Realtime bodycam_events

Run: `Open in browser`

### Task 3.10: Failure Analytics

Criar d-ui/views/failures.html:
- Top 10 erros mais comuns (agrupados por mensagem similar)
- Failure rate por modelo (haiku vs sonnet vs opus)
- Failure rate por agente
- Timeline de falhas (quando ocorrem mais)
- Pattern: "OAuth expira a cada X horas" detectado automaticamente
- Dados via failure_log

Run: `Open in browser`

## SUB-SISTEMA 4: Navigation + Design System

### Task 4.1: Main navigation

Criar d-ui/layout.html (shell que carrega views):
- Sidebar com icons: Overview, Pipeline, Forge, Timeline, Cost, Devices, Health, Repo, Brains, Bodycam, Failures
- Dark theme consistente
- Active state highlight
- Mobile responsive (sidebar collapsa)
- View loading via fetch + DOM inject

Run: `Open in browser`

### Task 4.2: Design tokens + components

Criar d-ui/design.css:
- CSS variables: colors, spacing, fonts, radius, shadows
- Components: card, badge, progress-bar, stat-number, timeline-item, table, chart-bar, heatmap-cell
- Animations: pulse (running), fade-in (new data), slide (transitions)
- Responsive breakpoints

Run: `Validate CSS`

### Task 4.3: Landing page redesign

Atualizar a landing page (GET /) com:
- Cards de summary usando design system
- Quick links pra cada view do /d/
- Números em tempo real via Supabase Realtime
- Status geral do sistema num glance

Run: `curl localhost:8080`
