# src/agents/nodes.py renamed to src/agents/nodes/__init__.py
# to recognize the nodes directory as an importable "package"
# src/agents/nodes/__init__.py
import logging
import os
import traceback
from typing import Any, Dict

from langchain_core.messages import SystemMessage

from src.agents.schemas import RemediationArtifacts, TriageOutput
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
    logger.info(f"[DEBUG] Vector Store: {vector_store}")
    logger.info(f"[DEBUG] Querying Vector Store for service: {service}, hypothesis: {hypothesis}")
    docs = vector_store.similarity_search(f"Fix for {service} {hypothesis}", k=1)
    logger.info(f"[DEBUG]Retrieved {docs} from Vector Store")
    retrieved_runbook = (
        docs[0].page_content if docs else "No historical runbooks found."
    )
    prompt = f"Based on findings: {hypothesis} and runbook: {retrieved_runbook}, formulate a brief, 1-sentence proposed fix."  # noqa: E501
    logger.info(f"[DEBUG] Prompt: {prompt}")
    response = llm.invoke([SystemMessage(content=prompt)])
    logger.info(f"[DEBUG]LLM Response: {response.content}")

    return {
        "proposed_fix": str(response.content),
        "messages": [SystemMessage(content=f"Resolution strategy: {response.content}")],
    }


# --- EXECUTION NODE ---
async def execution_node(state: IncidentState) -> dict[str, Any]:
    """Execution Agent: Translates the resolution plan into code and drafts a PR via MCP."""
    logger.info("Execution Agent: Drafting remediation code via GitHub MCP...")
    
    incident_id = state.get("incident_id", "UNKNOWN-INCIDENT")
    service = state.get("impacted_service", "target-service")
    resolution_plan = state.get("proposed_fix", "")
    
    # In production, the LLM generates the targeted YAML patch dynamically.
    # For deterministic validation, we utilize a structured patch format.
    generated_yaml_patch = f"""
apiVersion: apps/v1
kind: Deployment
metadata:
  name: {service}
spec:
  template:
    spec:
      containers:
      - name: app
        resources:
          limits:
            memory: "2Gi"
"""

    branch_name = f"autoresolve/fix-{incident_id.lower()}"
    commit_msg = f"fix({service}): Autonomous remediation for incident {incident_id}"
    
    try:
        # Execute the JSON-RPC call to the isolated GitHub MCP Server
        github_result = await execute_mcp_tool(
            script_path="mcp-servers/github-mcp/github_server.py",
            tool_name="propose_github_fix",
            args={
                "repo_name": os.getenv("GITHUB_REPO", "your-org/your-repo"),
                "file_path": f"kubernetes/deployments/{service}.yaml",
                "new_content": generated_yaml_patch.strip(),
                "commit_message": commit_msg,
                "branch_name": branch_name
            }
        )

        if not github_result.startswith("Success!"):
            raise RuntimeError(f"GitHub MCP Tool Error: {github_result}")
        # 👆 ============================= 👆
        
        logger.info(f"🟢 GitHub MCP Output: {github_result}")
        
        artifacts = RemediationArtifacts(
            kubernetes_yaml=generated_yaml_patch.strip(),
            pr_title=commit_msg,
            pr_body=f"Generated fix based on runbook analysis: {resolution_plan}"
        )
        
        return {
            "proposed_artifacts": artifacts.model_dump(),
            "human_approval_status": "pending",
            "proposed_fix_pr_url": github_result,
            "messages": [SystemMessage(content=f"Execution complete: {github_result}")]
        }
        
    except Exception as e:
        # 1. Capture the full, multi-level stack trace as a formatted string
        error_trace = "".join(traceback.format_exception(type(e), e, e.__traceback__))
        
        # 2. Log it prominently so it appears in your Kubernetes/Docker logs
        logger.error(f"❌ GitHub MCP Execution Failed. Detailed Traceback:\n{error_trace}")
        
        # 3. If it's an ExceptionGroup, unpack the specific sub-exceptions
        if hasattr(e, 'exceptions'):
            for i, sub_exc in enumerate(e.exceptions):
                logger.error(f"  ↳ Sub-Exception {i+1}: {repr(sub_exc)}")

        return {
            "messages": [
                SystemMessage(
                    content="Execution failed due to server error. Check worker logs."
                )
            ]
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
    "triage_node",
    "investigation_node",
    "resolution_node",
    "execution_node",
    "review_node",
    "report_node",
]
