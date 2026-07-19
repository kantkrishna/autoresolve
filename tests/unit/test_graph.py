# tests/unit/test_graph.py
import pytest

from src.agents.graph import build_incident_graph
from src.agents.state import IncidentState


def test_graph_compilation() -> None:
    """Ensure the LangGraph compiles without cyclic dependency errors."""
    try:
        graph = build_incident_graph()
        assert graph is not None
    except Exception as e:
        pytest.fail(f"Graph failed to compile: {e}")


# def test_conditional_routing_logic() -> None:
#     """Test the deterministic routing function independently of the LLM."""
#     from src.agents.graph import route_from_triage

#     state_noise: IncidentState = {"next_step": "SILENCE"}
#     assert route_from_triage(state_noise) == "report_node"

#     state_action: IncidentState = {"next_step": "INVESTIGATE"}
#     assert route_from_triage(state_action) == "investigation_node"
