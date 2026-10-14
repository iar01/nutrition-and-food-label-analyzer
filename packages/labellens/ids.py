import uuid

PRODUCT_NAMESPACE = uuid.UUID("6ba7b810-9dad-11d1-80b4-00c04fd430c8")


def point_id(code: str) -> str:
    """Generate a deterministic UUID for a product code."""
    return str(uuid.uuid5(PRODUCT_NAMESPACE, str(code)))
