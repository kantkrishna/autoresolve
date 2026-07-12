# src/agents/state.py
import operator
from typing import Annotated, Dict, List, Sequence, TypedDict

from langchain_core.messages import BaseMessage
from pydantic import BaseModel


# --- FIX D: Strict Type Hinting for Metrics ---
class MetricTimeSeries(BaseModel):
    """Strict schema to ensure the LLM receives consistently formatted Prometheus data."""  # noqa: E501

    timestamps: List[int]
    values: List[float]
    unit: str


class TelemetryData(BaseModel):
    service_name: str
    metrics: Dict[str, MetricTimeSeries]


# --- FIX C: Graph Memory Bloat Mitigation ---
def reduce_logs(existing_logs: List[str], new_logs: List[str]) -> List[str]:
    """
    Custom LangGraph Reducer: Acts as a sliding window.
    Instead of appending logs infinitely, it truncates to keep only
    the most recent 500 lines to strictly protect the context window.
    """
    combined = existing_logs + new_logs
    return combined[-500:]


# --- MASTER AGENT STATE ---
class IncidentState(TypedDict):
    """
    The central memory object for the LangGraph swarm.
    """

    messages: Annotated[Sequence[BaseMessage], operator.add]

    # Incident Metadata
    incident_id: str
    severity: str
    impacted_service: str

    # Safely bounded Context Engineering
    retrieved_logs: Annotated[List[str], reduce_logs]  # Sliding window applied
    retrieved_metrics: TelemetryData  # Strict types applied

    # Resolution State
    root_cause_hypothesis: str
    proposed_fix_pr_url: str
