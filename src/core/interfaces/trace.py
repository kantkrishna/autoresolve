from typing import Any, Dict, List, Protocol

from pydantic import BaseModel, Field


class TraceMetadata(BaseModel):
    trace_id: str = Field(..., description="Unique ID for the distributed trace")
    service_name: str = Field(..., description="Name of the failing microservice")
    duration_ms: float = Field(..., description="Total duration of trace in ms")
    has_errors: bool = Field(..., description="Flag if trace contains exceptions")


class TraceRetriever(Protocol):
    """
    Domain-Driven Interface for retrieving distributed traces.
    Decouples the AI Swarm from specific tracing vendors (Jaeger, OpenTelemetry).
    """

    async def get_trace_spans(self, trace_id: str) -> List[Dict[str, Any]]:
        """Retrieve full chronological spans for a specific trace."""
        ...

    async def query_failing_traces(
        self, service: str, lookback_minutes: int = 15
    ) -> List[TraceMetadata]:
        """Query the tracing backend for recent errors in a specific service."""
        ...
