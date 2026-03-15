"""Tests for cost_estimation module."""

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.cost_estimation import estimate_savings_hourly, format_savings, DEFAULT_HOURLY_RATES


def test_estimate_savings_hourly():
    # 1 RDS, 2 EC2, 12 hours
    rds_rate = DEFAULT_HOURLY_RATES["rds"]
    ec2_rate = DEFAULT_HOURLY_RATES["ec2_small"]
    expected = 1 * rds_rate * 12 + 2 * ec2_rate * 12
    result = estimate_savings_hourly(rds_count=1, ec2_count=2, hours_stopped=12.0)
    assert result == round(expected, 2)


def test_estimate_savings_zero():
    assert estimate_savings_hourly() == 0.0


def test_format_savings():
    assert format_savings(43.2) == "$43.20"
    assert format_savings(0) == "$0.00"
