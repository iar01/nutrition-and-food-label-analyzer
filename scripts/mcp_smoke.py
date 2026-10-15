import asyncio

from fastmcp import Client
from fastmcp.client.auth import BearerAuth
from labellens.config import settings


async def main() -> None:
    async with Client(settings.mcp_url, auth=BearerAuth(settings.mcp_auth_token or "")) as client:
        tools = await client.list_tools()
        print("tools:", sorted(t.name for t in tools))
        result = await client.call_tool("explain_additive", {"identifier": "E120"})
        print(result.structured_content or result.data)


asyncio.run(main())
