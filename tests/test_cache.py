"""Unit and integration tests for Tier 1 analysis caching."""

from __future__ import annotations

import time
from pathlib import Path
from typing import Any

from fastapi.testclient import TestClient
from labellens.agents.schemas import IngredientFindings
from labellens.api.app import create_app
from labellens.api.config import ApiConfig
from labellens.cache import (
    InMemoryTTLStore,
    PromptCache,
    SemanticCache,
    hash_profile,
    make_analysis_cache_key,
)
from labellens.cache.semantic_cache import cosine_similarity
from labellens.llm.fake import FakeLLM, FakeReply
from labellens.llm.structured import structured_call
from labellens.testing.fakes import make_fake_services

HEADERS = {"X-API-Key": "test-key"}
PROFILE_A = {"diets": ["vegan"], "allergens": ["milk"]}
PROFILE_B = {"diets": ["vegan"], "allergens": ["milk", "nuts"]}


def make_config(**overrides: Any) -> ApiConfig:
    base: dict[str, Any] = {
        "env": "test",
        "api_keys": ("test-key",),
        "cors_origins": ("http://localhost:3000",),
        "rate_limit_per_minute": 1000,
        "max_upload_bytes": 4_000_000,
        "max_concurrent_runs": 2,
    }
    return ApiConfig(**{**base, **overrides})


def test_hash_profile_order_independence() -> None:
    """Verifies that allergen/diet list ordering does not affect the hash."""
    prof1 = {"diets": ["vegan", "gluten-free"], "allergens": ["milk", "soy", "peanuts"]}
    prof2 = {"diets": ["gluten-free", "vegan"], "allergens": ["peanuts", "soy", "milk"]}
    assert hash_profile(prof1) == hash_profile(prof2)


def test_hash_profile_differentiation() -> None:
    """Verifies different dietary restrictions yield different hashes."""
    assert hash_profile(PROFILE_A) != hash_profile(PROFILE_B)
    assert hash_profile(None) == "default"
    assert hash_profile({}) == "default"


def test_make_analysis_cache_key() -> None:
    key = make_analysis_cache_key(" 12345678 ", PROFILE_A)
    assert key.startswith("analysis:12345678:")
    assert len(key.split(":")) == 3


def test_in_memory_ttl_store() -> None:
    store = InMemoryTTLStore(default_ttl_seconds=1, max_entries=2)
    store.set("k1", "v1")
    assert store.get("k1") == "v1"

    # Test TTL expiration
    time.sleep(1.1)
    assert store.get("k1") is None

    # Test capacity eviction
    store.set("k2", "v2", ttl_seconds=10)
    store.set("k3", "v3", ttl_seconds=10)
    store.set("k4", "v4", ttl_seconds=10)  # Evicts k2
    assert len(store) == 2
    assert store.get("k4") == "v4"


def test_api_analyze_caching(tmp_path: Path) -> None:
    """End-to-end test verifying /v1/analyze hits the cache on the second request."""
    services = make_fake_services(tmp_path / "feedback.sqlite")
    client = TestClient(create_app(make_config(), services))

    # 1. First call: Cache miss
    res1 = client.post(
        "/v1/analyze",
        data={"barcode": "12345678", "profile": '{"diets":["vegan"],"allergens":["milk"]}'},
        headers=HEADERS,
    )
    assert res1.status_code == 200
    assert services.analysis_cache.misses == 1
    assert services.analysis_cache.hits == 0

    # 2. Second call: Cache hit (instant)
    res2 = client.post(
        "/v1/analyze",
        data={"barcode": "12345678", "profile": '{"allergens":["milk"],"diets":["vegan"]}'},
        headers=HEADERS,
    )
    assert res2.status_code == 200
    assert res2.json()["product"]["code"] == "12345678"
    assert services.analysis_cache.hits == 1

    # 3. Third call with different profile: Cache miss
    res3 = client.post(
        "/v1/analyze",
        data={"barcode": "12345678", "profile": '{"diets":["vegan"],"allergens":["nuts"]}'},
        headers=HEADERS,
    )
    assert res3.status_code == 200
    assert services.analysis_cache.misses == 2


def test_api_chat_caching(tmp_path: Path) -> None:
    """End-to-end test verifying /v1/chat hits the cache on repeated barcode scans."""
    services = make_fake_services(tmp_path / "feedback.sqlite")
    client = TestClient(create_app(make_config(), services))

    # 1. First chat call populates cache
    res1 = client.post(
        "/v1/chat",
        json={"message": "check 12345678", "profile": PROFILE_A, "auto_pick": True},
        headers=HEADERS,
    )
    assert res1.status_code == 200
    assert "event: final" in res1.text
    # Cache was populated upon stream completion
    assert len(services.analysis_cache.store) == 1

    # 2. Second chat call hits instant cache
    res2 = client.post(
        "/v1/chat",
        json={"message": "12345678", "profile": PROFILE_A, "auto_pick": True},
        headers=HEADERS,
    )
    assert res2.status_code == 200
    assert "Retrieved from instant cache" in res2.text
    assert "event: final" in res2.text
    assert services.analysis_cache.hits == 1


