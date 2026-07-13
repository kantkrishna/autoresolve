# src/agents/schemas.py
from pydantic import BaseModel, Field


class TriageOutput(BaseModel):
    """Structured output enforcing how the Triage Agent must respond."""

    severity: str = Field(..., description="Must be 'CRITICAL', 'WARNING', or 'NOISE'")
    impacted_service: str = Field(
        ..., description="The name of the failing microservice"
    )
    summary: str = Field(..., description="A 1-sentence summary of the alert")
    next_step: str = Field(..., description="Must be 'INVESTIGATE' or 'SILENCE'")
