# tests/integration/test_mcp.py
import pytest

from src.core.mcp_client import execute_mcp_tool


@pytest.mark.asyncio
async def test_kubernetes_mcp_execution() -> None:
    """Test that the client can successfully communicate with the K8s MCP server."""
    result = await execute_mcp_tool(
        script_path="mcp-servers/kubernetes-mcp/k8s_server.py",
        tool_name="get_pod_logs",
        args={"namespace": "demo", "pod_name": "payment-gateway"},
    )

    assert "OOMKilled" in result
    assert "payment-gateway" in result


@pytest.mark.asyncio
async def test_prometheus_mcp_execution() -> None:
    """Test that the client can successfully communicate with the Prom MCP server."""
    result = await execute_mcp_tool(
        script_path="mcp-servers/prometheus-mcp/prom_server.py",
        tool_name="query_cpu_metrics",
        args={"service_name": "payment-gateway"},
    )

    assert "CPU utilization" in result
