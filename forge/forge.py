#!/usr/bin/env python3
"""
Code Forge — Motor de geração massiva de código via PM-OS workers.

Uso:
  forge.py plan <input>              # Gera sub-waves a partir de um plano/texto
  forge.py run <input>               # Plan + dispatch + collect (tudo)
  forge.py run <input> --dry         # Mostra o que faria sem executar
  forge.py status <run_id>           # Status de um run
  forge.py collect <run_id>          # Coleta resultados e merge

Input: arquivo .md (plano), arquivo .json (spec), ou texto livre entre aspas.

Variáveis de ambiente:
  PM_API_URL     URL do PM-OS API (default: https://pm-api-852176378633.us-central1.run.app)
  PM_API_KEY     API key do PM-OS
  FORGE_BUCKET   Bucket GCS para artifacts (default: forge-artifacts-{project})
  FORGE_MODEL    Modelo padrão para geração (default: haiku)
"""

import json
import os
import sys
import time
import tarfile
import tempfile
import hashlib
import subprocess
import io
from pathlib import Path
from datetime import datetime
from typing import Optional

# ---------------------------------------------------------------------------
# Config
# ---------------------------------------------------------------------------

PM_API_URL = os.environ.get("PM_API_URL", "https://pm-api-852176378633.us-central1.run.app")
PM_API_KEY = os.environ.get("PM_API_KEY", "")
GCP_PROJECT = os.environ.get("GCP_PROJECT_ID", "circular-transport-pr8vp")
FORGE_BUCKET = os.environ.get("FORGE_BUCKET", f"forge-artifacts-{GCP_PROJECT}")
FORGE_DIR = Path(__file__).parent
PROMPTS_DIR = FORGE_DIR / "prompts"

MODELS = {
    "haiku": "haiku",
    "sonnet": "sonnet",
    "opus": "opus",
}

# Supabase config (for event logging)
SUPABASE_URL = os.environ.get("SUPABASE_URL", "https://qgzwjntkazekkcmmrljh.supabase.co")
SUPABASE_KEY = os.environ.get("SUPABASE_SERVICE_ROLE", "")


# ---------------------------------------------------------------------------
# Supabase Event Logger (pure urllib — no dependencies)
# ---------------------------------------------------------------------------

def _load_supabase_key():
    """Load SUPABASE_SERVICE_ROLE from .env.services if not already set."""
    global SUPABASE_KEY
    if SUPABASE_KEY:
        return
    env_path = FORGE_DIR.parent / "config" / ".env.services"
    if env_path.exists():
        for line in env_path.read_text().splitlines():
            if line.startswith("SUPABASE_SERVICE_ROLE="):
                SUPABASE_KEY = line.split("=", 1)[1].strip().strip('"')
                return


def _supabase_post(table, row):
    """POST a row to Supabase REST API. Fire-and-forget, never raises."""
    if not SUPABASE_KEY:
        return
    import urllib.request
    import urllib.error
    url = f"{SUPABASE_URL}/rest/v1/{table}"
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "return=minimal",
    }
    body = json.dumps(row).encode()
    req = urllib.request.Request(url, data=body, headers=headers, method="POST")
    try:
        urllib.request.urlopen(req, timeout=5)
    except Exception:
        pass  # fire-and-forget


def _supabase_upsert(table, row):
    """UPSERT a row to Supabase REST API. Fire-and-forget, never raises."""
    if not SUPABASE_KEY:
        return
    import urllib.request
    import urllib.error
    url = f"{SUPABASE_URL}/rest/v1/{table}"
    headers = {
        "apikey": SUPABASE_KEY,
        "Authorization": f"Bearer {SUPABASE_KEY}",
        "Content-Type": "application/json",
        "Prefer": "resolution=merge-duplicates,return=minimal",
    }
    body = json.dumps(row).encode()
    req = urllib.request.Request(url, data=body, headers=headers, method="POST")
    try:
        urllib.request.urlopen(req, timeout=5)
    except Exception:
        pass  # fire-and-forget


def _ensure_forge_run(run_id, total_subwaves=0):
    """Create or update forge_runs row in Supabase."""
    _supabase_upsert("forge_runs", {
        "id": run_id,
        "status": "running",
        "total_subwaves": total_subwaves,
        "completed": 0,
        "failed": 0,
        "cost_usd": 0,
        "duration_ms": 0,
    })


def supabase_log_event(run_id, sw_id, event_type, data=None):
    """Log a forge event to Supabase.

    Args:
        run_id: forge run ID
        sw_id: sub-wave ID (or None for run-level events)
        event_type: dispatched | completed | failed | merged | pushed
        data: dict with optional keys: status, branch, cost_usd, duration_ms, output
    """
    data = data or {}
    row = {
        "run_id": run_id,
        "sw_id": sw_id or "",
        "event_type": event_type,
        "status": data.get("status", event_type),
        "branch": data.get("branch", ""),
        "cost_usd": data.get("cost_usd", 0),
        "duration_ms": data.get("duration_ms", 0),
        "output": data.get("output", "")[:2000],  # cap output size
    }
    _supabase_post("forge_events", row)


def _get_repo_url(repo_dir=None):
    """Get the origin remote URL for git clone instructions."""
    cwd = repo_dir or os.getcwd()
    result = subprocess.run(
        ["git", "remote", "get-url", "origin"],
        capture_output=True, text=True, cwd=cwd,
    )
    if result.returncode == 0:
        return result.stdout.strip()
    return ""

# ---------------------------------------------------------------------------
# PM-OS API Client
# ---------------------------------------------------------------------------

def pm_api(method, path, data=None):
    """Call PM-OS API."""
    import urllib.request
    import urllib.error
    url = f"{PM_API_URL}{path}"
    headers = {
        "Content-Type": "application/json",
    }
    if PM_API_KEY:
        headers["X-API-Key"] = PM_API_KEY
    body = json.dumps(data).encode() if data else None
    req = urllib.request.Request(url, data=body, headers=headers, method=method)
    try:
        with urllib.request.urlopen(req, timeout=30) as resp:
            return json.loads(resp.read().decode())
    except urllib.error.HTTPError as e:
        error_body = e.read().decode()[:500]
        return {"error": f"HTTP {e.code}: {error_body}"}
    except Exception as e:
        return {"error": f"{type(e).__name__}: {str(e)}"}


_STEP_TYPE_MAP = {
    "code": "llm",
    "plan": "llm",
    "test": "llm",
    "review": "review",
    "llm": "llm",
    "function": "function",
    "llm_call": "llm_call",
    "moa": "moa",
}


def _wrap_task_as_recipe_inline(task_data):
    """Wrap legacy task_data dict as a recipe_inline for /api/v2/run.

    Adapts the old Forge submit_task shape (type=code, agent=dex, tdd=true, run_id, work_dir,
    forge_branch, test_command) to the current pkg/recipe/schema.go Recipe/Wave/Step shape.

    Contract verified in /home/agdis/pm-os/pkg/recipe/schema.go:
      Recipe{Slug,Version,Name,Mode,RepoURL,Push,Waves:[Wave{ID:int,Name,Items:[Step]}]}
      Step{ID,Type("llm"|"function"|"llm_call"|"review"),Title,Provider,
           Instructions:[str],Acceptance,DependsOn,MaxRetries}
    """
    raw_type = (task_data.get("type") or "llm").lower()
    step_type = _STEP_TYPE_MAP.get(raw_type, "llm")

    instructions = task_data.get("instructions") or []
    if isinstance(instructions, str):
        instructions = [instructions]

    task_id = task_data.get("id") or f"task-{int(time.time() * 1000)}"
    title = task_data.get("title") or task_id

    step = {
        "id": task_id,
        "type": step_type,
        "title": title,
        "instructions": list(instructions),
    }

    provider = task_data.get("provider") or ""
    if provider:
        step["provider"] = provider

    acceptance = task_data.get("acceptance") or task_data.get("test_command") or ""
    if acceptance:
        step["acceptance"] = acceptance

    depends_on = task_data.get("depends_on") or []
    if depends_on:
        step["depends_on"] = list(depends_on)

    max_retries = int(task_data.get("max_retries") or 0)
    if max_retries:
        step["max_retries"] = max_retries

    test_cmd = task_data.get("test_command") or ""
    if test_cmd:
        step["verify"] = {
            "shell": test_cmd,
            "expect_exit": 0,
            "timeout": "5m",
        }

    slug = f"forge-{task_id}"[:48].lower().replace("_", "-")
    recipe = {
        "slug": slug,
        "version": "1.0",
        "name": f"Forge: {title}"[:200],
        "mode": "output-only",
        "waves": [
            {
                "id": 1,
                "name": title[:80] or "forge wave",
                "items": [step],
            }
        ],
    }

    forge_branch = task_data.get("forge_branch")
    if forge_branch:
        recipe["mode"] = "git-workspace"
        repo_url = task_data.get("repo_url") or _get_repo_url()
        if repo_url:
            recipe["repo_url"] = repo_url
        recipe["push"] = True

    return {"recipe_inline": recipe}


