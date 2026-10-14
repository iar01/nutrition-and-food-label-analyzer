from labellens.retrieval.qdrant_setup import (
    create_knowledge_collection,
    create_products_collection,
    get_client,
)

client = get_client()
create_products_collection(client)
create_knowledge_collection(client)