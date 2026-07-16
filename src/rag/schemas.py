from typing import Any, Dict

from pydantic import BaseModel, Field


class Citation(BaseModel):
    """Immutable link back to the source of truth."""

    source: str = Field(..., description="File path or URL of the runbook/document")
    chunk_id: str = Field(..., description="Unique hash of the specific document chunk")
    relevance_score: float = Field(
        ..., description="Mathematical relevance from the Cross-Encoder"
    )
    metadata: Dict[str, Any] = Field(default_factory=dict)


class ConfidenceScore(BaseModel):
    """Calibrated metric to mitigate LLM hallucinations."""

    retrieval_confidence: float = Field(
        ..., description="Base distance score from Vector DB"
    )
    reranker_score: float = Field(
        ..., description="Normalized logit from the Re-ranker"
    )
    evidence_quality: str = Field(..., description="Enum: 'high', 'medium', 'low'")
    composite_score: float = Field(
        ..., description="Weighted average of all confidence vectors"
    )
    is_actionable: bool = Field(
        ..., description="Circuit breaker: True if score exceeds safety threshold"
    )


class RetrievedDocument(BaseModel):
    """Standardized output for the AI context window."""

    content: str = Field(..., description="The raw text of the document")
    citation: Citation