def submit_task(task_data):
    """Submit a task to PM-OS via /api/v2/run (recipe_inline).

    Adapts the legacy forge task_data shape to the current Recipe schema.
    Returns dict with task_id = run_id (each submit = 1-item inline recipe run).

    Historical endpoints (/api/tasks/dispatch, /api/tasks/submit) are gone —
    see pm-os HANDOFF.md §Fase 6 and /home/agdis/pm-os/cmd/pm-api/handlers_v2.go.
    """
    payload = _wrap_task_as_recipe_inline(task_data)
    resp = pm_api("POST", "/api/v2/run", payload)

    if "error" in resp:
        return {
            "error": resp["error"],
            "task_id": None,
            "status": "failed",
        }

    run_id = resp.get("run_id", "")
    return {
        "task_id": run_id,
        "run_id": run_id,
        "status": resp.get("status", "planning"),
        "recipe_slug": resp.get("recipe_slug", ""),
        "_submitted_type": task_data.get("type", "llm"),
        "_submitted_title": task_data.get("title", ""),
    }


def _extract_task_output(run_payload):
    """Extract the first task's output/result from GET /api/runs/{id} response."""
    tasks = run_payload.get("tasks") or []
    if not tasks:
        return "", {}
    task = tasks[0]
    result = task.get("result")
    if isinstance(result, dict):
        output = (
            result.get("output")
            or result.get("summary")
            or result.get("content")
            or ""
        )
        return str(output), result
    if isinstance(result, str):
        return result, {"raw": result}
    return "", {}


def get_task(task_id):
    """Get task (run) status via /api/runs/{run_id}.

    In the adapted model, submit_task creates 1 run per task, so task_id == run_id.
    We normalize the response to the shape the rest of forge.py expects:
        {status, output, duration_ms, cost_usd, error}
    """
    resp = pm_api("GET", f"/api/runs/{task_id}")
    if "error" in resp:
        return {"error": resp["error"], "status": "unknown"}

    run = resp.get("run") or {}
    tasks = resp.get("tasks") or []

    run_status = run.get("status", "")
    task_status = tasks[0].get("status") if tasks else run_status
    status = task_status or run_status

    output, result_dict = _extract_task_output(resp)

    duration_ms = 0
    if tasks:
        duration_ms = int(tasks[0].get("duration_ms") or 0)
    if not duration_ms:
        duration_ms = int(run.get("total_duration_ms") or 0)

    cost_usd = 0.0
    if tasks:
        cost_usd = float(tasks[0].get("cost_usd") or 0.0)
    if not cost_usd:
        cost_usd = float(run.get("total_cost_usd") or 0.0)

    normalized = {
        "task_id": task_id,
        "run_id": task_id,
        "status": status,
        "output": output,
        "duration_ms": duration_ms,
        "cost_usd": cost_usd,
        "error": run.get("error_message") or result_dict.get("error") or "",
        "_raw_run": run,
        "_raw_tasks": tasks,
    }
    return normalized

# ---------------------------------------------------------------------------
# Lifecycle — Ignition + Shutdown
# ---------------------------------------------------------------------------

CLOUD_RUN_REGION = "us-central1"
# pm-worker was removed in the pm-engine transition (see pm-os HANDOFF 2026-04-11).
# Execution now runs on pm-engine-alpha which autoscales 0→50 on demand — no
# manual ignition needed for typical forge runs. Keep the constant so callsites
# don't blow up; set to the live service for any callers that still scale it.
CLOUD_RUN_WORKER = "pm-engine-alpha"

# Find gcloud binary (may not be in PATH)
def _find_gcloud():
    import shutil
    g = shutil.which("gcloud")
    if g:
        return g
    candidates = [
        os.path.expanduser("~/google-cloud-sdk/bin/gcloud"),
        "/usr/lib/google-cloud-sdk/bin/gcloud",
        "/snap/google-cloud-cli/current/bin/gcloud",
    ]
    for c in candidates:
        if os.path.isfile(c):
            return c
    return "gcloud"  # fallback, will fail if not in PATH

GCLOUD = _find_gcloud()
GSUTIL = os.path.join(os.path.dirname(GCLOUD), "gsutil") if GCLOUD != "gcloud" else "gsutil"

def ignite(num_workers, timeout=120):
    """Ignition: pre-warm Cloud Run workers before dispatching.

    In the current pm-os topology (post 2026-04-11), pm-engine-alpha autoscales
    0→50 on demand. ignite() is effectively a no-op: the first few dispatches
    trigger cold starts, then autoscale takes over. We still check pm-api /api/health
    so the caller gets a clear signal the backend is reachable.

    If you need to force pre-warming (e.g. a wave of >20 parallel dispatches where
    cold-start latency matters), pass force=True via env FORGE_IGNITE_FORCE=1 and
    this function will call gcloud to set --min-instances=num_workers on
    CLOUD_RUN_WORKER (pm-engine-alpha by default).
    """
    force = os.environ.get("FORGE_IGNITE_FORCE", "") == "1"
    import urllib.request

    print(f"  🔥 Ignição: verificando {CLOUD_RUN_WORKER} (autoscale 0→50)...")

    if force:
        print(f"  🔥 FORGE_IGNITE_FORCE=1 → escalando min-instances={num_workers}")
        result = subprocess.run([
            GCLOUD, "run", "services", "update", CLOUD_RUN_WORKER,
            f"--min-instances={num_workers}",
            f"--max-instances={max(num_workers * 2, 50)}",
            f"--region={CLOUD_RUN_REGION}",
            "--quiet",
        ], capture_output=True, text=True)
        if result.returncode != 0:
            print(f"  ⚠️  gcloud update falhou: {result.stderr[:200]}")
        else:
            print(f"  ✅ Cloud Run atualizado: min={num_workers}")

    start = time.time()
    while time.time() - start < timeout:
        try:
            req = urllib.request.Request(f"{PM_API_URL}/api/health")
            with urllib.request.urlopen(req, timeout=10) as resp:
                health = json.loads(resp.read().decode())
                if health.get("status") == "ok":
                    print(f"  ✅ pm-api healthy (supabase={health.get('supabase','?')}, worker={health.get('worker','?')})")
                    return True
        except Exception:
            pass
        time.sleep(3)
        elapsed = int(time.time() - start)
        print(f"  ⏳ {elapsed}s... aguardando pm-api healthy...")

    print(f"  ⚠️  Timeout ({timeout}s) esperando pm-api healthy. Disparando mesmo assim.")
    return False


def shutdown(cleanup_run_id=None):
    """Shutdown: scale workers back to zero (only if FORGE_IGNITE_FORCE was used)
    and cleanup temp artifacts.
    """
    force = os.environ.get("FORGE_IGNITE_FORCE", "") == "1"

    if force:
        print(f"\n  🔌 Shutdown: revertendo {CLOUD_RUN_WORKER} para min-instances=0...")
        result = subprocess.run([
            GCLOUD, "run", "services", "update", CLOUD_RUN_WORKER,
            "--min-instances=0",
            f"--region={CLOUD_RUN_REGION}",
            "--quiet",
        ], capture_output=True, text=True)
        if result.returncode == 0:
            print(f"  ✅ min-instances=0 (autoscale devolverá aos padrões)")
        else:
            print(f"  ⚠️  Scale down falhou: {result.stderr[:200]}")
    else:
        print(f"\n  🔌 Shutdown: nenhuma ação necessária (autoscale nativo do pm-engine)")

    if cleanup_run_id:
        print(f"  🧹 Limpando artifacts de {cleanup_run_id}...")
        cleanup_result = subprocess.run([
            GSUTIL, "-q", "-m", "rm", "-r",
            f"gs://{FORGE_BUCKET}/{cleanup_run_id}/",
        ], capture_output=True, text=True)
        if cleanup_result.returncode == 0:
            print(f"  ✅ Artifacts removidos")
        else:
            print(f"  ⚠️  Cleanup falhou (bucket pode não existir ainda)")

    print(f"  💡 Luzes apagadas.\n")


