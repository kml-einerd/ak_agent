#!/usr/bin/env python3
"""Run all Code Forge tests using unittest (no pytest dependency)."""
import sys
import os
import unittest
import json
import tempfile
import tarfile

# Add parent to path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

from atomic import atomic, AtomicRegistry, ParamMeta
from forge import (
    pack_context,
    unpack_result,
    _parse_plan_to_subwaves,
    _estimate_cost,
    _estimate_time,
    _extract_task_notes,
    _build_claude_md,
)


# ===========================================================================
# Atomic Tests
# ===========================================================================

class TestAtomicDecorator(unittest.TestCase):

    def setUp(self):
        AtomicRegistry.clear()

    def test_basic_registration(self):
        @atomic(group="test", title="My Func")
        def my_func(name: str):
            """Docstring here."""
            return f"hello {name}"
        self.assertIn("test.my_func", AtomicRegistry.list_keys())

    def test_introspection_required_param(self):
        @atomic(group="g")
        def func(required_str: str, opt: int = 42):
            pass
        meta = AtomicRegistry.get("g.func")
        self.assertEqual(len(meta.inputs), 2)
        self.assertEqual(meta.inputs[0].key, "required_str")
        self.assertEqual(meta.inputs[0].type, "string")
        self.assertTrue(meta.inputs[0].required)

    def test_introspection_optional_param(self):
        @atomic(group="g")
        def func(opt: int = 42):
            pass
        meta = AtomicRegistry.get("g.func")
        self.assertFalse(meta.inputs[0].required)
        self.assertEqual(meta.inputs[0].default, 42)

    def test_introspection_bool_type(self):
        @atomic(group="g")
        def func(flag: bool = False):
            pass
        meta = AtomicRegistry.get("g.func")
        self.assertEqual(meta.inputs[0].type, "boolean")

    def test_docstring(self):
        @atomic(group="d")
        def documented():
            """This is the description."""
            pass
        self.assertEqual(AtomicRegistry.get("d.documented").description, "This is the description.")

    def test_depends_on(self):
        @atomic(group="a", depends_on=["b.other"])
        def dep():
            pass
        self.assertEqual(AtomicRegistry.get("a.dep").depends_on, ["b.other"])

    def test_run(self):
        @atomic(group="r")
        def adder(x: int = 0, y: int = 0):
            return x + y
        self.assertEqual(AtomicRegistry.run("r.adder", x=3, y=7), 10)

    def test_run_defaults(self):
        @atomic(group="r")
        def greeter(name: str = "world"):
            return f"hello {name}"
        self.assertEqual(AtomicRegistry.run("r.greeter"), "hello world")

    def test_run_missing_key(self):
        with self.assertRaises(KeyError):
            AtomicRegistry.run("nonexistent")

    def test_wrapper_preserves_name(self):
        @atomic(group="w")
        def original():
            pass
        self.assertEqual(original.__name__, "original")

    def test_atomic_meta_attached(self):
        @atomic(group="m", title="Attached")
        def has_meta():
            pass
        self.assertTrue(hasattr(has_meta, "_atomic_meta"))
        self.assertEqual(has_meta._atomic_meta.title, "Attached")

    def test_json_schema(self):
        @atomic(group="s", title="Op", model="sonnet", acceptance="tests pass")
        def op(text: str, count: int = 5):
            """Op desc."""
            pass
        schema = AtomicRegistry.json()
        self.assertIn("s.op", schema)
        entry = schema["s.op"]
        self.assertEqual(entry["title"], "Op")
        self.assertEqual(entry["model"], "sonnet")
        inputs = entry["inputSchema"]
        self.assertEqual(inputs["type"], "object")
        self.assertIn("text", inputs["properties"])
        self.assertEqual(inputs["properties"]["count"]["default"], 5)
        self.assertIn("text", inputs["required"])
        self.assertNotIn("count", inputs["required"])

    def test_to_subwaves(self):
        @atomic(group="sw", title="Wave 1", model="haiku", depends_on=["sw.wave_0"])
        def wave_1():
            pass
        @atomic(group="sw", title="Wave 0", model="haiku")
        def wave_0():
            pass
        subwaves = AtomicRegistry.to_subwaves(group="sw")
        self.assertEqual(len(subwaves), 2)
        sw1 = [s for s in subwaves if s["id"] == "sw-sw-wave_1"][0]
        self.assertEqual(sw1["depends_on"], ["sw.wave_0"])

    def test_to_subwaves_filter(self):
        @atomic(group="a")
        def in_a():
            pass
        @atomic(group="b")
        def in_b():
            pass
        self.assertEqual(len(AtomicRegistry.to_subwaves(group="a")), 1)
        self.assertEqual(len(AtomicRegistry.to_subwaves(group="b")), 1)
        self.assertEqual(len(AtomicRegistry.to_subwaves()), 2)

    def test_list_type(self):
        @atomic(group="t")
        def with_list(items: list = None):
            pass
        self.assertEqual(AtomicRegistry.get("t.with_list").inputs[0].type, "array")

    def test_dict_type(self):
        @atomic(group="t")
        def with_dict(data: dict = None):
            pass
        self.assertEqual(AtomicRegistry.get("t.with_dict").inputs[0].type, "object")

    def test_clear(self):
        @atomic(group="c")
        def temp():
            pass
        self.assertEqual(len(AtomicRegistry.list_keys()), 1)
        AtomicRegistry.clear()
        self.assertEqual(len(AtomicRegistry.list_keys()), 0)


