"""
Safety checks for aws-cost-saver.
Prevents accidental stop of production or opted-out resources.
"""

import os
from typing import Any, Dict, Optional

from .aws_clients import get_ec2_client, get_rds_client


# Tag that explicitly opts out of cost-saver automation
COST_SAVER_DISABLED_TAG = "cost-saver"
COST_SAVER_DISABLED_VALUE = "false"

# Environment tag used to detect production
ENVIRONMENT_TAG = "Environment"
PRODUCTION_VALUES = ("production", "prod")


def is_production_environment(env_name: Optional[str] = None) -> bool:
    """Return True if the given environment name is considered production."""
    if not env_name:
        return False
    return env_name.lower() in PRODUCTION_VALUES


def is_safety_disabled() -> bool:
    """Return True if safety checks are disabled via env (e.g. in Lambda)."""
    return os.environ.get("AWS_COST_SAVER_DISABLE_SAFETY", "").lower() in ("1", "true", "yes")


def check_rds_safe_to_stop(
    db_identifier: str,
    region: Optional[str] = None,
    profile: Optional[str] = None,
    env_name: Optional[str] = None,
) -> tuple[bool, str]:
    """
    Verify RDS instance is safe to stop.
    Returns (is_safe, reason).
    """
    if is_production_environment(env_name):
        return False, "Environment is production; stopping is blocked."
    if is_safety_disabled():
        return True, "Safety checks disabled by environment."

    client = get_rds_client(region=region, profile=profile)
    try:
        resp = client.describe_db_instances(DBInstanceIdentifier=db_identifier)
    except client.exceptions.DBInstanceNotFoundFault:
        return False, f"RDS instance not found: {db_identifier}"

    instances = resp.get("DBInstances", [])
    if not instances:
        return False, f"RDS instance not found: {db_identifier}"

    instance = instances[0]
    tags_resp = client.list_tags_for_resource(ResourceName=instance["DBInstanceArn"])
    tags = {t["Key"]: t["Value"] for t in tags_resp.get("TagList", [])}

    if tags.get(COST_SAVER_DISABLED_TAG, "").lower() == COST_SAVER_DISABLED_VALUE:
        return False, f"RDS {db_identifier} has {COST_SAVER_DISABLED_TAG}=false."
    if tags.get(ENVIRONMENT_TAG, "").lower() in PRODUCTION_VALUES:
        return False, f"RDS {db_identifier} is tagged as production."

    return True, "OK"


def check_ec2_safe_to_stop(
    instance_id: str,
    region: Optional[str] = None,
    profile: Optional[str] = None,
    env_name: Optional[str] = None,
) -> tuple[bool, str]:
    """
    Verify EC2 instance is safe to stop.
    Returns (is_safe, reason).
    """
    if is_production_environment(env_name):
        return False, "Environment is production; stopping is blocked."
    if is_safety_disabled():
        return True, "Safety checks disabled by environment."

    client = get_ec2_client(region=region, profile=profile)
    try:
        resp = client.describe_instances(InstanceIds=[instance_id])
    except client.exceptions.ClientError as e:
        if "InvalidInstanceID" in str(e) or "NotFound" in str(e):
            return False, f"EC2 instance not found: {instance_id}"
        raise

    instances = []
    for r in resp.get("Reservations", []):
        instances.extend(r.get("Instances", []))
    if not instances:
        return False, f"EC2 instance not found: {instance_id}"

    instance = instances[0]
    tags = {t["Key"]: t["Value"] for t in instance.get("Tags", [])}

    if tags.get(COST_SAVER_DISABLED_TAG, "").lower() == COST_SAVER_DISABLED_VALUE:
        return False, f"EC2 {instance_id} has {COST_SAVER_DISABLED_TAG}=false."
    if tags.get(ENVIRONMENT_TAG, "").lower() in PRODUCTION_VALUES:
        return False, f"EC2 {instance_id} is tagged as production."

    return True, "OK"


def check_safe_to_modify(
    resource_type: str,
    resource_id: str,
    region: Optional[str] = None,
    profile: Optional[str] = None,
    env_name: Optional[str] = None,
) -> tuple[bool, str]:
    """Dispatch to the right safety check by resource type."""
    if resource_type == "rds":
        return check_rds_safe_to_stop(resource_id, region, profile, env_name)
    if resource_type == "ec2":
        return check_ec2_safe_to_stop(resource_id, region, profile, env_name)
    if resource_type in ("ecs", "asg"):
        if is_production_environment(env_name):
            return False, "Environment is production; modification is blocked."
        if is_safety_disabled():
            return True, "Safety checks disabled by environment."
        return True, "OK"
    return True, "OK"
