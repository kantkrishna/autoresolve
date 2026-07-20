# src/api/schemas.py
"""
API Request and Response Validation Schemas for AutoResolve.
Enforces strict structural data validation and prompt injection interception.
"""

import logging
import re
from typing import Optional

from pydantic import BaseModel, Field, field_validator

logger = logging.getLogger(__name__)

# List of known adversarial injection patterns targeting LLM orchestrations
SUSPICIOUS_SIGNATURES = [
    r"ignore\s+previous\s+instructions",
    r"system\s+prompt\s+override",
    r"download\s+env\s+values",
    r"print\s+cluster\s+secrets",
    r"execute\s+drop\s+database",
]


class PrometheusAlert(BaseModel):
    """
    Validates incoming payload structures from Prometheus Alertmanager.
    Actively scans textual inputs for adversarial injection signatures.
    """

    status: str = Field(..., description="Alert status, e.g., 'firing' or 'resolved'")
    alertname: str = Field(
        ..., description="The unique name identifying the operational alert metric"
    )
    service: str = Field(..., description="Target microservice domain name")
    description: str = Field(
        ..., description="Detailed textual description of the ongoing incident"
    )
    tracking_id: Optional[str] = Field(
        default=None, description="Deterministic idempotency hash"
    )

    @field_validator("description", mode="before")
    @classmethod
    def sanitize_and_check_injection(cls, value: str) -> str:
        """
        Scans description string values against dangerous instruction
        override signatures.
        """
        if not value:
            return value

        normalized_val = value.lower()
        for signature in SUSPICIOUS_SIGNATURES:
            if re.search(signature, normalized_val):
                logger.warning(
                    "🚨 Security Alert: Prompt injection pattern matched. Dropping payload data." # noqa: E501
                )
                raise ValueError(
                    "Potential prompt injection detected. Request rejected for security compliance." # noqa: E501
                )

        return value
