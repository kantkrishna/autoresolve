# mcp-servers/kubernetes-mcp/server.py
# MCP servers to pull live data directly from the cluster using the official Python
# Kubernetes and HTTP clients.

import os
import logging
from typing import List, Dict, Any, Optional
from mcp.server.fastmcp import FastMCP
from kubernetes import client, config

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger("kubernetes-mcp")

mcp = FastMCP("kubernetes-mcp")

# --- UPDATED AUTHENTICATION LOGIC ---
try:
    # 1. Try In-Cluster Auth (When running inside the Docker Pod)
    config.load_incluster_config()
    v1_api = client.CoreV1Api()
    logger.info("Successfully loaded IN-CLUSTER Kubernetes config (using ServiceAccount).")
except config.ConfigException:
    try:
        # 2. Fallback to Local Auth (When running from your VS Code terminal)
        config.load_kube_config()
        v1_api = client.CoreV1Api()
        logger.info("Successfully loaded LOCAL kube config.")
    except Exception as e:
        logger.error(f"Failed to load any Kubernetes config: {e}")
        v1_api = None

@mcp.tool()
async def get_pod_logs(namespace: str, label_selector: str, lines: int = 100) -> str:
    """Retrieves live stdout/stderr logs from pods matching a label selector."""
    if not v1_api:
        return "Error: Kubernetes client not initialized. Cannot connect to cluster."
        
    try:
        pods = v1_api.list_namespaced_pod(namespace=namespace, label_selector=label_selector)
        if not pods.items:
            return f"No pods found in namespace '{namespace}' matching label '{label_selector}'."
            
        pod_name = pods.items[0].metadata.name
        logger.info(f"Fetching logs for pod: {pod_name}")
        
        logs = v1_api.read_namespaced_pod_log(name=pod_name, namespace=namespace, tail_lines=lines)
        return f"--- Live Logs for {pod_name} ---\n{logs}"
        
    except client.exceptions.ApiException as e:
        return f"Kubernetes API Error fetching logs: {e.reason}"
    except Exception as e:
        return f"Unexpected error fetching logs: {str(e)}"

if __name__ == "__main__":
    logger.info("Starting Live Kubernetes MCP Server...")
    mcp.run()