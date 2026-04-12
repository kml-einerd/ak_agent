"""Tests for forge.py git branch system.

Uses temporary git repos (git init) to test branch operations
without touching any real remote.
"""

import os
import subprocess
import tempfile
import shutil
import pytest
import sys

# Add parent dir to path so we can import forge
sys.path.insert(0, os.path.dirname(os.path.dirname(os.path.abspath(__file__))))
from forge import (
    create_forge_branch,
    list_forge_branches,
    merge_forge_branches,
    cleanup_forge_branches,
    _check_branch_pushed,
)


def _run(cmd, cwd):
    """Helper: run git command."""
    return subprocess.run(cmd, capture_output=True, text=True, cwd=cwd, check=True)


@pytest.fixture
def git_repos(tmp_path):
    """Create a bare 'origin' repo and a cloned 'local' repo with an initial commit on main."""
    origin = tmp_path / "origin.git"
    local = tmp_path / "local"

    # Create bare origin
    _run(["git", "init", "--bare", str(origin)], cwd=tmp_path)

    # Clone it
    _run(["git", "clone", str(origin), str(local)], cwd=tmp_path)

    # Configure user in local
    _run(["git", "config", "user.email", "test@test.com"], cwd=str(local))
    _run(["git", "config", "user.name", "Test"], cwd=str(local))

    # Create initial commit on main
    readme = local / "README.md"
    readme.write_text("# Test repo\n")
    _run(["git", "add", "README.md"], cwd=str(local))
    _run(["git", "commit", "-m", "initial commit"], cwd=str(local))

    # Ensure branch is called main
    _run(["git", "branch", "-M", "main"], cwd=str(local))
    _run(["git", "push", "-u", "origin", "main"], cwd=str(local))

    return {"origin": str(origin), "local": str(local)}


class TestCreateForgeBranch:
    def test_creates_branch_and_pushes(self, git_repos):
        local = git_repos["local"]
        result = create_forge_branch("run-001", "sw-1a", repo_dir=local)

        assert result["ok"] is True
        assert result["branch"] == "forge/run-001/sw-1a"

        # Branch should exist remotely
        remote = subprocess.run(
            ["git", "branch", "-r", "--list", "origin/forge/run-001/sw-1a"],
            capture_output=True, text=True, cwd=local,
        )
        assert "origin/forge/run-001/sw-1a" in remote.stdout

    def test_creates_multiple_branches(self, git_repos):
        local = git_repos["local"]

        # Go back to main before creating second branch
        r1 = create_forge_branch("run-001", "sw-1a", repo_dir=local)
        _run(["git", "checkout", "main"], cwd=local)

        r2 = create_forge_branch("run-001", "sw-1b", repo_dir=local)

        assert r1["ok"] is True
        assert r2["ok"] is True

    def test_duplicate_branch_fails(self, git_repos):
        local = git_repos["local"]
        create_forge_branch("run-001", "sw-dup", repo_dir=local)
        _run(["git", "checkout", "main"], cwd=local)

        result = create_forge_branch("run-001", "sw-dup", repo_dir=local)
        assert result["ok"] is False


class TestListForgeBranches:
    def test_lists_branches_for_run(self, git_repos):
        local = git_repos["local"]

        create_forge_branch("run-002", "sw-a", repo_dir=local)
        _run(["git", "checkout", "main"], cwd=local)
        create_forge_branch("run-002", "sw-b", repo_dir=local)
        _run(["git", "checkout", "main"], cwd=local)

        branches = list_forge_branches("run-002", repo_dir=local)
        assert len(branches) == 2
        assert any("sw-a" in b for b in branches)
        assert any("sw-b" in b for b in branches)

    def test_empty_when_no_branches(self, git_repos):
        local = git_repos["local"]
        branches = list_forge_branches("run-nonexistent", repo_dir=local)
        assert branches == []

    def test_isolates_by_run_id(self, git_repos):
        local = git_repos["local"]

        create_forge_branch("run-aaa", "sw-1", repo_dir=local)
        _run(["git", "checkout", "main"], cwd=local)
        create_forge_branch("run-bbb", "sw-1", repo_dir=local)
        _run(["git", "checkout", "main"], cwd=local)

        branches_a = list_forge_branches("run-aaa", repo_dir=local)
        branches_b = list_forge_branches("run-bbb", repo_dir=local)

        assert len(branches_a) == 1
        assert len(branches_b) == 1
        assert "run-aaa" in branches_a[0]
        assert "run-bbb" in branches_b[0]