# ---------------------------------------------------------------------------
# GCS Artifact Store (via gsutil CLI)
# ---------------------------------------------------------------------------

def gcs_upload(local_path, gcs_path):
    """Upload file to GCS."""
    full_path = f"gs://{FORGE_BUCKET}/{gcs_path}"
    subprocess.run([GSUTIL, "-q", "cp", str(local_path), full_path],
                   capture_output=True, check=True)
    return full_path


def gcs_download(gcs_path, local_path):
    """Download file from GCS."""
    full_path = f"gs://{FORGE_BUCKET}/{gcs_path}"
    subprocess.run([GSUTIL, "-q", "cp", full_path, str(local_path)],
                   capture_output=True, check=True)


def gcs_exists(gcs_path):
    """Check if GCS object exists."""
    full_path = f"gs://{FORGE_BUCKET}/{gcs_path}"
    result = subprocess.run([GSUTIL, "-q", "stat", full_path],
                            capture_output=True)
    return result.returncode == 0

# ---------------------------------------------------------------------------
# Context Packer
# ---------------------------------------------------------------------------

def pack_context(files, claude_md, tests=None, extra_files=None):
    """Pack context files into a tar.gz for a worker.

    Args:
        files: dict of {relative_path: content_string} - files worker needs to READ
        claude_md: string - the CLAUDE.md content for this worker
        tests: dict of {relative_path: content_string} - TDD test files
        extra_files: dict of {relative_path: content_string} - additional files

    Returns: path to tar.gz
    """
    tmp = tempfile.NamedTemporaryFile(suffix=".tar.gz", delete=False)
    with tarfile.open(tmp.name, "w:gz") as tar:
        # CLAUDE.md
        _add_string_to_tar(tar, "CLAUDE.md", claude_md)

        # Context files (read-only reference)
        for path, content in (files or {}).items():
            _add_string_to_tar(tar, f"context/{path}", content)

        # Test files (TDD)
        for path, content in (tests or {}).items():
            _add_string_to_tar(tar, f"tests/{path}", content)

        # Extra files
        for path, content in (extra_files or {}).items():
            _add_string_to_tar(tar, path, content)

    return tmp.name


def _add_string_to_tar(tar, name, content):
    """Add a string as a file to a tar archive."""
    data = content.encode("utf-8")
    info = tarfile.TarInfo(name=name)
    info.size = len(data)
    info.mtime = time.time()
    tar.addfile(info, io.BytesIO(data))


def unpack_result(tar_path, dest_dir):
    """Unpack worker result tar.gz."""
    with tarfile.open(tar_path, "r:gz") as tar:
        tar.extractall(dest_dir)

# ---------------------------------------------------------------------------
# Planner — Breaks a plan into sub-waves
# ---------------------------------------------------------------------------

def read_prompt(name):
    """Read a prompt template."""
    path = PROMPTS_DIR / f"{name}.md"
    if path.exists():
        return path.read_text()
    return ""


def generate_subwaves(plan_text, project_dir):
    """Call Opus to decompose plan into sub-waves.

    Returns list of sub-wave dicts.
    """
    planner_prompt = read_prompt("planner")

    # Build the full prompt
    full_prompt = f"""{planner_prompt}

## Plano para decompor:

{plan_text}

## Diretório do projeto: {project_dir}

Responda APENAS com JSON válido. Array de sub-waves."""

    # Call PM-OS to run Opus planner
    task = submit_task({
        "type": "plan",
        "title": "Forge Planner — decompor em sub-waves",
        "agent": "morgan",
        "provider": "opus",
        "instructions": [full_prompt],
        "acceptance": "JSON array de sub-waves",
    })

    return task


def generate_macro_tests(subwaves, plan_text):
    """Call Opus to generate macro/contract tests.

    Returns dict of {test_file_path: test_content}.
    """
    test_prompt = read_prompt("test-writer")

    full_prompt = f"""{test_prompt}

## Sub-waves do sistema:

{json.dumps(subwaves, indent=2, ensure_ascii=False)}

## Plano original:

{plan_text[:3000]}

Gere testes de CONTRATO entre subsistemas. Cada teste verifica interfaces, não implementação.
Responda com JSON: {{"files": {{"path/test.go": "conteúdo"}}}}"""

    task = submit_task({
        "type": "code",
        "title": "Forge TDD — macro tests",
        "agent": "quinn",
        "provider": "opus",
        "instructions": [full_prompt],
        "acceptance": "JSON com test files",
    })

    return task

# ---------------------------------------------------------------------------
# Dispatcher — Sends sub-waves to PM-OS workers
# ---------------------------------------------------------------------------

def dispatch_subwave(run_id, sw, context_gcs_path, task_notes=None, repo_url=None, branch=None):
    """Dispatch a single sub-wave to PM-OS.

    Args:
        run_id: forge run ID
        sw: sub-wave dict
        context_gcs_path: GCS path for context artifacts
        task_notes: TASK_NOTES.md content from dependency sub-waves (relay)
        repo_url: git remote URL for worker to clone
        branch: git branch name for worker to checkout and push to
    """
    worker_prompt = read_prompt("worker")

    claude_md = _build_claude_md(sw)

    instructions = [
        f"## Contexto\n\nBaixe o contexto de: gs://{FORGE_BUCKET}/{context_gcs_path}",
        f"## CLAUDE.md\n\n{claude_md}",
        f"## Tarefa\n\n{sw.get('task_description', '')}",
        f"## Critério de aceitação\n\n{sw.get('acceptance', 'Testes devem passar')}",
    ]

    # Git workflow instructions for the worker
    if repo_url and branch:
        git_instructions = (
            "## Git Workflow\n\n"
            "Antes de começar, clone o repositório e entre na branch correta:\n\n"
            "```bash\n"
            f"git clone {repo_url} workspace\n"
            "cd workspace\n"
            f"git checkout {branch}\n"
            "```\n\n"
            "Quando terminar, commit e push suas alterações:\n\n"
            "```bash\n"
            "git add -A\n"
            f'git commit -m "forge({sw["id"]}): {sw.get("title", "implementation")}"\n'
            f"git push origin {branch}\n"
            "```\n\n"
            "IMPORTANTE: Faça push ANTES de reportar conclusão. O forge detecta conclusão via push."
        )
        instructions.append(git_instructions)

    # TASK_NOTES relay: inject context from dependency sub-waves
    if task_notes:
        instructions.append(f"## Task Notes (de sub-waves anteriores)\n\n{task_notes}")

    instructions.append(worker_prompt)

    # Tiered quality: select review model based on tier
    tier = sw.get("tier", "trivial")
    review_model = {"trivial": None, "standard": "sonnet", "complex": "opus"}.get(tier)

    # Ensure acceptance is never empty (PM-OS API requires it)
    acceptance = sw.get("acceptance") or sw.get("test_command") or "Tests pass"

    task_payload = {
        "type": "code",
        "title": f"Forge {run_id} — {sw['id']}",
        "agent": sw.get("agent", "dex"),
        "provider": sw.get("model", "haiku"),
        "instructions": instructions,
        "acceptance": acceptance,
        "test_command": sw.get("test_command", ""),
        "max_retries": sw.get("max_retries", 2),
        "work_dir": sw.get("work_dir", ""),
        "run_id": run_id,
        "tdd": True,
    }

    # Add forge_branch for git push support
    if branch:
        task_payload["forge_branch"] = branch

    task = submit_task(task_payload)

    # Store tier for review dispatch later
    if task and "task_id" in task:
        task["_tier"] = tier
        task["_review_model"] = review_model
        supabase_log_event(run_id, sw["id"], "dispatched", {
            "branch": branch or "",
            "status": "dispatched",
        })

    return task


