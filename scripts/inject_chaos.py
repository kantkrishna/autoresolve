# scripts/inject_chaos.py

# This script acts as a "chaos monkey." It will simulate a CPU spike alert firing from
# Prometheus directly into our API Gateway.
# Simulates a production outage by sending a mock Prometheus alert to the AutoResolve
# Ingestion Gateway. This triggers the AI workflow to demonstrate the system's
# ability to detect, analyze, and respond to incidents in real-time.

import sys
import json
import time
import httpx
import asyncio

# Enforce UTF-8 to prevent Windows terminal crashes
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

async def inject_chaos():
    print("==========================================================")
    print("🧨 AutoResolve - Phase 6: Simulating Production Outage")
    print("==========================================================\n")
    
    alert_payload = {
        "version": "4",
        "groupKey": "{}:{alertname=\"HighCPUUsage\"}",
        "status": "firing",
        "receiver": "autoresolve-webhook",
        "groupLabels": {"alertname": "HighCPUUsage"},
        "commonLabels": {
            "alertname": "HighCPUUsage",
            "severity": "critical",
            "namespace": "boutique-demo",
            "pod": "paymentservice-555dfd8b-mv2lc"
        },
        "commonAnnotations": {
            "summary": "High CPU usage detected on paymentservice",
            "description": "Pod paymentservice-555dfd8b-mv2lc is consuming over 80% CPU."
        },
        "alerts": [
            {
                "status": "firing",
                "labels": {"alertname": "HighCPUUsage", "severity": "critical", "pod": "paymentservice-555dfd8b-mv2lc"},
                "annotations": {"summary": "High CPU usage"}
            }
        ]
    }

    print("[INFO] 1. Simulated Prometheus Alert generated.")
    print("[INFO] 2. Firing webhook to AutoResolve Ingestion Gateway...")
    
    headers = {
        "Authorization": "Bearer mock-production-token",
        "X-API-Key": "mock-production-token",
        "Content-Type": "application/json"
    }

    try:
        async with httpx.AsyncClient() as client:
            response = await client.post(
                "http://localhost:8000/webhook/prometheus",
                json=alert_payload,
                headers=headers,
                timeout=10.0
            )
            response.raise_for_status()
            
            data = response.json()
            tracking_id = data.get("tracking_id", data.get("idempotency_key", "UNKNOWN"))
            
            print(f"\n[SUCCESS] Gateway returned 202 Accepted!")
            print(f"[SUCCESS] Incident assigned Tracking ID: {tracking_id}")
            print("\n🚨 KAFKA PIPELINE TRIGGERED! 🚨")
            print("Look at your AI Worker terminal logs! The swarm is waking up!")
            
    except httpx.HTTPStatusError as e:
        print(f"[ERROR] API Gateway rejected the payload: {e.response.text}")
    except httpx.RequestError as e:
        print(f"[ERROR] Failed to reach API Gateway. Ensure port-forwarding is running on port 8000.")
        print(f"Details: {e}")

if __name__ == "__main__":
    asyncio.run(inject_chaos())