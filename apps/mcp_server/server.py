"""FastMCP server entrypoint for LabelLens."""

from typing import Any


def create_mcp_server() -> Any:
    """Create and configure FastMCP server instance."""
    try:
        from fastmcp import FastMCP

        server = FastMCP(
            name="labellens",
            instructions="LabelLens nutrition and food label analysis tools",
        )
        return server
    except ImportError:
        # FastMCP package will be installed in Phase 7
        return None


server = create_mcp_server()

if __name__ == "__main__":
    if server is not None:
        server.run()
    else:
        print("FastMCP package is not yet installed (scheduled for Phase 7).")
