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

        # 2. Sanitize the file path (Strip Docker's '/app/' or Windows 'C:/...' prefixes)
        # This guarantees a repository-relative path 
        # (e.g., 'kubernetes/lab/autoresolve-core.yaml')
        clean_path = file_path.replace('\\', '/')
        clean_path = re.sub(r'^/app/', '', clean_path)
        if "autoresolve/" in clean_path:
            clean_path = clean_path.split("autoresolve/")[-1]
            clean_path = clean_path.lstrip('/')

            # Smart Create vs. Update Logic
            try:
                # Attempt to fetch the existing file's SHA
                contents = repo.get_contents(clean_path, ref=branch_name)
                
                # If successful, UPDATE the existing file
                repo.update_file(
                    path=clean_path,
                    message=commit_message,
                    content=new_content,
                    sha=contents.sha,
                    branch=branch_name
                )
            except GithubException as e:
                if e.status == 404:
                    # If the file DOES NOT exist (404), CREATE it natively
                    repo.create_file(
                        path=clean_path,
                        message=commit_message,
                        content=new_content,
                        branch=branch_name
                    )
                else:
                    # Re-raise if it's a legitimate auth or network error
                    raise RuntimeError(f"GitHub API Error: {str(e)}")

        # # 2. File Update Logic
        # try:
        #     file_obj = repo.get_contents(file_path, ref=default_branch)
        #     repo.update_file(
        #         path=file_path,
        #         message=commit_message,
        #         content=new_content,
        #         sha=file_obj.sha,
        #         branch=branch_name,
        #     )
        # except GithubException as e:
        #     # Catch file update collisions if the SHA doesn't match
        #     return f"Error updating file content: {e.data}"

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