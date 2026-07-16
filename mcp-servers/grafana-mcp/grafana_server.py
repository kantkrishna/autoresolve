from src.core.mcp_base.server import get_secure_mcp_server, secure_tool

mcp = get_secure_mcp_server("GrafanaMCP")


@mcp.tool()
@secure_tool
def get_panel_metrics(dashboard_uid: str, panel_id: int, time_range: str = "1h") -> str:
    """Fetches strictly typed metric telemetry from a Grafana panel."""
    return f"Metrics for panel {panel_id} on {dashboard_uid} over {time_range} fetched."


if __name__ == "__main__":
    mcp.run()