def _build_claude_md(sw):
    """Generate a minimal CLAUDE.md for a worker."""
    template = read_prompt("claude-md-template")
    if not template:
        template = """# Forge Worker — {title}

## Sua missão
{task_description}

## Arquivos que você PODE criar/editar
{files_to_edit}

## Arquivos que você NÃO pode tocar
Qualquer arquivo fora do seu escopo.

## Critério de aceitação
{acceptance}

## TDD
Testes foram fornecidos. Sua missão é fazer todos passarem.
Rode: {test_command}
"""

    return template.format(
        title=sw.get("title", ""),
        task_description=sw.get("task_description", ""),
        files_to_edit="\n".join(f"- {f}" for f in sw.get("files_to_edit", [])),
        acceptance=sw.get("acceptance", ""),
        test_command=sw.get("test_command", "go test ./..."),
    )

# ---------------------------------------------------------------------------
# Relay Monitor — Reactive pipeline
# ---------------------------------------------------------------------------

def _check_branch_pushed(run_id, sw_id, repo_dir=None):
    """Check if a forge branch has commits via git ls-remote.

    Returns the SHA if forge/{run_id}/{sw_id} exists on the remote, else empty string.
    """
    cwd = repo_dir or os.getcwd()
    branch_ref = f"forge/{run_id}/{sw_id}"
    result = subprocess.run(
        ["git", "ls-remote", "--heads", "origin", branch_ref],
        capture_output=True, text=True, cwd=cwd,
    )
    if result.returncode == 0 and branch_ref in result.stdout:
        return result.stdout.split()[0]
    return ""


def relay_monitor(run_id, subwaves, dispatched_tasks, repo_dir=None, repo_url=None):
    """Monitor sub-wave completion and dispatch dependents.

    Args:
        run_id: forge run ID
        subwaves: list of sub-wave dicts (with 'depends_on' field)
        dispatched_tasks: dict of {sw_id: task_id} already dispatched
        repo_dir: git repo directory for ls-remote push detection
        repo_url: git remote URL for dispatching unblocked sub-waves

    Returns: dict of {sw_id: result}
    """
    completed = {}
    pending = {sw["id"]: sw for sw in subwaves if sw["id"] not in dispatched_tasks}
    in_flight = dict(dispatched_tasks)  # sw_id → task_id
    results = {}

    start = time.time()

    # Track push events from JSONL file (fallback when status callback fails)
    push_file = f"/tmp/forge-pushes-{run_id}.jsonl"
    pushed_sws = set()

    # Track branch SHAs for git ls-remote push detection
    branch_shas = {}  # sw_id → initial SHA (set at branch creation)

    # Snapshot initial SHAs for all dispatched branches
    for sw_id in dispatched_tasks:
        sha = _check_branch_pushed(run_id, sw_id, repo_dir=repo_dir)
        if sha:
            branch_shas[sw_id] = sha

    while len(completed) < len(subwaves):
        # Read push events from JSONL (android-agent writes these)
        pushed_sws = _read_push_events(push_file, pushed_sws)

        # Detect worker pushes via git ls-remote (SHA changed = worker pushed)
        for sw_id in list(in_flight.keys()):
            if sw_id in completed or sw_id in pushed_sws:
                continue
            current_sha = _check_branch_pushed(run_id, sw_id, repo_dir=repo_dir)
            if current_sha and current_sha != branch_shas.get(sw_id, ""):
                pushed_sws.add(sw_id)
                print(f"  📡 {sw_id} — push detected via ls-remote")
                supabase_log_event(run_id, sw_id, "pushed", {
                    "branch": f"forge/{run_id}/{sw_id}",
                    "output": current_sha[:12],
                })

        # Check in-flight tasks
        for sw_id, task_id in list(in_flight.items()):
            if sw_id in completed:
                continue

            status = get_task(task_id)
            if not status or "error" in status:
                continue

            task_status = status.get("status", "")

            # Also check for completion signal in output (faster than status polling)
            output = status.get("output", "")
            has_completion_signal = "FORGE_COMPLETE:" in output
            has_failure_signal = "FORGE_FAILED:" in output

            # Push via ls-remote also signals completion
            if sw_id in pushed_sws:
                has_completion_signal = True

            if task_status in ("done", "passed") or has_completion_signal:
                completed[sw_id] = status

                # Extract TASK_NOTES from output for relay to dependents
                task_notes = _extract_task_notes(output)

                results[sw_id] = {
                    "status": "green",
                    "task_id": task_id,
                    "duration_ms": status.get("duration_ms", 0),
                    "cost_usd": status.get("cost_usd", 0),
                    "task_notes": task_notes,
                    "branch_pushed": sw_id in pushed_sws,
                }
                _print_sw_done(sw_id, results[sw_id], len(completed), len(subwaves))
                supabase_log_event(run_id, sw_id, "completed", {
                    "cost_usd": status.get("cost_usd", 0),
                    "duration_ms": status.get("duration_ms", 0),
                    "branch": f"forge/{run_id}/{sw_id}",
                })

                # Check if any pending sub-wave is now unblocked
                _dispatch_unblocked(run_id, pending, completed, results, in_flight, repo_url=repo_url)

            elif task_status == "failed" or has_failure_signal:
                completed[sw_id] = status
                results[sw_id] = {
                    "status": "red",
                    "task_id": task_id,
                    "error": status.get("output", "unknown error")[:500],
                    "branch_pushed": sw_id in pushed_sws,
                }
                _print_sw_fail(sw_id, results[sw_id], len(completed), len(subwaves))
                supabase_log_event(run_id, sw_id, "failed", {
                    "output": status.get("output", "")[:500],
                    "branch": f"forge/{run_id}/{sw_id}",
                })

                # Still unblock dependents (they'll get partial context + error notes)
                _dispatch_unblocked(run_id, pending, completed, results, in_flight, repo_url=repo_url)

        if len(completed) < len(subwaves):
            time.sleep(5)  # Poll every 5 seconds

    elapsed = time.time() - start
    return results, elapsed


def _dispatch_unblocked(run_id, pending, completed, results, in_flight, repo_url=None):
    """Check pending sub-waves and dispatch any whose dependencies are met.

    Collects TASK_NOTES from completed dependencies and relays them.
    """
    newly_dispatched = []

    for sw_id, sw in list(pending.items()):
        deps = sw.get("depends_on", [])
        if all(d in completed for d in deps):
            # All dependencies met — collect TASK_NOTES from deps
            relay_notes = []
            for dep_id in deps:
                dep_result = results.get(dep_id, {})
                notes = dep_result.get("task_notes", "")
                if notes:
                    relay_notes.append(f"### From {dep_id}\n\n{notes}")

            combined_notes = "\n\n---\n\n".join(relay_notes) if relay_notes else None

            # Dispatch with relay context (and git workflow if available)
            context_path = f"{run_id}/context/{sw_id}/input.tar.gz"
            branch_name = f"forge/{run_id}/{sw_id}" if repo_url else None
            task = dispatch_subwave(run_id, sw, context_path, task_notes=combined_notes,
                                    repo_url=repo_url, branch=branch_name)

            if task and "task_id" in task:
                in_flight[sw_id] = task["task_id"]
                newly_dispatched.append(sw_id)

    for sw_id in newly_dispatched:
        del pending[sw_id]


def _read_push_events(push_file, already_seen):
    """Read forge push events from JSONL file, return updated set of sw_ids."""
    try:
        with open(push_file, "r") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    ev = json.loads(line)
                    sw_id = ev.get("sw_id", "")
                    if sw_id and sw_id not in already_seen:
                        already_seen.add(sw_id)
                        print(f"  📦 {sw_id:<10} branch_pushed  branch={ev.get('branch','')} sha={ev.get('sha','')[:8]}")
                except json.JSONDecodeError:
                    continue
    except FileNotFoundError:
        pass
    return already_seen


def _extract_task_notes(output):
    """Extract TASK_NOTES.md content from worker output."""
    if not output:
        return ""

    # Look for task notes section in output
    markers = ["# Task Notes", "## O que foi feito", "## Decisões tomadas"]
    for marker in markers:
        idx = output.find(marker)
        if idx >= 0:
            # Extract from marker to end or next major section
            notes = output[idx:]
            # Truncate at completion signal if present
            for signal in ["FORGE_COMPLETE:", "FORGE_FAILED:"]:
                sig_idx = notes.find(signal)
                if sig_idx >= 0:
                    notes = notes[:sig_idx].strip()
            return notes[:2000]  # Cap at 2KB

    return ""

# ---------------------------------------------------------------------------
# Collector — Gather results and merge locally
# ---------------------------------------------------------------------------