class TestMergeForgeBranches:
    def test_merges_all_subwave_branches(self, git_repos):
        local = git_repos["local"]

        # Create two branches with different files
        create_forge_branch("run-003", "sw-a", repo_dir=local)
        (git_repos["local"] + "/file_a.txt") and open(
            os.path.join(local, "file_a.txt"), "w"
        ).write("content a")
        _run(["git", "add", "file_a.txt"], cwd=local)
        _run(["git", "commit", "-m", "add file_a"], cwd=local)
        _run(["git", "push"], cwd=local)
        _run(["git", "checkout", "main"], cwd=local)

        create_forge_branch("run-003", "sw-b", repo_dir=local)
        open(os.path.join(local, "file_b.txt"), "w").write("content b")
        _run(["git", "add", "file_b.txt"], cwd=local)
        _run(["git", "commit", "-m", "add file_b"], cwd=local)
        _run(["git", "push"], cwd=local)
        _run(["git", "checkout", "main"], cwd=local)

        result = merge_forge_branches("run-003", repo_dir=local)

        assert result["ok"] is True
        assert result["branch"] == "forge/run-003/integration"
        assert len(result["merged"]) == 2

        # Both files should exist on integration branch
        assert os.path.exists(os.path.join(local, "file_a.txt"))
        assert os.path.exists(os.path.join(local, "file_b.txt"))

    def test_no_branches_returns_error(self, git_repos):
        local = git_repos["local"]
        result = merge_forge_branches("run-empty", repo_dir=local)

        assert result["ok"] is False
        assert "no branches" in result["error"]

    def test_merge_conflict_reports_error(self, git_repos):
        local = git_repos["local"]

        # Two branches editing the same file differently
        create_forge_branch("run-conflict", "sw-a", repo_dir=local)
        open(os.path.join(local, "shared.txt"), "w").write("version A")
        _run(["git", "add", "shared.txt"], cwd=local)
        _run(["git", "commit", "-m", "version A"], cwd=local)
        _run(["git", "push"], cwd=local)
        _run(["git", "checkout", "main"], cwd=local)

        create_forge_branch("run-conflict", "sw-b", repo_dir=local)
        open(os.path.join(local, "shared.txt"), "w").write("version B")
        _run(["git", "add", "shared.txt"], cwd=local)
        _run(["git", "commit", "-m", "version B"], cwd=local)
        _run(["git", "push"], cwd=local)
        _run(["git", "checkout", "main"], cwd=local)

        result = merge_forge_branches("run-conflict", repo_dir=local)

        # First merge succeeds, second should conflict
        assert result["ok"] is False
        assert len(result["merged"]) == 1


class TestCleanupForgeBranches:
    def test_deletes_remote_branches(self, git_repos):
        local = git_repos["local"]

        create_forge_branch("run-del", "sw-x", repo_dir=local)
        _run(["git", "checkout", "main"], cwd=local)
        create_forge_branch("run-del", "sw-y", repo_dir=local)
        _run(["git", "checkout", "main"], cwd=local)

        # Verify they exist
        assert len(list_forge_branches("run-del", repo_dir=local)) == 2

        # Cleanup
        result = cleanup_forge_branches("run-del", repo_dir=local)

        assert result["ok"] is True
        assert len(result["deleted"]) == 2

        # Fetch and verify gone
        _run(["git", "fetch", "--prune", "origin"], cwd=local)
        assert len(list_forge_branches("run-del", repo_dir=local)) == 0

    def test_noop_when_no_branches(self, git_repos):
        local = git_repos["local"]
        result = cleanup_forge_branches("run-nope", repo_dir=local)

        assert result["ok"] is True
        assert result["deleted"] == []


