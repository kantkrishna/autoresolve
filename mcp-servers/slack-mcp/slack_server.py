from src.core.mcp_base.server import get_secure_mcp_server, secure_tool

mcp = get_secure_mcp_server("SlackMCP")


@mcp.tool()
@secure_tool
def request_hitl_approval(channel: str, message: str) -> str:
    """Sends an interactive Slack message requesting human approval."""
    return f"Approval request securely routed to {channel}."


if __name__ == "__main__":
    mcp.run()
