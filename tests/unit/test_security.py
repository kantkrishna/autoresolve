# tests/unit/test_security.py
import json
from unittest.mock import patch

from src.core.security.audit import log_audit_event
from src.core.security.pii_scrubber import PIIScrubber


def test_pii_scrubber_fallback():
    """Ensure basic regex scrubber functions if NLP engine is disabled."""
    scrubber = PIIScrubber()
    # Force fallback
    scrubber.analyzer = None

    raw_log = "User test@example.com connected from 192.168.1.1."
    scrubbed = scrubber._regex_fallback_scrub(raw_log)

    assert "test@example.com" not in scrubbed
    assert "[EMAIL_REDACTED]" in scrubbed
    assert "192.168.1.1" not in scrubbed
    assert "[IP_REDACTED]" in scrubbed


@patch("src.core.security.audit.audit_logger")
def test_soc2_audit_logger(mock_logger):
    """Ensure audit events are formatted as proper JSON."""
    log_audit_event(
        action="DRAFT_PR",
        actor="ExecutionAgent",
        resource="github/payment-gateway",
        status="SUCCESS",
        details={"pr_url": "https://github.com/org/repo/pull/1"},
    )

    assert mock_logger.info.called
    log_call = mock_logger.info.call_args[0][0]
    parsed_log = json.loads(log_call)

    assert parsed_log["action"] == "DRAFT_PR"
    assert parsed_log["actor"] == "ExecutionAgent"
    assert parsed_log["event_type"] == "security_audit"
    assert "timestamp" in parsed_log
