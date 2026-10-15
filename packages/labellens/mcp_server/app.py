from labellens.agents.deps import Deps
from labellens.embeddings.image import ClipImageEmbedder
from labellens.mcp_server.server import create_server
from labellens.ocr import EasyOcr
from labellens.retrieval.search import Searcher
from labellens.tools.knowledge import load_additive_cards
from labellens.tools.products import ProductRepo


def build_server_deps() -> Deps:
    """Called once, on the first tool call. Note: no LLM, the server is deterministic."""
    return Deps(
        llm=None, repo=ProductRepo(), searcher=Searcher(), additive_cards=load_additive_cards()
    )


mcp = create_server(build_server_deps, clip_factory=ClipImageEmbedder, ocr_factory=EasyOcr)
