import json
from dataclasses import dataclass
from typing import Any

CANNED: dict[str, dict[str, Any]] = {
    "RouterDecision": {
        "input_kind": "text",
        "barcode": None,
        "product_query": "test product",
        "wants_alternatives": False,
    },
    "IngredientFindings": {"notable": [], "summary": "Ingredient summary for tests."},
    "AdditiveFindings": {"notes": []},
    "FinalSummary": {"summary": "Test summary.", "tips": []},
}


@dataclass
class FakeReply:
    content: str


class FakeLLM:
    def invoke(self, messages: list[Any]) -> FakeReply:
        system = str(messages[0].content)
        for name, payload in CANNED.items():
            if f'"title": "{name}"' in system:
                return FakeReply(json.dumps(payload))
        return FakeReply("{}")
