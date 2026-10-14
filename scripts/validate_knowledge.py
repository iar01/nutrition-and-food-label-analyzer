import sys
from pathlib import Path
from typing import Any

import yaml

KNOWLEDGE_DIR = Path("docs/knowledge")
REQUIRED = ("key", "type", "title", "text")
VEGAN_VALUES = {"yes", "no", "varies"}
MAX_WORDS = 250


def load_cards() -> list[tuple[str, dict[str, Any]]]:
    cards: list[tuple[str, dict[str, Any]]] = []
    for path in sorted(KNOWLEDGE_DIR.glob("*.yaml")):
        data = yaml.safe_load(path.read_text(encoding="utf-8")) or []
        cards.extend((path.name, card) for card in data)
    return cards


def main() -> int:
    errors: list[str] = []
    seen: set[str] = set()
    missing_sources = 0
    cards = load_cards()

    for filename, card in cards:
        label = f"{filename}:{card.get('key', '?')}"
        for field in REQUIRED:
            if not card.get(field):
                errors.append(f"{label}: missing {field}")

        key = str(card.get("key", ""))
        if key in seen:
            errors.append(f"{label}: duplicate key")
        seen.add(key)

        if "vegan" in card and card["vegan"] not in VEGAN_VALUES:
            errors.append(
                f"{label}: vegan must be one of {sorted(VEGAN_VALUES)} "
                "(did you forget to quote it in YAML?)"
            )

        if len(str(card.get("text", "")).split()) > MAX_WORDS:
            errors.append(f"{label}: text is longer than {MAX_WORDS} words")

        if not card.get("source_url"):
            missing_sources += 1

    print(f"cards: {len(cards)} | missing source_url: {missing_sources}")
    for err in errors:
        print("ERROR:", err)
    return 1 if errors else 0


if __name__ == "__main__":
    sys.exit(main())