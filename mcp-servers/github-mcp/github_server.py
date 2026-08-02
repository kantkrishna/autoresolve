import os

from github import Github, GithubException
from mcp.server.fastmcp import FastMCP

mcp = FastMCP("GitHub Remediation Server")

@mcp.tool()
def propose_github_fix(
    repo_name: str,
    file_path: str,
    new_content: str,
    commit_message: str,
    branch_name: str,
) -> str:
    """Creates a branch, updates a file, and drafts a PR with idempotency checks."""
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        return "Error: GITHUB_TOKEN environment variable is not set."

    try:
        g = Github(token)
        repo = g.get_repo(repo_name)
        default_branch = repo.default_branch
        source_ref = repo.get_branch(default_branch)

        # 1. Idempotent Branch Creation
        try:
            repo.create_git_ref(ref=f"refs/heads/{branch_name}", sha=source_ref.commit.sha)
        except GithubException as e:
            if e.status == 422 and "Reference already exists" in str(e.data):
                # Branch exists; proceed to update the file on the existing branch
                pass
            else:
                raise e

        # 2. File Update Logic
        try:
            file_obj = repo.get_contents(file_path, ref=default_branch)
            repo.update_file(
                path=file_path,
                message=commit_message,
                content=new_content,
                sha=file_obj.sha,
                branch=branch_name,
            )
        except GithubException as e:
            # Catch file update collisions if the SHA doesn't match
            return f"Error updating file content: {e.data}"

        # 3. Idempotent Pull Request Creation
        try:
            pr = repo.create_pull(
                title=commit_message,
                body="🤖 AutoResolve AI has drafted this fix. Please review.",
                head=branch_name,
                base=default_branch,
            )
            return f"Success! Pull request drafted: {pr.html_url}"
        except GithubException as e:
            # Safely handle the PR collision boundary
            if e.status == 422 and "A pull request already exists" in str(e.data):
                # Fetch the existing PR and return its URL gracefully
                existing_prs = repo.get_pulls(state='open', head=f"{repo.owner.login}:{branch_name}")
                if existing_prs.totalCount > 0:
                    return f"Success! Existing Pull request updated: {existing_prs[0].html_url}"
            raise e

    except Exception as e:
        return f"GitHub Execution Error: {str(e)}"

if __name__ == "__main__":
    mcp.run()