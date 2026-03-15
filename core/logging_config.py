"""
Structured JSON logging for aws-cost-saver.
"""

import json
import logging
import os
from datetime import datetime, timezone
from typing import Any, Dict


class JSONFormatter(logging.Formatter):
    """Format log records as JSON with resource, action, status, timestamp."""

    def format(self, record: logging.LogRecord) -> str:
        log_obj: Dict[str, Any] = {
            "timestamp": datetime.now(timezone.utc).isoformat(),
            "level": record.levelname,
            "message": record.getMessage(),
        }
        if hasattr(record, "resource"):
            log_obj["resource"] = record.resource
        if hasattr(record, "action"):
            log_obj["action"] = record.action
        if hasattr(record, "status"):
            log_obj["status"] = record.status
        for key, value in record.__dict__.items():
            if key not in (
                "name", "msg", "args", "created", "filename", "funcName",
                "levelname", "levelno", "lineno", "module", "msecs",
                "pathname", "process", "processName", "relativeCreated",
                "stack_info", "exc_info", "exc_text", "thread", "threadName",
                "message", "taskName", "resource", "action", "status",
            ) and value is not None:
                log_obj[key] = value
        if record.exc_info:
            log_obj["exception"] = self.formatException(record.exc_info)
        return json.dumps(log_obj)


def setup_logging(use_json: bool = None) -> None:
    """Configure root logger. Use JSON if AWS_LAMBDA_FUNCTION_NAME is set or use_json=True."""
    use_json = use_json if use_json is not None else bool(os.environ.get("AWS_LAMBDA_FUNCTION_NAME"))
    root = logging.getLogger("aws_cost_saver")
    if not root.handlers:
        handler = logging.StreamHandler()
        handler.setFormatter(JSONFormatter() if use_json else logging.Formatter(
            "%(asctime)s %(levelname)s [%(name)s] %(message)s"
        ))
        root.addHandler(handler)
    level = os.environ.get("AWS_COST_SAVER_LOG_LEVEL", "INFO")
    root.setLevel(getattr(logging, level.upper(), logging.INFO))


def log_action(logger: logging.Logger, resource: str, action: str, status: str, **kwargs: Any) -> None:
    """Emit a structured action log."""
    extra = {"resource": resource, "action": action, "status": status, **kwargs}
    logger.info("%s %s %s", action, resource, status, extra=extra)
