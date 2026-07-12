# src/api/schemas.py
import hashlib

from pydantic import BaseModel, Field, computed_field, field_validator


class PrometheusAlert(BaseModel):
    """Strict validation of incoming webhooks with built-in idempotency."""

    status: str = Field(..., pattern="^(resolved|firing)$")
    alertname: str = Field(..., max_length=100)
    service: str = Field(..., max_length=100)
    description: str = Field(..., max_length=1000)

    @field_validator("description")
    @classmethod
    def sanitize_description(cls, v: str) -> str:
        """Basic Guardrail against obvious prompt injections."""
        dangerous_phrases = ["ignore previous instructions", "system prompt"]
        if any(phrase in v.lower() for phrase in dangerous_phrases):
            raise ValueError("Potential prompt injection detected in alert payload.")
        return v

    @computed_field
    @property
    def tracking_id(self) -> str:
        """
        Generates a deterministic SHA-256 hash based on core alert properties.
        Used for Kafka partition routing and idempotency.
        """
        unique_signature = f"{self.alertname}-{self.service}-{self.status}"
        return hashlib.sha256(unique_signature.encode("utf-8")).hexdigest()
