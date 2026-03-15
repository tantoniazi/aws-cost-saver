"""
Scheduling engine for aws-cost-saver.
Reads config and determines start/stop actions based on schedule.
"""

from pathlib import Path
from typing import Any, Dict, List, Optional

import yaml

# Default config path relative to project root
DEFAULT_CONFIG_PATH = Path(__file__).resolve().parent.parent / "config" / "environments.yaml"


def load_config(config_path: Optional[Path] = None) -> Dict[str, Any]:
    """Load environments.yaml and return parsed config."""
    path = config_path or DEFAULT_CONFIG_PATH
    if not path.exists():
        return {}
    with open(path) as f:
        return yaml.safe_load(f) or {}


def get_environment_config(env_name: str, config_path: Optional[Path] = None) -> Optional[Dict[str, Any]]:
    """Return config for a single environment, with defaults merged."""
    config = load_config(config_path)
    if env_name not in config:
        return None
    env_cfg = config.get(env_name, {}).copy()
    default = config.get("default", {})
    for key in ("schedule", "rds", "ecs", "ec2", "asg"):
        if key not in env_cfg and key in default:
            env_cfg[key] = default[key]
    return env_cfg


def get_schedule(env_name: str, config_path: Optional[Path] = None) -> Optional[Dict[str, str]]:
    """Return schedule (stop/start times) for environment."""
    cfg = get_environment_config(env_name, config_path)
    if not cfg:
        return None
    return cfg.get("schedule")


def get_resources_for_env(env_name: str, config_path: Optional[Path] = None) -> Dict[str, Any]:
    """Return all resource lists (rds, ecs, ec2, asg) for an environment."""
    cfg = get_environment_config(env_name, config_path)
    if not cfg:
        return {}
    return {
        "rds": cfg.get("rds") or [],
        "ecs": cfg.get("ecs") or {},
        "ec2": cfg.get("ec2") or [],
        "asg": cfg.get("asg") or [],
    }


def list_environments(config_path: Optional[Path] = None) -> List[str]:
    """Return list of environment names (excluding 'default')."""
    config = load_config(config_path)
    return [k for k in config if k != "default"]
