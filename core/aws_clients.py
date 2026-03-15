"""
AWS client factory for aws-cost-saver.
Provides boto3 clients with optional region and profile support.
"""

import os
from typing import Optional

import boto3
from botocore.config import Config


def get_rds_client(region: Optional[str] = None, profile: Optional[str] = None):
    """Return RDS boto3 client."""
    return _get_client("rds", region, profile)


def get_ecs_client(region: Optional[str] = None, profile: Optional[str] = None):
    """Return ECS boto3 client."""
    return _get_client("ecs", region, profile)


def get_ec2_client(region: Optional[str] = None, profile: Optional[str] = None):
    """Return EC2 boto3 client."""
    return _get_client("ec2", region, profile)


def get_autoscaling_client(region: Optional[str] = None, profile: Optional[str] = None):
    """Return Auto Scaling boto3 client."""
    return _get_client("autoscaling", region, profile)


def _get_client(
    service: str,
    region: Optional[str] = None,
    profile: Optional[str] = None,
):
    region = region or os.environ.get("AWS_REGION", os.environ.get("AWS_DEFAULT_REGION"))
    session_kw = {}
    if profile:
        session_kw["profile_name"] = profile
    session = boto3.Session(**session_kw)
    config = Config(retries={"max_attempts": 3, "mode": "standard"})
    return session.client(service, region_name=region, config=config)
