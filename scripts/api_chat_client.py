import json
import sys
from typing import Any

import httpx
from labellens.config import settings

BASE = "http://127.0.0.1:8000"
KEY = (settings.api_keys or "").split(",")[0].strip()
HEADERS = {"X-API-Key": KEY}


def stream_chat(client: httpx.Client, payload: dict[str, Any]) -> dict[str, Any] | None:
    """Print events as they arrive. Returns the choose_product payload if the graph paused."""
    pending: dict[str, Any] | None = None
    event = ""
    with client.stream(
        "POST", f"{BASE}/v1/chat", json=payload, headers=HEADERS, timeout=180
    ) as response:
        if response.status_code != 200:
            print("HTTP", response.status_code, response.read().decode())
            return None
        for line in response.iter_lines():
            if line.startswith("event: "):
                event = line[7:]
            elif line.startswith("data: "):
                data = json.loads(line[6:])
                if event == "step":
                    print(f"  ... {data['label']}")
                elif event == "choose_product":
                    pending = data
                elif event == "answer_chunk":
                    print(data["text"], end="")
                elif event == "error":
                    print("ERROR:", data["message"])
    return pending


def main() -> None:
    message = " ".join(sys.argv[1:]) or "nutella"
    profile = {"diets": ["vegan"], "allergens": ["milk"]}
    with httpx.Client() as client:
        pending = stream_chat(client, {"message": message, "profile": profile})
        while pending:
            print("\n" + pending["question"])
            for i, c in enumerate(pending["candidates"], 1):
                print(f"  {i}. {c['name']} | {c['brands']} | {c['code']}")
            choice = int(input("Number: ")) - 1
            code = pending["candidates"][choice]["code"]
            pending = stream_chat(client, {"thread_id": pending["thread_id"], "resume_code": code})


if __name__ == "__main__":
    main()
