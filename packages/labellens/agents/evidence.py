from typing import Any


def product_evidence(product: dict[str, Any]) -> dict[str, Any]:
    code = product["code"]
    text = f"{product.get('name')} ({product.get('brand')}). Ingredients: {(product.get('ingredients') or 'not available')[:300]}"
    return {
        "id": f"product:{code}",
        "kind": "product",
        "title": f"{product.get('name')} (Open Food Facts)",
        "text": text,
        "source_url": f"https://world.openfoodfacts.org/product/{code}",
    }


def card_evidence(card: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": f"kb:{card['key']}",
        "kind": "knowledge",
        "title": card["title"],
        "text": card["text"],
        "source_url": card.get("source_url", ""),
    }


def kb_hit_evidence(payload: dict[str, Any]) -> dict[str, Any]:
    return {
        "id": f"kb:{payload['key']}",
        "kind": "knowledge",
        "title": payload.get("title", ""),
        "text": payload.get("text", ""),
        "source_url": payload.get("source_url", ""),
    }
