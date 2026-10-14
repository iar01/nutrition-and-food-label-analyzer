import sys

from labellens.config import settings
from labellens.embeddings.image import ClipImageEmbedder
from labellens.retrieval.qdrant_setup import get_client

query = " ".join(sys.argv[1:]) or "a jar of chocolate spread"
client = get_client()
clip = ClipImageEmbedder()

res = client.query_points(
    collection_name=settings.products_collection,
    query=clip.embed_text(query).tolist(),
    using="image_clip",
    limit=5,
    with_payload=True,
)
for p in res.points:
    payload = p.payload or {}
    print(
        f"{p.score:.3f}  {payload.get('name')}  |  "
        f"{payload.get('brands')}  |  {payload.get('code')}"
    )