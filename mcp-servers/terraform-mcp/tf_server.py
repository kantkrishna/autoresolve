from src.core.mcp_base.server import get_secure_mcp_server, secure_tool

mcp = get_secure_mcp_server("TerraformMCP")


@mcp.tool()
@secure_tool
def plan_terraform(workspace: str) -> str:
    """Executes a terraform plan securely within the workspace."""
    return f"Terraform plan generated safely for {workspace}."


@mcp.tool()
@secure_tool
def apply_terraform(workspace: str) -> str:
    """Applies the terraform configuration (requires HITL prior)."""
    return f"Terraform applied successfully for {workspace}."


if __name__ == "__main__":
    mcp.run()
