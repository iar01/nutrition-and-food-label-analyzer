.PHONY: setup-qdrant index download-images embed-images index-images index-knowledge test-retrieval eval-retrieval

setup-qdrant:
	uv run python scripts/setup_qdrant.py

index:
	uv run python scripts/index_products.py

download-images:
	uv run python scripts/download_images.py

embed-images:
	uv run python scripts/embed_images.py

index-images:
	uv run python scripts/attach_image_vectors.py

index-knowledge:
	uv run python scripts/index_knowledge.py

test-retrieval:
	uv run pytest tests/test_retrieval.py -v

eval-retrieval:
	uv run python scripts/eval_retrieval_ablations.py

