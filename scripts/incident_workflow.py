"""
scripts/incident_workflow.py

AutoResolve Unified SRE Control Console & Operational CLI
--------------------------------------------------------------------------------
PURPOSE:
Master operational command-line interface for AutoResolve. Integrates:
    1. Chaos Injection: Simulates secure Prometheus alerts.
    2. Durable State Inspection: Pulls live agent reasoning and runbook context from Postgres.
    3. HITL Approval: Unpauses LangGraph execution threads to trigger GitHub PR creation.

EXECUTION INSTRUCTIONS:
Execute directly inside the containerized AI worker environment:
    docker exec -it infra-ai-worker-1 python scripts/incident_workflow.py
--------------------------------------------------------------------------------
"""

import sys
import asyncio
if sys.platform == "win32":
    asyncio.set_event_loop_policy(asyncio.WindowsSelectorEventLoopPolicy())
import hashlib
import hmac
import json
import logging
import os
import random
import time
import urllib.request
from pathlib import Path

from dotenv import load_dotenv

# FORCE the local tunnel address so it never tries to use K8s internal DNS
os.environ["DB_URI"] = "postgresql://admin:admin@127.0.0.1:5433/autoresolve"
os.environ["POSTGRES_DSN"] = "postgresql://admin:admin@127.0.0.1:5433/autoresolve"

# Load the rest of the env file, overriding any stale system variables
load_dotenv(override=True)

# --- SUPPRESS NOISY DATABASE POOL LOGS ---
logging.basicConfig(level=logging.ERROR, format="%(asctime)s [%(levelname)s] %(message)s")
logging.getLogger("psycopg").setLevel(logging.ERROR)
logging.getLogger("psycopg_pool").setLevel(logging.ERROR)
# ----------------------------------------

PROJECT_ROOT = Path(__file__).resolve().parent.parent
if str(PROJECT_ROOT) not in sys.path:
    sys.path.insert(0, str(PROJECT_ROOT))

# from src.agents.graph import app  # noqa: E402
import psycopg  # noqa: E402

# WEBHOOK_URL = "http://api-gateway:8000/webhook/prometheus"
WEBHOOK_URL = "http://127.0.0.1:8000/webhook/prometheus"
SECRET_KEY = b"dev-secret-key"

SCENARIOS = [
    {
        "alertname": "HighMemoryUsage",
        "service": "payment-gateway",
        "description": "Pod payment-gateway memory usage is at 99%. OOMKilled imminent."
    },
    {
        "alertname": "CPUThrottlingSpike",
        "service": "payment-gateway",
        "description": "CPU throttling detected on payment-gateway. API Latency degrading."
    },
    {
        "alertname": "DatabaseConnectionLost",
        "service": "payment-gateway",
        "description": "payment-gateway unable to reach mock-database. 500 errors spiking."
    },
    {
        "alertname": "ScrapeTimeout",
        "service": "mock-prometheus",
        "description": "mock-prometheus target scrape timeout exceeded."
    }
]


def fetch_latest_thread_id() -> str | None:
    """Queries the PostgreSQL checkpoints table safely to find the latest thread ID."""
    dsn = os.getenv("POSTGRES_DSN") or os.getenv("DATABASE_URL") or "postgresql://postgres:postgres@postgres:5432/autoresolve"
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


def inject_chaos_action():
    """Injects a random synthetic Prometheus fault and retrieves the worker-assigned Thread ID."""
    scenario = random.choice(SCENARIOS)
    payload = {
        "status": "firing",
        "alertname": scenario["alertname"],
        "service": scenario["service"],
        "description": scenario["description"]
    }
    
    payload_bytes = json.dumps(payload, separators=(',', ':')).encode('utf-8')
    signature = hmac.new(SECRET_KEY, payload_bytes, hashlib.sha256).hexdigest()
    
    api_key = os.getenv("AUTORESOLVE_API_KEY", "mock-production-token")
    
    headers = {
        "Content-Type": "application/json",
        "X-Signature": f"sha256={signature}",
        "X-API-Key": api_key,
        "Authorization": f"Bearer {api_key}"
    }
    
    print(f"\n🔥 Injecting Chaos: {scenario['alertname']} into '{scenario['service']}'...")
    try:
        req = urllib.request.Request(WEBHOOK_URL, data=payload_bytes, headers=headers, method="POST")
        with urllib.request.urlopen(req, timeout=5.0) as response:
            status_code = response.status
            resp_body = json.loads(response.read().decode("utf-8"))
            print("✅ Alert Accepted by API Gateway!")
            print(f"📦 HTTP Ingestion Receipt UUID: {resp_body.get('tracking_id', 'N/A')}")
            
            print("🔍 Querying PostgreSQL checkpointer for worker-assigned Thread ID...")
            thread_id = fetch_latest_thread_id()
            if thread_id:
                print(f"🎯 Assigned Kafka Thread ID: {thread_id}")
                print("👉 (This ID has been automatically saved to your session memory)")
                print("⏳ Note: Give the AI worker 3-5 seconds to complete its investigation loop before inspecting.")
                return thread_id
            else:
                print("⚠️  Worker is still processing. Check 'docker logs infra-ai-worker-1' for progress.")
                return None
    except urllib.error.HTTPError as e:
        print(f"❌ API Gateway rejected payload: HTTP Error {e.code}: {e.reason}")
        return None
    except urllib.error.URLError as e:
        print(f"❌ Failed to reach API Gateway: {e.reason}")
        print("💡 Hint: Ensure your port-forwarding tunnel is active: kubectl port-forward svc/autoresolve-api-gateway 8000:8000 -n autoresolve-ai")
        return None
    except TimeoutError:
        print("❌ Request timed out! The API Gateway took too long to respond.")
        return None
    except Exception as e:
        print(f"❌ Failed to inject alert: {e}")
        return None


