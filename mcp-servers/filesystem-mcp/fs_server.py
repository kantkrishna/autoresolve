import os

from src.core.mcp_base.server import get_secure_mcp_server, secure_tool

mcp = get_secure_mcp_server("FilesystemMCP")
BASE_DIR = os.getenv("ALLOWED_DIR", "/tmp/autoresolve")


@mcp.tool()
@secure_tool
def read_file(path: str) -> str:
    """Reads a file from the strictly allowed directory."""
    target = os.path.abspath(os.path.join(BASE_DIR, path))
    if not target.startswith(os.path.abspath(BASE_DIR)):
        return "Error: Strict path traversal boundary violated."
    try:
        with open(target, "r") as f:
            return f.read()
    except Exception as e:
        return f"Error reading file: {e}"


if __name__ == "__main__":
    mcp.run()
