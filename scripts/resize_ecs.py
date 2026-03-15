#!/usr/bin/env python3
"""
Resize ECS service desired count. Used by CLI and Lambda.
"""

import argparse
import sys
from typing import Optional

from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.aws_clients import get_ecs_client
from core.logging_config import setup_logging, log_action
from core.safety_checks import check_safe_to_modify

import logging
setup_logging()
logger = logging.getLogger("aws_cost_saver.scripts.resize_ecs")


def resize_ecs_service(
    cluster: str,
    service: str,
    desired_count: int,
    region: Optional[str] = None,
    profile: Optional[str] = None,
    dry_run: bool = False,
    force: bool = False,
    env_name: Optional[str] = None,
) -> bool:
    """Set ECS service desired count. Returns True on success."""
    resource_id = f"{cluster}/{service}"
    if not force:
        safe, reason = check_safe_to_modify("ecs", resource_id, region, profile, env_name)
        if not safe:
            log_action(logger, resource_id, "resize-ecs", "blocked", reason=reason)
            return False
    if dry_run:
        log_action(logger, resource_id, "resize-ecs", "dry-run", desired_count=desired_count)
        return True
    client = get_ecs_client(region=region, profile=profile)
    try:
        client.update_service(
            cluster=cluster,
            service=service,
            desiredCount=desired_count,
        )
        log_action(logger, resource_id, "resize-ecs", "success", desired_count=desired_count)
        return True
    except Exception as e:
        log_action(logger, resource_id, "resize-ecs", "error", error=str(e))
        raise


def main() -> int:
    parser = argparse.ArgumentParser(description="Resize ECS service desired count")
    parser.add_argument("cluster", help="ECS cluster name")
    parser.add_argument("service", help="ECS service name")
    parser.add_argument("desired_count", type=int, help="Desired task count (e.g. 0 to scale down)")
    parser.add_argument("--region", help="AWS region")
    parser.add_argument("--profile", help="AWS profile")
    parser.add_argument("--dry-run", action="store_true", help="Preview only")
    parser.add_argument("--force", action="store_true", help="Skip safety checks")
    parser.add_argument("--env", dest="env_name", help="Environment name for safety checks")
    args = parser.parse_args()
    ok = resize_ecs_service(
        args.cluster, args.service, args.desired_count,
        args.region, args.profile, args.dry_run, args.force, args.env_name,
    )
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
