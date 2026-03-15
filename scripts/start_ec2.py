#!/usr/bin/env python3
"""
Start EC2 instance(s). Used by CLI and Lambda.
"""

import argparse
import sys
from typing import Optional

from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.aws_clients import get_ec2_client
from core.logging_config import setup_logging, log_action

import logging
setup_logging()
logger = logging.getLogger("aws_cost_saver.scripts.start_ec2")


def start_ec2_instance(
    instance_id: str,
    region: Optional[str] = None,
    profile: Optional[str] = None,
    dry_run: bool = False,
) -> bool:
    """Start a single EC2 instance. Returns True on success."""
    if dry_run:
        log_action(logger, instance_id, "start-ec2", "dry-run")
        return True
    client = get_ec2_client(region=region, profile=profile)
    try:
        client.start_instances(InstanceIds=[instance_id])
        log_action(logger, instance_id, "start-ec2", "success")
        return True
    except Exception as e:
        log_action(logger, instance_id, "start-ec2", "error", error=str(e))
        raise


def main() -> int:
    parser = argparse.ArgumentParser(description="Start EC2 instance(s)")
    parser.add_argument("instance_ids", nargs="+", help="EC2 instance ID(s)")
    parser.add_argument("--region", help="AWS region")
    parser.add_argument("--profile", help="AWS profile")
    parser.add_argument("--dry-run", action="store_true", help="Preview only")
    args = parser.parse_args()
    ok = 0
    for iid in args.instance_ids:
        if start_ec2_instance(iid, args.region, args.profile, args.dry_run):
            ok += 1
    return 0 if ok == len(args.instance_ids) else 1


if __name__ == "__main__":
    sys.exit(main())
