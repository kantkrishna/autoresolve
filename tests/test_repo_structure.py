# tests/test_repo_structure.py
from pathlib import Path

import pytest

REQUIRED_FILES = [
    "README.md",
    "CONTRIBUTING.md",
    "LICENSE",
    "Makefile",
    "pyproject.toml",
]

REQUIRED_DIRECTORIES = [
    ".github/ISSUE_TEMPLATE",
    "src/api",
    "src/agents",
    "src/rag",
    "mcp-servers/kubernetes-mcp",
    "infra/target-environments",
    "tests/unit",
    "docs/adr",
]


@pytest.fixture
def root_dir():
    """Returns the absolute path of the repository root."""
    return Path(__file__).parent.parent


def test_required_root_files_exist(root_dir):
    """Ensure OSS governance files are present at the root."""
    for file_name in REQUIRED_FILES:
        file_path = root_dir / file_name
        assert (
            file_path.is_file()
        ), f"Repository compliance failure: Missing {file_name}"


def test_required_directories_exist(root_dir):
    """Ensure the Domain-Driven structure remains intact."""
    for dir_name in REQUIRED_DIRECTORIES:
        dir_path = root_dir / dir_name
        assert (
            dir_path.is_dir()
        ), f"Architecture compliance failure: Missing directory {dir_name}"


def test_mcp_servers_have_independent_configs(root_dir):
    """Ensure MCP servers remain decoupled with their own dependency files."""
    mcp_dir = root_dir / "mcp-servers"
    for server in mcp_dir.iterdir():
        if server.is_dir():
            # Each MCP server must have its own pyproject.toml to ensure isolated
            # dependencies
            assert (
                server / "pyproject.toml"
            ).is_file(), f"MCP Server {server.name} missing pyproject.toml"
