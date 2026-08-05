# scripts/incident_workflow.py
"""
AutoResolve Unified SRE Control Console & Operational CLI
--------------------------------------------------------------------------------
PURPOSE:
Master operational command-line interface for AutoResolve.

Integrates:
1. Chaos Injection: Simulates secure Prometheus alerts with ULID tracking keys.
2. Durable State Inspection: Pulls live agent reasoning and runbook context from Postgres.
3. Incident Thread Querying: Lists recent incident threads with user-configurable limits.
4. HITL Approval: Unpauses LangGraph execution threads to trigger GitHub PR creation.
"""

import sys
from pathlib import Path

# Ensure project root directory is in sys.path for relative imports
PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

import asyncio
import hashlib
import hmac
import json
import logging
import os
import random
import time
import urllib.request
from typing import List, Tuple

import psycopg
import ulid
from dotenv import load_dotenv

# Auto-load environment variables from .env file
load_dotenv(PROJECT_ROOT / ".env")

logging.basicConfig(level=logging.ERROR)
logger = logging.getLogger("incident_workflow")

# Webhook endpoint URL (API Gateway)
WEBHOOK_URL = os.getenv("AUTORESOLVE_WEBHOOK_URL", "http://localhost:8000/webhook/prometheus")
SECRET_KEY = b"dev-secret-key"

SCENARIOS = [
    {
        "alertname": "HighMemoryUsage",
        "service": "payment-gateway",
        "description": "Pod payment-gateway memory usage is at 99%. OOMKilled imminent.",
    },
    {
        "alertname": "CPUThrottlingSpike",
        "service": "payment-gateway",
        "description": "CPU throttling detected on payment-gateway. API Latency degrading.",
    },
    {
        "alertname": "DatabaseConnectionLost",
        "service": "payment-gateway",
        "description": "payment-gateway unable to reach mock-database. 500 errors spiking.",
    },
    {
        "alertname": "ScrapeTimeout",
        "service": "mock-prometheus",
        "description": "mock-prometheus target scrape timeout exceeded.",
    },
]


def get_postgres_dsn() -> str:
    """Resolves PostgreSQL DSN from env vars with smart fallback for local host execution."""
    dsn = os.getenv("POSTGRES_DSN") or os.getenv("DATABASE_URL")
    if dsn:
        return dsn
    return "postgresql://postgres:postgres@localhost:5432/autoresolve"


def fetch_latest_thread_id() -> str | None:
    """Queries the PostgreSQL checkpoints table safely to find the latest thread ID."""
    dsn = get_postgres_dsn()
    try:
        time.sleep(2.0)  # Allow async worker to pick up the event from Kafka
        with psycopg.connect(dsn) as conn:
            with conn.cursor() as cur:
                cur.execute("SELECT thread_id FROM checkpoints ORDER BY checkpoint_id DESC LIMIT 1;")
                row = cur.fetchone()
                if row:
                    return row[0]
    except Exception:
        pass
    return None


def fetch_recent_thread_ids(limit: int = 10) -> List[Tuple[str, str]]:
    """Queries the PostgreSQL checkpoints table safely to retrieve recent thread IDs and their last checkpoint."""
    dsn = get_postgres_dsn()
    try:
        with psycopg.connect(dsn) as conn:
            with conn.cursor() as cur:
                cur.execute(
                    """
                    SELECT thread_id, MAX(checkpoint_id) as max_cp
                    FROM checkpoints
                    GROUP BY thread_id
                    ORDER BY max_cp DESC
                    LIMIT %s;
                    """,
                    (limit,),
                )
                rows = cur.fetchall()
                return [(row[0], str(row[1])) for row in rows if row and row[0]]
    except Exception as e:
        print(f"❌ Database Query Failed: {e}")
        return []


