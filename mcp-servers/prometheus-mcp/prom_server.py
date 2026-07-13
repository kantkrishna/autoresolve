# mcp-servers/prometheus-mcp/server.py
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("Prometheus_Metrics_Tools")


@mcp.tool()
async def query_cpu_metrics(service_name: str) -> str:
    """Query Prometheus for the CPU utilization of a specific service."""
    # Placeholder for async httpx call to Prometheus
    # async with httpx.AsyncClient() as client:
    #     res = await client.get(f"http://prometheus:9090/api/v1/query?query={...}")

    return f"CPU utilization for {service_name} spiked to 98% at 03:00 UTC."


if __name__ == "__main__":
    mcp.run()
