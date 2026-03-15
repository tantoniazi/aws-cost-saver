#!/usr/bin/env python3
"""
aws-cost-saver CLI: stop/start/resize AWS resources to reduce costs.
Usage: python cli/cost_saver.py <command> [options]
Or: cost-saver <command> [options] when installed.
"""

from pathlib import Path
import sys

# Ensure project root is on path when run as script
_PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(_PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(_PROJECT_ROOT))

import argparse
from typing import Optional

from core.scheduler_engine import (
    get_environment_config,
    get_resources_for_env,
    list_environments,
    get_schedule,
)
from core.resource_discovery import resolve_rds_identifiers, resolve_ec2_identifiers
from core.logging_config import setup_logging
from core.cost_estimation import estimate_savings_hourly, format_savings

# Script actions (import here so CLI can call them)
from scripts.stop_rds import stop_rds_instance
from scripts.start_rds import start_rds_instance
from scripts.stop_ec2 import stop_ec2_instance
from scripts.start_ec2 import start_ec2_instance
from scripts.resize_ecs import resize_ecs_service
from scripts.scale_asg import scale_asg

import logging
setup_logging()
logger = logging.getLogger("aws_cost_saver.cli")


def _config_path(args) -> Optional[Path]:
    return Path(args.config) if getattr(args, "config", None) else None


def _common_parser(parser: argparse.ArgumentParser):
    parser.add_argument("--config", help="Path to environments.yaml")
    parser.add_argument("--region", help="AWS region")
    parser.add_argument("--profile", help="AWS profile")
    parser.add_argument("--dry-run", action="store_true", help="Preview only, do not execute")
    parser.add_argument("--force", action="store_true", help="Skip safety checks (use with caution)")
    parser.add_argument("-v", "--verbose", action="store_true", help="Verbose output")


def cmd_stop_rds(args):
    """Stop RDS instance(s)."""
    ok = 0
    for db_id in args.identifiers:
        if stop_rds_instance(
            db_id, args.region, args.profile, args.dry_run, args.force, getattr(args, "env", None)
        ):
            ok += 1
    return 0 if ok == len(args.identifiers) else 1


def cmd_start_rds(args):
    """Start RDS instance(s)."""
    ok = 0
    for db_id in args.identifiers:
        if start_rds_instance(db_id, args.region, args.profile, args.dry_run):
            ok += 1
    return 0 if ok == len(args.identifiers) else 1


def cmd_stop_ec2(args):
    """Stop EC2 instance(s)."""
    ok = 0
    for iid in args.instance_ids:
        if stop_ec2_instance(
            iid, args.region, args.profile, args.dry_run, args.force, getattr(args, "env", None)
        ):
            ok += 1
    return 0 if ok == len(args.instance_ids) else 1


def cmd_start_ec2(args):
    """Start EC2 instance(s)."""
    ok = 0
    for iid in args.instance_ids:
        if start_ec2_instance(iid, args.region, args.profile, args.dry_run):
            ok += 1
    return 0 if ok == len(args.instance_ids) else 1


def cmd_resize_ecs(args):
    """Resize ECS service desired count."""
    ok = resize_ecs_service(
        args.cluster, args.service, args.desired_count,
        args.region, args.profile, args.dry_run, args.force, getattr(args, "env", None),
    )
    return 0 if ok else 1


def cmd_scale_asg(args):
    """Scale Auto Scaling Group."""
    ok = scale_asg(
        args.asg_name, args.desired,
        min_size=getattr(args, "min_size", None),
        max_size=getattr(args, "max_size", None),
        region=args.region, profile=args.profile,
        dry_run=args.dry_run, force=args.force, env_name=getattr(args, "env", None),
    )
    return 0 if ok else 1


