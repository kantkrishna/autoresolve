# src/agents/nodes.py renamed to src/agents/nodes/__init__.py to recognize the nodes directory as an importable "package"
# src/agents/nodes/__init__.py
import logging
from typing import Any, Dict

from langchain_core.messages import SystemMessage

from src.agents.schemas import TriageOutput, RemediationArtifacts
from src.agents.state import IncidentState
from src.core.llm import get_agnostic_llm
from src.core.mcp_client import execute_mcp_tool
from src.rag.vector_store import get_vector_store

logger = logging.getLogger(__name__)
llm = get_agnostic_llm(temperature=0.1)

# --- TRIAGE NODE ---
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

# --- INVESTIGATION NODE ---
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

# --- RESOLUTION NODE ---
def resolution_node(state: IncidentState) -> dict[str, Any]:
    """Queries the Vector DB for historical runbooks to formulate a fix."""
    logger.info("Executing ResolutionNode via Hybrid RAG")

    # 1. Extract what we found during investigation
    hypothesis = state.get("root_cause_hypothesis", "")
    service = state.get("impacted_service", "")

    # 2. Query Qdrant
    vector_store = get_vector_store()
    docs = vector_store.similarity_search(f"Fix for {service} {hypothesis}", k=1)
    retrieved_runbook = docs[0].page_content if docs else "No historical runbooks found."
    prompt = f"Based on findings: {hypothesis} and runbook: {retrieved_runbook}, formulate a brief, 1-sentence proposed fix."
    response = llm.invoke([SystemMessage(content=prompt)])
    return {
        "proposed_fix": str(response.content),
        "messages": [SystemMessage(content=f"Resolution strategy: {response.content}")],
    }

# --- EXECUTION NODE ---
def execution_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """Execution Agent: Drafts remediation artifacts."""
    logger.info("Execution Agent: Drafting remediation code...")
    resolution_plan = state.get("proposed_fix", "")
    # Placeholder for actual GitHub MCP call logic
    mock_yaml = "apiVersion: apps/v1\nkind: Deployment\n..."
    artifacts = RemediationArtifacts(
        kubernetes_yaml=mock_yaml,
        pr_title="fix(infra): Auto-remediate",
        pr_body=f"Generated fix: {resolution_plan}",
    )
    return {
        "proposed_artifacts": artifacts.model_dump(),
        "human_approval_status": "pending",
        "messages": [SystemMessage(content="Execution complete: PR drafted.")]
    }

# --- REVIEW NODE ---
def review_node(state: Dict[str, Any]) -> Dict[str, Any]:
    """Review Agent: Processes HITL feedback."""
    logger.info("Review Agent processing status.")
    status = state.get("human_approval_status", "pending")
    return {"audit_trail": [f"Review status: {status}"]}

# --- REPORT NODE ---
def report_node(state: IncidentState) -> dict[str, Any]:
    """Generates the final incident post-mortem."""
    logger.info("Executing ReportNode")
    return {
        "messages": [
            SystemMessage(content="Incident closed and documented in knowledge base.")
        ]
    }

__all__ = [
    "triage_node", "investigation_node", "resolution_node", 
    "execution_node", "review_node", "report_node"
]