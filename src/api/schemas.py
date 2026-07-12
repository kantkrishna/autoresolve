# src/api/schemas.py
import logging
import re

from pydantic import BaseModel, Field, field_validator

logger = logging.getLogger(__name__)


class PrometheusAlert(BaseModel):
    """
    Strict validation of incoming webhooks to ensure malicious payloads
    (Prompt Injections disguised as alerts) are rejected at the edge.
    """

    status: str = Field(..., pattern="^(resolved|firing)$")
    alertname: str = Field(..., max_length=100)
    service: str = Field(..., max_length=100)
    description: str = Field(..., max_length=2000)

    @field_validator("description")
    @classmethod
    def enterprise_security_scan(cls, v: str) -> str:
        """
        Hardened Guardrail:
        In production, this is where we inject Lakera Guard or PromptArmor API calls.
        For MVP, we implement a layered Regex and Entropy heuristic.
        """
        # 1. Semantic Override Blocking
        suspicious_patterns = [
            r"(?i)(ignore|disregard|forget)\s+(all\s+)?(previous\s+)?(instructions|directives|prompts)",
            r"(?i)(system\s+prompt|you\s+are\s+now|bypass\s+rules)",
        ]
        for pattern in suspicious_patterns:
            if re.search(pattern, v):
                logger.warning(
                    "Security Alert: Semantic injection attempt intercepted."
                )
                raise ValueError("Security Exception: Adversarial intent detected.")

        # 2. Base64 / Encoding Obfuscation Blocking
        # Hackers often encode prompts to bypass basic regex.
        # Alerts rarely contain 50+ chars of unbroken alphanumeric strings.
        if len(re.findall(r"[A-Za-z0-9+/=]{60,}", v)) > 0:
            logger.warning("Security Alert: Potential Base64 encoded payload detected.")
            raise ValueError(
                "Security Exception: Malformed or encoded payload detected."
            )

        return v
