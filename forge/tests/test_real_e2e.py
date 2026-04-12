#!/usr/bin/env python3
"""
Forge Real E2E Tests — Submete tasks reais ao PM-OS API.

Testa 3 mini-aplicações com complexidades diferentes:
  1. Trivial: Utility function (1 task)
  2. Standard: Data pipeline com 3 tasks
  3. Complex: Micro API com 5 tasks e dependências

Cada teste:
  - Parseia um plano
  - Pack context
  - Submete ao PM-OS real
  - Verifica status
  - Extrai métricas
"""
import sys
import os
import json
import time
import unittest

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import forge

# Force real API
forge.PM_API_URL = "https://pm-api-852176378633.us-central1.run.app"
forge.PM_API_KEY = ""

from forge import (
    submit_task,
    get_task,
    pack_context,
    _parse_plan_to_subwaves,
    _build_claude_md,
    _estimate_cost,
    _extract_task_notes,
)
from atomic import atomic, AtomicRegistry


class TestRealSubmit(unittest.TestCase):
    """Testa submit real ao PM-OS."""

    def test_submit_and_poll(self):
        """Submit uma task e verifica que ela aparece no PM-OS."""
        result = submit_task({
            "type": "code",
            "title": "Forge E2E — test_submit_and_poll",
            "agent": "dex",
            "provider": "haiku",
            "instructions": ["Return: FORGE_TEST_OK"],
            "acceptance": "Output contains FORGE_TEST_OK",
        })
        self.assertIn("task_id", result, f"Submit failed: {result}")
        self.assertIsNotNone(result["task_id"])

        # Poll
        time.sleep(2)
        status = get_task(result["task_id"])
        self.assertIn("id", status)
        self.assertIn(status["status"], ("pending", "running", "done", "passed", "failed"))
        print(f"    task_id={result['task_id']} status={status['status']}")


class TestRealTrivial(unittest.TestCase):
    """Mini-app trivial: StringUtils — 1 task."""

    PLAN = """
### Task 1.1: String Utils Package

**Files:**
- Create: `pkg/stringutils/utils.go`
- Create: `pkg/stringutils/utils_test.go`

Run: `go test ./pkg/stringutils/ -v`
"""

    def test_parse_and_submit(self):
        sws = _parse_plan_to_subwaves(self.PLAN)
        self.assertEqual(len(sws), 1)

        sw = sws[0]
        claude_md = _build_claude_md(sw)

        # Pack context
        tar_path = pack_context(
            files={"go.mod": "module forge-test-trivial\ngo 1.25"},
            claude_md=claude_md,
            tests={"pkg/stringutils/utils_test.go": """package stringutils

import "testing"

func TestReverse(t *testing.T) {
    if Reverse("hello") != "olleh" {
        t.Fatal("Reverse failed")
    }
}

func TestCapitalize(t *testing.T) {
    if Capitalize("hello world") != "Hello World" {
        t.Fatal("Capitalize failed")
    }
}
"""},
        )
        size = os.path.getsize(tar_path)
        self.assertLess(size, 5000)
        os.unlink(tar_path)

        # Submit to real PM-OS
        result = submit_task({
            "type": "code",
            "title": f"Forge Trivial — {sw['id']}: {sw['title']}",
            "agent": "dex",
            "provider": "haiku",
            "instructions": [
                f"## CLAUDE.md\n{claude_md}",
                "Implement Reverse(s string) string and Capitalize(s string) string in Go.",
                "Make the tests pass. Signal FORGE_COMPLETE when done.",
            ],
            "test_command": "go test ./pkg/stringutils/ -v",
            "acceptance": "All tests pass",
        })
        self.assertIn("task_id", result, f"Submit failed: {result}")
        print(f"    Trivial submitted: {result['task_id']}")

        time.sleep(2)
        status = get_task(result["task_id"])
        print(f"    Status: {status.get('status')}")
        self.assertIn(status["status"], ("pending", "running", "done", "passed", "failed"))


