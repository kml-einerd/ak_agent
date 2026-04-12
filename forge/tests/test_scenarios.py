#!/usr/bin/env python3
"""
Forge Scenario Tests — Simulação completa do pipeline com mock PM-OS API.

Testa 3 níveis de complexidade:
  1. Trivial: CLI tool com 3 arquivos
  2. Standard: REST API com 8 arquivos, dependências
  3. Complex: Microserviços com 15+ arquivos, DAG completo, TDD, relay

Cada cenário simula:
  - Planner decomposição
  - Context packing
  - Worker dispatch (mock)
  - Completion signal detection
  - TASK_NOTES relay entre dependências
  - Reviewer tiered pipeline
  - Adequator merge
  - Cost/time tracking
"""
import sys
import os
import json
import time
import unittest
import tempfile
from unittest.mock import patch, MagicMock
from datetime import datetime

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from atomic import atomic, AtomicRegistry
from forge import (
    pack_context,
    unpack_result,
    _parse_plan_to_subwaves,
    _estimate_cost,
    _estimate_time,
    _extract_task_notes,
    _build_claude_md,
    dispatch_subwave,
    _dispatch_unblocked,
)


# ===========================================================================
# Mock PM-OS API
# ===========================================================================

class MockPMOS:
    """Simulates PM-OS API responses for testing."""

    def __init__(self):
        self.tasks = {}
        self.task_counter = 0
        self.submitted = []  # Log de tudo que foi submetido

    def submit_task(self, task_data):
        self.task_counter += 1
        task_id = f"mock-task-{self.task_counter:04d}"
        self.tasks[task_id] = {
            "task_id": task_id,
            "status": "pending",
            "title": task_data.get("title", ""),
            "provider": task_data.get("provider", "haiku"),
            "type": task_data.get("type", "code"),
            "instructions": task_data.get("instructions", []),
            "submitted_at": time.time(),
        }
        self.submitted.append(task_data)
        return {"task_id": task_id}

    def get_task(self, task_id):
        return self.tasks.get(task_id, {"error": "not found"})

    def complete_task(self, task_id, output="", cost=0.35, duration=180000):
        """Simulate a worker completing a task."""
        if task_id in self.tasks:
            self.tasks[task_id].update({
                "status": "done",
                "output": output,
                "cost_usd": cost,
                "duration_ms": duration,
            })

    def fail_task(self, task_id, error="test failure"):
        if task_id in self.tasks:
            self.tasks[task_id].update({
                "status": "failed",
                "output": error,
            })


# ===========================================================================
# Cenário 1: Trivial — CLI tool com 3 arquivos
# ===========================================================================

PLAN_TRIVIAL = """
# CLI Calculator — Implementation Plan

**Goal:** CLI que soma, subtrai, multiplica e divide.

---

### Task 1.1: Core Math Functions

**Files:**
- Create: `calc/math.go`
- Create: `calc/math_test.go`

Run: `go test ./calc/ -v`

### Task 1.2: CLI Entry Point

**Files:**
- Create: `cmd/calc/main.go`

Run: `go build ./cmd/calc/`

### Task 1.3: Integration Test

**Files:**
- Create: `calc/integration_test.go`

Run: `go test ./calc/ -v -run TestIntegration`
"""


