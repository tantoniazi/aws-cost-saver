"""
AWS Lambda entrypoint for aws-cost-saver.
Invoked by EventBridge on schedule; reads event action (start/stop) and runs for configured environments.
"""

import json
import os
import sys
from pathlib import Path

# Lambda loads from deployment package root
if __name__ == "__main__":
    _root = Path(__file__).resolve().parent
else:
    _root = Path("/var/task")  # Lambda runtime
if str(_root) not in sys.path:
    sys.path.insert(0, str(_root))

from core.scheduler_engine import list_environments, get_environment_config, load_config
from core.logging_config import setup_logging
from cli.cost_saver import cmd_stop_all, cmd_start_all

import logging
setup_logging(use_json=True)
logger = logging.getLogger("aws_cost_saver.lambda_handler")


def _get_environments_from_event(event: dict) -> list:
    """Determine which environments to run from event or env."""
    envs = event.get("environments") or os.environ.get("COST_SAVER_ENVIRONMENTS", "")
    if isinstance(envs, list):
        return envs
    return [e.strip() for e in str(envs).split(",") if e.strip()]


def _get_config_path():
    """If config is in S3, Lambda layer or /tmp should have it; else use bundled config."""
    bucket = os.environ.get("CONFIG_S3_BUCKET")
    key = os.environ.get("CONFIG_S3_KEY", "config/environments.yaml")
    if bucket and key:
        try:
            import boto3
            s3 = boto3.client("s3")
            local = "/tmp/environments.yaml"
            s3.download_file(bucket, key, local)
            return Path(local)
        except Exception as e:
            logger.warning("Could not fetch config from S3: %s", e)
    return Path(__file__).parent / "config" / "environments.yaml"


def handler(event: dict, context) -> dict:
    """
    Lambda handler. Expects event: { "action": "start"|"stop", optional "environments": ["dev", "staging"] }.
    """
    action = (event.get("action") or "stop").lower()
    if action not in ("start", "stop"):
        return {"statusCode": 400, "body": json.dumps({"error": "action must be start or stop"})}

    config_path = _get_config_path()
    if not config_path.exists():
        load_config(config_path)  # ensure default is used
    envs = _get_environments_from_event(event)
    if not envs:
        envs = list_environments(config_path)
    if not envs:
        logger.info("No environments configured")
        return {"statusCode": 200, "body": json.dumps({"message": "No environments", "action": action})}

    results = []
    for env_name in envs:
        cfg = get_environment_config(env_name, config_path)
        if not cfg:
            results.append({"env": env_name, "status": "skipped", "reason": "not in config"})
            continue
        # Build minimal argparse namespace for cmd_stop_all / cmd_start_all
        class Args:
            pass
        args = Args()
        args.env = env_name
        args.config = str(config_path)
        args.region = os.environ.get("AWS_REGION")
        args.profile = None
        args.dry_run = False
        args.force = False
        args.verbose = False
        try:
            if action == "start":
                code = cmd_start_all(args)
            else:
                code = cmd_stop_all(args)
            results.append({"env": env_name, "status": "ok" if code == 0 else "failed", "exit_code": code})
        except Exception as e:
            logger.exception("Failed for env %s", env_name)
            results.append({"env": env_name, "status": "error", "error": str(e)})

    body = {"action": action, "environments": envs, "results": results}
    return {"statusCode": 200, "body": json.dumps(body)}
