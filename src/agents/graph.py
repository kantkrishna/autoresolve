# src/agents/graph.py
from typing import Literal

from langgraph.graph import END, StateGraph

from src.agents.nodes import (
    investigation_node,
    report_node,
    resolution_node,
    triage_node,
)
from src.agents.state import IncidentState


def route_from_triage(
    state: IncidentState,
) -> Literal["investigation_node", "report_node"]:
    """Conditional edge routing based on Triage Agent's decision."""
    if state.get("next_step") == "SILENCE":
        return "report_node"
    return "investigation_node"


def build_incident_graph() -> StateGraph:
    """Compiles the agent nodes and edges into a deterministic state machine."""
    workflow = StateGraph(IncidentState)

    workflow.add_node("triage_node", triage_node)
    workflow.add_node("investigation_node", investigation_node)
    workflow.add_node("resolution_node", resolution_node)
    workflow.add_node("report_node", report_node)

    workflow.set_entry_point("triage_node")

    workflow.add_conditional_edges(
        "triage_node",
        route_from_triage,
        {"investigation_node": "investigation_node", "report_node": "report_node"},
    )

    workflow.add_edge("investigation_node", "resolution_node")
    workflow.add_edge("resolution_node", "report_node")
    workflow.add_edge("report_node", END)

    return workflow.compile()


incident_graph = build_incident_graph()
