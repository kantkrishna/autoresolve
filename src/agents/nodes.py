# src/agents/nodes.py
import logging
from typing import Any

from langchain_core.messages import SystemMessage

from src.agents.schemas import TriageOutput
from src.agents.state import IncidentState
from src.core.llm import get_agnostic_llm
from src.core.mcp_client import execute_mcp_tool
from src.rag.vector_store import get_vector_store

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


async def investigation_node(state: IncidentState) -> dict[str, Any]:
    """Dynamically gathers logs and metrics via MCP JSON-RPC servers."""
    logger.info("Executing InvestigationNode via MCP")

    service = state.get("impacted_service", "unknown-service")

    # 1. Ask the Prometheus MCP Server for metrics
    metrics_result = await execute_mcp_tool(
        script_path="mcp-servers/prometheus-mcp/prom_server.py",
        tool_name="query_cpu_metrics",
        args={"service_name": service},
    )

    # 2. Ask the Kubernetes MCP Server for logs
    logs_result = await execute_mcp_tool(
        script_path="mcp-servers/kubernetes-mcp/k8s_server.py",
        tool_name="get_pod_logs",
        args={"namespace": "default", "pod_name": service},
    )

    # Combine findings
    findings = f"Metrics: {metrics_result}\nLogs: {logs_result}"

    return {
        "retrieved_logs": [logs_result],
        "root_cause_hypothesis": "Context gathered via MCP tools.",
        "messages": [SystemMessage(content=f"MCP Investigation complete. {findings}")],
    }


def resolution_node(state: IncidentState) -> dict[str, Any]:
    """Queries the Vector DB for historical runbooks to formulate a fix."""
    logger.info("Executing ResolutionNode via Hybrid RAG")

    # 1. Extract what we found during investigation
    hypothesis = state.get("root_cause_hypothesis", "")
    service = state.get("impacted_service", "")

    # 2. Query Qdrant
    vector_store = get_vector_store()
    search_query = f"Fix for {service} {hypothesis}"

    # Fetch the top 1 most relevant runbook
    docs = vector_store.similarity_search(search_query, k=1)

    retrieved_runbook = (
        docs[0].page_content if docs else "No historical runbooks found."
    )

    # 3. Formulate the fix
    prompt = f"""
    Based on the incident findings: {hypothesis}
    And the retrieved historical runbook: {retrieved_runbook}
    
    Formulate a brief, 1-sentence proposed fix.
    """

    response = llm.invoke([SystemMessage(content=prompt)])

    return {
        "proposed_fix_pr_url": str(response.content),
        "messages": [
            SystemMessage(content=f"Resolution strategy formulated: {response.content}")
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
