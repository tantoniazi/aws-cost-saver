#!/usr/bin/env python3
"""
Stop RDS instance(s). Used by CLI and Lambda.
"""

import argparse
import sys
from typing import List, Optional

from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.aws_clients import get_rds_client
from core.logging_config import setup_logging, log_action
from core.safety_checks import check_rds_safe_to_stop

import logging
setup_logging()
logger = logging.getLogger("aws_cost_saver.scripts.stop_rds")


def stop_rds_instance(
    db_identifier: str,
    region: Optional[str] = None,
    profile: Optional[str] = None,
    dry_run: bool = False,
    force: bool = False,
    env_name: Optional[str] = None,
) -> bool:
    """Stop a single RDS instance. Returns True on success."""
    if not force:
        safe, reason = check_rds_safe_to_stop(db_identifier, region, profile, env_name)
        if not safe:
            log_action(logger, db_identifier, "stop-rds", "blocked", reason=reason)
            return False
    if dry_run:
        log_action(logger, db_identifier, "stop-rds", "dry-run")
        return True
    client = get_rds_client(region=region, profile=profile)
    try:
        client.stop_db_instance(DBInstanceIdentifier=db_identifier)
        log_action(logger, db_identifier, "stop-rds", "success")
        return True
    except client.exceptions.InvalidDBInstanceStateFault as e:
        log_action(logger, db_identifier, "stop-rds", "invalid-state", error=str(e))
        return False
    except Exception as e:
        log_action(logger, db_identifier, "stop-rds", "error", error=str(e))
        raise


def main() -> int:
    parser = argparse.ArgumentParser(description="Stop RDS instance(s)")
    parser.add_argument("identifiers", nargs="+", help="RDS instance identifier(s)")
    parser.add_argument("--region", help="AWS region")
    parser.add_argument("--profile", help="AWS profile")
    parser.add_argument("--dry-run", action="store_true", help="Preview only")
    parser.add_argument("--force", action="store_true", help="Skip safety checks")
    parser.add_argument("--env", dest="env_name", help="Environment name for safety checks")
    args = parser.parse_args()
    ok = 0
    for db_id in args.identifiers:
        if stop_rds_instance(db_id, args.region, args.profile, args.dry_run, args.force, args.env_name):
            ok += 1
    return 0 if ok == len(args.identifiers) else 1


if __name__ == "__main__":
    sys.exit(main())
