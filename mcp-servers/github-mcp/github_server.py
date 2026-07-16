from src.core.mcp_base.server import get_secure_mcp_server, secure_tool

mcp = get_secure_mcp_server("GitHubMCP")


@mcp.tool()
@secure_tool
def create_pull_request(repo: str, title: str, body: str, branch: str) -> str:
    """Drafts a new PR for infrastructure/code auto-remediation."""
    return f"PR '{title}' created successfully on {repo}/{branch}."


@mcp.prompt()
def review_prompt(pr_number: int) -> str:
    """System prompt for human reviewers analyzing the generated PR."""
    return f"Please review AutoResolve PR #{pr_number} for security and compliance."


if __name__ == "__main__":
    mcp.run()
