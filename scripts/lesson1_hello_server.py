from fastmcp import FastMCP

mcp = FastMCP("hello")


@mcp.tool
def add(a: int, b: int) -> int:
    """Add two whole numbers and return the sum."""
    return a + b


if __name__ == "__main__":
    mcp.run()  # stdio by default
