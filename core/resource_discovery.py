"""
Resource discovery for aws-cost-saver.
Finds RDS, EC2, ECS resources by tag or from config.
"""

from typing import Any, Dict, List, Optional

from .aws_clients import get_ec2_client, get_ecs_client, get_rds_client


def discover_rds_by_tag(
    tag_key: str = "Environment",
    tag_value: str = "dev",
    region: Optional[str] = None,
    profile: Optional[str] = None,
) -> List[str]:
    """Return list of RDS instance identifiers with the given tag."""
    client = get_rds_client(region=region, profile=profile)
    identifiers = []
    paginator = client.get_paginator("describe_db_instances")
    for page in paginator.paginate():
        for db in page.get("DBInstances", []):
            arn = db.get("DBInstanceArn")
            if not arn:
                continue
            tags = client.list_tags_for_resource(ResourceName=arn)
            for t in tags.get("TagList", []):
                if t.get("Key") == tag_key and t.get("Value") == tag_value:
                    identifiers.append(db["DBInstanceIdentifier"])
                    break
    return identifiers


def discover_ec2_by_tag(
    tag_key: str = "Environment",
    tag_value: str = "dev",
    region: Optional[str] = None,
    profile: Optional[str] = None,
) -> List[str]:
    """Return list of EC2 instance IDs with the given tag."""
    client = get_ec2_client(region=region, profile=profile)
    filters = [
        {"Name": f"tag:{tag_key}", "Values": [tag_value]},
        {"Name": "instance-state-name", "Values": ["running", "stopped"]},
    ]
    resp = client.describe_instances(Filters=filters)
    ids = []
    for r in resp.get("Reservations", []):
        for i in r.get("Instances", []):
            ids.append(i["InstanceId"])
    return ids


def discover_ec2_by_name(
    name_tag_value: str,
    region: Optional[str] = None,
    profile: Optional[str] = None,
) -> List[str]:
    """Return EC2 instance IDs with Name tag matching (substring)."""
    client = get_ec2_client(region=region, profile=profile)
    filters = [
        {"Name": "tag:Name", "Values": [f"*{name_tag_value}*"]},
        {"Name": "instance-state-name", "Values": ["running", "stopped"]},
    ]
    resp = client.describe_instances(Filters=filters)
    ids = []
    for r in resp.get("Reservations", []):
        for i in r.get("Instances", []):
            ids.append(i["InstanceId"])
    return ids


def get_ecs_services_in_cluster(
    cluster: str,
    region: Optional[str] = None,
    profile: Optional[str] = None,
) -> List[Dict[str, Any]]:
    """Return list of ECS services in the cluster (service name and ARN)."""
    client = get_ecs_client(region=region, profile=profile)
    services = []
    paginator = client.get_paginator("list_services")
    for page in paginator.paginate(cluster=cluster):
        arns = page.get("serviceArns", [])
        if not arns:
            continue
        desc = client.describe_services(cluster=cluster, services=arns)
        for svc in desc.get("services", []):
            services.append({
                "serviceName": svc["serviceName"],
                "serviceArn": svc["serviceArn"],
                "desiredCount": svc.get("desiredCount", 0),
            })
    return services


def resolve_rds_identifiers(
    config_list: List[str],
    env_name: str,
    region: Optional[str] = None,
    profile: Optional[str] = None,
    discover_by_tag: bool = True,
) -> List[str]:
    """Combine config list with optionally discovered RDS by Environment tag."""
    result = list(config_list) if config_list else []
    if discover_by_tag:
        by_tag = discover_rds_by_tag(
            tag_key="Environment",
            tag_value=env_name,
            region=region,
            profile=profile,
        )
        for id in by_tag:
            if id not in result:
                result.append(id)
    return result


def resolve_ec2_identifiers(
    config_list: List[str],
    env_name: str,
    region: Optional[str] = None,
    profile: Optional[str] = None,
    discover_by_tag: bool = True,
) -> List[str]:
    """
    Resolve EC2 list from config. Config can contain instance IDs or Name tag values.
    If discover_by_tag, also add instances with Environment=<env_name>.
    """
    client = get_ec2_client(region=region, profile=profile)
    result = []
    # Instance IDs start with i-
    for item in config_list or []:
        if item.startswith("i-"):
            result.append(item)
        else:
            # Treat as Name tag search
            result.extend(discover_ec2_by_name(item, region, profile))
    if discover_by_tag:
        by_tag = discover_ec2_by_tag(
            tag_key="Environment",
            tag_value=env_name,
            region=region,
            profile=profile,
        )
        for iid in by_tag:
            if iid not in result:
                result.append(iid)
    return result
