import logging
from typing import Any, Dict

logger = logging.getLogger(__name__)


def review_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """
    Review Agent: Processes the injected human feedback after graph resumption.
    Returns the updated audit trail and routes conditionally.
    """
    status = state.get("human_approval_status", "pending")
    feedback = state.get("human_feedback", "No feedback provided.")
    audit_trail = state.get("audit_trail", [])

    logger.info(f"Review Agent processing HITL status: {status}")

    if status == "approved":
        audit_trail.append("Human-in-the-Loop: APPROVED. Proceeding to deployment.")
    elif status == "rejected":
        audit_trail.append(
            f"Human-in-the-Loop: REJECTED. Reason: {feedback}. Terminating."
        )
    elif status == "revision":
        audit_trail.append(
            f"Human-in-the-Loop: REVISION REQUESTED. Feedback: {feedback}. "
            "Routing back to Execution."
        )
    else:
        audit_trail.append("Human-in-the-Loop: Timeout or invalid state.")

    return {"audit_trail": audit_trail}


def route_after_review(state: Dict[str, Any]) -> str:
    """Conditional edge routing logic for LangGraph."""
    status = state.get("human_approval_status", "pending")
    if status == "approved":
        # CRITICAL FIX: Change from non-existent 'deploy_node' to 'execution_node'
        return "execution_node" 
    elif status == "revision":
        return "resolution_node" # Route back to formulate a new fix
    elif status == "rejected":
        return "report_node"     # Finalize incident without action
    return "__end__"