"""Type stubs for the mcp.server.fastmcp module.

This module provides type definitions for the mcp.server.fastmcp module.
"""

from typing import (
    Any,
    Callable,
    TypeVar,
)

F = TypeVar("F", bound=Callable[..., Any])

class FastMCP:
    """MCP server implementation using FastAPI.

    This class provides a way to define and register tools for an MCP server.
    """

    def __init__(self, name: str) -> None:
        """Initialize a new FastMCP server.

        Args:
            name: The name of the server
        """
        ...

    def tool(self) -> Callable[[F], F]:
        """Decorator for registering a function as a tool.

        Returns:
            A decorator function that registers the decorated function as a tool
        """
        ...

    def run(self) -> None:
        """Run the server."""
        ...

    def sse_app(self) -> Any:
        """Return an ASGI application for the MCP server that can be used with SSE.

        Returns:
            An ASGI application
        """
        ...