class TestFullForgeFlow:
    """End-to-end: create branches → workers commit → merge → verify all files."""

    def _simulate_worker(self, origin_url, branch, filename, content, tmp_path):
        """Simulate a worker: clone, checkout branch, add file, commit, push."""
        worker_dir = tmp_path / f"worker-{filename}"
        _run(["git", "clone", origin_url, str(worker_dir)], cwd=str(tmp_path))
        _run(["git", "config", "user.email", "worker@forge.ai"], cwd=str(worker_dir))
        _run(["git", "config", "user.name", "Forge Worker"], cwd=str(worker_dir))
        _run(["git", "checkout", branch], cwd=str(worker_dir))

        filepath = worker_dir / filename
        filepath.parent.mkdir(parents=True, exist_ok=True)
        filepath.write_text(content)

        _run(["git", "add", "-A"], cwd=str(worker_dir))
        _run(["git", "commit", "-m", f"forge: implement {filename}"], cwd=str(worker_dir))
        _run(["git", "push", "origin", branch], cwd=str(worker_dir))

    def test_full_flow_3_workers(self, git_repos, tmp_path):
        """3 workers each add files to their branch, merge has all files."""
        local = git_repos["local"]
        origin = git_repos["origin"]
        run_id = "run-e2e-001"

        workers = [
            {"sw_id": "sw-api", "file": "pkg/api/handler.go", "content": "package api\n\nfunc Handler() {}\n"},
            {"sw_id": "sw-db", "file": "pkg/db/store.go", "content": "package db\n\nfunc Store() {}\n"},
            {"sw_id": "sw-ui", "file": "frontend/app.tsx", "content": "export default function App() { return <div/> }\n"},
        ]

        # Phase 1: Create branches (like cmd_run does)
        for w in workers:
            result = create_forge_branch(run_id, w["sw_id"], repo_dir=local)
            assert result["ok"], f"branch create failed for {w['sw_id']}: {result}"
            _run(["git", "checkout", "main"], cwd=local)

        # Verify all branches exist
        branches = list_forge_branches(run_id, repo_dir=local)
        assert len(branches) == 3

        # Phase 2: Each worker clones, commits, pushes (simulated)
        for w in workers:
            branch = f"forge/{run_id}/{w['sw_id']}"
            self._simulate_worker(origin, branch, w["file"], w["content"], tmp_path)

        # Phase 3: Detect pushes via ls-remote (SHA should change)
        for w in workers:
            sha = _check_branch_pushed(run_id, w["sw_id"], repo_dir=local)
            assert sha, f"ls-remote should detect push for {w['sw_id']}"

        # Phase 4: Merge all into integration
        _run(["git", "checkout", "main"], cwd=local)
        result = merge_forge_branches(run_id, repo_dir=local)

        assert result["ok"], f"merge failed: {result}"
        assert result["branch"] == f"forge/{run_id}/integration"
        assert len(result["merged"]) == 3

        # Verify integration branch has ALL worker files
        for w in workers:
            full_path = os.path.join(local, w["file"])
            assert os.path.exists(full_path), f"missing after merge: {w['file']}"
            assert open(full_path).read() == w["content"]

        # Original README should still be there
        assert os.path.exists(os.path.join(local, "README.md"))

    def test_full_flow_with_cleanup(self, git_repos, tmp_path):
        """Full flow including cleanup: branches should be gone after."""
        local = git_repos["local"]
        origin = git_repos["origin"]
        run_id = "run-e2e-cleanup"

        # Create 2 branches + worker commits
        for sw_id in ["sw-alpha", "sw-beta"]:
            create_forge_branch(run_id, sw_id, repo_dir=local)
            _run(["git", "checkout", "main"], cwd=local)

        self._simulate_worker(origin, f"forge/{run_id}/sw-alpha",
                              "alpha.py", "print('alpha')\n", tmp_path)
        self._simulate_worker(origin, f"forge/{run_id}/sw-beta",
                              "beta.py", "print('beta')\n", tmp_path)

        # Merge
        result = merge_forge_branches(run_id, repo_dir=local)
        assert result["ok"]
        assert len(result["merged"]) == 2

        # Cleanup
        _run(["git", "checkout", "main"], cwd=local)
        cleanup = cleanup_forge_branches(run_id, repo_dir=local)
        assert cleanup["ok"]
        assert len(cleanup["deleted"]) >= 2

        # Branches should be gone
        _run(["git", "fetch", "--prune", "origin"], cwd=local)
        remaining = list_forge_branches(run_id, repo_dir=local)
        assert remaining == []

    def test_push_detection_sha_change(self, git_repos, tmp_path):
        """ls-remote SHA changes after worker pushes new commits."""
        local = git_repos["local"]
        origin = git_repos["origin"]
        run_id = "run-e2e-sha"

        create_forge_branch(run_id, "sw-x", repo_dir=local)
        _run(["git", "checkout", "main"], cwd=local)

        # SHA before worker push
        sha_before = _check_branch_pushed(run_id, "sw-x", repo_dir=local)
        assert sha_before  # branch exists after create

        # Worker pushes
        self._simulate_worker(origin, f"forge/{run_id}/sw-x",
                              "x.txt", "pushed\n", tmp_path)

        # SHA after worker push — should be different
        sha_after = _check_branch_pushed(run_id, "sw-x", repo_dir=local)
        assert sha_after
        assert sha_before != sha_after

    def test_partial_failure_merge(self, git_repos, tmp_path):
        """If one worker doesn't push, merge only includes branches that have commits."""
        local = git_repos["local"]
        origin = git_repos["origin"]
        run_id = "run-e2e-partial"

        # Create 3 branches
        for sw_id in ["sw-done1", "sw-done2", "sw-nopush"]:
            create_forge_branch(run_id, sw_id, repo_dir=local)
            _run(["git", "checkout", "main"], cwd=local)

        # Only 2 workers push
        self._simulate_worker(origin, f"forge/{run_id}/sw-done1",
                              "done1.txt", "ok\n", tmp_path)
        self._simulate_worker(origin, f"forge/{run_id}/sw-done2",
                              "done2.txt", "ok\n", tmp_path)

        # Merge — all 3 branches exist but sw-nopush has no new commits
        # merge_forge_branches merges all branches (even empty ones — they just have main content)
        result = merge_forge_branches(run_id, repo_dir=local)
        assert result["ok"]
        # All 3 merge cleanly (sw-nopush is identical to main)
        assert len(result["merged"]) == 3

        # But only the 2 pushed files exist
        assert os.path.exists(os.path.join(local, "done1.txt"))
        assert os.path.exists(os.path.join(local, "done2.txt"))


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