# ------------------------------------------------------------------ Tier 3: Prompt Cache
def test_prompt_cache_hit_and_miss() -> None:
    cache = PromptCache()
    sys_prompt = "You are an expert nutritionist."
    usr_prompt = "Analyze these ingredients: sugar, water."
    schema = "IngredientFindings"
    canned_reply = '{"notable": [], "summary": "Simple sugar syrup."}'

    assert cache.get(sys_prompt, usr_prompt, schema) is None
    assert cache.misses == 1

    cache.set(sys_prompt, usr_prompt, canned_reply, schema)
    hit = cache.get(sys_prompt, usr_prompt, schema)
    assert hit == canned_reply
    assert cache.hits == 1

    # Varying user prompt yields a miss
    assert cache.get(sys_prompt, "Different user prompt", schema) is None
    assert cache.misses == 2

    # Varying schema yields a miss
    assert cache.get(sys_prompt, usr_prompt, "OtherSchema") is None
    assert cache.misses == 3


def test_structured_call_with_prompt_cache() -> None:
    class CountingLLM(FakeLLM):
        def __init__(self) -> None:
            self.count = 0

        def invoke(self, messages: list[Any]) -> FakeReply:
            self.count += 1
            return super().invoke(messages)

    llm = CountingLLM()
    cache = PromptCache()
    sys_prompt = "Analyze ingredients."
    usr_prompt = '{"ingredients": "sugar, oats"}'

    # First call: LLM is invoked
    res1 = structured_call(llm, IngredientFindings, sys_prompt, usr_prompt, cache=cache)
    assert res1.summary == "Ingredient summary for tests."
    assert llm.count == 1
    assert cache.misses == 1
    assert cache.hits == 0

    # Second identical call: served from PromptCache, LLM is not called again!
    res2 = structured_call(llm, IngredientFindings, sys_prompt, usr_prompt, cache=cache)
    assert res2.summary == "Ingredient summary for tests."
    assert llm.count == 1
    assert cache.hits == 1


# ------------------------------------------------------------------ Tier 2: Semantic Cache
def test_cosine_similarity() -> None:
    assert cosine_similarity([1.0, 0.0], [1.0, 0.0]) == 1.0
    assert cosine_similarity([1.0, 0.0], [0.0, 1.0]) == 0.0
    assert cosine_similarity([1.0, 0.0], [-1.0, 0.0]) == -1.0
    assert cosine_similarity([0.0, 0.0], [1.0, 0.0]) == 0.0


def test_semantic_cache_matching_and_isolation() -> None:
    cache = SemanticCache(similarity_threshold=0.90)
    profile_vegan = {"diets": ["vegan"]}
    profile_nuts = {"allergens": ["nuts"]}

    vec_a = [1.0, 0.0, 0.0]
    cache.set(
        query="Is this spread vegan?",
        product_code="12345678",
        profile=profile_vegan,
        answer="Yes, it contains no animal products.",
        vector=vec_a,
    )
    assert len(cache) == 1

    # Exact query match
    hit = cache.get(
        query="Is this spread vegan?",
        product_code="12345678",
        profile=profile_vegan,
        query_vector=vec_a,
    )
    assert hit is not None
    assert hit.similarity == 1.0
    assert "no animal products" in hit.answer
    assert cache.hits == 1

    # Paraphrased query match (high cosine similarity >= 0.90)
    vec_paraphrase = [0.98, 0.02, 0.0]
    hit2 = cache.get(
        query="Can vegans eat this spread?",
        product_code="12345678",
        profile=profile_vegan,
        query_vector=vec_paraphrase,
    )
    assert hit2 is not None
    assert hit2.similarity > 0.95
    assert cache.hits == 2

    # Completely different question (low similarity)
    vec_unrelated = [0.0, 1.0, 0.0]
    hit_unrelated = cache.get(
        query="What is the sugar content?",
        product_code="12345678",
        profile=profile_vegan,
        query_vector=vec_unrelated,
    )
    assert hit_unrelated is None
    assert cache.misses == 1

    # Cross-product isolation: same question and vector, different product code -> Miss
    hit_diff_product = cache.get(
        query="Is this spread vegan?",
        product_code="99999999",
        profile=profile_vegan,
        query_vector=vec_a,
    )
    assert hit_diff_product is None
    assert cache.misses == 2

    # Cross-profile isolation: same question, but for nut allergy user -> Miss (safety invariant)
    hit_diff_profile = cache.get(
        query="Is this spread vegan?",
        product_code="12345678",
        profile=profile_nuts,
        query_vector=vec_a,
    )
    assert hit_diff_profile is None
    assert cache.misses == 3


def test_api_chat_semantic_caching(tmp_path: Path) -> None:
    services = make_fake_services(tmp_path / "feedback.sqlite")
    client = TestClient(create_app(make_config(), services))

    # Pre-populate semantic cache with a question for product 12345678
    assert services.deps.searcher.text_emb is not None
    vec = services.deps.searcher.text_emb.embed_query("is this okay for vegans?").tolist()
    services.semantic_cache.set(
        query="is this okay for vegans?",
        product_code="12345678",
        profile=PROFILE_A,
        answer="It is completely vegan and delicious.",
        vector=vec,
    )

    # When a user asks a question with barcode 12345678 and matching profile
    res = client.post(
        "/v1/chat",
        json={"message": "check 12345678 is this okay for vegans?", "profile": PROFILE_A},
        headers=HEADERS,
    )
    assert res.status_code == 200
    assert "Retrieved from semantic cache" in res.text
    assert "It is completely vegan and delicious." in res.text
    assert services.semantic_cache.hits == 1
