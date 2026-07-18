# src/agents/graph.py
from typing import Literal

from langgraph.checkpoint.memory import MemorySaver
from langgraph.graph import END, StateGraph

from src.agents.nodes import (
    investigation_node,
    report_node,
    resolution_node,
    triage_node,
)

# Import the new Phase 6 nodes
from src.agents.nodes.execution import execution_node
from src.agents.nodes.review import review_node, route_after_review
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

    # 1. Register all nodes
    workflow.add_node("triage_node", triage_node)
    workflow.add_node("investigation_node", investigation_node)
    workflow.add_node("resolution_node", resolution_node)
    workflow.add_node("execution_node", execution_node)  # <-- NEW
    workflow.add_node("review_node", review_node)  # <-- NEW
    workflow.add_node("report_node", report_node)

    # 2. Set Entry Point
    workflow.set_entry_point("triage_node")

    # 3. Define Triage Routing
    workflow.add_conditional_edges(
        "triage_node",
        route_from_triage,
        {"investigation_node": "investigation_node", "report_node": "report_node"},
    )

    # 4. Define Linear Edges up to Execution
    workflow.add_edge("investigation_node", "resolution_node")
    workflow.add_edge("resolution_node", "execution_node")  # <-- Modified
    workflow.add_edge("execution_node", "review_node")  # <-- NEW

    # 5. Define HITL Review Routing
    workflow.add_conditional_edges(
        "review_node",
        route_after_review,
        {
            # If approved, route to report_node (which will act as our deploy/notify
            # step for now)
            "deploy_node": "report_node",
            # If revision requested, route back to execution to rewrite code
            "execution_node": "execution_node",
            # If rejected, end the graph
            "__end__": END,
        },
    )

    # 6. Final Edge
    workflow.add_edge("report_node", END)

    # This saves the graph's memory at every single step, allowing for
    # Human-in-the-Loop pauses or resuming from a network crash.
    checkpointer = MemorySaver()

    # CRITICAL ADDITION: interrupt_before=["review_node"]
    # This instructs the orchestrator to physically pause execution BEFORE running the
    # review_node.
    return workflow.compile(checkpointer=checkpointer, interrupt_before=["review_node"])


# ident_graph = build_incident_graph()

# Since the function already compiles the graph, we just need to assign it to 'app'!
app = build_incident_graph()