async def inspect_incident_action(incident_id: str):
    """Fetches and displays the paused LangGraph state from PostgreSQL."""
    from src.agents.graph import app  # <--- INJECT HERE
    
    print(f"\n🔍 Querying PostgreSQL checkpointer for {incident_id}...")

    if not incident_id:
        print("❌ No active Thread ID found in memory. Please inject chaos first or provide a Thread ID.")
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
        
        service = values.get('impacted_service', 'N/A')
        severity = values.get('severity', 'N/A')
        root_cause = values.get('root_cause_hypothesis') or values.get('root_cause') or 'Analysis still in progress...'
        proposed_fix = values.get('proposed_fix') or values.get('remediation_plan') or 'Drafting remediation plan...'
        next_step = values.get('next_step', 'N/A')

        print(f"🛠️ Impacted Service : {service}")
        print(f"📊 Severity / Status: {severity}")
        print(f"🔄 Next Action      : {next_step}")
        print(f"\n🧠 Root Cause Hypothesis:")
        print(f"   {root_cause}")
        
        print(f"\n💡 Proposed Remediation / Code Fix:")
        print(f"   {proposed_fix}")
        
        print("\n" + "=" * 60)
        current_node = state.next
        print(f"⏸️  Current Execution Node: {current_node}")
        if current_node and 'execution_node' not in str(current_node):
            print("⚠️  NOTICE: The AI is still investigating or formulating its fix.")
            print("   Wait a few seconds and run inspection again before approving.")
        print("=" * 60)
    except Exception as e:
        print(f"❌ Error fetching incident state: {e}")


async def approve_incident_action(incident_id: str):
    """Unpauses the LangGraph execution thread to execute the GitHub MCP fix."""
    from src.agents.graph import app  # <--- INJECT HERE
    
    print(f"\n✅ Sending HITL Approval for {incident_id}...")
    if not incident_id:
        print("❌ No active Thread ID found in memory. Please inject chaos first or provide a Thread ID.")
        return

    config = {"configurable": {"thread_id": incident_id}}
    try:
        state = await app.aget_state(config)
        if not state.next:
            print(f"❌ Incident {incident_id} has no pending interruptions.")
            print("It either finished executing or hasn't reached the execution node yet.")
            return

        print(f"\n✅ Found paused graph for {incident_id}.")
        print(f"⏸️  Paused right before executing: {state.next}")
        print("🚀 Human Approval received. Resuming execution and triggering GitHub MCP...\n")

        async for output in app.astream(None, config):
            for key, value in output.items():
                print(f"Finished node: {key}")

        print("\n🎉 Execution complete! Check your GitHub repository for the drafted Pull Request.")
    except Exception as e:
        print(f"❌ Error during approval execution: {e}")


async def main_menu():
    latest_tracking_id = None
    
    while True:
        print("\n=======================================================")
        print("         AUTORESOLVE UNIFIED CONTROL CONSOLE")
        print("=======================================================")
        if latest_tracking_id:
            print(f"📌 Active Thread ID: {latest_tracking_id}")
        else:
            print("📌 Active Thread ID: None (Inject Chaos to generate)")
        print("-------------------------------------------------------")
        print("1. 🧨 Inject Chaos (Simulate Outage)")
        print("2. 🔍 Inspect Active Incident State")
        print("3. ✅ Approve HITL Response (Execute Remediation)")
        print("4. 🚪 Exit")
        print("=======================================================")
        
        choice = input("Select an option (1-4): ").strip()
        
        try:
            if choice == "1":
                latest_tracking_id = inject_chaos_action()
            elif choice == "2":
                inc_id = input(f"Enter Thread ID [Default: {latest_tracking_id}]: ").strip()
                target_id = inc_id if inc_id else latest_tracking_id
                await inspect_incident_action(target_id)
            elif choice == "3":
                inc_id = input(f"Enter Thread ID [Default: {latest_tracking_id}]: ").strip()
                target_id = inc_id if inc_id else latest_tracking_id
                await approve_incident_action(target_id)
            elif choice == "4":
                print("\nExiting AutoResolve Unified Control Console. Stay reliable!")
                sys.exit(0)
            else:
                print("❌ Invalid option. Please select a number between 1 and 4.")
        except (KeyboardInterrupt, SystemExit):
            print("\nExiting...")
            sys.exit(0)
        except Exception as ex:
            print(f"❌ An error occurred: {ex}")


if __name__ == "__main__":
    try:
        asyncio.run(main_menu())
    except KeyboardInterrupt:
        print("\nExiting...")
        sys.exit(0)