def cmd_stop_all(args):
    """Stop all resources for an environment (RDS, EC2, ECS→0, ASG→0)."""
    env = args.env
    config_path = _config_path(args)
    cfg = get_environment_config(env, config_path)
    if not cfg:
        logger.error("Environment not found: %s", env)
        return 1

    resources = get_resources_for_env(env, config_path)
    rds_list = resolve_rds_identifiers(
        resources.get("rds") or [], env, args.region, args.profile
    )
    ec2_list = resolve_ec2_identifiers(
        resources.get("ec2") or [], env, args.region, args.profile
    )
    ecs_cfg = resources.get("ecs") or {}
    cluster = ecs_cfg.get("cluster")
    services = ecs_cfg.get("services") or []
    asg_list = resources.get("asg") or []

    if args.dry_run:
        logger.info("DRY RUN stop-all env=%s: RDS=%s EC2=%s ECS=%s/%s ASG=%s",
                    env, rds_list, ec2_list, cluster, services, asg_list)

    failed = 0
    for db_id in rds_list:
        if not stop_rds_instance(db_id, args.region, args.profile, args.dry_run, args.force, env):
            failed += 1
    for iid in ec2_list:
        if not stop_ec2_instance(iid, args.region, args.profile, args.dry_run, args.force, env):
            failed += 1
    for svc in services:
        if cluster and not resize_ecs_service(
            cluster, svc, 0, args.region, args.profile, args.dry_run, args.force, env
        ):
            failed += 1
    for asg_name in asg_list:
        if not scale_asg(asg_name, 0, 0, 0, args.region, args.profile, args.dry_run, args.force, env):
            failed += 1

    if args.dry_run and not failed:
        hours = 12.0
        est = estimate_savings_hourly(
            rds_count=len(rds_list),
            ec2_count=len(ec2_list),
            ecs_tasks_stopped=len(services),
            asg_instances_stopped=len(asg_list),
            hours_stopped=hours,
        )
        print(f"Estimated savings today (if stopped {hours}h): {format_savings(est)}")
    return 0 if failed == 0 else 1


def cmd_start_all(args):
    """Start all resources for an environment."""
    env = args.env
    config_path = _config_path(args)
    cfg = get_environment_config(env, config_path)
    if not cfg:
        logger.error("Environment not found: %s", env)
        return 1

    resources = get_resources_for_env(env, config_path)
    rds_list = resolve_rds_identifiers(
        resources.get("rds") or [], env, args.region, args.profile
    )
    ec2_list = resolve_ec2_identifiers(
        resources.get("ec2") or [], env, args.region, args.profile
    )
    ecs_cfg = resources.get("ecs") or {}
    cluster = ecs_cfg.get("cluster")
    services = ecs_cfg.get("services") or []
    asg_list = resources.get("asg") or []

    if args.dry_run:
        logger.info("DRY RUN start-all env=%s: RDS=%s EC2=%s ECS=%s/%s ASG=%s",
                    env, rds_list, ec2_list, cluster, services, asg_list)

    failed = 0
    for db_id in rds_list:
        if not start_rds_instance(db_id, args.region, args.profile, args.dry_run):
            failed += 1
    for iid in ec2_list:
        if not start_ec2_instance(iid, args.region, args.profile, args.dry_run):
            failed += 1
    # ECS/ASG: start typically means scale to 1 (or desired from config); we use 1 here
    for svc in services:
        if cluster and not resize_ecs_service(
            cluster, svc, 1, args.region, args.profile, args.dry_run, args.force, env
        ):
            failed += 1
    for asg_name in asg_list:
        if not scale_asg(asg_name, 1, 1, 1, args.region, args.profile, args.dry_run, args.force, env):
            failed += 1

    return 0 if failed == 0 else 1


def cmd_schedule_run(args):
    """
    Run scheduled action (start or stop) for an environment.
    Typically invoked by EventBridge/Lambda at configured times.
    Use --action start or --action stop and --env <env>.
    """
    env = args.env
    action = (args.action or "stop").lower()
    if action not in ("start", "stop"):
        logger.error("--action must be 'start' or 'stop'")
        return 1
    if action == "start":
        return cmd_start_all(args)
    return cmd_stop_all(args)


def cmd_estimate(args):
    """Print estimated savings for an environment."""
    env = args.env
    config_path = _config_path(args)
    resources = get_resources_for_env(env, config_path)
    rds_list = resolve_rds_identifiers(
        resources.get("rds") or [], env, args.region, args.profile
    )
    ec2_list = resolve_ec2_identifiers(
        resources.get("ec2") or [], env, args.region, args.profile
    )
    ecs_cfg = resources.get("ecs") or {}
    services = ecs_cfg.get("services") or []
    asg_list = resources.get("asg") or []
    hours = float(getattr(args, "hours", 12) or 12)
    est = estimate_savings_hourly(
        rds_count=len(rds_list),
        ec2_count=len(ec2_list),
        ecs_tasks_stopped=len(services),
        asg_instances_stopped=len(asg_list),
        hours_stopped=hours,
    )
    print(f"Estimated savings ({hours}h stopped): {format_savings(est)}")
    return 0