def is_valid_ulid(ulid_str: str) -> bool:
    """Validates if a given string is a proper ULID."""
    if not ulid_str or len(ulid_str) != 26:
        return False
    try:
        ulid.ULID.from_str(ulid_str)
        return True
    except ValueError:
        return False


def get_target_thread_id(latest_tracking_id: str | None) -> str | None:
    """Prompts the user for a thread ID, defaults to latest, and validates ULID format."""
    default_display = latest_tracking_id if latest_tracking_id else "None"
    inc_id = input(f"Enter Thread ID [Default: {default_display}]: ").strip()
    
    if not inc_id:
        if not latest_tracking_id:
            print("❌ No active Thread ID available. Please inject chaos or query threads first.")
            return None
        return latest_tracking_id

    # Validate user-provided ULID format
    if not is_valid_ulid(inc_id):
        print(f"⚠️ Warning: '{inc_id}' does not match standard 26-character ULID format.")
        confirm = input("Do you still want to proceed with this ID? (y/N): ").strip().lower()
        if confirm != 'y':
            return None

    return inc_id


def inject_chaos_action() -> str | None:
    """Injects a random synthetic Prometheus fault and retrieves the worker-assigned ULID Thread ID."""
    scenario = random.choice(SCENARIOS)
    incident_ulid = str(ulid.ULID())
    payload = {
        "status": "firing",
        "alertname": scenario["alertname"],
        "service": scenario["service"],
        "description": scenario["description"],
        "tracking_id": incident_ulid,
    }
    payload_bytes = json.dumps(payload, separators=(",", ":")).encode("utf-8")
    signature = hmac.new(SECRET_KEY, payload_bytes, hashlib.sha256).hexdigest()
    api_key = os.getenv("AUTORESOLVE_API_KEY", "mock-production-token")
    headers = {
        "Content-Type": "application/json",
        "X-Signature": f"sha256={signature}",
        "X-API-Key": api_key,
        "Authorization": f"Bearer {api_key}",
    }

    print(f"\n🔥 Injecting Chaos: {scenario['alertname']} into '{scenario['service']}'...")
    try:
        req = urllib.request.Request(WEBHOOK_URL, data=payload_bytes, headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=5.0) as response:
            resp_body = json.loads(response.read().decode("utf-8"))
            print("✅ Alert Accepted by API Gateway!")
            print(f"📦 HTTP Ingestion Receipt ULID: {resp_body.get('tracking_id', incident_ulid)}")
            print("🔍 Querying PostgreSQL checkpointer for worker-assigned Thread ID...")

            thread_id = fetch_latest_thread_id() or resp_body.get("tracking_id", incident_ulid)
            print(f"🟢 Active LangGraph Thread Assigned: {thread_id}")
            return thread_id
    except Exception as e:
        print(f"❌ Failed to reach API Gateway: {e}")
        return None


