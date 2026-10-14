import sys

from labellens.retrieval.hybrid import HybridRetriever
from labellens.retrieval.qdrant_setup import get_client


def main() -> None:
    client = get_client()
    retriever = HybridRetriever(client)

    query = " ".join(sys.argv[1:]) or "Nutella Ferrero chocolate spread"
    hits = retriever.search(query=query, limit=5)

    print(f"\n--- Top Hybrid Hits for: {query!r} ---")
    for h in hits:
        print(f"#{h.rank} [score={h.score:.4f}] {h.name} | {h.brand} (barcode: {h.code})")


if __name__ == "__main__":
    main()