def main():
    parser = argparse.ArgumentParser(
        prog="cost-saver",
        description="AWS Cost Saver: stop/start/resize resources to reduce costs.",
    )
    parser.add_argument("--config", help="Path to config/environments.yaml")
    parser.add_argument("--region", help="AWS region")
    parser.add_argument("--profile", help="AWS profile")
    parser.add_argument("--dry-run", action="store_true", help="Preview only")
    parser.add_argument("--force", action="store_true", help="Skip safety checks")
    sub = parser.add_subparsers(dest="command", required=True)

    # stop-rds
    p = sub.add_parser("stop-rds", help="Stop RDS instance(s)")
    _common_parser(p)
    p.add_argument("identifiers", nargs="+", help="RDS instance identifier(s)")
    p.add_argument("--env", help="Environment name (for safety checks)")
    p.set_defaults(func=cmd_stop_rds)

    # start-rds
    p = sub.add_parser("start-rds", help="Start RDS instance(s)")
    _common_parser(p)
    p.add_argument("identifiers", nargs="+", help="RDS instance identifier(s)")
    p.set_defaults(func=cmd_start_rds)

    # stop-ec2
    p = sub.add_parser("stop-ec2", help="Stop EC2 instance(s)")
    _common_parser(p)
    p.add_argument("instance_ids", nargs="+", help="EC2 instance ID(s)")
    p.add_argument("--env", help="Environment name (for safety checks)")
    p.set_defaults(func=cmd_stop_ec2)

    # start-ec2
    p = sub.add_parser("start-ec2", help="Start EC2 instance(s)")
    _common_parser(p)
    p.add_argument("instance_ids", nargs="+", help="EC2 instance ID(s)")
    p.set_defaults(func=cmd_start_ec2)

    # resize-ecs
    p = sub.add_parser("resize-ecs", help="Resize ECS service desired count")
    _common_parser(p)
    p.add_argument("cluster", help="ECS cluster name")
    p.add_argument("service", help="ECS service name")
    p.add_argument("desired_count", type=int, help="Desired task count")
    p.add_argument("--env", help="Environment name (for safety checks)")
    p.set_defaults(func=cmd_resize_ecs)

    # scale-asg
    p = sub.add_parser("scale-asg", help="Scale Auto Scaling Group")
    _common_parser(p)
    p.add_argument("asg_name", help="ASG name")
    p.add_argument("desired", type=int, help="Desired capacity")
    p.add_argument("--min", dest="min_size", type=int, help="Min size")
    p.add_argument("--max", dest="max_size", type=int, help="Max size")
    p.add_argument("--env", help="Environment name (for safety checks)")
    p.set_defaults(func=cmd_scale_asg)

    # stop-all
    p = sub.add_parser("stop-all", help="Stop all resources for an environment")
    _common_parser(p)
    p.add_argument("env", help="Environment name (e.g. dev, staging)")
    p.set_defaults(func=cmd_stop_all)

    # start-all
    p = sub.add_parser("start-all", help="Start all resources for an environment")
    _common_parser(p)
    p.add_argument("env", help="Environment name")
    p.set_defaults(func=cmd_start_all)

    # schedule-run
    p = sub.add_parser("schedule-run", help="Run scheduled start/stop (for EventBridge/Lambda)")
    _common_parser(p)
    p.add_argument("--env", required=True, dest="env", help="Environment name")
    p.add_argument("--action", choices=["start", "stop"], default="stop", help="start or stop")
    p.set_defaults(func=cmd_schedule_run)

    # estimate
    p = sub.add_parser("estimate", help="Estimate savings for an environment")
    p.add_argument("--config", help="Path to config")
    p.add_argument("--region", help="AWS region")
    p.add_argument("--profile", help="AWS profile")
    p.add_argument("env", help="Environment name")
    p.add_argument("--hours", type=float, default=12, help="Hours resources would be stopped")
    p.set_defaults(func=cmd_estimate)

    args = parser.parse_args()
    return args.func(args)


if __name__ == "__main__":
    sys.exit(main())
