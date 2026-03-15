#!/usr/bin/env python3
"""
Scale Auto Scaling Group (min, max, desired). Used by CLI and Lambda.
"""

import argparse
import sys
from typing import Optional

from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.aws_clients import get_autoscaling_client
from core.logging_config import setup_logging, log_action
from core.safety_checks import check_safe_to_modify

import logging
setup_logging()
logger = logging.getLogger("aws_cost_saver.scripts.scale_asg")


def scale_asg(
    asg_name: str,
    desired: int,
    min_size: Optional[int] = None,
    max_size: Optional[int] = None,
    region: Optional[str] = None,
    profile: Optional[str] = None,
    dry_run: bool = False,
    force: bool = False,
    env_name: Optional[str] = None,
) -> bool:
    """Set ASG desired capacity and optionally min/max. Returns True on success."""
    if not force:
        safe, reason = check_safe_to_modify("asg", asg_name, region, profile, env_name)
        if not safe:
            log_action(logger, asg_name, "scale-asg", "blocked", reason=reason)
            return False
    if dry_run:
        log_action(logger, asg_name, "scale-asg", "dry-run", desired=desired, min_size=min_size, max_size=max_size)
        return True
    client = get_autoscaling_client(region=region, profile=profile)
    kwargs = {"AutoScalingGroupName": asg_name, "DesiredCapacity": desired}
    if min_size is not None:
        kwargs["MinSize"] = min_size
    if max_size is not None:
        kwargs["MaxSize"] = max_size
    try:
        client.update_auto_scaling_group(**kwargs)
        log_action(logger, asg_name, "scale-asg", "success", desired=desired, min_size=min_size, max_size=max_size)
        return True
    except Exception as e:
        log_action(logger, asg_name, "scale-asg", "error", error=str(e))
        raise


def main() -> int:
    parser = argparse.ArgumentParser(description="Scale Auto Scaling Group")
    parser.add_argument("asg_name", help="ASG name")
    parser.add_argument("desired", type=int, help="Desired capacity")
    parser.add_argument("--min", dest="min_size", type=int, help="Min size")
    parser.add_argument("--max", dest="max_size", type=int, help="Max size")
    parser.add_argument("--region", help="AWS region")
    parser.add_argument("--profile", help="AWS profile")
    parser.add_argument("--dry-run", action="store_true", help="Preview only")
    parser.add_argument("--force", action="store_true", help="Skip safety checks")
    parser.add_argument("--env", dest="env_name", help="Environment name for safety checks")
    args = parser.parse_args()
    ok = scale_asg(
        args.asg_name, args.desired,
        min_size=args.min_size, max_size=args.max_size,
        region=args.region, profile=args.profile,
        dry_run=args.dry_run, force=args.force, env_name=args.env_name,
    )
    return 0 if ok else 1


if __name__ == "__main__":
    sys.exit(main())
