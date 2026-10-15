import io
import json
from pathlib import Path
from typing import Any

import pytest
from fastapi.testclient import TestClient
from labellens.api.app import create_app
from labellens.api.config import ApiConfig
from labellens.api.services import ReadyCheck
from labellens.testing.fakes import make_fake_services
from PIL import Image

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


def make_client(tmp_path: Path, n_candidates: int = 1, **config_overrides: Any) -> TestClient:
    services = make_fake_services(tmp_path / "feedback.sqlite", n_candidates)
    return TestClient(create_app(make_config(**config_overrides), services))


@pytest.fixture
def client(tmp_path: Path) -> TestClient:
    return make_client(tmp_path)


def png_bytes() -> bytes:
    buffer = io.BytesIO()
    Image.new("RGB", (32, 32), "red").save(buffer, "PNG")
    return buffer.getvalue()


def parse_sse(text: str) -> list[tuple[str, dict[str, Any]]]:
    events: list[tuple[str, dict[str, Any]]] = []
    for block in text.strip().split("\n\n"):
        lines = block.split("\n")
        events.append(
            (lines[0].removeprefix("event: "), json.loads(lines[1].removeprefix("data: ")))
        )
    return events


# ------------------------------------------------------------------- ops
def test_health_needs_no_key(client: TestClient) -> None:
    assert client.get("/health").json() == {"status": "ok"}


def test_ready_ok(client: TestClient) -> None:
    body = client.get("/ready").json()
    assert body["status"] == "ok"
    assert {c["name"] for c in body["checks"]} == {"database", "qdrant", "llm"}


def test_ready_degraded_when_only_llm_fails(tmp_path: Path) -> None:
    services = make_fake_services(tmp_path / "f.sqlite")
    services.checks[2] = ReadyCheck("llm", lambda: False, critical=False)
    response = TestClient(create_app(make_config(), services)).get("/ready")
    assert response.status_code == 200 and response.json()["status"] == "degraded"


def test_ready_unavailable_when_critical_fails(tmp_path: Path) -> None:
    services = make_fake_services(tmp_path / "f.sqlite")
    services.checks[0] = ReadyCheck("database", lambda: False, critical=True)
    response = TestClient(create_app(make_config(), services)).get("/ready")
    assert response.status_code == 503 and response.json()["status"] == "unavailable"


def test_production_refuses_to_start_without_api_keys(tmp_path: Path) -> None:
    services = make_fake_services(tmp_path / "f.sqlite")
    with pytest.raises(RuntimeError):
        create_app(ApiConfig(env="production"), services)


# ------------------------------------------------------------ auth + limits
def test_v1_requires_a_valid_api_key(client: TestClient) -> None:
    assert client.get("/v1/products/12345678").status_code == 401
    assert client.get("/v1/products/12345678", headers={"X-API-Key": "wrong"}).status_code == 401
    assert client.get("/v1/products/12345678", headers=HEADERS).status_code == 200


def test_rate_limit(tmp_path: Path) -> None:
    client = make_client(tmp_path, rate_limit_per_minute=3)
    for _ in range(3):
        assert client.get("/v1/products/12345678", headers=HEADERS).status_code == 200
    blocked = client.get("/v1/products/12345678", headers=HEADERS)
    assert blocked.status_code == 429 and "retry-after" in blocked.headers


def test_request_id_is_generated_and_echoed(client: TestClient) -> None:
    assert len(client.get("/health").headers["x-request-id"]) == 32
    echoed = client.get("/health", headers={"X-Request-ID": "my-test-id-123"})
    assert echoed.headers["x-request-id"] == "my-test-id-123"


def test_cors_preflight(client: TestClient) -> None:
    ok = client.options(
        "/v1/search",
        headers={
            "Origin": "http://localhost:3000",
            "Access-Control-Request-Method": "GET",
            "Access-Control-Request-Headers": "x-api-key",
        },
    )
    assert ok.headers["access-control-allow-origin"] == "http://localhost:3000"
    bad = client.options(
        "/v1/search",
        headers={"Origin": "http://evil.example", "Access-Control-Request-Method": "GET"},
    )
    assert "access-control-allow-origin" not in bad.headers


# --------------------------------------------------------- products + search
def test_product_found_missing_and_invalid(client: TestClient) -> None:
    ok = client.get("/v1/products/12345678", headers=HEADERS)
    assert ok.json()["name"] == "Test Spread" and ok.json()["nova_group"] == 4
    missing = client.get("/v1/products/99999999", headers=HEADERS)
    assert missing.status_code == 404 and missing.json()["error"] == "not_found"
    assert client.get("/v1/products/abc", headers=HEADERS).status_code == 422


def test_search(client: TestClient) -> None:
    body = client.get(
        "/v1/search", params={"q": "spread", "diet": ["vegan"]}, headers=HEADERS
    ).json()
    assert body["count"] == 1 and body["results"][0]["code"] == "12345678"
    assert (
        client.get(
            "/v1/search", params={"q": "spread", "diet": ["keto"]}, headers=HEADERS
        ).status_code
        == 422
    )


# ------------------------------------------------------------------ analyze
def test_analyze_by_barcode(client: TestClient) -> None:
    response = client.post(
        "/v1/analyze", headers=HEADERS, data={"barcode": "12345678", "profile": json.dumps(PROFILE)}
    )
    body = response.json()
    assert response.status_code == 200 and body["matched_by"] == "barcode"
    assert body["verdicts"]["allergens"]["milk"]["status"] == "contains"
    assert body["verdicts"]["diets"]["vegan"]["status"] == "not_suitable"
    assert body["verdicts"]["overall"] == "not_suitable"
    assert body["request_id"] == response.headers["x-request-id"]


