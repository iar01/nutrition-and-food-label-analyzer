import json
import random
from pathlib import Path

import pyarrow.parquet as pq
from labellens.config import settings

random.seed(42)


def introduce_typo(text: str) -> str:
    """Introduce realistic typing errors (swapping adjacent letters, dropping a vowel)."""
    words = text.split()
    if not words:
        return text
    target_idx = random.randint(0, len(words) - 1)
    word = list(words[target_idx])
    if len(word) > 4:
        # Swap two adjacent characters
        i = random.randint(1, len(word) - 2)
        word[i], word[i + 1] = word[i + 1], word[i]
    words[target_idx] = "".join(word)
    return " ".join(words)


def main() -> None:
    table = pq.read_table(
        settings.clean_products_path,
        columns=["code", "name", "brand", "categories_tags", "additives_tags"],
    )
    # Filter for products that have a clear name and brand
    rows = [
        r
        for r in table.slice(0, 5000).to_pylist()
        if r["name"] and r["brand"] and len(r["name"]) > 3
    ]
    selected = rows[:120]

    golden_set = []

    for i, r in enumerate(selected):
        name = r["name"]
        brand = r["brand"]
        code = r["code"]
        mod = i % 4

        if mod == 0:
            # Type 1: Brand + Product Name
            query = f"{brand} {name}"
            q_type = "brand_and_name"
        elif mod == 1:
            # Type 2: Description / Name only (no brand mentioned)
            query = name
            q_type = "description_only"
        elif mod == 2:
            # Type 3: Typo / Misspelling
            query = introduce_typo(f"{brand} {name}")
            q_type = "typo"
        else:
            # Type 4: Category or Additive context
            additives = r.get("additives_tags") or []
            if additives:
                clean_additive = additives[0].replace("en:", "").upper()
                query = f"{brand} {name} {clean_additive}"
            else:
                cats = r.get("categories_tags") or []
                cat = cats[0].replace("en:", "").replace("-", " ") if cats else ""
                query = f"{brand} {cat}".strip()
            q_type = "context_lookup"

        golden_set.append(
            {
                "query": query.strip(),
                "target_code": str(code),
                "target_name": name,
                "target_brand": brand,
                "query_type": q_type,
            }
        )

    out_path = Path("evals/golden_retrieval_set.jsonl")
    out_path.parent.mkdir(parents=True, exist_ok=True)
    with open(out_path, "w", encoding="utf-8") as f:
        for item in golden_set:
            f.write(json.dumps(item) + "\n")

    print(f"Generated {len(golden_set)} golden evaluation queries in {out_path}")


if __name__ == "__main__":
    main()
