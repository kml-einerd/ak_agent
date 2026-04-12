"""Tests for collect_results git-based merge collector."""
import sys
import os
import subprocess
import tempfile
import shutil
from unittest.mock import patch

sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest
from forge import collect_results

# Real subprocess.run — we intercept go/gh commands, pass git through
_real_run = subprocess.run


def _mock_run(cmd, **kwargs):
    """Intercept go/gh commands, let git pass through."""
    prog = cmd[0] if isinstance(cmd, list) else cmd.split()[0]
    if prog in ("go", "gh"):
        return subprocess.CompletedProcess(cmd, 0, stdout="ok\n", stderr="")
    return _real_run(cmd, **kwargs)


@pytest.fixture(autouse=True)
def _patch_external_tools():
    """Mock go/gh so tests don't need them installed."""
    with patch("forge.subprocess.run", side_effect=_mock_run):
        yield


def _git(repo, args):
    """Run git command in repo dir."""
    env = {
        **os.environ,
        "GIT_AUTHOR_NAME": "test", "GIT_AUTHOR_EMAIL": "t@t",
        "GIT_COMMITTER_NAME": "test", "GIT_COMMITTER_EMAIL": "t@t",
        "GIT_CONFIG_NOSYSTEM": "1",
    }
    r = subprocess.run(
        ["git"] + args, cwd=repo,
        capture_output=True, text=True, env=env,
    )
    assert r.returncode == 0, f"git {args} failed: {r.stderr}"
    return r


def _write(repo, path, content):
    """Write a file relative to repo root."""
    full = os.path.join(repo, path)
    os.makedirs(os.path.dirname(full), exist_ok=True)
    with open(full, "w") as f:
        f.write(content)


def _setup_repo_with_branches(tmpdir, run_id, branches):
    """Create a bare 'origin' + local clone with forge branches.

    branches: dict of {sw_id: {filename: content, ...}}
    Each branch is created from main with the given file changes.
    """
    origin = os.path.join(tmpdir, "origin.git")
    local = os.path.join(tmpdir, "local")

    # Create bare origin
    subprocess.run(["git", "init", "--bare", "-b", "main", origin], capture_output=True, check=True)

    # Create local repo with main branch
    os.makedirs(local)
    _git(local, ["init", "-b", "main"])
    _git(local, ["config", "user.name", "test"])
    _git(local, ["config", "user.email", "t@t"])
    _git(local, ["remote", "add", "origin", origin])
    _write(local, "main.go", "package main\n\nfunc main() {}\n")
    _git(local, ["add", "."])
    _git(local, ["commit", "-m", "initial"])
    _git(local, ["push", "-u", "origin", "main"])

    # Create each forge branch from main
    for sw_id, files in branches.items():
        branch_name = f"forge/{run_id}/{sw_id}"
        _git(local, ["checkout", "-b", branch_name, "main"])
        for filename, content in files.items():
            _write(local, filename, content)
        _git(local, ["add", "."])
        _git(local, ["commit", "-m", f"work from {sw_id}"])
        _git(local, ["push", "origin", branch_name])

    # Back to main
    _git(local, ["checkout", "main"])
    return local


