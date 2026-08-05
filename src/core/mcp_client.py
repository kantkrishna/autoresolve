# src/core/mcp_client.py

# This module provides an asynchronous client for interacting with MCP servers over
# stdio.

import logging
import os
import sys
from pathlib import Path
from typing import Any, Dict, Union

from mcp.client.session import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client

logger = logging.getLogger(__name__)

# Dynamically resolve the absolute path to the project root
PROJECT_ROOT = Path(__file__).resolve().parent.parent.parent

# Explicit mapping matching actual repository file structure
MCP_SERVER_MAP: Dict[str, str] = {
    "filesystem": "mcp-servers/filesystem-mcp/fs_server.py",
    "github": "mcp-servers/github-mcp/github_server.py",
    "grafana": "mcp-servers/grafana-mcp/grafana_server.py",
    "kubernetes": "mcp-servers/kubernetes-mcp/k8s_server.py",
    "k8s": "mcp-servers/kubernetes-mcp/k8s_server.py",
    "prometheus": "mcp-servers/prometheus-mcp/prom_server.py",
    "prom": "mcp-servers/prometheus-mcp/prom_server.py",
    "slack": "mcp-servers/slack-mcp/slack_server.py",
    "terraform": "mcp-servers/terraform-mcp/tf_server.py",
    "tf": "mcp-servers/terraform-mcp/tf_server.py",
}


def resolve_mcp_script(server_name: str, script_path: str = None) -> Path | None:
    """Dynamically resolves the absolute path to the MCP server python script."""
    # 1. If caller passed an explicit script_path, check if it exists
    if script_path:
        path = PROJECT_ROOT / script_path
        if path.exists():
            return path

    # 2. Check explicit server mapping
    if server_name in MCP_SERVER_MAP:
        path = PROJECT_ROOT / MCP_SERVER_MAP[server_name]
        if path.exists():
            return path

    # 3. Dynamic candidate resolution fallback
    dirs_to_check = [
        PROJECT_ROOT / "mcp-servers" / f"{server_name}-mcp",
        PROJECT_ROOT / "mcp-servers" / server_name,
    ]

    for server_dir in dirs_to_check:
        if not server_dir.exists():
            continue

        short_names = {
            "filesystem": "fs_server.py",
            "kubernetes": "k8s_server.py",
            "prometheus": "prom_server.py",
            "terraform": "tf_server.py",
            "github": "github_server.py",
            "grafana": "grafana_server.py",
            "slack": "slack_server.py",
        }

        candidates = [
            server_dir / short_names.get(server_name, f"{server_name}_server.py"),
            server_dir / f"{server_name}_server.py",
            server_dir / "server.py",
            server_dir / "main.py",
        ]

        for candidate in candidates:
            if candidate.exists():
                return candidate

    return None


async def execute_mcp_tool(
    server_name: str,
    tool_name: str = None,
    tool_args: dict = None,
    script_path: str = None,
    **kwargs,
) -> Union[Dict[str, Any], str]:
    """Executes a tool on an MCP server over stdio with auto-resolving script paths."""
    # Handle legacy argument positioning if passed differently
    if tool_name is None and tool_args is None and isinstance(script_path, dict):
        tool_args = script_path
        script_path = None

    tool_args = tool_args or {}

    abs_script_path = resolve_mcp_script(server_name, script_path)
    if not abs_script_path:
        err = f"MCP Server script for '{server_name}' not found under {PROJECT_ROOT / 'mcp-servers'}"
        logger.error(f"❌ {err}")
        return {"error": err}

    env = os.environ.copy()
    env["PYTHONUNBUFFERED"] = "1"

    server_params = StdioServerParameters(
        command=sys.executable,
        args=[str(abs_script_path)],
        env=env,
    )

    logger.info(f"🔌 Initializing MCP Connection to {server_name} at {abs_script_path}...")

    try:
        async with stdio_client(server_params) as (read, write):
            async with ClientSession(read, write) as session:
                await session.initialize()
                logger.info(f"⚙️ Executing tool '{tool_name}' on '{server_name}'...")
                result = await session.call_tool(tool_name, arguments=tool_args)

                if hasattr(result, "content") and isinstance(result.content, list) and len(result.content) > 0:
                    return result.content[0].text
                else:
                    return str(result)

    except Exception as e:
        logger.error(f"❌ Failed to connect or execute MCP tool: {str(e)}", exc_info=True)
        return {"error": f"MCP Client Connection Error: {str(e)}"}