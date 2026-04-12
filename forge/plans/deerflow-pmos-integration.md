# DeerFlow + PM-OS Integration — Full Implementation

**Goal:** Integrar o PM-OS como motor de execução dentro do DeerFlow 2.0. O DeerFlow vira a interface (chat, memória, channels) e o PM-OS vira o backend de execução (workers, forge, TDD, monitoring).

**Working dir:** /home/agdis/pm-os-gcp/deer-flow/

**API Keys disponíveis em /home/agdis/pm-os-gcp/config/.env.providers:**
- ANTHROPIC_API_KEY
- OPENAI_API_KEY
- GEMINI_API_KEY

**PM-OS API:** https://pm-api-852176378633.us-central1.run.app
**Supabase:** https://yppmptpcpffuubvpiveu.supabase.co (anon key: `${SUPABASE_ANON_KEY}` — redacted, see reference_credentials memory)

---

### Task 1: DeerFlow config.yaml com Claude + Gemini + PM-OS

Criar `deer-flow/config.yaml` a partir do `config.example.yaml`:
- Configurar modelo Claude (claude-sonnet-4-6) como default usando ANTHROPIC_API_KEY
- Configurar Gemini (gemini-2.5-flash) como alternativa
- Habilitar memory, sandbox local, skills
- Configurar subagents com timeout 900s
- Tool groups: web, file:read, file:write, bash
- Carregar API keys de /home/agdis/pm-os-gcp/config/.env.providers via $ENV_VAR syntax
- Habilitar token_usage tracking

Ler `config.example.yaml` inteiro primeiro pra entender o schema.

Run: `cd deer-flow && python3 -c "import yaml; yaml.safe_load(open('config.yaml'))" && echo "Config valid"`

### Task 2: extensions_config.json com PM-OS MCP Server

Criar `deer-flow/extensions_config.json` a partir do `extensions_config.example.json`:
- Habilitar PM-OS MCP server:
  ```json
  "pm-os": {
    "enabled": true,
    "type": "stdio",
    "command": "python3",
    "args": ["/home/agdis/pm-os-gcp/tools/pmos-mcp/server.py"],
    "env": { "PM_API_URL": "https://pm-api-852176378633.us-central1.run.app" },
    "description": "PM-OS orchestration — submit tasks, monitor workers, forge execution"
  }
  ```
- Habilitar Supabase MCP server:
  ```json
  "supabase": {
    "enabled": true,
    "type": "stdio",
    "command": "python3",
    "args": ["/home/agdis/pm-os-gcp/tools/supabase-mcp/server.py"],
    "env": {
      "SUPABASE_URL": "https://yppmptpcpffuubvpiveu.supabase.co",
      "SUPABASE_SERVICE_ROLE": "${SUPABASE_SERVICE_ROLE}"
    },
    "description": "Supabase direct SQL — monitoring, analytics, data"
  }
  ```
- Habilitar todas as skills públicas (bootstrap, deep-research, image-generation, etc)

Run: `cd deer-flow && python3 -c "import json; json.load(open('extensions_config.json'))" && echo "Extensions valid"`

### Task 3: Skill PM-OS Integration

Criar `deer-flow/skills/public/pm-os-integration/SKILL.md`:

```markdown
---
name: pm-os-integration
description: "Orchestrate parallel development tasks via PM-OS workers. Use when the user wants to build apps, generate code, run parallel tasks, or deploy. Also triggers for: forge, build, create app, implement, develop, scale."
license: MIT
author: PM-OS
version: 1.0
---

# PM-OS Integration

## When to Use
- User wants to BUILD something (app, API, tool, page)
- User wants PARALLEL execution (multiple tasks at once)
- User wants to DEPLOY (Cloud Run, Cloudflare)
- User mentions "forge", "workers", "parallel"

## How It Works
PM-OS has 80 Cloud Run workers that execute code in parallel with TDD quality gates.

## Available Tools (via MCP)
- `pm_submit_task` — Submit a task for parallel execution
- `pm_list_tasks` — Check status of running tasks
- `pm_get_task` — Get detailed result of a task
- `pm_health` — Check system health
- `pm_list_workers` — See active workers

## Workflow
1. Plan the work (decompose into independent tasks)
2. Submit each task via `pm_submit_task` with:
   - title: what to build
   - type: "code" (for code gen) or "content" (for text/creative)
   - instructions: detailed step-by-step
   - acceptance: test command to validate
   - agent: "dex" (dev) or "sage" (content)
3. Monitor via `pm_list_tasks`
4. Collect results via `pm_get_task`

## Example: Build 3 APIs in Parallel
```python
# Task 1
pm_submit_task(title="Users API", type="code",
  instructions=["Create REST API for users CRUD with Go..."],
  acceptance="go test -v")

# Task 2 (runs in parallel!)
pm_submit_task(title="Products API", type="code",
  instructions=["Create REST API for products..."],
  acceptance="go test -v")

# Task 3 (parallel!)
pm_submit_task(title="Orders API", type="code",
  instructions=["Create REST API for orders..."],
  acceptance="go test -v")
```

## Dashboard
Monitor everything at: https://pm-os-dashboard.pages.dev
```

Run: `test -f deer-flow/skills/public/pm-os-integration/SKILL.md && echo "Skill created"`

