from enum import Enum
from typing import Protocol


class Role(str, Enum):
    ADMIN = "admin"
    AGENT = "agent"
    READONLY = "readonly"


class AuthorizationProvider(Protocol):
    def evaluate_permission(self, role: Role, resource: str, action: str) -> bool:
        """
        Evaluates if the given role can perform the action on the specified resource.
        """
        ...


class RBACProvider:
    def evaluate_permission(self, role: Role, resource: str, action: str) -> bool:
        if role == Role.ADMIN:
            return True
        if role == Role.READONLY and action == "read":
            return True
        # Stricter rules for AI agents: Can only interact with specific MCP integrations
        if role == Role.AGENT and resource in [
            "kubernetes_mcp",
            "github_mcp",
            "trace_mcp",
        ]:
            return True
        return False