class TestRealStandard(unittest.TestCase):
    """Mini-app standard: Data Pipeline — 3 tasks com dependência."""

    def setUp(self):
        forge.PM_API_URL = "https://pm-api-852176378633.us-central1.run.app"
        forge.PM_API_KEY = ""

    PLAN = """
### Task 1.1: Data Types

**Files:**
- Create: `pkg/pipeline/types.go`
- Create: `pkg/pipeline/types_test.go`

Run: `go test ./pkg/pipeline/ -run TestTypes -v`

### Task 1.2: Transformer

**Files:**
- Create: `pkg/pipeline/transform.go`
- Create: `pkg/pipeline/transform_test.go`

Run: `go test ./pkg/pipeline/ -run TestTransform -v`

### Task 2.1: Pipeline Runner

**Files:**
- Create: `pkg/pipeline/runner.go`
- Create: `pkg/pipeline/runner_test.go`

Run: `go test ./pkg/pipeline/ -run TestRunner -v`
"""

    def test_parse_and_submit_with_dependency(self):
        sws = _parse_plan_to_subwaves(self.PLAN)
        self.assertEqual(len(sws), 3)

        submitted = []
        for i, sw in enumerate(sws):
            result = submit_task({
                "type": "code",
                "title": f"Forge Standard — {sw['id']}: {sw['title']}",
                "agent": "dex",
                "provider": "haiku",
                "instructions": [
                    f"Task {i+1}/3 of data pipeline.",
                    f"Implement: {sw['title']}",
                    f"Files: {', '.join(sw['files_to_edit'])}",
                    "Signal FORGE_COMPLETE when done.",
                ],
                "acceptance": sw.get("acceptance") or sw.get("test_command") or "Tests pass",
            })
            tid = result.get("task_id")
            submitted.append({"sw_id": sw["id"], "task_id": tid})
            print(f"    {sw['id']}: {tid}")
            time.sleep(0.5)  # Small delay between rapid submissions

        self.assertEqual(len(submitted), 3)
        self.assertTrue(all(s["task_id"] for s in submitted), f"Some tasks failed: {submitted}")

        # Poll all
        time.sleep(3)
        for item in submitted:
            status = get_task(item["task_id"])
            s = status.get("status", "?")
            print(f"    {item['sw_id']}: {s}")
            self.assertIn(s, ("pending", "running", "done", "passed", "failed"))

    def test_relay_simulation_real(self):
        """Simula TASK_NOTES relay entre tasks 1.1 → 2.1."""
        # Task 1.1 completes with notes
        r1 = submit_task({
            "type": "code",
            "title": "Forge Relay Test — types",
            "agent": "dex",
            "provider": "haiku",
            "instructions": [
                "Create type Record struct { ID string; Data map[string]interface{} }",
                "Create type Pipeline struct { Steps []Step }",
                "Output TASK_NOTES with interfaces.",
                "Signal FORGE_COMPLETE when done.",
            ],
            "acceptance": "Types defined",
        })
        self.assertIn("task_id", r1)

        # Task 2.1 receives relay notes
        fake_notes = """### From sw-1-1
## Interfaces expostas
- type Record struct { ID string; Data map[string]interface{} }
- type Pipeline struct { Steps []Step }
"""
        r2 = submit_task({
            "type": "code",
            "title": "Forge Relay Test — runner (with notes)",
            "agent": "dex",
            "provider": "haiku",
            "instructions": [
                f"## Task Notes from dependencies\n\n{fake_notes}",
                "Use the Record and Pipeline types from sw-1-1 to build RunPipeline().",
                "Signal FORGE_COMPLETE when done.",
            ],
            "acceptance": "Pipeline runs",
        })
        self.assertIn("task_id", r2)
        print(f"    Relay: types={r1['task_id']} → runner={r2['task_id']}")


class TestRealComplex(unittest.TestCase):
    """Mini-app complex: Micro API — 5 tasks, DAG completo."""

    PLAN = """
### Task 1.1: Config Package

**Files:**
- Create: `pkg/config/config.go`
- Create: `pkg/config/config_test.go`

Run: `go test ./pkg/config/ -v`

### Task 1.2: Logger Package

**Files:**
- Create: `pkg/log/logger.go`
- Create: `pkg/log/logger_test.go`

Run: `go test ./pkg/log/ -v`

### Task 2.1: HTTP Router

**Files:**
- Create: `pkg/router/router.go`
- Create: `pkg/router/router_test.go`

Run: `go test ./pkg/router/ -v`

### Task 2.2: Health Handler

**Files:**
- Create: `pkg/handlers/health.go`
- Create: `pkg/handlers/health_test.go`

Run: `go test ./pkg/handlers/ -v`

### Task 3.1: Server Entry Point

**Files:**
- Create: `cmd/api/main.go`

Run: `go build ./cmd/api/`
"""

    def test_full_complex_submission(self):
        sws = _parse_plan_to_subwaves(self.PLAN)
        self.assertEqual(len(sws), 5)

        cost = _estimate_cost(sws)
        print(f"    Estimated cost: ${cost:.2f}")

        # Group into waves
        wave_a = sws[:2]   # config, logger (independent)
        wave_b = sws[2:4]  # router, health (depend on config+logger)
        wave_c = sws[4:]   # server (depends on all)

        # Submit Wave A
        wave_a_tasks = []
        for sw in wave_a:
            r = submit_task({
                "type": "code",
                "title": f"Forge Complex WaveA — {sw['id']}",
                "agent": "dex",
                "provider": "haiku",
                "instructions": [f"Implement: {sw['title']}", "FORGE_COMPLETE when done."],
                "acceptance": "Tests pass",
            })
            self.assertIn("task_id", r, f"Failed: {r}")
            wave_a_tasks.append(r["task_id"])
            print(f"    Wave A: {sw['id']} → {r['task_id']}")

        # Submit Wave B (with relay context referencing Wave A)
        wave_b_tasks = []
        for sw in wave_b:
            r = submit_task({
                "type": "code",
                "title": f"Forge Complex WaveB — {sw['id']}",
                "agent": "dex",
                "provider": "haiku",
                "instructions": [
                    "## Dependencies: config and logger packages from Wave A are available.",
                    f"Implement: {sw['title']}",
                    "FORGE_COMPLETE when done.",
                ],
                "acceptance": "Tests pass",
            })
            self.assertIn("task_id", r, f"Failed: {r}")
            wave_b_tasks.append(r["task_id"])
            print(f"    Wave B: {sw['id']} → {r['task_id']}")

        # Submit Wave C
        for sw in wave_c:
            r = submit_task({
                "type": "code",
                "title": f"Forge Complex WaveC — {sw['id']}",
                "agent": "dex",
                "provider": "haiku",
                "instructions": [
                    "## Dependencies: all packages from Wave A and B.",
                    f"Implement: {sw['title']}",
                    "FORGE_COMPLETE when done.",
                ],
                "acceptance": "Build succeeds",
            })
            self.assertIn("task_id", r, f"Failed: {r}")
            print(f"    Wave C: {sw['id']} → {r['task_id']}")

        # Poll all
        time.sleep(3)
        all_tasks = wave_a_tasks + wave_b_tasks
        statuses = {}
        for tid in all_tasks:
            status = get_task(tid)
            statuses[tid] = status.get("status", "?")

        print(f"    Statuses: {statuses}")
        self.assertTrue(all(s in ("pending", "running", "done", "passed", "failed") for s in statuses.values()))


