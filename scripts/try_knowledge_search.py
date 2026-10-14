import sys

from labellens.config import settings
from labellens.embeddings.text import BgeTextEmbedder
from labellens.retrieval.qdrant_setup import get_client

query = " ".join(sys.argv[1:]) or "is carmine vegan?"
client = get_client()
emb = BgeTextEmbedder()

res = client.query_points(
    collection_name=settings.knowledge_collection,
    query=emb.embed_query(query).tolist(),
    using="text_dense",
    limit=5,
    with_payload=True,
)
for p in res.points:
    payload = p.payload or {}
    print(
        f"{p.score:.3f}  [{payload.get('type')}]  {payload.get('title')}  vegan={payload.get('vegan')}"
    )
