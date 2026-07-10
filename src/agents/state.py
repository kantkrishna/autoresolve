# src/agents/state.py
from typing import TypedDict, Annotated, Sequence
from langchain_core.messages import BaseMessage
import operator

class IncidentState(TypedDict):
    """
    The central memory object for the LangGraph swarm. 
    Agents do not talk to each other; they mutate this state graph.
    """
    # The conversational history and tool invocations
    messages: Annotated[Sequence[BaseMessage], operator.add]
    
    # Incident Metadata
    incident_id: str
    severity: str
    impacted_service: str
    
    # Context Engineering: Stores constrained log chunks, not the whole file
    retrieved_logs: list[str]
    retrieved_metrics: dict
    
    # Resolution State
    root_cause_hypothesis: str
    proposed_fix_pr_url: str