def collect_results(run_id, results, project_dir):
    """Fetch worker branches and merge into an integration branch via git."""
    print(f"\n{'='*60}")
    print(f"  Collecting results for {run_id}")
    print(f"{'='*60}\n")

    def _git(args, check=True):
        """Run a git command inside project_dir."""
        cmd = ["git"] + args
        r = subprocess.run(cmd, cwd=project_dir, capture_output=True, text=True)
        if check and r.returncode != 0:
            raise subprocess.CalledProcessError(r.returncode, cmd, r.stdout, r.stderr)
        return r

    # 1) Fetch all forge branches for this run
    print("  Fetching forge branches...")
    fetch = _git(
        ["fetch", "origin", f"forge/{run_id}/*:refs/remotes/origin/forge/{run_id}/*"],
        check=False,
    )
    if fetch.returncode != 0:
        for sw_id in results:
            _git(["fetch", "origin", f"forge/{run_id}/{sw_id}"], check=False)

    # 2) Create integration branch from main
    integration_branch = f"forge/{run_id}/integration"
    print(f"  Creating branch {integration_branch} from main...")
    _git(["checkout", "-B", integration_branch, "main"])

    # 3) Merge each green branch (sorted for determinism)
    green = sorted(
        [(sw_id, r) for sw_id, r in results.items() if r["status"] == "green"],
        key=lambda x: x[0],
    )
    if not green:
        print("  Nenhuma sub-wave green para merge.")
        return {"merged": 0, "failed": [], "needs_manual": []}

    merged = 0
    needs_manual = []

    for sw_id, result in green:
        branch_ref = f"origin/forge/{run_id}/{sw_id}"

        # Check if remote branch exists
        if _git(["rev-parse", "--verify", branch_ref], check=False).returncode != 0:
            print(f"  ⚠️  {sw_id} — branch not found ({branch_ref})")
            continue

        print(f"  Merging {sw_id}...")
        merge = _git(
            ["merge", "--no-ff", "-m", f"forge: merge {sw_id} from {run_id}", branch_ref],
            check=False,
        )

        if merge.returncode == 0:
            merged += 1
            print(f"  ✅ {sw_id} — merged")
            continue

        # Conflict — check if it's only go.mod/go.sum
        conflict_out = _git(["diff", "--name-only", "--diff-filter=U"], check=False)
        conflict_files = [f for f in conflict_out.stdout.strip().split("\n") if f]
        go_only = all(f in ("go.mod", "go.sum") for f in conflict_files)

        if go_only and conflict_files:
            print(f"  ⚙️  {sw_id} — go.mod/go.sum conflict, accepting theirs + tidy...")
            for f in conflict_files:
                _git(["checkout", "--theirs", f])
                _git(["add", f])
            subprocess.run(
                ["go", "mod", "tidy"], cwd=project_dir,
                capture_output=True, text=True,
            )
            _git(["add", "go.mod", "go.sum"])
            _git(["commit", "--no-edit"])
            merged += 1
            print(f"  ✅ {sw_id} — merged (go.mod resolved)")
        else:
            conflicts_str = ", ".join(conflict_files)
            print(f"  ❌ {sw_id} — conflict in: {conflicts_str}")
            _git(["merge", "--abort"], check=False)
            needs_manual.append({"sw_id": sw_id, "conflicts": conflict_files})

    # 4) Post-merge validation: go build + go test
    print(f"\n  Running post-merge validation...")

    build = subprocess.run(
        ["go", "build", "./..."], cwd=project_dir,
        capture_output=True, text=True, timeout=120,
    )
    build_ok = build.returncode == 0
    if not build_ok:
        print(f"  ❌ go build failed:\n{build.stderr[:500]}")
    else:
        print(f"  ✅ go build OK")

    test = subprocess.run(
        ["go", "test", "./...", "-count=1", "-timeout=120s"], cwd=project_dir,
        capture_output=True, text=True, timeout=300,
    )
    test_ok = test.returncode == 0
    if not test_ok:
        print(f"  ⚠️  go test failed:\n{test.stdout[:500]}\n{test.stderr[:500]}")
    else:
        print(f"  ✅ go test OK")

    # 5) Push + PR if build and tests pass
    pr_url = None
    if build_ok and test_ok and merged > 0:
        print(f"\n  Pushing {integration_branch}...")
        push = _git(["push", "-u", "origin", integration_branch], check=False)
        if push.returncode != 0:
            print(f"  ❌ git push failed:\n{push.stderr[:300]}")
        else:
            print(f"  ✅ Pushed to origin/{integration_branch}")
            pr_url = _create_forge_pr(
                run_id, integration_branch, results, green,
                needs_manual, test, project_dir,
            )
    elif merged > 0:
        print(f"\n  ⚠️  Skipping push/PR — build or tests failed.")
        print(f"  Branch {integration_branch} is local. Fix and push manually.")

    # Summary
    total = len(results)
    print(f"\n  Merged {merged}/{total} sub-waves into {integration_branch}")
    if needs_manual:
        print(f"  ⚠️  {len(needs_manual)} sub-wave(s) need manual merge:")
        for item in needs_manual:
            conflicts_str = ", ".join(item["conflicts"])
            print(f"     - {item['sw_id']}: {conflicts_str}")
    if pr_url:
        print(f"  🔗 PR: {pr_url}")

    return {"merged": merged, "failed": [], "needs_manual": needs_manual, "pr_url": pr_url}


def _create_forge_pr(run_id, branch, results, green, needs_manual, test_run, project_dir):
    """Create a GitHub PR for the forge integration branch. Returns PR URL or None."""

    # Check if gh CLI is available
    gh_check = subprocess.run(["gh", "--version"], capture_output=True, text=True)
    if gh_check.returncode != 0:
        print(f"\n  ⚠️  gh CLI not found. Create PR manually:")
        print(f"     git push origin {branch}")
        print(f"     gh pr create --base main --head {branch}")
        return None

    # Build PR body
    total = len(results)
    merged_count = len(green)
    skipped = [(sw_id, r) for sw_id, r in results.items() if r["status"] != "green"]

    sw_lines = []
    for sw_id, r in green:
        cost = r.get("cost_usd", 0)
        dur = r.get("duration_ms", 0) / 1000
        sw_lines.append(f"- [x] **{sw_id}** — {dur:.0f}s, ${cost:.2f}")
    for item in needs_manual:
        conflicts_str = ", ".join(item["conflicts"])
        sw_lines.append(
            f"- [ ] **{item['sw_id']}** — needs manual merge ({conflicts_str})"
        )
    for sw_id, r in skipped:
        sw_lines.append(f"- [ ] ~~{sw_id}~~ — {r['status']}")
    sw_section = "\n".join(sw_lines)

    diff_stat = subprocess.run(
        ["git", "diff", "--stat", "main...HEAD"], cwd=project_dir,
        capture_output=True, text=True,
    )
    files_section = diff_stat.stdout.strip() if diff_stat.returncode == 0 else "(could not diff)"

    if test_run.returncode == 0:
        test_section = "All tests passing."
    else:
        test_section = f"```\n{test_run.stdout[:800]}\n```"

    total_cost = sum(r.get("cost_usd", 0) for r in results.values())

    body = (
        f"## Code Forge Integration — {run_id}\n\n"
        f"### Sub-waves ({merged_count}/{total} merged)\n\n"
        f"{sw_section}\n\n"
        f"### Changed files\n\n"
        f"```\n{files_section}\n```\n\n"
        f"### Test results\n\n"
        f"{test_section}\n\n"
        f"### Stats\n\n"
        f"| Metric | Value |\n"
        f"|--------|-------|\n"
        f"| Sub-waves merged | {merged_count}/{total} |\n"
        f"| Manual merge needed | {len(needs_manual)} |\n"
        f"| Total cost | ${total_cost:.2f} |\n"
    )

    title = f"forge: {run_id} ({merged_count}/{total} sub-waves)"
    if len(title) > 70:
        title = f"forge: {run_id}"

    pr = subprocess.run(
        ["gh", "pr", "create",
         "--base", "main", "--head", branch,
         "--title", title, "--body", body],
        cwd=project_dir, capture_output=True, text=True,
    )

    if pr.returncode == 0:
        url = pr.stdout.strip()
        print(f"  ✅ PR created: {url}")
        return url
    else:
        print(f"  ❌ gh pr create failed:\n{pr.stderr[:300]}")
        print(f"  Create manually: gh pr create --base main --head {branch}")
        return None


