"""Tests for scheduler_engine module."""

import sys
from pathlib import Path
import tempfile
import yaml

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.scheduler_engine import (
    load_config,
    get_environment_config,
    get_schedule,
    get_resources_for_env,
    list_environments,
)


def test_load_config_empty_path():
    with tempfile.NamedTemporaryFile(suffix=".yaml", delete=False) as f:
        pass
    # Non-existent path returns {}
    result = load_config(Path("/nonexistent/env.yaml"))
    assert result == {}


def test_load_config_parses_yaml():
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        yaml.dump({"dev": {"rds": ["db1"], "schedule": {"stop": "19:00", "start": "07:00"}}}, f)
        path = Path(f.name)
    try:
        result = load_config(path)
        assert "dev" in result
        assert result["dev"]["rds"] == ["db1"]
        assert result["dev"]["schedule"]["stop"] == "19:00"
    finally:
        path.unlink(missing_ok=True)


def test_get_environment_config_merges_default():
    config = {
        "default": {"schedule": {"stop": "20:00", "start": "06:00"}},
        "dev": {"rds": ["db1"]},
    }
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        yaml.dump(config, f)
        path = Path(f.name)
    try:
        cfg = get_environment_config("dev", path)
        assert cfg is not None
        assert cfg.get("rds") == ["db1"]
        assert cfg.get("schedule", {}).get("stop") == "20:00"
    finally:
        path.unlink(missing_ok=True)


def test_list_environments_excludes_default():
    config = {"default": {}, "dev": {}, "staging": {}}
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        yaml.dump(config, f)
        path = Path(f.name)
    try:
        envs = list_environments(path)
        assert "default" not in envs
        assert set(envs) == {"dev", "staging"}
    finally:
        path.unlink(missing_ok=True)


def test_get_resources_for_env():
    config = {
        "dev": {
            "rds": ["db1"],
            "ecs": {"cluster": "c1", "services": ["api"]},
            "ec2": ["i-123"],
            "asg": ["asg1"],
        },
    }
    with tempfile.NamedTemporaryFile(mode="w", suffix=".yaml", delete=False) as f:
        yaml.dump(config, f)
        path = Path(f.name)
    try:
        res = get_resources_for_env("dev", path)
        assert res["rds"] == ["db1"]
        assert res["ecs"]["cluster"] == "c1"
        assert res["ecs"]["services"] == ["api"]
        assert res["ec2"] == ["i-123"]
        assert res["asg"] == ["asg1"]
    finally:
        path.unlink(missing_ok=True)
