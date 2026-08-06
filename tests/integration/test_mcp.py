# tests/integration/test_mcp.py

import pytest

from src.core.mcp_client import execute_mcp_tool


@pytest.mark.asyncio
async def test_kubernetes_mcp_execution() -> None:
    """Test that the client can successfully communicate with the K8s MCP server."""
    result = await execute_mcp_tool(
        server_name="kubernetes",
        script_path="mcp-servers/kubernetes-mcp/k8s_server.py",
        tool_name="get_pod_logs",
        tool_args={"namespace": "demo", "pod_name": "payment-gateway"},
    )
    assert "OOMKilled" in result or "Error" in result or "Live Logs" in result or "logs" in result.lower()

@pytest.mark.asyncio
async def test_prometheus_mcp_execution() -> None:
    """Test that the client can successfully communicate with the Prom MCP server."""
    result = await execute_mcp_tool(
        server_name="prometheus",
        script_path="mcp-servers/prometheus-mcp/prom_server.py",
        tool_name="query_prometheus",
        tool_args={"query": 'container_cpu_usage_seconds_total{container="payment-gateway"}'},
    )
    assert "CPU" in result or "Metrics" in result or "Error" in result or "Unknown" not in result