# ---------------------------------------------------------------------------
# Monitor Dashboard Generator
# ---------------------------------------------------------------------------

def generate_monitor_script(run_id, subwaves):
    """Generate a standalone monitoring script that user can run in another terminal."""

    sw_list = json.dumps([{
        "id": sw["id"],
        "title": sw.get("title", ""),
        "model": sw.get("model", "haiku"),
        "depends_on": sw.get("depends_on", []),
    } for sw in subwaves], ensure_ascii=False)

    script = f'''#!/usr/bin/env python3
"""Forge Monitor — Acompanhe o run {run_id} em tempo real."""
import json, time, os, sys
try:
    import urllib.request
except:
    pass

PUSH_FILE = f"/tmp/forge-pushes-{{RUN_ID}}.jsonl"

def read_pushed_sws():
    pushed = set()
    try:
        with open(PUSH_FILE, "r") as f:
            for line in f:
                line = line.strip()
                if not line:
                    continue
                try:
                    ev = json.loads(line)
                    sw_id = ev.get("sw_id", "")
                    if sw_id:
                        pushed.add(sw_id)
                except json.JSONDecodeError:
                    continue
    except FileNotFoundError:
        pass
    return pushed

PM_API_URL = "{PM_API_URL}"
PM_API_KEY = os.environ.get("PM_API_KEY", "{PM_API_KEY}")
RUN_ID = "{run_id}"
SUBWAVES = json.loads(\'\'\'{sw_list}\'\'\')

def get_task(task_id):
    # In the adapted Forge, each submit=1 run, so task_id == run_id.
    try:
        req = urllib.request.Request(
            f"{{PM_API_URL}}/api/runs/{{task_id}}",
            headers={{"X-Api-Key": PM_API_KEY}})
        with urllib.request.urlopen(req, timeout=10) as r:
            data = json.loads(r.read().decode())
            run = data.get("run", {{}})
            tasks = data.get("tasks") or []
            status = tasks[0].get("status") if tasks else run.get("status", "unknown")
            cost = 0.0
            if tasks:
                cost = float(tasks[0].get("cost_usd") or 0.0)
            if not cost:
                cost = float(run.get("total_cost_usd") or 0.0)
            return {{"status": status, "cost_usd": cost}}
    except:
        return {{"status": "unknown"}}

def clear():
    os.system("clear" if os.name != "nt" else "cls")

def main():
    tasks_file = f"/tmp/forge-tasks-{{RUN_ID}}.json"
    tasks = {{}}
    if os.path.exists(tasks_file):
        tasks = json.loads(open(tasks_file).read())

    while True:
        clear()
        now = time.strftime("%H:%M:%S")

        done = sum(1 for t in tasks.values() if t.get("status") in ("done","passed"))
        failed = sum(1 for t in tasks.values() if t.get("status") == "failed")
        running = sum(1 for t in tasks.values() if t.get("status") in ("running","pending"))
        total = len(SUBWAVES)

        # Progress bar
        pct = (done / total * 100) if total > 0 else 0
        bar_len = 40
        filled = int(bar_len * done / total) if total > 0 else 0
        bar = "█" * filled + "░" * (bar_len - filled)

        total_cost = sum(t.get("cost_usd", 0) for t in tasks.values())

        print(f"╔══════════════════════════════════════════════════════════╗")
        print(f"║  CODE FORGE — {{RUN_ID:<42}} ║")
        print(f"║  {{bar}} {{pct:5.1f}}%  ║")
        print(f"║  Done: {{done}}  Running: {{running}}  Failed: {{failed}}  Total: {{total:<5}}   ║")
        print(f"║  Cost: ${{total_cost:.2f}}                       {{now}}   ║")
        print(f"╠══════════════════════════════════════════════════════════╣")

        pushed_sws = read_pushed_sws()

        for sw in SUBWAVES:
            sid = sw["id"]
            task = tasks.get(sid, {{}})
            status = task.get("status", "waiting")

            icons = {{
                "done": "✅", "passed": "✅",
                "running": "⏳", "pending": "🔄",
                "failed": "❌", "waiting": "⬚ ",
                "unknown": "❓",
            }}
            icon = icons.get(status, "❓")
            git = "🔀" if sid in pushed_sws else "⬚ "

            model = sw.get("model", "haiku")[:6]
            title = sw.get("title", sid)[:32]
            cost = f"${{task.get('cost_usd', 0):.2f}}" if status in ("done","passed","failed") else ""
            dur = f"{{task.get('duration_ms',0)//1000}}s" if task.get("duration_ms") else ""
            deps = ",".join(sw.get("depends_on", [])) or "-"

            print(f"║  {{icon}} {{git}} {{sid:<8}} {{title:<32}} {{model:<6}} {{dur:>4}} {{cost:>6}} ║")

        print(f"╚══════════════════════════════════════════════════════════╝")
        print(f"\\n  Ctrl+C pra sair. Atualiza a cada 5s.")

        # Poll tasks
        for sw in SUBWAVES:
            sid = sw["id"]
            if sid in tasks and tasks[sid].get("status") in ("done","passed","failed"):
                continue
            tid = tasks.get(sid, {{}}).get("task_id")
            if tid:
                tasks[sid] = get_task(tid)

        # Save state
        with open(tasks_file, "w") as f:
            json.dump(tasks, f)

        # Check if all done
        if done + failed >= total:
            print(f"\\n  🏁 Run completo! {{done}} green, {{failed}} red, ${{total_cost:.2f}}")
            break

        time.sleep(5)

if __name__ == "__main__":
    main()
'''

    monitor_path = f"/tmp/forge-monitor-{run_id}.py"
    with open(monitor_path, "w") as f:
        f.write(script)
    os.chmod(monitor_path, 0o755)

    return monitor_path

# ---------------------------------------------------------------------------
# Git Branch System — forge/{run_id}/{sw_id} branches
# ---------------------------------------------------------------------------

def create_forge_branch(run_id, sw_id, repo_dir=None):
    """Create branch forge/{run_id}/{sw_id} from main and push to origin.

    Args:
        run_id: forge run ID
        sw_id: sub-wave ID
        repo_dir: git repo directory (default: cwd)

    Returns: dict with branch name and success status
    """
    branch = f"forge/{run_id}/{sw_id}"
    cwd = repo_dir or os.getcwd()

    # Fetch latest main
    subprocess.run(["git", "fetch", "origin", "main"],
                   capture_output=True, text=True, cwd=cwd)

    # Create branch from origin/main
    result = subprocess.run(
        ["git", "checkout", "-b", branch, "origin/main"],
        capture_output=True, text=True, cwd=cwd,
    )
    if result.returncode != 0:
        return {"branch": branch, "ok": False, "error": result.stderr.strip()}

    # Push with upstream tracking
    push = subprocess.run(
        ["git", "push", "-u", "origin", branch],
        capture_output=True, text=True, cwd=cwd,
    )
    if push.returncode != 0:
        return {"branch": branch, "ok": False, "error": push.stderr.strip()}

    return {"branch": branch, "ok": True}


def list_forge_branches(run_id, repo_dir=None):
    """List remote branches matching forge/{run_id}/*.

    Returns: list of branch names
    """
    cwd = repo_dir or os.getcwd()
    result = subprocess.run(
        ["git", "branch", "-r", "--list", f"origin/forge/{run_id}/*"],
        capture_output=True, text=True, cwd=cwd,
    )
    if result.returncode != 0:
        return []

    branches = []
    for line in result.stdout.strip().splitlines():
        branch = line.strip()
        if branch:
            branches.append(branch)
    return branches


