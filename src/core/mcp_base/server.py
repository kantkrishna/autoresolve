import logging
import os
from functools import wraps
from typing import Any, Callable

from mcp.server.fastmcp import FastMCP

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def require_mcp_auth() -> None:
    """Security hook ensuring subprocess was spawned by authorized parent."""
    if os.getenv("AUTORESOLVE_MCP_BOUNDARY") != "secure":
        logger.error("Unauthorized MCP execution attempt blocked.")
        raise PermissionError("MCP execution blocked: Invalid Security Boundary")


def secure_tool(func: Callable[..., Any]) -> Callable[..., Any]:
    """Decorator to enforce the security boundary on all MCP tool executions."""

    @wraps(func)
    def wrapper(*args: Any, **kwargs: Any) -> Any:
        require_mcp_auth()
        return func(*args, **kwargs)

    return wrapper


def get_secure_mcp_server(name: str) -> FastMCP:
    """Factory for generating secure FastMCP servers."""
    return FastMCP(name)
