"""Tests for forge.py core functions."""
import sys
import os
import json
import tempfile
import tarfile
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from forge import (
    pack_context,
    unpack_result,
    _parse_plan_to_subwaves,
    _estimate_cost,
    _estimate_time,
    _extract_task_notes,
    _build_claude_md,
)


class TestContextPacker:
    """Test tar.gz context packing/unpacking."""

    def test_pack_creates_tarball(self):
        path = pack_context(
            files={"src/main.go": "package main"},
            claude_md="# Test",
        )
        assert os.path.exists(path)
        assert path.endswith(".tar.gz")
        os.unlink(path)

    def test_pack_contains_claude_md(self):
        path = pack_context(
            files={},
            claude_md="# Worker Instructions",
        )
        with tarfile.open(path, "r:gz") as tar:
            names = tar.getnames()
            assert "CLAUDE.md" in names

            f = tar.extractfile("CLAUDE.md")
            content = f.read().decode()
            assert "Worker Instructions" in content

        os.unlink(path)

    def test_pack_contains_context_files(self):
        path = pack_context(
            files={"pkg/types.go": "package pkg\ntype Foo struct{}"},
            claude_md="# Test",
        )
        with tarfile.open(path, "r:gz") as tar:
            names = tar.getnames()
            assert "context/pkg/types.go" in names

        os.unlink(path)

    def test_pack_contains_test_files(self):
        path = pack_context(
            files={},
            claude_md="# Test",
            tests={"pkg/types_test.go": "package pkg\nfunc TestFoo(t *testing.T){}"},
        )
        with tarfile.open(path, "r:gz") as tar:
            names = tar.getnames()
            assert "tests/pkg/types_test.go" in names

        os.unlink(path)

    def test_unpack_restores_files(self):
        path = pack_context(
            files={"src/main.go": "package main\nfunc main(){}"},
            claude_md="# Hello",
        )

        with tempfile.TemporaryDirectory() as dest:
            unpack_result(path, dest)
            claude_path = os.path.join(dest, "CLAUDE.md")
            assert os.path.exists(claude_path)
            with open(claude_path) as f:
                assert "Hello" in f.read()

        os.unlink(path)


class TestPlanParser:
    """Test markdown plan → sub-waves parser."""

    SAMPLE_PLAN = """
# Implementation Plan

## Sub 1

### Task 1.1: Portal Client Types

**Files:**
- Create: `pkg/android/types.go`
- Create: `pkg/android/types_test.go`

- [ ] **Step 1: Write test**

Run: `go test ./pkg/android/ -v`

### Task 1.2: Portal Client Methods

**Files:**
- Modify: `pkg/android/client.go`

Run: `go test ./pkg/android/ -run TestClient -v`

### Task 2.1: BodyCam Logger

**Files:**
- Create: `pkg/bodycam/logger.go`
- Test: `pkg/bodycam/logger_test.go`
"""

    def test_parses_correct_number_of_tasks(self):
        subwaves = _parse_plan_to_subwaves(self.SAMPLE_PLAN)
        assert len(subwaves) == 3

    def test_parses_task_ids(self):
        subwaves = _parse_plan_to_subwaves(self.SAMPLE_PLAN)
        ids = [sw["id"] for sw in subwaves]
        assert "sw-1-1" in ids
        assert "sw-1-2" in ids
        assert "sw-2-1" in ids

    def test_parses_titles(self):
        subwaves = _parse_plan_to_subwaves(self.SAMPLE_PLAN)
        titles = [sw["title"] for sw in subwaves]
        assert "Portal Client Types" in titles

    def test_parses_files_to_edit(self):
        subwaves = _parse_plan_to_subwaves(self.SAMPLE_PLAN)
        sw1 = [s for s in subwaves if s["id"] == "sw-1-1"][0]
        assert "pkg/android/types.go" in sw1["files_to_edit"]
        assert "pkg/android/types_test.go" in sw1["files_to_edit"]

    def test_parses_test_command(self):
        subwaves = _parse_plan_to_subwaves(self.SAMPLE_PLAN)
        sw1 = [s for s in subwaves if s["id"] == "sw-1-1"][0]
        assert "go test ./pkg/android/ -v" in sw1["test_command"]

    def test_default_model(self):
        subwaves = _parse_plan_to_subwaves(self.SAMPLE_PLAN, default_model="sonnet")
        assert all(sw["model"] == "sonnet" for sw in subwaves)


class TestEstimation:
    """Test cost and time estimation."""

    def test_cost_haiku(self):
        subwaves = [{"model": "haiku"} for _ in range(10)]
        cost = _estimate_cost(subwaves)
        # 10 haiku ($0.35 each) + review ($10)
        assert cost == pytest.approx(13.5, abs=0.1)

    def test_cost_mixed(self):
        subwaves = [
            {"model": "haiku"},
            {"model": "sonnet"},
            {"model": "opus"},
        ]
        cost = _estimate_cost(subwaves)
        # 0.35 + 1.50 + 5.00 + 10.00 (review)
        assert cost == pytest.approx(16.85, abs=0.1)

    def test_time_estimate_reasonable(self):
        subwaves = [{"depends_on": []} for _ in range(20)]
        t = _estimate_time(subwaves)
        # Should be 5 (parallel) + 0 (no sequential) + 5 (review) = 10
        assert t == 10


class TestTaskNotesExtraction:
    """Test TASK_NOTES extraction from worker output."""

    def test_extracts_task_notes(self):
        output = """
Some worker logs here...

# Task Notes — sw-01

## O que foi feito
- Created portal client types
- Added A11yNode struct

## Decisões tomadas
- Used string for bounds instead of Rect

FORGE_COMPLETE: all tests green, ready for review
"""
        notes = _extract_task_notes(output)
        assert "O que foi feito" in notes
        assert "Created portal client types" in notes
        assert "FORGE_COMPLETE" not in notes

    def test_extracts_empty_on_no_notes(self):
        output = "Just some logs\nFORGE_COMPLETE: done"
        notes = _extract_task_notes(output)
        assert notes == ""

    def test_truncates_long_notes(self):
        output = "# Task Notes — sw-01\n" + "x" * 5000
        notes = _extract_task_notes(output)
        assert len(notes) <= 2000


class TestBuildClaudeMd:
    """Test CLAUDE.md generation for workers."""

    def test_includes_title(self):
        sw = {"title": "Portal Client", "task_description": "Build it", "files_to_edit": ["a.go"], "acceptance": "tests pass", "test_command": "go test"}
        md = _build_claude_md(sw)
        assert "Portal Client" in md

    def test_includes_files(self):
        sw = {"title": "T", "task_description": "D", "files_to_edit": ["pkg/a.go", "pkg/b.go"], "acceptance": "ok", "test_command": "test"}
        md = _build_claude_md(sw)
        assert "pkg/a.go" in md
        assert "pkg/b.go" in md

    def test_includes_test_command(self):
        sw = {"title": "T", "task_description": "D", "files_to_edit": [], "acceptance": "ok", "test_command": "go test ./pkg/... -v"}
        md = _build_claude_md(sw)
        assert "go test ./pkg/... -v" in md
