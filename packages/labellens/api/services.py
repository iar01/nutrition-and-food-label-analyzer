import sqlite3
import threading
from collections.abc import Callable
from dataclasses import dataclass, field
from datetime import UTC, datetime
from functools import cache, lru_cache
from pathlib import Path
from typing import Any

import httpx
from fastapi import Request
from langgraph.checkpoint.sqlite import SqliteSaver

from labellens.agents.deps import Deps, build_default_deps
from labellens.agents.graph import build_graph
from labellens.api.errors import ApiError
from labellens.cache import AnalysisCache, SemanticCache
from labellens.config import settings
from labellens.embeddings.image import ClipImageEmbedder


class FeedbackStore:
    def __init__(self, path: Path) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        self.conn = sqlite3.connect(str(path), check_same_thread=False)
        self.lock = threading.Lock()
        self.conn.execute(
            "CREATE TABLE IF NOT EXISTS feedback ("
            "id INTEGER PRIMARY KEY AUTOINCREMENT, created_at TEXT NOT NULL, rating TEXT NOT NULL, "
            "comment TEXT, request_id TEXT, thread_id TEXT, product_code TEXT)"
        )
        self.conn.commit()

    def add(
        self,
        rating: str,
        comment: str | None,
        request_id: str | None,
        thread_id: str | None,
        product_code: str | None,
    ) -> int:
        with self.lock:
            cur = self.conn.execute(
                "INSERT INTO feedback (created_at, rating, comment, request_id, thread_id, product_code) "
                "VALUES (?, ?, ?, ?, ?, ?)",
                (
                    datetime.now(UTC).isoformat(),
                    rating,
                    comment,
                    request_id,
                    thread_id,
                    product_code,
                ),
            )
            self.conn.commit()
            return int(cur.lastrowid or 0)


@dataclass
class ReadyCheck:
    name: str
    fn: Callable[[], bool]
    critical: bool


@dataclass
class Services:
    deps: Deps
    graph: Any
    feedback: FeedbackStore
    get_product: Callable[[str], dict[str, Any] | None]
    get_clip: Callable[[], Any] | None
    checks: list[ReadyCheck]
    analysis_cache: AnalysisCache = field(default_factory=AnalysisCache)
    semantic_cache: SemanticCache = field(default_factory=SemanticCache)


def build_services() -> Services:
    """Called once, at server startup. Loading the models takes a few seconds."""
    deps = build_default_deps()
    settings.checkpoint_db_path.parent.mkdir(parents=True, exist_ok=True)
    conn = sqlite3.connect(str(settings.checkpoint_db_path), check_same_thread=False)
    graph = build_graph(deps, SqliteSaver(conn))

    def llm_reachable() -> bool:
        response = httpx.get(settings.llm_base_url.rstrip("/") + "/models", timeout=2.0)
        return response.status_code == 200

    checks = [
        ReadyCheck("database", deps.repo.ping, critical=True),
        ReadyCheck(
            "qdrant",
            lambda: bool(deps.searcher.client.collection_exists(settings.products_collection)),
            critical=True,
        ),
        ReadyCheck("llm", llm_reachable, critical=False),
    ]
    return Services(
        deps=deps,
        graph=graph,
        feedback=FeedbackStore(settings.feedback_db_path),
        get_product=lru_cache(maxsize=4096)(deps.repo.get),
        get_clip=cache(ClipImageEmbedder),
        checks=checks,
        analysis_cache=AnalysisCache(),
        semantic_cache=SemanticCache(),
    )


def get_services(request: Request) -> Services:
    services: Services | None = request.app.state.services
    if services is None:
        raise ApiError(503, "starting", "The service is still starting.")
    return services
