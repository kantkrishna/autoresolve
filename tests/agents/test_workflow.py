from src.agents.nodes.execution import execution_node
from src.agents.nodes.review import review_node, route_after_review


def test_execution_node_generates_artifacts() -> None:
    initial_state = {"resolution_plan": "Increase memory to 2Gi", "audit_trail": []}
    result = execution_node(initial_state)
    assert "proposed_artifacts" in result
    assert result["human_approval_status"] == "pending"


def test_review_node_approval_routing() -> None:
    state = {"human_approval_status": "approved", "audit_trail": []}
    result = review_node(state)
    assert "APPROVED" in result["audit_trail"][-1]
    assert route_after_review(state) == "deploy_node"


def test_review_node_revision_routing() -> None:
    state = {
        "human_approval_status": "revision",
        "human_feedback": "Please use 4Gi instead of 2Gi.",
        "audit_trail": [],
    }
    result = review_node(state)
    assert "REVISION REQUESTED" in result["audit_trail"][-1]
    assert route_after_review(state) == "execution_node"