# ===========================================================================
# Forge Tests
# ===========================================================================

class TestContextPacker(unittest.TestCase):

    def test_pack_creates_file(self):
        path = pack_context(files={"a.go": "package main"}, claude_md="# Test")
        self.assertTrue(os.path.exists(path))
        self.assertTrue(path.endswith(".tar.gz"))
        os.unlink(path)

    def test_pack_contains_claude_md(self):
        path = pack_context(files={}, claude_md="# Worker Instructions")
        with tarfile.open(path, "r:gz") as tar:
            self.assertIn("CLAUDE.md", tar.getnames())
            f = tar.extractfile("CLAUDE.md")
            self.assertIn("Worker Instructions", f.read().decode())
        os.unlink(path)

    def test_pack_contains_context_files(self):
        path = pack_context(files={"pkg/t.go": "package pkg"}, claude_md="# T")
        with tarfile.open(path, "r:gz") as tar:
            self.assertIn("context/pkg/t.go", tar.getnames())
        os.unlink(path)

    def test_pack_contains_test_files(self):
        path = pack_context(files={}, claude_md="# T", tests={"t_test.go": "test"})
        with tarfile.open(path, "r:gz") as tar:
            self.assertIn("tests/t_test.go", tar.getnames())
        os.unlink(path)

    def test_unpack_restores(self):
        path = pack_context(files={"a.go": "code"}, claude_md="# Hello")
        with tempfile.TemporaryDirectory() as dest:
            unpack_result(path, dest)
            self.assertTrue(os.path.exists(os.path.join(dest, "CLAUDE.md")))
            with open(os.path.join(dest, "CLAUDE.md")) as f:
                self.assertIn("Hello", f.read())
        os.unlink(path)


class TestPlanParser(unittest.TestCase):

    PLAN = """
### Task 1.1: Portal Types

**Files:**
- Create: `pkg/android/types.go`
- Create: `pkg/android/types_test.go`

Run: `go test ./pkg/android/ -v`

### Task 1.2: Portal Methods

**Files:**
- Modify: `pkg/android/client.go`

Run: `go test ./pkg/android/ -run TestClient -v`

### Task 2.1: BodyCam Logger

**Files:**
- Create: `pkg/bodycam/logger.go`
"""

    def test_count(self):
        sws = _parse_plan_to_subwaves(self.PLAN)
        self.assertEqual(len(sws), 3)

    def test_ids(self):
        sws = _parse_plan_to_subwaves(self.PLAN)
        ids = [s["id"] for s in sws]
        self.assertIn("sw-1-1", ids)
        self.assertIn("sw-1-2", ids)
        self.assertIn("sw-2-1", ids)

    def test_files(self):
        sws = _parse_plan_to_subwaves(self.PLAN)
        sw1 = [s for s in sws if s["id"] == "sw-1-1"][0]
        self.assertIn("pkg/android/types.go", sw1["files_to_edit"])

    def test_command(self):
        sws = _parse_plan_to_subwaves(self.PLAN)
        sw1 = [s for s in sws if s["id"] == "sw-1-1"][0]
        self.assertIn("go test ./pkg/android/ -v", sw1["test_command"])

    def test_model_default(self):
        sws = _parse_plan_to_subwaves(self.PLAN, "sonnet")
        self.assertTrue(all(s["model"] == "sonnet" for s in sws))


