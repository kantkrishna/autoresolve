# scripts/test_live_mcp.py
# This script tests the live MCP servers for Kubernetes and Prometheus by querying
# the running k3d cluster and Prometheus instance. It demonstrates how to use the  
# MCP servers to pull live data for AI training and validation.

import sys
import asyncio
from pathlib import Path

# Enforce UTF-8 to prevent Windows terminal crashes
if sys.platform == "win32":
    sys.stdout.reconfigure(encoding="utf-8")

# Dynamically add the specific MCP server directories to the Python path 
# so we can import them even though the parent folders have hyphens.
base_dir = Path(__file__).resolve().parent.parent
sys.path.append(str(base_dir / "mcp-servers" / "kubernetes-mcp"))
sys.path.append(str(base_dir / "mcp-servers" / "prometheus-mcp"))

# Now we can safely import the functions directly from the files
try:
    from k8s_server import get_pod_logs
    from prom_server import query_prometheus
except ImportError as e:
    print(f"[ERROR] Failed to import MCP modules. Ensure your file paths are correct. Details: {e}")
    sys.exit(1)

async def main():
    print("==============================================")
    print("🧪 Testing Live Kubernetes MCP Server")
    print("==============================================\n")
    
    # Let's ask the MCP server to pull the logs for the payment service!
    logs = await get_pod_logs(namespace="boutique-demo", label_selector="app=paymentservice", lines=10)
    print(logs)
    
    print("\n==============================================")
    print("🧪 Testing Live Prometheus MCP Server")
    print("==============================================\n")
    
    # Let's ask the MCP server to check the CPU usage of the boutique pods!
    promql = 'sum(rate(container_cpu_usage_seconds_total{namespace="boutique-demo"}[1m])) by (pod) > 0'
    #promql = 'up{kubernetes_namespace="boutique-demo"}'
    metrics = await query_prometheus(query=promql)
    print(metrics)

if __name__ == "__main__":
    asyncio.run(main())