import sys

from labellens.config import settings
from labellens.embeddings.text import BgeTextEmbedder
from labellens.retrieval.qdrant_setup import get_client

query = " ".join(sys.argv[1:]) or "hazelnut chocolate spread"
client = get_client()
emb = BgeTextEmbedder()

res = client.query_points(
    collection_name=settings.products_collection,
    query=emb.embed_query(query).tolist(),
    using="text_dense",
    limit=5,
    with_payload=True,
)
for p in res.points:
    payload = p.payload or {}
    print(
        f"{p.score:.3f}  {payload.get('name')}  |  "
        f"{payload.get('brands')}  |  {payload.get('code')}"
    )
