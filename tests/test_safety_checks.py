"""Tests for safety_checks module."""

import os
import pytest
from unittest.mock import patch, MagicMock

# Ensure project root on path
import sys
from pathlib import Path
sys.path.insert(0, str(Path(__file__).resolve().parent.parent))

from core.safety_checks import (
    is_production_environment,
    is_safety_disabled,
    check_rds_safe_to_stop,
    check_ec2_safe_to_stop,
)


def test_is_production_environment():
    assert is_production_environment("production") is True
    assert is_production_environment("prod") is True
    assert is_production_environment("PRODUCTION") is True
    assert is_production_environment("dev") is False
    assert is_production_environment("staging") is False
    assert is_production_environment(None) is False
    assert is_production_environment("") is False


def test_is_safety_disabled():
    with patch.dict(os.environ, {}, clear=False):
        assert is_safety_disabled() is False
    with patch.dict(os.environ, {"AWS_COST_SAVER_DISABLE_SAFETY": "1"}):
        assert is_safety_disabled() is True
    with patch.dict(os.environ, {"AWS_COST_SAVER_DISABLE_SAFETY": "true"}):
        assert is_safety_disabled() is True


@patch("core.safety_checks.get_rds_client")
def test_check_rds_safe_to_stop_blocks_production(mock_client):
    safe, reason = check_rds_safe_to_stop("db-1", env_name="production")
    assert safe is False
    assert "production" in reason.lower()


@patch("core.safety_checks.get_rds_client")
def test_check_rds_safe_to_stop_allowed_when_safety_disabled(mock_client):
    with patch("core.safety_checks.is_safety_disabled", return_value=True):
        safe, reason = check_rds_safe_to_stop("db-1", env_name="dev")
    assert safe is True


@patch("core.safety_checks.get_ec2_client")
def test_check_ec2_safe_to_stop_blocks_production(mock_client):
    safe, reason = check_ec2_safe_to_stop("i-123", env_name="prod")
    assert safe is False
    assert "production" in reason.lower()
