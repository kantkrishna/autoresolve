# src/agents/nodes.py
import logging
from typing import Any

from langchain_core.messages import SystemMessage

from src.agents.schemas import TriageOutput
from src.agents.state import IncidentState
from src.core.llm import get_agnostic_llm

logger = logging.getLogger(__name__)
llm = get_agnostic_llm(temperature=0.1)


def triage_node(state: IncidentState) -> dict[str, Any]:
    """Analyzes the raw alert and determines the severity and routing."""
    incident_id = state.get("incident_id", "UNKNOWN")
    logger.info(f"Executing TriageNode for Incident: {incident_id}")

    structured_llm = llm.with_structured_output(TriageOutput)

    # Safely extract the last message payload
    messages = state.get("messages", [])
    alert_payload = messages[-1].content if messages else "No alert payload provided."

    prompt = f"""
    You are an Expert Site Reliability Engineer. 
    Analyze this incident payload and determine if it is actionable or noise:
    {alert_payload}
    """

    response = structured_llm.invoke([SystemMessage(content=prompt)])

    return {
        "severity": response.severity,
        "impacted_service": response.impacted_service,
        "next_step": response.next_step,
        "messages": [
            SystemMessage(content=f"Triage complete. Verdict: {response.summary}")
        ],
    }


def investigation_node(state: IncidentState) -> dict[str, Any]:
    """Gathers logs and metrics (Placeholder for Phase 7 MCP Integration)."""
    logger.info("Executing InvestigationNode")
    return {
        # This will securely slide through the reduce_logs window
        "retrieved_logs": [
            "[INFO] System stable",
            "[ERROR] OOMKilled Exception in payment-gateway",
        ],
        "root_cause_hypothesis": "The payment-gateway service exceeded memory limits.",
        "messages": [
            SystemMessage(
                content="Investigation complete. Logs retrieved and hypothesis formed."
            )
        ],
    }


def resolution_node(state: IncidentState) -> dict[str, Any]:
    """Determines the fix (Placeholder for Phase 8 RAG Integration)."""
    logger.info("Executing ResolutionNode")
    return {
        "proposed_fix_pr_url": "https://github.com/mock-org/repo/pull/1",
        "messages": [
            SystemMessage(content="Resolution strategy formulated and PR drafted.")
        ],
    }


def report_node(state: IncidentState) -> dict[str, Any]:
    """Generates the final incident post-mortem."""
    logger.info("Executing ReportNode")
    return {
        "messages": [
            SystemMessage(content="Incident closed and documented in knowledge base.")
        ]
    }