def test_analyze_unknown_barcode_is_404(client: TestClient) -> None:
    response = client.post("/v1/analyze", headers=HEADERS, data={"barcode": "99999999"})
    assert response.status_code == 404 and response.json()["error"] == "not_found"


def test_analyze_validation(client: TestClient) -> None:
    assert client.post("/v1/analyze", headers=HEADERS, data={}).status_code == 422
    bad_profile = client.post(
        "/v1/analyze", headers=HEADERS, data={"barcode": "12345678", "profile": "{nope"}
    )
    assert bad_profile.status_code == 422 and bad_profile.json()["error"] == "invalid_profile"
    unknown_diet = client.post(
        "/v1/analyze",
        headers=HEADERS,
        data={"barcode": "12345678", "profile": '{"diets": ["keto"]}'},
    )
    assert unknown_diet.status_code == 422


def test_analyze_by_image(client: TestClient) -> None:
    response = client.post(
        "/v1/analyze",
        headers=HEADERS,
        files={"image": ("pack.png", png_bytes(), "image/png")},
        data={"profile": json.dumps(PROFILE)},
    )
    body = response.json()
    assert response.status_code == 200 and body["matched_by"] == "image"
    assert body["candidates"][0]["code"] == "12345678"


def test_upload_checks(tmp_path: Path) -> None:
    client = make_client(tmp_path, max_upload_bytes=1000)
    wrong_type = client.post(
        "/v1/analyze", headers=HEADERS, files={"image": ("x.txt", b"hello", "text/plain")}
    )
    assert wrong_type.status_code == 415 and wrong_type.json()["error"] == "unsupported_media_type"
    fake_png = client.post(
        "/v1/analyze", headers=HEADERS, files={"image": ("x.png", b"not an image", "image/png")}
    )
    assert fake_png.status_code == 415 and fake_png.json()["error"] == "invalid_image"
    too_big = client.post(
        "/v1/analyze", headers=HEADERS, files={"image": ("x.png", b"x" * 5000, "image/png")}
    )
    assert too_big.status_code == 413


# --------------------------------------------------------------------- chat
def test_chat_streams_steps_then_final(client: TestClient) -> None:
    response = client.post(
        "/v1/chat", headers=HEADERS, json={"message": "check 12345678", "profile": PROFILE}
    )
    assert response.headers["content-type"].startswith("text/event-stream")
    events = parse_sse(response.text)
    names = [name for name, _ in events]
    assert "step" in names and "answer_chunk" in names
    assert names[-2:] == ["final", "done"]
    assert dict(events)["final"]["product"]["code"] == "12345678"
    assert dict(events)["done"]["status"] == "complete"


def test_chat_pauses_then_resumes(tmp_path: Path) -> None:
    client = make_client(tmp_path, n_candidates=2)
    first = parse_sse(client.post("/v1/chat", headers=HEADERS, json={"message": "nutella"}).text)
    names = [name for name, _ in first]
    assert "choose_product" in names and names[-1] == "done"
    thread_id = dict(first)["choose_product"]["thread_id"]
    assert dict(first)["done"]["status"] == "waiting_for_choice"

    second = parse_sse(
        client.post(
            "/v1/chat", headers=HEADERS, json={"thread_id": thread_id, "resume_code": "12345678"}
        ).text
    )
    assert dict(second)["done"]["status"] == "complete"
    assert dict(second)["final"]["product"]["code"] == "12345678"

    again = client.post(
        "/v1/chat", headers=HEADERS, json={"thread_id": thread_id, "resume_code": "12345678"}
    )
    assert again.status_code == 409


def test_chat_request_validation(client: TestClient) -> None:
    assert client.post("/v1/chat", headers=HEADERS, json={}).status_code == 422
    both = {"message": "hello", "thread_id": "abcdefgh1234"}
    assert client.post("/v1/chat", headers=HEADERS, json=both).status_code == 422
    unknown = {"thread_id": "abcdefgh1234", "resume_code": "12345678"}
    assert client.post("/v1/chat", headers=HEADERS, json=unknown).status_code == 409


# ----------------------------------------------------------------- feedback
def test_feedback(client: TestClient) -> None:
    ok = client.post(
        "/v1/feedback", headers=HEADERS, json={"rating": "up", "product_code": "12345678"}
    )
    assert ok.status_code == 201 and ok.json()["id"] == 1
    assert client.post("/v1/feedback", headers=HEADERS, json={"rating": "meh"}).status_code == 422


def test_openapi_lists_the_endpoints(client: TestClient) -> None:
    paths = client.get("/openapi.json").json()["paths"]
    assert {"/health", "/ready", "/v1/analyze", "/v1/chat", "/v1/search", "/v1/feedback"} <= set(
        paths
    )


# ------------------------------------------------------- Try it yourself tests
def test_analyze_returns_sources_in_answer_markdown(client: TestClient) -> None:
    response = client.post(
        "/v1/analyze", headers=HEADERS, data={"barcode": "12345678", "profile": json.dumps(PROFILE)}
    )
    assert response.status_code == 200
    markdown = response.json()["answer_markdown"]
    assert "Sources" in markdown


def test_unhandled_route_exception_returns_500_with_request_id(tmp_path: Path) -> None:
    services = make_fake_services(tmp_path / "f.sqlite")

    def broken_search(*args: Any, **kwargs: Any) -> Any:
        raise RuntimeError("database exploded")

    services.deps.searcher.products = broken_search  # type: ignore[assignment]
    client = TestClient(create_app(make_config(), services))
    response = client.get("/v1/search?q=spread", headers=HEADERS)
    assert response.status_code == 500
    body = response.json()
    assert body["error"] == "internal_error"
    assert "request_id" in body and body["request_id"] != "-"
    assert response.headers.get("x-request-id") == body["request_id"]
