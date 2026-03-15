#!/usr/bin/env python3
"""
Start RDS instance(s). Used by CLI and Lambda.
"""

import argparse
import sys
from typing import Optional

from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.aws_clients import get_rds_client
from core.logging_config import setup_logging, log_action

import logging
setup_logging()
logger = logging.getLogger("aws_cost_saver.scripts.start_rds")


def start_rds_instance(
    db_identifier: str,
    region: Optional[str] = None,
    profile: Optional[str] = None,
    dry_run: bool = False,
) -> bool:
    """Start a single RDS instance. Returns True on success."""
    if dry_run:
        log_action(logger, db_identifier, "start-rds", "dry-run")
        return True
    client = get_rds_client(region=region, profile=profile)
    try:
        client.start_db_instance(DBInstanceIdentifier=db_identifier)
        log_action(logger, db_identifier, "start-rds", "success")
        return True
    except client.exceptions.InvalidDBInstanceStateFault as e:
        log_action(logger, db_identifier, "start-rds", "invalid-state", error=str(e))
        return False
    except Exception as e:
        log_action(logger, db_identifier, "start-rds", "error", error=str(e))
        raise


def main() -> int:
    parser = argparse.ArgumentParser(description="Start RDS instance(s)")
    parser.add_argument("identifiers", nargs="+", help="RDS instance identifier(s)")
    parser.add_argument("--region", help="AWS region")
    parser.add_argument("--profile", help="AWS profile")
    parser.add_argument("--dry-run", action="store_true", help="Preview only")
    args = parser.parse_args()
    ok = 0
    for db_id in args.identifiers:
        if start_rds_instance(db_id, args.region, args.profile, args.dry_run):
            ok += 1
    return 0 if ok == len(args.identifiers) else 1


if __name__ == "__main__":
    sys.exit(main())