class TestRealAtomicDriven(unittest.TestCase):
    """Teste: definir via @atomic() e submeter sub-waves reais."""

    def setUp(self):
        AtomicRegistry.clear()

    def test_atomic_to_real_tasks(self):
        @atomic(group="auth", title="JWT Token", model="haiku",
                acceptance="go test ./pkg/auth/ -v",
                test_command="go test ./pkg/auth/ -v")
        def jwt_token(secret_key: str = "test-key", expiry_hours: int = 24):
            """Generate and validate JWT tokens."""
            pass

        @atomic(group="auth", title="Auth Middleware", model="haiku",
                depends_on=["auth.jwt_token"],
                acceptance="go test ./pkg/middleware/ -v")
        def auth_middleware(header_name: str = "Authorization"):
            """HTTP middleware that validates JWT from request headers."""
            pass

        # Generate sub-waves
        sws = AtomicRegistry.to_subwaves(group="auth")
        self.assertEqual(len(sws), 2)

        # Submit first (independent) sub-wave
        sw = sws[0]  # jwt_token (no deps)
        self.assertEqual(len(sw["depends_on"]), 0)

        result = submit_task({
            "type": "code",
            "title": f"Forge Atomic — {sw['id']}: {sw['title']}",
            "agent": "dex",
            "provider": sw["model"],
            "instructions": [
                f"Implement: {sw['task_description']}",
                "Signal FORGE_COMPLETE when done.",
            ],
            "acceptance": sw.get("acceptance", "Tests pass"),
        })
        self.assertIn("task_id", result)
        print(f"    Atomic jwt_token: {result['task_id']}")

        # Verify second has dependency
        sw2 = sws[1]  # auth_middleware (depends on jwt_token)
        self.assertEqual(sw2["depends_on"], ["auth.jwt_token"])

        result2 = submit_task({
            "type": "code",
            "title": f"Forge Atomic — {sw2['id']}: {sw2['title']}",
            "agent": "dex",
            "provider": sw2["model"],
            "instructions": [
                "## Dependencies: jwt_token package is available.",
                f"Implement: {sw2['task_description']}",
                "Signal FORGE_COMPLETE when done.",
            ],
            "acceptance": sw2.get("acceptance", "Tests pass"),
        })
        self.assertIn("task_id", result2)
        print(f"    Atomic auth_middleware: {result2['task_id']}")


class TestRealCostTracking(unittest.TestCase):
    """Verifica contabilidade de tasks submetidas."""

    def test_count_forge_tasks(self):
        """Conta quantas tasks Forge foram submetidas."""
        import urllib.request
        req = urllib.request.Request(f"{forge.PM_API_URL}/api/tasks")
        with urllib.request.urlopen(req, timeout=10) as resp:
            all_tasks = json.loads(resp.read().decode())

        if isinstance(all_tasks, list):
            forge_tasks = [t for t in all_tasks if "Forge" in (t.get("title") or "")]
            print(f"    Total tasks in PM-OS: {len(all_tasks)}")
            print(f"    Forge test tasks: {len(forge_tasks)}")
            for ft in forge_tasks[-5:]:
                print(f"      - {ft.get('title','?')[:50]}: {ft.get('status','?')}")
            self.assertGreater(len(forge_tasks), 0, "No forge tasks found")


if __name__ == "__main__":
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromModule(sys.modules[__name__])
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)
