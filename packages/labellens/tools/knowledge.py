from pathlib import Path
from typing import Any

import yaml


def load_additive_cards(
    path: Path = Path("docs/knowledge/additives.yaml"),
) -> dict[str, dict[str, Any]]:
    """Map card key (for example 'e471') to its card."""
    cards = yaml.safe_load(path.read_text(encoding="utf-8")) or []
    return {card["key"]: card for card in cards}
