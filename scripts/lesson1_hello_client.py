import asyncio

from fastmcp import Client
from lesson1_hello_server import mcp


async def main() -> None:
    async with Client(mcp) as client:
        tools = await client.list_tools()
        print("tools:", [t.name for t in tools])
        print("schema:", tools[0].inputSchema)
        result = await client.call_tool("add", {"a": 2, "b": 3})
        print("result:", result.data)


asyncio.run(main())
