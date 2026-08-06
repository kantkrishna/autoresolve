# mcp-servers/github-mcp/github_server.py

# This file is part of the GitHub Remediation Server, which provides an interface to
# propose fixes to GitHub repositories.

import os
import re

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
    """Creates a branch, updates or creates a file, and drafts a PR with idempotency checks."""
    token = os.getenv("GITHUB_TOKEN")
    if not token:
        return "Error: GITHUB_TOKEN environment variable is not set."

    # Defensive Fallback for repo name
    configured_repo = os.getenv("GITHUB_REPO")
    if not repo_name or "your-org" in repo_name or "owner" in repo_name or "repo" in repo_name:
        if configured_repo:
            repo_name = configured_repo

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
                pass
            else:
                raise e

        # 2. Sanitize file path (Strip leading slashes or container prefixes)
        file_path = re.sub(r"^(/app/|C:[\/\\])", "", file_path).lstrip("/")

        # 3. Robust File Commit (Update if exists, Create if not)
        file_updated = False
        try:
            file_obj = repo.get_contents(file_path, ref=branch_name)
            repo.update_file(
                path=file_path,
                message=commit_message,
                content=new_content,
                sha=file_obj.sha,
                branch=branch_name,
            )
            file_updated = True
        except GithubException as e:
            if e.status == 404:
                # File doesn't exist yet, create it fresh
                repo.create_file(
                    path=file_path,
                    message=commit_message,
                    content=new_content,
                    branch=branch_name,
                )
                file_updated = True
            else:
                return f"Error updating file content: {e.data}"

        if not file_updated:
            return "Error: Failed to commit file changes to the branch."

        # 4. Idempotent Pull Request Creation
        try:
            pr = repo.create_pull(
                title=commit_message,
                body="🤖 AutoResolve AI has drafted this fix. Please review.",
                head=branch_name,
                base=default_branch,
            )
            return f"Success! Pull request drafted: {pr.html_url}"
        except GithubException as e:
            if e.status == 422 and "A pull request already exists" in str(e.data):
                existing_prs = repo.get_pulls(state='open', head=f"{repo.owner.login}:{branch_name}")
                if existing_prs.totalCount > 0:
                    return f"Success! Existing Pull request updated: {existing_prs[0].html_url}"
            return f"GitHub Execution Error: {str(e)}"

    except Exception as e:
        return f"GitHub Execution Error: {str(e)}"

if __name__ == "__main__":
    mcp.run()