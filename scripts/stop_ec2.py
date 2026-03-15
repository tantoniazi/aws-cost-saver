#!/usr/bin/env python3
"""
Stop EC2 instance(s). Used by CLI and Lambda.
"""

import argparse
import sys
from typing import List, Optional

from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.aws_clients import get_ec2_client
from core.logging_config import setup_logging, log_action
from core.safety_checks import check_ec2_safe_to_stop

import logging
setup_logging()
logger = logging.getLogger("aws_cost_saver.scripts.stop_ec2")


def stop_ec2_instance(
    instance_id: str,
    region: Optional[str] = None,
    profile: Optional[str] = None,
    dry_run: bool = False,
    force: bool = False,
    env_name: Optional[str] = None,
) -> bool:
    """Stop a single EC2 instance. Returns True on success."""
    if not force:
        safe, reason = check_ec2_safe_to_stop(instance_id, region, profile, env_name)
        if not safe:
            log_action(logger, instance_id, "stop-ec2", "blocked", reason=reason)
            return False
    if dry_run:
        log_action(logger, instance_id, "stop-ec2", "dry-run")
        return True
    client = get_ec2_client(region=region, profile=profile)
    try:
        client.stop_instances(InstanceIds=[instance_id])
        log_action(logger, instance_id, "stop-ec2", "success")
        return True
    except Exception as e:
        log_action(logger, instance_id, "stop-ec2", "error", error=str(e))
        raise


def main() -> int:
    parser = argparse.ArgumentParser(description="Stop EC2 instance(s)")
    parser.add_argument("instance_ids", nargs="+", help="EC2 instance ID(s)")
    parser.add_argument("--region", help="AWS region")
    parser.add_argument("--profile", help="AWS profile")
    parser.add_argument("--dry-run", action="store_true", help="Preview only")
    parser.add_argument("--force", action="store_true", help="Skip safety checks")
    parser.add_argument("--env", dest="env_name", help="Environment name for safety checks")
    args = parser.parse_args()
    ok = 0
    for iid in args.instance_ids:
        if stop_ec2_instance(iid, args.region, args.profile, args.dry_run, args.force, args.env_name):
            ok += 1
    return 0 if ok == len(args.instance_ids) else 1


if __name__ == "__main__":
    sys.exit(main())
