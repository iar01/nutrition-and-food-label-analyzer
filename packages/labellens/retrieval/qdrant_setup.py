from qdrant_client import QdrantClient, models

from labellens.config import settings


def get_client() -> QdrantClient:
    return QdrantClient(url=settings.qdrant_url)


def create_products_collection(
    client: QdrantClient,
    name: str | None = None,
    text_dim: int = 384,
    recreate: bool = False,
) -> None:
    name = name or settings.products_collection
    if client.collection_exists(name):
        if not recreate:
            print(f"Collection {name!r} already exists, leaving it alone.")
            return
        client.delete_collection(name)

    client.create_collection(
        collection_name=name,
        vectors_config={
            "text_dense": models.VectorParams(size=text_dim, distance=models.Distance.COSINE),
            "image_clip": models.VectorParams(size=512, distance=models.Distance.COSINE),
        },
        sparse_vectors_config={"bm25": models.SparseVectorParams(modifier=models.Modifier.IDF)},
    )

    keyword_fields = [
        "nutriscore",
        "categories",
        "allergens",
        "diet_vegan",
        "diet_vegetarian",
        "diet_gluten_free",
    ]
    for field in keyword_fields:
        client.create_payload_index(
            name, field_name=field, field_schema=models.PayloadSchemaType.KEYWORD
        )
    client.create_payload_index(
        name, field_name="nova", field_schema=models.PayloadSchemaType.INTEGER
    )
    client.create_payload_index(
        name, field_name="has_image", field_schema=models.PayloadSchemaType.BOOL
    )
    print(f"Created collection {name!r}.")


def create_knowledge_collection(
    client: QdrantClient, text_dim: int = 384, recreate: bool = False
) -> None:
    name = settings.knowledge_collection
    if client.collection_exists(name):
        if not recreate:
            print(f"Collection {name!r} already exists, leaving it alone.")
            return
        client.delete_collection(name)

    client.create_collection(
        collection_name=name,
        vectors_config={
            "text_dense": models.VectorParams(size=text_dim, distance=models.Distance.COSINE)
        },
    )
    for field in ["type", "key", "e_number", "category", "vegan"]:
        client.create_payload_index(
            name, field_name=field, field_schema=models.PayloadSchemaType.KEYWORD
        )
    print(f"Created collection {name!r}.")
