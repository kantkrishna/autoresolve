# src/core/mcp_client.py
import sys
from typing import Any

from mcp.client.session import ClientSession
from mcp.client.stdio import StdioServerParameters, stdio_client


async def execute_mcp_tool(
    script_path: str, tool_name: str, args: dict[str, Any]
) -> str:
    """
    Securely spawns an MCP server script, executes a tool via JSON-RPC,
    and terminates the subprocess to prevent zombie processes.
    """
    # Define the command to run the external MCP server
    server_params = StdioServerParameters(
        command=sys.executable,  # Uses the current poetry environment Python
        args=[script_path],
    )

    # Context managers ensure the subprocess is cleanly destroyed after execution
    async with stdio_client(server_params) as (read, write):
        async with ClientSession(read, write) as session:
            await session.initialize()

            # Execute the requested tool
            result = await session.call_tool(tool_name, arguments=args)
            # Extract text content from the MCP response object
            return str(result.content[0].text)