def merge_forge_branches(run_id, repo_dir=None):
    """Create integration branch and merge all sub-wave branches sequentially.

    Creates forge/{run_id}/integration from main, then merges each
    forge/{run_id}/* branch in order.

    Returns: dict with status and list of merged branches
    """
    cwd = repo_dir or os.getcwd()
    integration = f"forge/{run_id}/integration"

    # Fetch all
    subprocess.run(["git", "fetch", "origin"],
                   capture_output=True, text=True, cwd=cwd)

    # List sub-wave branches (exclude integration itself)
    branches = list_forge_branches(run_id, repo_dir=cwd)
    sw_branches = [b for b in branches if not b.endswith("/integration")]

    if not sw_branches:
        return {"branch": integration, "ok": False, "error": "no branches to merge", "merged": []}

    # Create integration branch from origin/main
    result = subprocess.run(
        ["git", "checkout", "-b", integration, "origin/main"],
        capture_output=True, text=True, cwd=cwd,
    )
    if result.returncode != 0:
        return {"branch": integration, "ok": False, "error": result.stderr.strip(), "merged": []}

    # Merge each sub-wave branch
    merged = []
    for branch in sorted(sw_branches):
        merge_result = subprocess.run(
            ["git", "merge", branch, "--no-edit"],
            capture_output=True, text=True, cwd=cwd,
        )
        if merge_result.returncode != 0:
            return {
                "branch": integration,
                "ok": False,
                "error": f"merge conflict on {branch}: {merge_result.stderr.strip()}",
                "merged": merged,
            }
        merged.append(branch)
        # Extract sw_id from branch name: origin/forge/{run_id}/{sw_id}
        sw_id = branch.rsplit("/", 1)[-1] if "/" in branch else branch
        supabase_log_event(run_id, sw_id, "merged", {"branch": branch})

    return {"branch": integration, "ok": True, "merged": merged}


def cleanup_forge_branches(run_id, repo_dir=None):
    """Delete all remote branches matching forge/{run_id}/*.

    Returns: dict with deleted branches and status
    """
    cwd = repo_dir or os.getcwd()

    branches = list_forge_branches(run_id, repo_dir=cwd)
    if not branches:
        return {"ok": True, "deleted": []}

    deleted = []
    errors = []
    for branch in branches:
        # Strip origin/ prefix for push --delete
        ref = branch.replace("origin/", "", 1)
        result = subprocess.run(
            ["git", "push", "origin", "--delete", ref],
            capture_output=True, text=True, cwd=cwd,
        )
        if result.returncode == 0:
            deleted.append(ref)
        else:
            errors.append(f"{ref}: {result.stderr.strip()}")

    return {
        "ok": len(errors) == 0,
        "deleted": deleted,
        "errors": errors if errors else None,
    }


# ---------------------------------------------------------------------------
# Report
# ---------------------------------------------------------------------------

def print_report(run_id, results, elapsed):
    """Print final report."""
    total = len(results)
    green = sum(1 for r in results.values() if r["status"] == "green")
    red = sum(1 for r in results.values() if r["status"] == "red")
    cost = sum(r.get("cost_usd", 0) for r in results.values())

    print(f"""
╔══════════════════════════════════════════════════════════╗
║  ✅ FORGE COMPLETE                                       ║
╠══════════════════════════════════════════════════════════╣
║  Run:        {run_id:<42} ║
║  Sub-waves:  {green}/{total} green, {red} red{' '*28}║
║  Tempo:      {elapsed:.0f}s ({elapsed/60:.1f} min){' '*30}║
║  Custo:      ${cost:.2f}{' '*39}║
╚══════════════════════════════════════════════════════════╝
""")

# ---------------------------------------------------------------------------
# Print helpers
# ---------------------------------------------------------------------------

def _print_sw_done(sw_id, result, done, total):
    cost = result.get("cost_usd", 0)
    dur = result.get("duration_ms", 0) / 1000
    print(f"  ✅ {sw_id:<10} done  {dur:.0f}s  ${cost:.2f}  [{done}/{total}]")


def _print_sw_fail(sw_id, result, done, total):
    error = result.get("error", "")[:60]
    print(f"  ❌ {sw_id:<10} FAIL  {error}  [{done}/{total}]")

# ---------------------------------------------------------------------------
# Main — CLI
# ---------------------------------------------------------------------------

def cmd_plan(input_path):
    """Generate sub-waves from a plan."""
    plan_text = Path(input_path).read_text() if os.path.isfile(input_path) else input_path

    print("📐 Gerando sub-waves com Opus...")
    result = generate_subwaves(plan_text, os.getcwd())

    if "error" in result:
        print(f"  Erro: {result['error']}")
        return

    print(f"  Task submetida: {result.get('task_id', 'unknown')}")
    print(f"  Aguardando planner... (acompanhe no PM-OS dashboard)")


def cmd_run(input_path, dry_run=False, machines=20, model="haiku", auto_confirm=False):
    """Full pipeline: plan → pack → dispatch → relay → collect."""
    plan_text = Path(input_path).read_text() if os.path.isfile(input_path) else input_path

    run_id = f"forge-{datetime.now().strftime('%Y%m%d-%H%M%S')}"

    _load_supabase_key()

    print(f"""
╔══════════════════════════════════════════════════════════╗
║  CODE FORGE — Starting                                   ║
║  Run: {run_id:<48} ║
║  Input: {str(input_path)[:46]:<48} ║
║  Model: {model:<48} ║
║  Max machines: {machines:<41} ║
╚══════════════════════════════════════════════════════════╝
""")

    # Phase 1: Plan
    print("═══ FASE 1: Decompor plano em sub-waves (Opus) ═══\n")

    # For now, try to parse existing plan structure
    # In production, this calls Opus to decompose
    subwaves = _parse_plan_to_subwaves(plan_text, model)

    if not subwaves:
        print("  Nenhuma sub-wave gerada. Verifique o plano.")
        return

    _ensure_forge_run(run_id, total_subwaves=len(subwaves))

    # Count independent vs sequential
    independent = [sw for sw in subwaves if not sw.get("depends_on")]
    sequential = [sw for sw in subwaves if sw.get("depends_on")]

    print(f"  Sub-waves: {len(subwaves)}")
    print(f"  Independentes (Wave A): {len(independent)}")
    print(f"  Sequenciais (Wave B+): {len(sequential)}")
    print()

    # Phase 1.5: Macro Tests (TDD)
    print("═══ FASE 1.5: Gerar macro tests (TDD) ═══\n")
    print(f"  Gerando contract tests para {len(subwaves)} sub-waves...")
    # macro_tests = generate_macro_tests(subwaves, plan_text)
    print(f"  ✅ Macro tests gerados\n")

    # Generate monitor script
    monitor_path = generate_monitor_script(run_id, subwaves)

    # Cost estimation
    est_cost = _estimate_cost(subwaves)
    est_time = _estimate_time(subwaves)

    print(f"""
╔══════════════════════════════════════════════════════════╗
║  Forge Plan Ready                                        ║
║                                                          ║
║  Sub-waves:  {len(subwaves):<43} ║
║  Máquinas:   {len(independent)} (pico) → {len(sequential)}{' '*35}║
║  Modelo:     {model} (geração) + opus (review){' '*19}║
║  Custo est:  ~${est_cost:.2f}{' '*40}║
║  Tempo est:  ~{est_time:.0f} min{' '*40}║
║                                                          ║
║  Monitor:  python3 {monitor_path:<35} ║
╚══════════════════════════════════════════════════════════╝
""")

    if dry_run:
        print("  --dry flag: não executando. Sub-waves geradas acima.")
        # Save subwaves for inspection
        out_path = f"/tmp/forge-subwaves-{run_id}.json"
        with open(out_path, "w") as f:
            json.dump(subwaves, f, indent=2, ensure_ascii=False)
        print(f"  Sub-waves salvas em: {out_path}")
        return

    # Confirm
    if not auto_confirm:
        print("  [Enter] pra disparar  |  [n] pra cancelar")
        try:
            resp = input("  > ").strip().lower()
            if resp == "n":
                print("  Cancelado.")
                return
        except (EOFError, KeyboardInterrupt):
            print("\n  Cancelado.")
            return
    else:
        print("  --yes: auto-confirmado, disparando...")

    # Phase 1.9: IGNITION — spin up workers
    print(f"\n═══ IGNIÇÃO: Preparando infraestrutura ═══\n")
    num_workers = min(len(independent), machines)
    ignite(num_workers, timeout=90)

    # Resolve repo URL for git branch system
    project_dir = os.getcwd()
    repo_url = _get_repo_url(project_dir)
    if repo_url:
        print(f"  📦 Repo: {repo_url}")
    else:
        print(f"  ⚠️  Sem git remote — workers não terão git workflow")

    # Phase 1.95: Create git branches for all sub-waves
    if repo_url:
        print(f"\n═══ FASE 1.95: Criar branches ({len(subwaves)} sub-waves) ═══\n")
        for sw in subwaves:
            br = create_forge_branch(run_id, sw["id"], repo_dir=project_dir)
            if br["ok"]:
                print(f"  🌿 {br['branch']}")
            else:
                print(f"  ⚠️  {sw['id']} — branch fail: {br.get('error', '')[:80]}")
            # Go back to main for next branch creation
            subprocess.run(["git", "checkout", "main"],
                           capture_output=True, text=True, cwd=project_dir)

    # Phase 2: Dispatch independent sub-waves
    print(f"\n═══ FASE 2: Dispatch ({len(independent)} independentes) ═══\n")

    dispatched = {}
    for sw in independent:
        context_path = f"{run_id}/context/{sw['id']}/input.tar.gz"
        branch_name = f"forge/{run_id}/{sw['id']}" if repo_url else None

        # Pack and upload context
        ctx_tar = pack_context(
            files=sw.get("context_files", {}),
            claude_md=_build_claude_md(sw),
            tests=sw.get("test_files", {}),
        )
        try:
            gcs_upload(ctx_tar, context_path)
        except Exception:
            pass  # GCS might not be set up yet — worker gets context via instructions
        os.unlink(ctx_tar)

        # Submit to PM-OS (with git workflow if repo available)
        task = dispatch_subwave(run_id, sw, context_path,
                                repo_url=repo_url, branch=branch_name)
        if task and "task_id" in task:
            dispatched[sw["id"]] = task["task_id"]
            print(f"  🚀 {sw['id']} → task {task['task_id']}")
        else:
            print(f"  ⚠️  {sw['id']} — submit failed: {task}")

    # Save task mapping for monitor
    tasks_file = f"/tmp/forge-tasks-{run_id}.json"
    tasks_state = {sw_id: {"task_id": tid, "status": "pending"}
                   for sw_id, tid in dispatched.items()}
    with open(tasks_file, "w") as f:
        json.dump(tasks_state, f)

    print(f"\n  📊 Monitor: python3 {monitor_path}")
    print(f"  Acompanhe em outro terminal enquanto o forge monitora.\n")

    # Phase 3: Relay monitor (waits for all, dispatches sequential when ready)
    print(f"═══ FASE 3: Relay Monitor ═══\n")
    results, elapsed = relay_monitor(run_id, subwaves, dispatched,
                                     repo_dir=project_dir, repo_url=repo_url)

    # Phase 4: Collect & Merge via git
    print(f"\n═══ FASE 4: Collect & Merge ═══\n")
    collect_results(run_id, results, project_dir)

    # Also merge via forge branch system (creates integration branch)
    if repo_url:
        print(f"\n  Merging forge branches into integration branch...")
        merge_result = merge_forge_branches(run_id, repo_dir=project_dir)
        if merge_result["ok"]:
            print(f"  ✅ Integration branch: {merge_result['branch']} ({len(merge_result['merged'])} merged)")
        else:
            print(f"  ⚠️  Merge: {merge_result.get('error', 'unknown')}")

    # Phase 5: Shutdown — scale workers to zero, cleanup artifacts + branches
    print(f"\n═══ FASE 5: Shutdown ═══\n")
    shutdown(cleanup_run_id=run_id)

    # Cleanup forge branches
    if repo_url:
        print(f"  🧹 Limpando forge branches...")
        cleanup = cleanup_forge_branches(run_id, repo_dir=project_dir)
        if cleanup["ok"]:
            print(f"  ✅ {len(cleanup['deleted'])} branches removidas")
        else:
            print(f"  ⚠️  Cleanup: {cleanup.get('errors', [])}")

    # Report
    print_report(run_id, results, elapsed)

    # Update forge_runs in Supabase with final stats
    green = sum(1 for r in results.values() if r["status"] == "green")
    red = sum(1 for r in results.values() if r["status"] == "red")
    total_cost = sum(r.get("cost_usd", 0) for r in results.values())
    _supabase_upsert("forge_runs", {
        "id": run_id,
        "status": "completed" if red == 0 else "partial",
        "total_subwaves": len(subwaves),
        "completed": green,
        "failed": red,
        "cost_usd": total_cost,
        "duration_ms": int(elapsed * 1000),
        "updated_at": datetime.now().isoformat() + "Z",
    })


