from labellens.retrieval.models import InputType, SearchHit, SearchResponse
from labellens.retrieval.qdrant_setup import get_client
from labellens.retrieval.router import SearchEngine


def test_search_models_structure() -> None:
    hit = SearchHit(
        id="test-123",
        code="4008400401829",
        name="Nutella",
        brand="Ferrero",
        score=0.95,
        rank=1,
        match_source="test",
    )
    assert hit.code == "4008400401829"
    resp = SearchResponse(
        query="Nutella",
        input_type=InputType.TEXT,
        hits=[hit],
        total_found=1,
        latency_ms=12.5,
    )
    assert resp.total_found == 1
    assert resp.input_type == InputType.TEXT


def test_search_engine_barcode_route() -> None:
    client = get_client()
    engine = SearchEngine(client)
    # Known barcode from dataset
    resp = engine.search(query="4008400401829")
    assert resp.input_type == InputType.BARCODE
    assert len(resp.hits) >= 1
    assert resp.hits[0].code == "4008400401829"


def test_search_engine_text_route() -> None:
    client = get_client()
    engine = SearchEngine(client)
    resp = engine.search(query="hazelnut spread", top_k=5)
    assert resp.input_type == InputType.TEXT
    assert len(resp.hits) > 0
    assert resp.hits[0].match_source in ("reranked", "hybrid_rrf")


def test_search_engine_diet_filter() -> None:
    client = get_client()
    engine = SearchEngine(client)
    resp = engine.search(
        query="organic bread",
        diet_filters={"diet_vegan": "yes"},
        top_k=3,
    )
    assert resp.input_type == InputType.TEXT
    assert resp.filters_applied == {"diet_vegan": "yes"}
    for hit in resp.hits:
        assert hit.payload.get("diet_vegan") == "yes"
