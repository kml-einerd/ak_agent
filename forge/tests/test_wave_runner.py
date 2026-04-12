"""Tests for wave-runner.py core functions."""
import sys
import os
import json
sys.path.insert(0, os.path.join(os.path.dirname(__file__), "..", ".."))
sys.path.insert(0, os.path.join(os.path.dirname(__file__), ".."))

import pytest


class TestWaveConfig:
    """Test wave-config.json structure."""

    @pytest.fixture
    def config(self):
        config_path = os.path.join(os.path.dirname(__file__), "..", "..", "scripts", "wave-config.json")
        with open(config_path) as f:
            return json.load(f)

    def test_has_project_dir(self, config):
        assert "project_dir" in config
        assert config["project_dir"] == "/home/agdis/pm-os-gcp"

    def test_has_7_terminals(self, config):
        assert len(config["terminals"]) == 7

    def test_each_terminal_has_name(self, config):
        for t in config["terminals"]:
            assert "name" in t
            assert t["name"].startswith("T")

    def test_each_terminal_has_track(self, config):
        for t in config["terminals"]:
            assert "track" in t
            assert len(t["track"]) > 5

    def test_each_terminal_has_wave_a(self, config):
        for t in config["terminals"]:
            assert "wave_a" in t
            wa = t["wave_a"]
            assert "description" in wa
            assert "prompt" in wa
            assert len(wa["prompt"]) > 50  # Prompts should be substantial

    def test_each_terminal_has_waves_b_and_c(self, config):
        for t in config["terminals"]:
            assert "wave_b" in t
            assert "wave_c" in t

    def test_terminal_names_unique(self, config):
        names = [t["name"] for t in config["terminals"]]
        assert len(names) == len(set(names))

    def test_no_file_conflicts_between_terminals(self, config):
        """Verify that track descriptions suggest non-overlapping file scopes."""
        tracks = [t["track"] for t in config["terminals"]]
        # Basic check: no two tracks mention the exact same primary path
        primary_paths = []
        for track in tracks:
            # Extract the part in parentheses
            if "(" in track and ")" in track:
                paths = track.split("(")[1].split(")")[0]
                primary_paths.append(paths)

        # All primary paths should be unique
        assert len(primary_paths) == len(set(primary_paths))


class TestForgeConfig:
    """Test code-forge config.json."""

    @pytest.fixture
    def config(self):
        config_path = os.path.join(os.path.dirname(__file__), "..", "config.json")
        with open(config_path) as f:
            return json.load(f)

    def test_has_pm_api_url(self, config):
        assert "pm_api_url" in config
        assert "run.app" in config["pm_api_url"]

    def test_has_defaults(self, config):
        d = config["defaults"]
        assert d["model_generation"] == "haiku"
        assert d["model_review"] == "opus"
        assert d["max_retries"] == 3

    def test_has_tdd_config(self, config):
        tdd = config["tdd"]
        assert tdd["enabled"] is True

    def test_escalation_chain(self, config):
        esc = config["defaults"]["escalation"]
        assert esc["haiku_fails"] == "sonnet"
        assert esc["sonnet_fails"] == "opus"