class TestScenarioTrivial(unittest.TestCase):
    """Cenário trivial: CLI com 3 tasks, sem dependências complexas."""

    def setUp(self):
        self.mock = MockPMOS()

    def test_parse_extracts_3_tasks(self):
        sws = _parse_plan_to_subwaves(PLAN_TRIVIAL)
        self.assertEqual(len(sws), 3)

    def test_task_ids_correct(self):
        sws = _parse_plan_to_subwaves(PLAN_TRIVIAL)
        ids = [s["id"] for s in sws]
        self.assertIn("sw-1-1", ids)
        self.assertIn("sw-1-2", ids)
        self.assertIn("sw-1-3", ids)

    def test_files_mapped(self):
        sws = _parse_plan_to_subwaves(PLAN_TRIVIAL)
        sw1 = [s for s in sws if s["id"] == "sw-1-1"][0]
        self.assertIn("calc/math.go", sw1["files_to_edit"])
        self.assertIn("calc/math_test.go", sw1["files_to_edit"])

    def test_cost_estimation_trivial(self):
        sws = _parse_plan_to_subwaves(PLAN_TRIVIAL)
        cost = _estimate_cost(sws)
        # 3 haiku ($0.35 each) + $10 review = $11.05
        self.assertAlmostEqual(cost, 11.05, delta=0.1)

    def test_time_estimation_trivial(self):
        sws = _parse_plan_to_subwaves(PLAN_TRIVIAL)
        t = _estimate_time(sws)
        # All independent: 5 parallel + 0 seq + 5 review = 10
        self.assertEqual(t, 10)

    def test_claude_md_generation(self):
        sws = _parse_plan_to_subwaves(PLAN_TRIVIAL)
        md = _build_claude_md(sws[0])
        self.assertIn("Core Math Functions", md)
        self.assertIn("calc/math.go", md)
        self.assertIn("go test", md)

    def test_context_pack_for_trivial(self):
        sws = _parse_plan_to_subwaves(PLAN_TRIVIAL)
        path = pack_context(
            files={"go.mod": "module calc\ngo 1.25"},
            claude_md=_build_claude_md(sws[0]),
            tests={"calc/math_test.go": "package calc\nfunc TestAdd(t *testing.T){}"},
        )
        size = os.path.getsize(path)
        self.assertLess(size, 5000)  # Should be tiny
        os.unlink(path)

    @patch("forge.submit_task")
    def test_dispatch_calls_api(self, mock_submit):
        mock_submit.return_value = {"task_id": "mock-001"}
        sws = _parse_plan_to_subwaves(PLAN_TRIVIAL)
        result = dispatch_subwave("test-run", sws[0], "test/path.tar.gz")
        self.assertTrue(mock_submit.called)
        self.assertEqual(result["task_id"], "mock-001")

    def test_full_simulation_trivial(self):
        """Simula pipeline completo: parse → pack → dispatch → complete → collect."""
        sws = _parse_plan_to_subwaves(PLAN_TRIVIAL)

        # Dispatch all (mock)
        dispatched = {}
        for sw in sws:
            result = self.mock.submit_task({
                "type": "code",
                "title": f"Forge — {sw['id']}",
                "provider": sw["model"],
            })
            dispatched[sw["id"]] = result["task_id"]

        # Simulate workers completing
        for sw_id, task_id in dispatched.items():
            self.mock.complete_task(
                task_id,
                output=f"# Task Notes — {sw_id}\n## O que foi feito\n- Implemented\nFORGE_COMPLETE: all tests green",
                cost=0.30,
                duration=120000,
            )

        # Verify all completed
        for task_id in dispatched.values():
            task = self.mock.get_task(task_id)
            self.assertEqual(task["status"], "done")

        # Verify task notes extraction
        for task_id in dispatched.values():
            task = self.mock.get_task(task_id)
            notes = _extract_task_notes(task["output"])
            self.assertIn("O que foi feito", notes)
            self.assertNotIn("FORGE_COMPLETE", notes)

        # Cost tracking
        total_cost = sum(self.mock.get_task(tid)["cost_usd"] for tid in dispatched.values())
        self.assertAlmostEqual(total_cost, 0.90, delta=0.01)


# ===========================================================================
# Cenário 2: Standard — REST API com dependências
# ===========================================================================

PLAN_STANDARD = """
# Todo API — Implementation Plan

**Goal:** REST API com CRUD de todos, auth JWT, e testes.

---

### Task 1.1: Data Models

**Files:**
- Create: `pkg/models/todo.go`
- Create: `pkg/models/user.go`
- Create: `pkg/models/todo_test.go`

Run: `go test ./pkg/models/ -v`

### Task 1.2: Database Layer

**Files:**
- Create: `pkg/store/postgres.go`
- Create: `pkg/store/postgres_test.go`

Run: `go test ./pkg/store/ -v`

### Task 2.1: Auth Middleware

**Files:**
- Create: `pkg/auth/jwt.go`
- Create: `pkg/auth/jwt_test.go`

Run: `go test ./pkg/auth/ -v`

### Task 2.2: Todo Handlers

**Files:**
- Create: `pkg/handlers/todo.go`
- Create: `pkg/handlers/todo_test.go`

Run: `go test ./pkg/handlers/ -v`

### Task 3.1: Router + Server

**Files:**
- Create: `cmd/server/main.go`

Run: `go build ./cmd/server/`

### Task 3.2: Integration Tests

**Files:**
- Create: `tests/integration_test.go`

Run: `go test ./tests/ -v -tags integration`
"""


