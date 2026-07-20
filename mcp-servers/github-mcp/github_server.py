import os

from github import Github
from mcp.server.fastmcp import FastMCP

# Initialize the FastMCP server for GitHub
mcp = FastMCP("GitHub Remediation Server")


@mcp.tool()
def propose_github_fix(
    repo_name: str,
    file_path: str,
    new_content: str,
    commit_message: str,
    branch_name: str,
) -> str:
    """
    Forks the repository (if necessary), creates a new branch, updates a specified file
    (e.g., deployment YAML) to resolve an incident, and drafts a Pull Request.
    """
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        return "Error: GITHUB_TOKEN environment variable is not set."

    try:
        g = Github(token)
        repo = g.get_repo(repo_name)

        # Get default branch to branch off from
        default_branch = repo.default_branch
        source_ref = repo.get_branch(default_branch)

        # Create new branch for the fix
        repo.create_git_ref(ref=f"refs/heads/{branch_name}", sha=source_ref.commit.sha)

        # Fetch the file to get its current SHA (required for updating)
        file_obj = repo.get_contents(file_path, ref=default_branch)

        # Update the file
        repo.update_file(
            path=file_path,
            message=commit_message,
            content=new_content,
            sha=file_obj.sha,
            branch=branch_name,
        )

        # Create the Pull Request
        pr = repo.create_pull(
            title=commit_message,
            body="🤖 AutoResolve AI has drafted this fix based on a recent telemetry alert. Please review.",  # noqa: E501
            head=branch_name,
            base=default_branch,
        )

        return f"Success! Pull request drafted: {pr.html_url}"

    except Exception as e:
        return f"GitHub Execution Error: {str(e)}"


if __name__ == "__main__":
    # Start the MCP stdio server
    mcp.run_stdio()
