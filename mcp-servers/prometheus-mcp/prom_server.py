# mcp-servers/prometheus-mcp/server.py
# Asynchronous HTTP client that fires real PromQL queries against the live Prometheus
# service running inside k3d cluster via the port-forward

import os
import json
import logging
import httpx
from typing import Dict, Any
from mcp.server.fastmcp import FastMCP

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("prometheus-mcp")

mcp = FastMCP("prometheus-mcp")

# Since we mapped k3d port 9090 to localhost, we query it directly
PROMETHEUS_URL = os.getenv("PROMETHEUS_URL", "http://localhost:9090")

@mcp.tool()
async def query_prometheus(query: str) -> str:
    """
    Executes a PromQL query against the live Prometheus time-series database.
    
    Args:
        query: The PromQL string (e.g., 'sum(rate(container_cpu_usage_seconds_total[1m])) by (pod)')
    """
    logger.info(f"Executing live PromQL query: {query}")
    
    try:
        async with httpx.AsyncClient() as client:
            response = await client.get(
                f"{PROMETHEUS_URL}/api/v1/query",
                params={"query": query},
                timeout=10.0
            )
            response.raise_for_status()
            data = response.json()
            
            if data.get("status") != "success":
                return f"Prometheus returned an error: {data.get('error')}"
                
            results = data.get("data", {}).get("result", [])
            
            if not results:
                return f"Query executed successfully, but returned 0 metric results."
            
            # Format the output cleanly for the LLM
            formatted_output = "--- Live Prometheus Metrics ---\n"
            for metric in results[:10]: # Limit to top 10 results to protect context window
                pod_name = metric.get("metric", {}).get("pod", "unknown_pod")
                value = metric.get("value", [0, "0"])[1]
                formatted_output += f"Pod: {pod_name} | Value: {value}\n"
                
            return formatted_output
            
    except httpx.RequestError as e:
        return f"HTTP Connection Error to Prometheus: {str(e)}"
    except Exception as e:
        return f"Unexpected error querying Prometheus: {str(e)}"

if __name__ == "__main__":
    logger.info("Starting Live Prometheus MCP Server...")
    mcp.run()