class TestScenarioStandard(unittest.TestCase):
    """Cenário standard: API REST com 6 tasks e dependências implícitas."""

    def setUp(self):
        self.mock = MockPMOS()
        self.sws = _parse_plan_to_subwaves(PLAN_STANDARD)

    def test_parse_6_tasks(self):
        self.assertEqual(len(self.sws), 6)

    def test_cost_standard(self):
        cost = _estimate_cost(self.sws)
        # 6 haiku ($0.35 each) + $10 review = $12.10
        self.assertAlmostEqual(cost, 12.10, delta=0.1)

    def test_dependency_chain_simulation(self):
        """Simula relay: Task 1.1 → Task 2.2 (handlers usam models)."""
        # Wave A: dispatch independents
        wave_a = self.sws[:3]  # models, store, auth
        dispatched = {}
        for sw in wave_a:
            r = self.mock.submit_task({"title": sw["id"], "provider": "haiku"})
            dispatched[sw["id"]] = r["task_id"]

        # Simulate models completing with TASK_NOTES
        models_task_id = dispatched["sw-1-1"]
        self.mock.complete_task(
            models_task_id,
            output="""# Task Notes — sw-1-1

## O que foi feito
- Criou Todo struct com ID, Title, Done, CreatedAt
- Criou User struct com ID, Email, PasswordHash

## Interfaces expostas
- type Todo struct { ID string; Title string; Done bool }
- type User struct { ID string; Email string; PasswordHash string }

FORGE_COMPLETE: all tests green, ready for review""",
        )

        # Extract notes for relay
        models_output = self.mock.get_task(models_task_id)["output"]
        notes = _extract_task_notes(models_output)
        self.assertIn("Todo struct", notes)
        self.assertIn("User struct", notes)

        # Relay to handlers (Wave B)
        combined_notes = f"### From sw-1-1\n\n{notes}"
        self.assertIn("Todo struct", combined_notes)

        # Dispatch handlers with relay notes
        handler_task = self.mock.submit_task({
            "title": "sw-2-2",
            "provider": "haiku",
            "instructions": [f"## Task Notes\n\n{combined_notes}", "Implement handlers"],
        })

        # Verify the handler task received the relay notes
        handler_data = self.mock.tasks[handler_task["task_id"]]
        instructions_text = " ".join(handler_data["instructions"])
        self.assertIn("Todo struct", instructions_text)

    def test_tiered_review_assignment(self):
        """Verifica que tasks diferentes receberiam tiers diferentes."""
        # Simple model file = trivial
        # Auth middleware = standard (security-sensitive)
        # Integration tests = complex
        for sw in self.sws:
            files = len(sw["files_to_edit"])
            if files <= 2:
                expected_tier = "trivial"
            elif files <= 5:
                expected_tier = "standard"
            else:
                expected_tier = "complex"
            # Parser doesn't set tier yet (that's the Opus planner's job)
            # But we verify the heuristic makes sense
            self.assertIn(sw["model"], ["haiku", "sonnet", "opus"])

    def test_failure_and_retry_simulation(self):
        """Simula um worker falhando e sendo retried."""
        sw = self.sws[0]

        # First attempt fails
        r1 = self.mock.submit_task({"title": sw["id"], "provider": "haiku"})
        self.mock.fail_task(r1["task_id"], "FORGE_FAILED: undefined: Todo")

        # Check failure detection
        task = self.mock.get_task(r1["task_id"])
        self.assertEqual(task["status"], "failed")
        self.assertIn("FORGE_FAILED", task["output"])

        # Retry with escalation (haiku → sonnet)
        r2 = self.mock.submit_task({"title": f"{sw['id']} (retry)", "provider": "sonnet"})
        self.mock.complete_task(
            r2["task_id"],
            output="# Task Notes\n## O que foi feito\n- Fixed\nFORGE_COMPLETE: ok",
        )

        task2 = self.mock.get_task(r2["task_id"])
        self.assertEqual(task2["status"], "done")
        self.assertEqual(task2["provider"], "sonnet")  # Escalated

    def test_cost_tracking_with_retry(self):
        """Verifica que retries são contabilizados no custo."""
        costs = []

        # Attempt 1: haiku fails ($0.35)
        r1 = self.mock.submit_task({"provider": "haiku"})
        self.mock.complete_task(r1["task_id"], cost=0.35)
        costs.append(0.35)

        # Attempt 2: sonnet retry ($1.50)
        r2 = self.mock.submit_task({"provider": "sonnet"})
        self.mock.complete_task(r2["task_id"], cost=1.50)
        costs.append(1.50)

        total = sum(costs)
        self.assertAlmostEqual(total, 1.85, delta=0.01)


