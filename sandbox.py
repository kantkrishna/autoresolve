# sandbox.py
import asyncio
import logging

from dotenv import load_dotenv
from langchain_core.messages import HumanMessage

from src.agents.graph import incident_graph
from src.agents.state import IncidentState
from src.rag.vector_store import ingest_document

load_dotenv()

logging.basicConfig(level=logging.INFO)

async def run_sandbox():
    print("--- 1. Ingesting Runbook into Qdrant ---")
    with open("data/runbooks/payment-gateway-OOM.md", "r") as f:
        runbook_text = f.read()

    ingest_document(text=runbook_text, metadata={"service": "payment-gateway"})

    print("\n--- 2. Triggering AI Swarm ---")
    # Simulate an incoming Prometheus webhook payload
    alert_payload = """
    Alert: HighMemoryUsage
    Service: payment-gateway
    Status: FIRING
    Description: Pod payment-gateway-pod-xyz memory usage is at 99%. OOMKilled imminent.
    """

    # Initialize the graph memory state
    initial_state: IncidentState = {
        "incident_id": "INC-001",
        "messages": [HumanMessage(content=alert_payload)],
    }

    # We must provide a thread_id for the SQLite MemorySaver to track the state
    config = {"configurable": {"thread_id": "1"}}

    # Invoke the graph
    print("Graph executing... (Watch the magic happen)\n")
    final_state = await incident_graph.ainvoke(initial_state, config=config)

    print("\n--- 3. Final State ---")
    print(f"Impacted Service: {final_state.get('impacted_service')}")
    print(f"Severity: {final_state.get('severity')}")
    print(f"Proposed Fix: {final_state.get('proposed_fix_pr_url')}")


if __name__ == "__main__":
    asyncio.run(run_sandbox())