class TestEstimation(unittest.TestCase):

    def test_cost_haiku(self):
        sws = [{"model": "haiku"}] * 10
        cost = _estimate_cost(sws)
        self.assertAlmostEqual(cost, 13.5, delta=0.1)

    def test_cost_mixed(self):
        sws = [{"model": "haiku"}, {"model": "sonnet"}, {"model": "opus"}]
        cost = _estimate_cost(sws)
        self.assertAlmostEqual(cost, 16.85, delta=0.1)

    def test_time_reasonable(self):
        sws = [{"depends_on": []}] * 20
        t = _estimate_time(sws)
        self.assertEqual(t, 10)


class TestTaskNotes(unittest.TestCase):

    def test_extracts(self):
        output = "logs\n# Task Notes — sw-01\n## O que foi feito\n- Built it\nFORGE_COMPLETE: done"
        notes = _extract_task_notes(output)
        self.assertIn("O que foi feito", notes)
        self.assertIn("Built it", notes)
        self.assertNotIn("FORGE_COMPLETE", notes)

    def test_empty_on_no_notes(self):
        self.assertEqual(_extract_task_notes("just logs"), "")

    def test_truncates(self):
        output = "# Task Notes — sw-01\n" + "x" * 5000
        self.assertLessEqual(len(_extract_task_notes(output)), 2000)


class TestBuildClaudeMd(unittest.TestCase):

    def test_title(self):
        sw = {"title": "Portal", "task_description": "D", "files_to_edit": [], "acceptance": "ok", "test_command": "t"}
        self.assertIn("Portal", _build_claude_md(sw))

    def test_files(self):
        sw = {"title": "T", "task_description": "D", "files_to_edit": ["a.go", "b.go"], "acceptance": "ok", "test_command": "t"}
        md = _build_claude_md(sw)
        self.assertIn("a.go", md)
        self.assertIn("b.go", md)


# ===========================================================================
# Config Tests
# ===========================================================================

class TestWaveConfig(unittest.TestCase):

    def setUp(self):
        config_path = os.path.join(os.path.dirname(__file__), "..", "..", "scripts", "wave-config.json")
        with open(config_path) as f:
            self.config = json.load(f)

    def test_has_terminals(self):
        self.assertGreaterEqual(len(self.config["terminals"]), 3)
        self.assertLessEqual(len(self.config["terminals"]), 8)

    def test_terminal_names_unique(self):
        names = [t["name"] for t in self.config["terminals"]]
        self.assertEqual(len(names), len(set(names)))

    def test_all_have_wave_a(self):
        for t in self.config["terminals"]:
            self.assertIn("wave_a", t)
            self.assertIn("prompt", t["wave_a"])
            self.assertGreater(len(t["wave_a"]["prompt"]), 50)

    def test_all_have_waves_b_c(self):
        for t in self.config["terminals"]:
            self.assertIn("wave_b", t)
            self.assertIn("wave_c", t)

    def test_no_overlapping_tracks(self):
        tracks = []
        for t in self.config["terminals"]:
            if "(" in t["track"] and ")" in t["track"]:
                tracks.append(t["track"].split("(")[1].split(")")[0])
        self.assertEqual(len(tracks), len(set(tracks)))


class TestForgeConfig(unittest.TestCase):

    def setUp(self):
        config_path = os.path.join(os.path.dirname(__file__), "..", "config.json")
        with open(config_path) as f:
            self.config = json.load(f)

    def test_api_url(self):
        self.assertIn("run.app", self.config["pm_api_url"])

    def test_defaults(self):
        d = self.config["defaults"]
        self.assertEqual(d["model_generation"], "haiku")
        self.assertEqual(d["model_review"], "opus")
        self.assertEqual(d["max_retries"], 3)

    def test_tdd(self):
        self.assertTrue(self.config["tdd"]["enabled"])

    def test_escalation(self):
        esc = self.config["defaults"]["escalation"]
        self.assertEqual(esc["haiku_fails"], "sonnet")
        self.assertEqual(esc["sonnet_fails"], "opus")


# ===========================================================================
# Run
# ===========================================================================

if __name__ == "__main__":
    # Run with verbose output
    loader = unittest.TestLoader()
    suite = loader.loadTestsFromModule(sys.modules[__name__])
    runner = unittest.TextTestRunner(verbosity=2)
    result = runner.run(suite)
    sys.exit(0 if result.wasSuccessful() else 1)