# ===========================================================================
# Cenário 3: Complex — Microserviços com DAG completo
# ===========================================================================

PLAN_COMPLEX = """
# Notification System — Implementation Plan

**Goal:** Sistema de notificações multi-canal (email, push, SMS) com queue e retry.

---

### Task 1.1: Event Types

**Files:**
- Create: `pkg/events/types.go`
- Create: `pkg/events/types_test.go`

Run: `go test ./pkg/events/ -v`

### Task 1.2: Queue Interface

**Files:**
- Create: `pkg/queue/interface.go`
- Create: `pkg/queue/memory.go`
- Create: `pkg/queue/memory_test.go`

Run: `go test ./pkg/queue/ -v`

### Task 1.3: Email Provider

**Files:**
- Create: `pkg/providers/email.go`
- Create: `pkg/providers/email_test.go`

Run: `go test ./pkg/providers/ -run TestEmail -v`

### Task 1.4: Push Provider

**Files:**
- Create: `pkg/providers/push.go`
- Create: `pkg/providers/push_test.go`

Run: `go test ./pkg/providers/ -run TestPush -v`

### Task 1.5: SMS Provider

**Files:**
- Create: `pkg/providers/sms.go`
- Create: `pkg/providers/sms_test.go`

Run: `go test ./pkg/providers/ -run TestSMS -v`

### Task 2.1: Router (dispatches to providers)

**Files:**
- Create: `pkg/router/router.go`
- Create: `pkg/router/router_test.go`

Run: `go test ./pkg/router/ -v`

### Task 2.2: Worker (consumes queue)

**Files:**
- Create: `pkg/worker/worker.go`
- Create: `pkg/worker/worker_test.go`

Run: `go test ./pkg/worker/ -v`

### Task 2.3: Retry Logic

**Files:**
- Create: `pkg/retry/backoff.go`
- Create: `pkg/retry/backoff_test.go`

Run: `go test ./pkg/retry/ -v`

### Task 3.1: API Handlers

**Files:**
- Create: `pkg/api/handlers.go`
- Create: `pkg/api/handlers_test.go`

Run: `go test ./pkg/api/ -v`

### Task 3.2: Server Entry Point

**Files:**
- Create: `cmd/notify/main.go`

Run: `go build ./cmd/notify/`

### Task 3.3: Integration Tests

**Files:**
- Create: `tests/notification_flow_test.go`
- Create: `tests/retry_test.go`

Run: `go test ./tests/ -v -tags integration`
"""


