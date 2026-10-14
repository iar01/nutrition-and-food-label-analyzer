import sys

from labellens.retrieval.hybrid import HybridRetriever
from labellens.retrieval.qdrant_setup import get_client
from labellens.retrieval.reranker import CrossEncoderReranker


def main() -> None:
    client = get_client()
    hybrid = HybridRetriever(client)
    reranker = CrossEncoderReranker()

    query = " ".join(sys.argv[1:]) or "whole wheat organic bread"
    candidates = hybrid.search(query=query, limit=15)
    final_results = reranker.rerank(query=query, hits=candidates, top_k=5)

    print(f"\n--- Reranked Results for {query!r} ---")
    for h in final_results:
        print(f"#{h.rank} [CrossEncoder={h.score:+.3f}] {h.name} | {h.brand}")


if __name__ == "__main__":
    main()
