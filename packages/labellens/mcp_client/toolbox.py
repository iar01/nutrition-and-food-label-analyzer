import asyncio
from typing import Any

from fastmcp import Client
from fastmcp.client.auth import BearerAuth
from fastmcp.exceptions import ToolError

from labellens.agents.deps import Deps
from labellens.llm.client import get_llm
from labellens.tools.knowledge import load_additive_cards


class McpToolbox:
    """Calls tools on the LabelLens MCP server and returns plain dictionaries."""

    def __init__(self, url: str, token: str | None = None) -> None:
        self.url = url
        self.token = token

    async def _acall(self, name: str, args: dict[str, Any]) -> dict[str, Any]:
        auth = BearerAuth(self.token) if self.token else None
        async with Client(self.url, auth=auth) as client:
            result = await client.call_tool(name, args)
        return dict(result.structured_content or {})

    def call(self, name: str, args: dict[str, Any]) -> dict[str, Any]:
        return asyncio.run(self._acall(name, args))


class McpRepo:
    """Same interface as ProductRepo."""

    def __init__(self, box: McpToolbox) -> None:
        self.box = box

    def get(self, code: str) -> dict[str, Any] | None:
        try:
            out = self.box.call("lookup_by_barcode", {"code": code})
        except ToolError:  # e.g. the code is not 8 to 14 digits
            return None
        return out.get("product") if out.get("found") else None


class McpSearcher:
    """Same interface as Searcher."""

    def __init__(self, box: McpToolbox) -> None:
        self.box = box

    def products(
        self, query: str, limit: int = 5, filters: dict[str, Any] | None = None
    ) -> list[dict[str, Any]]:
        args: dict[str, Any] = {"query": query[:200], "limit": limit}
        for key, value in (filters or {}).items():
            if value:  # skip None and empty lists
                args[key] = value
        out = self.box.call("search_products", args)
        return list(out.get("results", []))

    def knowledge(self, query: str, k: int = 3, exclude_types: Any = ()) -> list[dict[str, Any]]:
        args: dict[str, Any] = {"query": query[:200], "k": k}
        if exclude_types:
            args["exclude_types"] = list(exclude_types)
        return list(self.box.call("search_knowledge", args).get("results", []))


def build_mcp_deps(url: str, token: str | None) -> Deps:
    box = McpToolbox(url, token)
    return Deps(
        llm=get_llm(),
        repo=McpRepo(box),
        searcher=McpSearcher(box),
        additive_cards=load_additive_cards(),
    )