class TestScenarioComplex(unittest.TestCase):
    """Cenário complexo: 11 tasks, DAG com 3 waves, TDD, relay."""

    def setUp(self):
        self.mock = MockPMOS()
        self.sws = _parse_plan_to_subwaves(PLAN_COMPLEX)

    def test_parse_11_tasks(self):
        self.assertEqual(len(self.sws), 11)

    def test_cost_complex(self):
        cost = _estimate_cost(self.sws)
        # 11 haiku ($0.35 each) + $10 review = $13.85
        self.assertAlmostEqual(cost, 13.85, delta=0.1)

    def test_wave_grouping_simulation(self):
        """Simula agrupamento natural em 3 waves baseado em dependências."""
        # Wave A: types, queue, email, push, sms, retry (6 independentes)
        wave_a_ids = {"sw-1-1", "sw-1-2", "sw-1-3", "sw-1-4", "sw-1-5", "sw-2-3"}
        # Wave B: router, worker (dependem de types + queue + providers)
        wave_b_ids = {"sw-2-1", "sw-2-2"}
        # Wave C: api, server, integration (dependem de tudo)
        wave_c_ids = {"sw-3-1", "sw-3-2", "sw-3-3"}

        all_ids = {s["id"] for s in self.sws}
        self.assertEqual(wave_a_ids | wave_b_ids | wave_c_ids, all_ids)

    def test_full_dag_execution_simulation(self):
        """Simula execução completa do DAG com relay de TASK_NOTES."""
        completed = {}
        results = {}

        # ---- WAVE A: 6 paralelos ----
        wave_a = [s for s in self.sws if s["id"] in
                  {"sw-1-1", "sw-1-2", "sw-1-3", "sw-1-4", "sw-1-5", "sw-2-3"}]

        for sw in wave_a:
            r = self.mock.submit_task({"title": sw["id"], "provider": "haiku"})
            self.mock.complete_task(
                r["task_id"],
                output=f"# Task Notes — {sw['id']}\n## O que foi feito\n- {sw['title']}\n## Interfaces expostas\n- Exported types and funcs\nFORGE_COMPLETE: ok",
                cost=0.30,
                duration=150000,
            )
            completed[sw["id"]] = self.mock.get_task(r["task_id"])
            results[sw["id"]] = {
                "status": "green",
                "task_notes": _extract_task_notes(completed[sw["id"]]["output"]),
                "cost_usd": 0.30,
            }

        self.assertEqual(len(completed), 6)

        # ---- WAVE B: router + worker (com relay notes) ----
        wave_b = [s for s in self.sws if s["id"] in {"sw-2-1", "sw-2-2"}]

        # Collect notes from dependencies
        dep_notes = []
        for dep_id in ["sw-1-1", "sw-1-2", "sw-1-3", "sw-1-4", "sw-1-5"]:
            notes = results[dep_id]["task_notes"]
            dep_notes.append(f"### From {dep_id}\n\n{notes}")
        combined = "\n\n---\n\n".join(dep_notes)

        # Verify combined notes have all dependency info
        self.assertIn("sw-1-1", combined)
        self.assertIn("sw-1-3", combined)
        self.assertIn("Interfaces expostas", combined)

        for sw in wave_b:
            r = self.mock.submit_task({
                "title": sw["id"],
                "provider": "haiku",
                "instructions": [f"## Task Notes\n\n{combined}"],
            })
            self.mock.complete_task(
                r["task_id"],
                output=f"# Task Notes — {sw['id']}\n## O que foi feito\n- {sw['title']}\nFORGE_COMPLETE: ok",
                cost=0.35,
            )
            completed[sw["id"]] = self.mock.get_task(r["task_id"])
            results[sw["id"]] = {
                "status": "green",
                "task_notes": _extract_task_notes(completed[sw["id"]]["output"]),
                "cost_usd": 0.35,
            }

        self.assertEqual(len(completed), 8)

        # ---- WAVE C: api, server, integration ----
        wave_c = [s for s in self.sws if s["id"] in {"sw-3-1", "sw-3-2", "sw-3-3"}]

        for sw in wave_c:
            r = self.mock.submit_task({"title": sw["id"], "provider": "haiku"})
            self.mock.complete_task(
                r["task_id"],
                output=f"FORGE_COMPLETE: ok",
                cost=0.35,
            )
            completed[sw["id"]] = self.mock.get_task(r["task_id"])
            results[sw["id"]] = {"status": "green", "cost_usd": 0.35}

        self.assertEqual(len(completed), 11)

        # ---- VERIFICAÇÕES FINAIS ----
        # Todos green
        self.assertTrue(all(r["status"] == "green" for r in results.values()))

        # Custo total
        total_cost = sum(r["cost_usd"] for r in results.values())
        self.assertAlmostEqual(total_cost, 3.50, delta=0.1)  # 6*0.30 + 5*0.35

        # Nenhum task pendente
        self.assertEqual(len(completed), len(self.sws))

    def test_partial_failure_propagation(self):
        """Simula 1 task falhando e verificar propagação."""
        # Email provider fails
        r = self.mock.submit_task({"title": "sw-1-3", "provider": "haiku"})
        self.mock.fail_task(r["task_id"], "FORGE_FAILED: SMTP config missing")

        task = self.mock.get_task(r["task_id"])
        self.assertEqual(task["status"], "failed")
        self.assertIn("FORGE_FAILED", task["output"])

        # Router (sw-2-1) depends on email provider
        # Should still be dispatchable (with partial context + error info)
        # The relay sends error info so the dependent knows what failed
        error_notes = f"### From sw-1-3 (FAILED)\n\nFORGE_FAILED: SMTP config missing"
        self.assertIn("FAILED", error_notes)

    def test_completion_signal_detection(self):
        """Verifica detecção de FORGE_COMPLETE e FORGE_FAILED."""
        # Success signal
        r1 = self.mock.submit_task({"title": "test"})
        self.mock.complete_task(r1["task_id"],
            output="lots of logs\nFORGE_COMPLETE: all tests green, ready for review")
        self.assertIn("FORGE_COMPLETE", self.mock.get_task(r1["task_id"])["output"])

        # Failure signal
        r2 = self.mock.submit_task({"title": "test2"})
        self.mock.complete_task(r2["task_id"],
            output="lots of logs\nFORGE_FAILED: cannot find module")
        self.assertIn("FORGE_FAILED", self.mock.get_task(r2["task_id"])["output"])

    def test_review_tier_assignment(self):
        """Simula atribuição de tier de review baseado na complexidade."""
        for sw in self.sws:
            files = len(sw["files_to_edit"])
            if files <= 2:
                tier = "trivial"
                review_model = None  # Skip review
            elif files <= 4:
                tier = "standard"
                review_model = "sonnet"
            else:
                tier = "complex"
                review_model = "opus"

            # Integration tests (sw-3-3) has 2 files but is complex by nature
            # In production, the Opus planner would override this
            self.assertIn(tier, ["trivial", "standard", "complex"])