class TestMergeNoConflict:
    """3 branches, no conflicts — all touch different files."""

    def test_merges_all_green(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            run_id = "forge-test-001"
            local = _setup_repo_with_branches(tmpdir, run_id, {
                "sw-01": {"pkg/alpha.go": "package pkg\n// alpha\n"},
                "sw-02": {"pkg/beta.go": "package pkg\n// beta\n"},
                "sw-03": {"pkg/gamma.go": "package pkg\n// gamma\n"},
            })

            results = {
                "sw-01": {"status": "green", "cost_usd": 0.10, "duration_ms": 5000},
                "sw-02": {"status": "green", "cost_usd": 0.15, "duration_ms": 6000},
                "sw-03": {"status": "green", "cost_usd": 0.12, "duration_ms": 4000},
            }

            out = collect_results(run_id, results, local)

            assert out["merged"] == 3
            assert out["needs_manual"] == []

            # Verify files exist in working tree
            assert os.path.exists(os.path.join(local, "pkg/alpha.go"))
            assert os.path.exists(os.path.join(local, "pkg/beta.go"))
            assert os.path.exists(os.path.join(local, "pkg/gamma.go"))

            # Verify we're on the integration branch
            branch = subprocess.run(
                ["git", "branch", "--show-current"], cwd=local,
                capture_output=True, text=True,
            )
            assert branch.stdout.strip() == f"forge/{run_id}/integration"

    def test_skips_non_green(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            run_id = "forge-test-002"
            local = _setup_repo_with_branches(tmpdir, run_id, {
                "sw-01": {"pkg/a.go": "package pkg\n"},
                "sw-02": {"pkg/b.go": "package pkg\n"},
            })

            results = {
                "sw-01": {"status": "green", "cost_usd": 0.10, "duration_ms": 5000},
                "sw-02": {"status": "red", "cost_usd": 0.05, "duration_ms": 3000},
            }

            out = collect_results(run_id, results, local)

            assert out["merged"] == 1
            assert os.path.exists(os.path.join(local, "pkg/a.go"))
            assert not os.path.exists(os.path.join(local, "pkg/b.go"))


class TestMergeGoModConflict:
    """Two branches both modify go.mod — should auto-resolve with theirs."""

    def test_go_mod_conflict_resolved(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            run_id = "forge-test-003"
            origin = os.path.join(tmpdir, "origin.git")
            local = os.path.join(tmpdir, "local")

            subprocess.run(["git", "init", "--bare", "-b", "main", origin], capture_output=True, check=True)
            os.makedirs(local)
            _git(local, ["init", "-b", "main"])
            _git(local, ["config", "user.name", "test"])
            _git(local, ["config", "user.email", "t@t"])
            _git(local, ["remote", "add", "origin", origin])

            # Main has go.mod + go.sum
            _write(local, "main.go", "package main\n\nfunc main() {}\n")
            _write(local, "go.mod", "module example.com/test\n\ngo 1.21\n")
            _write(local, "go.sum", "")
            _git(local, ["add", "."])
            _git(local, ["commit", "-m", "initial with go.mod"])
            _git(local, ["push", "-u", "origin", "main"])

            # sw-01: adds a require to go.mod + a file
            _git(local, ["checkout", "-b", f"forge/{run_id}/sw-01", "main"])
            _write(local, "go.mod", "module example.com/test\n\ngo 1.21\n\nrequire foo v1.0.0\n")
            _write(local, "go.sum", "foo v1.0.0 h1:abc=\n")
            _write(local, "pkg/one.go", "package pkg\n")
            _git(local, ["add", "."])
            _git(local, ["commit", "-m", "sw-01 work"])
            _git(local, ["push", "origin", f"forge/{run_id}/sw-01"])

            # sw-02: different require in go.mod + a file
            _git(local, ["checkout", "-b", f"forge/{run_id}/sw-02", "main"])
            _write(local, "go.mod", "module example.com/test\n\ngo 1.21\n\nrequire bar v2.0.0\n")
            _write(local, "go.sum", "bar v2.0.0 h1:xyz=\n")
            _write(local, "pkg/two.go", "package pkg\n")
            _git(local, ["add", "."])
            _git(local, ["commit", "-m", "sw-02 work"])
            _git(local, ["push", "origin", f"forge/{run_id}/sw-02"])

            _git(local, ["checkout", "main"])

            results = {
                "sw-01": {"status": "green", "cost_usd": 0.10, "duration_ms": 5000},
                "sw-02": {"status": "green", "cost_usd": 0.15, "duration_ms": 6000},
            }

            out = collect_results(run_id, results, local)

            # sw-01 merges clean, sw-02 conflicts on go.mod → auto-resolved
            assert out["merged"] == 2
            assert out["needs_manual"] == []

            # Both files should exist
            assert os.path.exists(os.path.join(local, "pkg/one.go"))
            assert os.path.exists(os.path.join(local, "pkg/two.go"))


class TestMergeRealConflict:
    """Two branches edit the same non-go.mod file — needs_manual_merge."""

    def test_real_conflict_aborts_and_marks(self):
        with tempfile.TemporaryDirectory() as tmpdir:
            run_id = "forge-test-004"
            origin = os.path.join(tmpdir, "origin.git")
            local = os.path.join(tmpdir, "local")

            subprocess.run(["git", "init", "--bare", "-b", "main", origin], capture_output=True, check=True)
            os.makedirs(local)
            _git(local, ["init", "-b", "main"])
            _git(local, ["config", "user.name", "test"])
            _git(local, ["config", "user.email", "t@t"])
            _git(local, ["remote", "add", "origin", origin])

            # Main has a shared file
            _write(local, "main.go", "package main\n\nfunc main() {}\n")
            _write(local, "pkg/shared.go", "package pkg\n\n// original\nvar X = 1\n")
            _git(local, ["add", "."])
            _git(local, ["commit", "-m", "initial"])
            _git(local, ["push", "-u", "origin", "main"])

            # sw-01: clean branch (different file)
            _git(local, ["checkout", "-b", f"forge/{run_id}/sw-01", "main"])
            _write(local, "pkg/clean.go", "package pkg\n// clean\n")
            _git(local, ["add", "."])
            _git(local, ["commit", "-m", "sw-01"])
            _git(local, ["push", "origin", f"forge/{run_id}/sw-01"])

            # sw-02: modifies shared.go one way
            _git(local, ["checkout", "-b", f"forge/{run_id}/sw-02", "main"])
            _write(local, "pkg/shared.go", "package pkg\n\n// modified by sw-02\nvar X = 200\n")
            _git(local, ["add", "."])
            _git(local, ["commit", "-m", "sw-02"])
            _git(local, ["push", "origin", f"forge/{run_id}/sw-02"])

            # sw-03: modifies shared.go a different way
            _git(local, ["checkout", "-b", f"forge/{run_id}/sw-03", "main"])
            _write(local, "pkg/shared.go", "package pkg\n\n// modified by sw-03\nvar X = 999\n")
            _git(local, ["add", "."])
            _git(local, ["commit", "-m", "sw-03"])
            _git(local, ["push", "origin", f"forge/{run_id}/sw-03"])

            _git(local, ["checkout", "main"])

            results = {
                "sw-01": {"status": "green", "cost_usd": 0.10, "duration_ms": 3000},
                "sw-02": {"status": "green", "cost_usd": 0.15, "duration_ms": 5000},
                "sw-03": {"status": "green", "cost_usd": 0.12, "duration_ms": 4000},
            }

            out = collect_results(run_id, results, local)

            # sw-01 clean, sw-02 clean (first to touch shared.go), sw-03 conflicts
            assert out["merged"] == 2
            assert len(out["needs_manual"]) == 1
            assert out["needs_manual"][0]["sw_id"] == "sw-03"
            assert "pkg/shared.go" in out["needs_manual"][0]["conflicts"]

            # sw-01 and sw-02 files should exist
            assert os.path.exists(os.path.join(local, "pkg/clean.go"))
            # shared.go should have sw-02's version (merged before sw-03)
            with open(os.path.join(local, "pkg/shared.go")) as f:
                content = f.read()
            assert "sw-02" in content
