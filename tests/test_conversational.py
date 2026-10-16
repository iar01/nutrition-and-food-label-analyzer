"""Tests for multi-turn conversational chatbot capabilities."""

from __future__ import annotations

import json
from pathlib import Path
from typing import Any

from fastapi.testclient import TestClient
from labellens.api.app import create_app
from labellens.api.config import ApiConfig
from labellens.testing.fakes import make_fake_services

HEADERS = {"X-API-Key": "test-key"}
PROFILE = {"diets": ["vegan"], "allergens": ["milk"]}


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


def parse_sse(raw: str) -> list[tuple[str, dict[str, Any]]]:
    events: list[tuple[str, dict[str, Any]]] = []
    current_event = "message"
    for line in raw.splitlines():
        if line.startswith("event: "):
            current_event = line[len("event: ") :].strip()
        elif line.startswith("data: "):
            data = json.loads(line[len("data: ") :])
            events.append((current_event, data))
    return events


def test_conversational_followup_on_same_thread(tmp_path: Path) -> None:
    """Verifies that follow-up questions in the same thread answer in context of the active product."""
    services = make_fake_services(tmp_path / "feedback.sqlite")
    client = TestClient(create_app(make_config(), services))

    # Turn 1: Initial analysis of barcode 12345678
    res1 = client.post(
        "/v1/chat",
        headers=HEADERS,
        json={"message": "check 12345678", "profile": PROFILE, "auto_pick": True},
    )
    assert res1.status_code == 200
    events1 = parse_sse(res1.text)
    step_nodes1 = [d.get("node") for name, d in events1 if name == "step"]
    assert "router" in step_nodes1
    assert "ingredient_analyst" in step_nodes1

    final1 = dict(events1)["final"]
    thread_id = final1["thread_id"]
    assert thread_id is not None
    assert final1["product"]["code"] == "12345678"

    # Turn 2: Follow-up question on the same thread
    res2 = client.post(
        "/v1/chat",
        headers=HEADERS,
        json={
            "message": "Does this spread contain hazelnuts?",
            "thread_id": thread_id,
            "profile": PROFILE,
        },
    )
    assert res2.status_code == 200
    events2 = parse_sse(res2.text)
    step_nodes2 = [d.get("node") for name, d in events2 if name == "step"]
    # Should route to product_qa, not re-search products
    assert "product_qa" in step_nodes2
    assert "find_candidates" not in step_nodes2

    final2 = dict(events2)["final"]
    assert final2["product"]["code"] == "12345678"
    assert "answer_markdown" in final2
    assert dict(events2)["done"]["status"] == "complete"


def test_conversational_switch_product_on_same_thread(tmp_path: Path) -> None:
    """Verifies that providing a new barcode in an existing thread cleanly switches products."""
    services = make_fake_services(tmp_path / "feedback.sqlite")
    client = TestClient(create_app(make_config(), services))

    # Turn 1: Initial product
    res1 = client.post(
        "/v1/chat",
        headers=HEADERS,
        json={"message": "check 12345678", "profile": PROFILE, "auto_pick": True},
    )
    events1 = parse_sse(res1.text)
    thread_id = dict(events1)["final"]["thread_id"]

    # Turn 2: Switch to another barcode
    res2 = client.post(
        "/v1/chat",
        headers=HEADERS,
        json={
            "message": "Now check 0000012345678",
            "thread_id": thread_id,
            "profile": PROFILE,
            "auto_pick": True,
        },
    )
    events2 = parse_sse(res2.text)
    step_nodes2 = [d.get("node") for name, d in events2 if name == "step"]
    assert "find_candidates" in step_nodes2
    assert "product_qa" not in step_nodes2
    final2 = dict(events2)["final"]
    assert final2["product"]["code"] in ("0000012345678", "12345678")