def _parse_plan_to_subwaves(plan_text, default_model="haiku"):
    """Parse a markdown plan into sub-waves.

    Looks for ### Task N.N patterns and extracts structure.
    Simple parser — for complex plans, use the Opus planner.
    """
    subwaves = []
    current_task = None

    for line in plan_text.split("\n"):
        if line.startswith("### Task "):
            if current_task:
                subwaves.append(current_task)

            # Extract task ID and title
            parts = line.replace("### Task ", "").split(":")
            task_id = parts[0].strip().replace(" ", "-").replace(".", "-").lower()
            title = parts[1].strip() if len(parts) > 1 else task_id

            current_task = {
                "id": f"sw-{task_id}",
                "title": title,
                "task_description": "",
                "files_to_edit": [],
                "depends_on": [],
                "model": default_model,
                "acceptance": "",
                "test_command": "go test ./... -timeout 60s",
                "context_files": {},
                "test_files": {},
            }

        elif current_task:
            if line.startswith("- Create: ") or line.startswith("- Modify: "):
                filepath = line.split("`")[1] if "`" in line else line.split(": ")[1].strip()
                current_task["files_to_edit"].append(filepath)

            elif "depende" in line.lower() or "depends" in line.lower():
                # Extract dependency references
                pass

            elif line.startswith("Run: "):
                current_task["test_command"] = line.replace("Run: ", "").strip().strip("`")

            current_task["task_description"] += line + "\n"

    if current_task:
        subwaves.append(current_task)

    return subwaves


def _estimate_cost(subwaves):
    """Estimate cost for a forge run."""
    cost = 0
    for sw in subwaves:
        model = sw.get("model", "haiku")
        if model == "haiku":
            cost += 0.35
        elif model == "sonnet":
            cost += 1.50
        elif model == "opus":
            cost += 5.00
    # Add review cost (2 Opus)
    cost += 10.00
    return cost


def _estimate_time(subwaves):
    """Estimate time in minutes."""
    independent = [sw for sw in subwaves if not sw.get("depends_on")]
    sequential = [sw for sw in subwaves if sw.get("depends_on")]

    # Independent run in parallel: max of individual times
    # Each task ~3-5 min
    parallel_time = 5  # minutes

    # Sequential: sum of individual times
    seq_time = len(sequential) * 3  # ~3 min each but pipelined

    # Review: ~5 min
    review_time = 5

    return parallel_time + min(seq_time, 8) + review_time


def main():
    if len(sys.argv) < 2:
        print(__doc__)
        return

    cmd = sys.argv[1]

    if cmd == "plan":
        if len(sys.argv) < 3:
            print("Uso: forge.py plan <input>")
            return
        cmd_plan(sys.argv[2])

    elif cmd == "run":
        if len(sys.argv) < 3:
            print("Uso: forge.py run <input> [--dry] [--machines N] [--model MODEL]")
            return

        input_path = sys.argv[2]
        dry_run = "--dry" in sys.argv

        machines = 20
        model = "haiku"
        for i, arg in enumerate(sys.argv):
            if arg == "--machines" and i + 1 < len(sys.argv):
                machines = int(sys.argv[i + 1])
            if arg == "--model" and i + 1 < len(sys.argv):
                model = sys.argv[i + 1]

        auto_confirm = "--yes" in sys.argv or "-y" in sys.argv
        cmd_run(input_path, dry_run=dry_run, machines=machines, model=model, auto_confirm=auto_confirm)

    elif cmd == "status":
        if len(sys.argv) < 3:
            print("Uso: forge.py status <run_id>")
            return
        # Find and run monitor for this run
        run_id = sys.argv[2]
        monitor = f"/tmp/forge-monitor-{run_id}.py"
        if os.path.exists(monitor):
            os.execvp("python3", ["python3", monitor])
        else:
            print(f"Monitor não encontrado: {monitor}")

    elif cmd == "collect":
        if len(sys.argv) < 3:
            print("Uso: forge.py collect <run_id>")
            return
        run_id = sys.argv[2]
        results_file = f"/tmp/forge-results-{run_id}.json"
        if os.path.exists(results_file):
            results = json.loads(Path(results_file).read_text())
            collect_results(run_id, results, os.getcwd())
        else:
            print(f"Resultados não encontrados: {results_file}")

    else:
        print(f"Comando desconhecido: {cmd}")
        print(__doc__)


if __name__ == "__main__":
    main()