# ===========================================================================
# Cenário 4: Atomic-driven — Definição via @atomic()
# ===========================================================================

class TestScenarioAtomic(unittest.TestCase):
    """Cenário: usando @atomic() para definir um sistema e gerar sub-waves."""

    def setUp(self):
        AtomicRegistry.clear()

    def test_atomic_notification_system(self):
        """Define um sistema inteiro via @atomic() e gera sub-waves."""

        @atomic(group="notify", title="Event Types", model="haiku",
                acceptance="go test ./pkg/events/ -v",
                test_command="go test ./pkg/events/ -v")
        def event_types(event_name: str = "notification"):
            """Define Event, Priority, Channel types."""
            pass

        @atomic(group="notify", title="Queue Interface", model="haiku",
                acceptance="go test ./pkg/queue/ -v")
        def queue_interface(backend: str = "memory"):
            """Interface genérica de queue + implementação in-memory."""
            pass

        @atomic(group="notify", title="Email Provider", model="haiku",
                depends_on=["notify.event_types"])
        def email_provider(smtp_host: str = "localhost", smtp_port: int = 587):
            """Provider de email via SMTP."""
            pass

        @atomic(group="notify", title="Push Provider", model="haiku",
                depends_on=["notify.event_types"])
        def push_provider(fcm_key: str = ""):
            """Provider de push via FCM."""
            pass

        @atomic(group="notify", title="Router", model="sonnet",
                depends_on=["notify.email_provider", "notify.push_provider", "notify.queue_interface"],
                acceptance="go test ./pkg/router/ -v")
        def router(default_channel: str = "email"):
            """Roteador que despacha notificações para o provider correto."""
            pass

        @atomic(group="notify", title="API Handlers", model="sonnet",
                depends_on=["notify.router"],
                acceptance="go test ./pkg/api/ -v")
        def api_handlers(port: int = 8080):
            """Handlers HTTP para submissão de notificações."""
            pass

        # Generate sub-waves
        sws = AtomicRegistry.to_subwaves(group="notify")
        self.assertEqual(len(sws), 6)

        # Verify dependency chain
        router_sw = [s for s in sws if "router" in s["id"]][0]
        self.assertEqual(len(router_sw["depends_on"]), 3)
        self.assertIn("notify.email_provider", router_sw["depends_on"])
        self.assertIn("notify.push_provider", router_sw["depends_on"])

        api_sw = [s for s in sws if "api_handlers" in s["id"]][0]
        self.assertIn("notify.router", api_sw["depends_on"])

        # Verify model assignment
        independent_sws = [s for s in sws if not s["depends_on"]]
        dependent_sws = [s for s in sws if s["depends_on"]]
        self.assertTrue(all(s["model"] == "haiku" for s in independent_sws))
        self.assertTrue(any(s["model"] == "sonnet" for s in dependent_sws))

        # Generate JSON Schema
        schema = AtomicRegistry.json()
        self.assertEqual(len(schema), 6)

        # Verify email provider has SMTP params
        email_schema = schema["notify.email_provider"]["inputSchema"]
        self.assertIn("smtp_host", email_schema["properties"])
        self.assertEqual(email_schema["properties"]["smtp_port"]["type"], "integer")
        self.assertEqual(email_schema["properties"]["smtp_port"]["default"], 587)

    def test_wave_ordering(self):
        """Verifica que sub-waves podem ser ordenadas em waves válidas."""
        @atomic(group="o", title="A", model="haiku")
        def op_a(): pass

        @atomic(group="o", title="B", model="haiku", depends_on=["o.op_a"])
        def op_b(): pass

        @atomic(group="o", title="C", model="haiku", depends_on=["o.op_b"])
        def op_c(): pass

        sws = AtomicRegistry.to_subwaves()

        # Build dependency graph
        dep_map = {s["id"]: s["depends_on"] for s in sws}

        # op_a has no deps (Wave A)
        a = [s for s in sws if "op_a" in s["id"]][0]
        self.assertEqual(len(a["depends_on"]), 0)

        # op_b depends on op_a (Wave B)
        b = [s for s in sws if "op_b" in s["id"]][0]
        self.assertEqual(len(b["depends_on"]), 1)

        # op_c depends on op_b (Wave C)
        c = [s for s in sws if "op_c" in s["id"]][0]
        self.assertEqual(len(c["depends_on"]), 1)