async def inspect_incident_action(incident_id: str):
    """Fetches and displays the live incident graph state for a specific thread from PostgreSQL."""
    from src.agents.graph import app

    print(f"\n🔍 Querying PostgreSQL checkpointer for {incident_id}...")
    if not incident_id:
        print("❌ No active Thread ID found in memory. Please inject chaos or select a thread first.")
        return

    config = {"configurable": {"thread_id": incident_id}}
    try:
        state = await app.aget_state(config)
        if not state.values:
            print(f"❌ No state found for Thread ID: {incident_id}")
            print("Note: The async worker is still consuming the event from Kafka. Try again in 3 seconds.")
            return

        print("\n" + "=" * 60)
        print(f"📋 INCIDENT INSPECTION REPORT: {incident_id}")
        print("=" * 60)
        values = state.values
        service = values.get("impacted_service", "N/A")
        severity = values.get("severity", "N/A")
        root_cause = (
            values.get("root_cause_hypothesis")
            or values.get("root_cause")
            or "Analysis still in progress..."
        )

        proposed_fix = values.get("proposed_fix")
        if not proposed_fix or proposed_fix == "":
            messages = values.get("messages", [])
            if messages:
                last_msg = messages[-1]
                if hasattr(last_msg, "tool_calls") and last_msg.tool_calls:
                    tool_args = last_msg.tool_calls[0].get("args", {})
                    proposed_fix = f"Drafted File: {tool_args.get('file_path')}\nCommit Message: {tool_args.get('commit_message')}"
                else:
                    proposed_fix = getattr(last_msg, "content", "Drafting remediation plan...")
        
        proposed_fix = proposed_fix or "Drafting remediation plan..."

        next_step = values.get("next_step", "N/A")

        print(f"🛠️ Impacted Service : {service}")
        print(f"📊 Severity / Status: {severity}")
        print(f"🔄 Next Action      : {next_step}")
        print("\n🧠 Root Cause Hypothesis:")
        print(f"   {root_cause}")
        print("\n💡 Proposed Remediation / Code Fix:")
        print(f"   {proposed_fix}")
        print("\n" + "=" * 60)

        current_node = state.next
        print(f"⏸️ Current Execution Node: {current_node}")
        if current_node and "execution_node" not in str(current_node):
            print("⚠️ NOTICE: The AI is still investigating or formulating its fix.")
            print("   Wait a few seconds and run inspection again before approving.")
        print("=" * 60)
    except Exception as e:
        print(f"❌ Error fetching incident state: {e}")


async def query_incident_threads_action() -> str | None:
    """Queries and lists recent incident thread IDs from database checkpoints with clean HITL status and full PR URLs."""
    import re

    limit_str = input("Enter number of threads to retrieve [Default: 10]: ").strip()
    try:
        limit = int(limit_str) if limit_str else 10
        if limit <= 0:
            limit = 10
    except ValueError:
        limit = 10

    print(f"\n🔍 Querying PostgreSQL checkpointer for top {limit} recent incident threads...")
    base_results = fetch_recent_thread_ids(limit=limit)

    if not base_results:
        print("❌ No incident threads found in PostgreSQL database.")
        return None

    from src.agents.graph import app

    results = []
    for thread_id, checkpoint_id in base_results:
        hitl_status = "No"
        pr_url = "N/A"
        try:
            config = {"configurable": {"thread_id": thread_id}}
            state = await app.aget_state(config)
            if state and state.values:
                values = state.values
                raw_url = values.get("proposed_fix_pr_url")
                if raw_url:
                    # Extract clean https URL using regex if conversational text was cached
                    match = re.search(r'https://github\.com/[^\s]+', str(raw_url))
                    pr_url = match.group(0) if match else str(raw_url)
                    hitl_status = "Yes"
                elif state.next:
                    if any("execution" in str(n) or "review" in str(n) for n in state.next):
                        hitl_status = "Pending"
                    else:
                        hitl_status = "In Progress"
        except Exception:
            pass
        results.append((thread_id, hitl_status, pr_url))

    print("\n" + "=" * 110)
    print(f"📜 RECENT INCIDENT WORKFLOW THREADS (Top {len(results)})")
    print("=" * 110)
    print(f"{'#':<4} | {'Thread ID (ULID)':<26} | {'HITL Exec':<10} | {'GitHub PR URL'}")
    print("-" * 110)

    for idx, (thread_id, hitl_status, pr_url) in enumerate(results, 1):
        print(f"{idx:<4} | {thread_id:<26} | {hitl_status:<10} | {pr_url}")
    print("=" * 110)

    select_str = input("\nSelect a thread number or paste ULID to set as active (or press Enter to skip): ").strip()
    if select_str.isdigit():
        idx = int(select_str) - 1
        if 0 <= idx < len(results):
            selected_id = results[idx][0]
            print(f"✅ Active Thread ID set to: {selected_id}")
            return selected_id
        else:
            print("⚠️ Invalid thread number selected.")
    elif is_valid_ulid(select_str):
        print(f"✅ Active Thread ID set to: {select_str}")
        return select_str
    elif select_str:
        print("⚠️ Invalid input.")
    return None