### Task 4: Skill Forge Execution

Criar `deer-flow/skills/public/forge-execution/SKILL.md`:

```markdown
---
name: forge-execution
description: "Run Code Forge for massive parallel code generation. Use when user says 'forge', 'forja', or wants to generate many files/projects at once. Triggers for: mass generation, parallel build, stress test, bulk create."
license: MIT
author: PM-OS
version: 1.0
---

# Code Forge

Mass-parallel code generation with TDD quality gates.

## When to Use
- Generating 3+ files/projects simultaneously
- Building a full application from scratch
- Running stress tests
- Any "forja" or "forge" command

## How to Run
```bash
python3 /home/agdis/pm-os-gcp/code-forge/forge.py run <plan.md> --model sonnet --machines N
```

## Plan Format (.md file)
Each `### Task N:` becomes a parallel worker:
```markdown
### Task 1: Feature Name (Complexity)
Create `path/to/file`:
- Description of what to implement
- Specific requirements

Run: `test command here`
```

## Workers
- Each task runs in an isolated Cloud Run container
- Ralph TDD loop: implement → test → fix → commit
- Git push per branch on success
- Max 80 workers parallel

## Monitor
Dashboard: https://pm-os-dashboard.pages.dev/#forge
```

Run: `test -f deer-flow/skills/public/forge-execution/SKILL.md && echo "Skill created"`

### Task 5: Install Dependencies + Setup

Criar `deer-flow/setup-pmos.sh`:
```bash
#!/bin/bash
# Setup DeerFlow + PM-OS Integration
set -e

cd "$(dirname "$0")"

# Load PM-OS API keys
source /home/agdis/pm-os-gcp/config/.env.providers 2>/dev/null || true

# Export for DeerFlow
export ANTHROPIC_API_KEY
export OPENAI_API_KEY
export GEMINI_API_KEY

# Install Python deps
cd backend
pip install uv 2>/dev/null || true
uv sync 2>/dev/null || pip install -e "packages/harness[all]" -e "app[all]" 2>/dev/null

# Install frontend deps
cd ../frontend
npm install --legacy-peer-deps 2>/dev/null || pnpm install 2>/dev/null

echo "Setup complete. Run: cd deer-flow && make dev"
```

Run: `chmod +x deer-flow/setup-pmos.sh && echo "Setup script created"`

### Task 6: Nginx config for integrated access

Criar `deer-flow/docker/nginx.pmos.conf` that routes:
- `/` → DeerFlow frontend (3000)
- `/api/langgraph/*` → LangGraph (2024)
- `/api/*` → DeerFlow Gateway (8001)
- `/pmos/` → PM-OS Dashboard (proxy to pm-os-dashboard.pages.dev)
- `/pmos/api/*` → PM-OS API (proxy to pm-api-852176378633.us-central1.run.app)

Standard nginx reverse proxy config. Listen on port 2026.

Run: `nginx -t -c $(pwd)/deer-flow/docker/nginx.pmos.conf 2>/dev/null || echo "Nginx config created (validate after install)"`

### Task 7: Startup script

Criar `deer-flow/start-pmos.sh`:
```bash
#!/bin/bash
# Start DeerFlow + PM-OS integrated
set -e
cd "$(dirname "$0")"

# Load API keys
source /home/agdis/pm-os-gcp/config/.env.providers 2>/dev/null || true
export ANTHROPIC_API_KEY OPENAI_API_KEY GEMINI_API_KEY

echo "Starting DeerFlow + PM-OS..."
echo "Dashboard: http://localhost:2026"
echo "PM-OS Dashboard: https://pm-os-dashboard.pages.dev"
echo "PM-OS API: https://pm-api-852176378633.us-central1.run.app"

# Start backend (LangGraph + Gateway)
cd backend
nohup uv run langgraph dev --host 0.0.0.0 --port 2024 > /tmp/deerflow-langgraph.log 2>&1 &
nohup uv run uvicorn app.gateway.app:app --host 0.0.0.0 --port 8001 > /tmp/deerflow-gateway.log 2>&1 &

# Start frontend
cd ../frontend
nohup npx next dev -p 3000 > /tmp/deerflow-frontend.log 2>&1 &

echo "Services starting..."
echo "  LangGraph: http://localhost:2024 (log: /tmp/deerflow-langgraph.log)"
echo "  Gateway:   http://localhost:8001 (log: /tmp/deerflow-gateway.log)"
echo "  Frontend:  http://localhost:3000 (log: /tmp/deerflow-frontend.log)"
```

Run: `chmod +x deer-flow/start-pmos.sh && echo "Start script created"`

### Task 8: Systemd service for DeerFlow

Criar `deer-flow/deerflow-pmos.service` (template for systemd):
```ini
[Unit]
Description=DeerFlow + PM-OS Integration
After=network.target

[Service]
Type=forking
User=agdis
WorkingDirectory=/home/agdis/pm-os-gcp/deer-flow
EnvironmentFile=/home/agdis/pm-os-gcp/config/.env.providers
ExecStart=/home/agdis/pm-os-gcp/deer-flow/start-pmos.sh
Restart=on-failure
RestartSec=10

[Install]
WantedBy=multi-user.target
```

Run: `echo "Systemd template created"`