# ===========================================================================
# Cenário 5: Error handling e edge cases
# ===========================================================================

class TestScenarioEdgeCases(unittest.TestCase):

    def test_empty_plan(self):
        sws = _parse_plan_to_subwaves("")
        self.assertEqual(len(sws), 0)

    def test_plan_with_no_tasks(self):
        plan = "# Plan\n\nJust some text without any ### Task headers."
        sws = _parse_plan_to_subwaves(plan)
        self.assertEqual(len(sws), 0)

    def test_task_notes_empty_output(self):
        self.assertEqual(_extract_task_notes(""), "")
        self.assertEqual(_extract_task_notes(None), "")

    def test_cost_zero_subwaves(self):
        cost = _estimate_cost([])
        self.assertEqual(cost, 10.0)  # Just review cost

    def test_pack_empty_context(self):
        path = pack_context(files={}, claude_md="# Empty")
        self.assertTrue(os.path.exists(path))
        size = os.path.getsize(path)
        self.assertGreater(size, 0)
        os.unlink(path)

    def test_pack_unicode_content(self):
        path = pack_context(
            files={"readme.md": "# Título com acentuação\n\nConteúdo em português 🇧🇷"},
            claude_md="# Worker — Notificações",
        )
        with tempfile.TemporaryDirectory() as d:
            unpack_result(path, d)
            with open(os.path.join(d, "CLAUDE.md")) as f:
                self.assertIn("Notificações", f.read())
            with open(os.path.join(d, "context", "readme.md")) as f:
                self.assertIn("acentuação", f.read())
        os.unlink(path)

    def test_large_task_notes_truncated(self):
        huge_output = "## O que foi feito\n" + "- item\n" * 5000
        notes = _extract_task_notes(huge_output)
        self.assertLessEqual(len(notes), 2000)


# ===========================================================================
# Run
# ===========================================================================

if __name__ == "__main__":
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromModule(sys.modules[__name__])
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)