async def approve_incident_action(incident_id: str):
    """Unpauses the LangGraph execution flow to trigger GitHub PR generation."""
    from src.agents.graph import app

    print(f"\n✅ Approving Remediation for Thread: {incident_id}...")
    if not incident_id:
        print("❌ No active Thread ID provided for approval.")
        return

    config = {"configurable": {"thread_id": incident_id}}
    try:
        state = await app.aget_state(config)
        if not state.next:
            print(f"⚠️ Thread {incident_id} is not currently paused in a wait state.")
            return

        print("🚀 Resuming LangGraph execution pipeline...")
        async for event in app.astream(None, config=config):
            for node_name, state_update in event.items():
                
                # Bulletproof check for execution errors
                if isinstance(state_update, dict):
                    err = state_update.get("error")
                    
                    # Fallback check: Did we inject an error into the messages array?
                    msgs = state_update.get("messages", [])
                    if not err and msgs:
                        last_msg = msgs[-1]
                        if hasattr(last_msg, "content") and "❌" in str(last_msg.content):
                            err = last_msg.content
                            
                    if err:
                        print(f"\n❌ Pipeline Error in Node '{node_name}':\n{err}")
                        print("⚠️ Graph execution halted. The LLM provided bad instructions or the MCP server failed.")
                        return
                
                print(f"💾 Node '{node_name}' executed successfully.")
                
                if isinstance(state_update, dict) and state_update.get("proposed_fix_pr_url"):
                    print(f"\n🎉 PULL REQUEST CREATED SUCCESSFULLY!")
                    print(f"🔗 GitHub PR URL: {state_update['proposed_fix_pr_url']}")

        print(f"\n🎯 Incident workflow {incident_id} completed successfully!")
    except Exception as e:
        print(f"\n❌ FATAL: Error during HITL approval execution:\n{e}")


async def main_menu():
    """Main operational CLI loop."""
    latest_tracking_id = None

    while True:
        print("\n=======================================================")
        print("           AUTORESOLVE UNIFIED CONTROL CONSOLE          ")
        print("=======================================================")
        if latest_tracking_id:
            print(f"📌 Active Thread ID: {latest_tracking_id}")
        else:
            print("📌 Active Thread ID: None (Inject Chaos or Query Threads to select)")
        print("-------------------------------------------------------")
        print("1. 🧨 Inject Chaos (Simulate Outage)")
        print("2. 🔍 Inspect Active Incident State")
        print("3. 📜 Query Incident Threads (List Database Checkpoints)")
        print("4. ✅ Approve HITL Response (Execute Remediation)")
        print("5. 🚪 Exit")
        print("=======================================================")

        choice = input("Select an option (1-5): ").strip()

        try:
            if choice == "1":
                latest_tracking_id = inject_chaos_action()
            elif choice == "2":
                target_id = get_target_thread_id(latest_tracking_id)
                if target_id:
                    await inspect_incident_action(target_id)
            elif choice == "3":
                selected_thread = await query_incident_threads_action()
                if selected_thread:
                    latest_tracking_id = selected_thread
            elif choice == "4":
                target_id = get_target_thread_id(latest_tracking_id)
                if target_id:
                    await approve_incident_action(target_id)
            elif choice == "5":
                print("👋 Exiting AutoResolve Console. Goodbye!")
                sys.exit(0)
            else:
                print("⚠️ Invalid option selected. Please enter a number between 1 and 5.")
        except Exception as e:
            print(f"❌ An error occurred: {e}")


if __name__ == "__main__":
    if sys.platform == "win32":
        asyncio.run(
            main_menu(),
            loop_factory=asyncio.WindowsSelectorEventLoopPolicy().new_event_loop,
        )
    else:
        asyncio.run(main_menu())