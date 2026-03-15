"""
Basic cost estimation for aws-cost-saver.
Uses approximate hourly rates for estimation; for production use AWS Cost Explorer API.
"""

# Approximate hourly USD rates (single-AZ, on-demand, us-east-1 style)
# Update or override via config for your region/instance types
DEFAULT_HOURLY_RATES = {
    "rds": 0.10,      # Small RDS instance approx
    "ec2_small": 0.01,   # t3.micro / t3.small approx
    "ec2_medium": 0.04,
    "ecs_task": 0.02,   # Fargate small task approx
    "asg_instance": 0.02,
}


def estimate_savings_hourly(
    rds_count: int = 0,
    ec2_count: int = 0,
    ecs_tasks_stopped: int = 0,
    asg_instances_stopped: int = 0,
    hours_stopped: float = 12.0,
    rates: dict = None,
) -> float:
    """
    Estimate daily savings in USD when resources are stopped for hours_stopped.
    """
    rates = rates or DEFAULT_HOURLY_RATES
    per_hour = 0.0
    per_hour += rds_count * rates.get("rds", DEFAULT_HOURLY_RATES["rds"])
    per_hour += ec2_count * rates.get("ec2_small", DEFAULT_HOURLY_RATES["ec2_small"])
    per_hour += ecs_tasks_stopped * rates.get("ecs_task", DEFAULT_HOURLY_RATES["ecs_task"])
    per_hour += asg_instances_stopped * rates.get("asg_instance", DEFAULT_HOURLY_RATES["asg_instance"])
    return round(per_hour * hours_stopped, 2)


def format_savings(amount_usd: float) -> str:
    """Return formatted string for cost output."""
    return f"${amount_usd:.2f}"
