# src/api/schemas.py
from pydantic import BaseModel, Field, field_validator

class PrometheusAlert(BaseModel):
    """
    Strict validation of incoming webhooks to ensure malicious payloads 
    (Prompt Injections disguised as alerts) are rejected at the edge.
    """
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