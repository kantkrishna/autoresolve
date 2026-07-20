# src/core/security/audit.py
# SOC2 Audit Logger for security and compliance
import json
import logging
from datetime import datetime, timezone
from typing import Any, Dict

# Create an isolated logger that routes to a dedicated file or SIEM forwarder
audit_logger = logging.getLogger("soc2_audit")
audit_logger.setLevel(logging.INFO)
# In production, attach a FileHandler writing to /var/log/autoresolve_audit.log


def log_audit_event(
    action: str, actor: str, resource: str, status: str, details: Dict[str, Any]
) -> None:
    """
    Writes structured, immutable JSON logs for SOC2 compliance.

    Args:
        action (str): The operation performed (e.g., "EXECUTE_TERRAFORM", "APPROVE_PR")
        actor (str): The entity performing the action
            (e.g., "ExecutionAgent", "slack_user_id")
        resource (str): The target infrastructure component
        status (str): "SUCCESS", "FAILURE", or "PENDING"
        details (Dict): Contextual metadata
    """
    event = {
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "action": action,
        "actor": actor,
        "resource": resource,
        "status": status,
        "details": details,
        "event_type": "security_audit",
    }

    audit_logger.info(json.dumps(event))
