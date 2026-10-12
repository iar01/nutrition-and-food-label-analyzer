"""End-to-end smoke verification against an OpenAI-compatible HTTP endpoint."""

import json
import threading
from http.server import BaseHTTPRequestHandler, HTTPServer

from labellens.config import Settings
from labellens.llm.client import get_llm_client


class MockOpenAIHandler(BaseHTTPRequestHandler):
    """Minimal mock handler matching OpenAI /v1/chat/completions specification."""

    def do_POST(self) -> None:  # noqa: N802
        if self.path == "/v1/chat/completions":
            content_length = int(self.headers.get("Content-Length", 0))
            request_body = self.rfile.read(content_length)
            _ = json.loads(request_body)

            response_data = {
                "id": "chatcmpl-mock-123",
                "object": "chat.completion",
                "created": 1728734400,
                "model": "qwen2.5:7b",
                "choices": [
                    {
                        "index": 0,
                        "message": {
                            "role": "assistant",
                            "content": "READY",
                        },
                        "finish_reason": "stop",
                    }
                ],
                "usage": {
                    "prompt_tokens": 8,
                    "completion_tokens": 1,
                    "total_tokens": 9,
                },
            }
            response_bytes = json.dumps(response_data).encode("utf-8")

            self.send_response(200)
            self.send_header("Content-Type", "application/json")
            self.send_header("Content-Length", str(len(response_bytes)))
            self.end_headers()
            self.wfile.write(response_bytes)
        else:
            self.send_response(404)
            self.end_headers()

    def log_message(self, format: str, *args: object) -> None:  # noqa: A002
        """Silence HTTP request logs in test output."""
        return


def test_openai_compatible_smoke_end_to_end() -> None:
    """Verify OpenAI client successfully communicates with OpenAI-compatible endpoint."""
    server = HTTPServer(("127.0.0.1", 0), MockOpenAIHandler)
    port = server.server_port
    thread = threading.Thread(target=server.serve_forever, daemon=True)
    thread.start()

    try:
        settings = Settings(
            LLM_BASE_URL=f"http://127.0.0.1:{port}/v1",
            LLM_MODEL="qwen2.5:7b",
            LLM_API_KEY="test-key",
            LLM_TIMEOUT_SECONDS=5.0,
        )

        client = get_llm_client(settings)
        completion = client.chat.completions.create(
            model=settings.llm_model,
            messages=[{"role": "user", "content": "Respond with the word 'READY' only."}],
            temperature=0.0,
            max_tokens=10,
        )

        reply = completion.choices[0].message.content or ""
        print(f"\n[OpenAI Compatible Smoke Test] Model '{settings.llm_model}' reply: '{reply.strip()}'")
        assert reply.strip() == "READY"
    finally:
        server.shutdown()
        server.server_close()
