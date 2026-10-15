"""Pytest test configuration and fixtures."""

import os
from collections.abc import Generator

import pytest
from labellens.config import Settings, get_settings


@pytest.fixture
def test_settings() -> Generator[Settings, None, None]:
    """Provide isolated Settings instance for unit tests."""
    original_env = dict(os.environ)
    # Ensure test environment overrides
    os.environ["APP_ENV"] = "test"
    os.environ["POSTGRES_DB"] = "test_labellens"
    os.environ["POSTGRES_HOST"] = "localhost"
    os.environ["POSTGRES_PORT"] = "5432"
    os.environ["QDRANT_HOST"] = "localhost"
    os.environ["QDRANT_PORT"] = "6333"

    # Invalidate cache and create fresh settings
    get_settings.cache_clear()
    settings = get_settings()

    yield settings

    os.environ.clear()
    os.environ.update(original_env)
    get_settings.cache_clear()


@pytest.fixture(scope="session", autouse=True)
def setup_test_infrastructure() -> None:
    """Ensure database schema, test products, and Qdrant collections exist for integration tests."""
    cfg = get_settings()

    # 1. Setup PostgreSQL schema & seed minimal product records if empty
    try:
        from labellens.db.base import Base
        from labellens.db.models import Nutrition, Product, ProductDietFlag
        from sqlalchemy import create_engine, text
        from sqlalchemy.orm import Session

        engine = create_engine(cfg.sync_database_url, connect_args={"connect_timeout": 3})
        with engine.begin() as conn:
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS pg_trgm;"))
            conn.execute(text("CREATE EXTENSION IF NOT EXISTS btree_gin;"))
            Base.metadata.create_all(conn)

            count = conn.execute(text("SELECT count(*) FROM products")).scalar() or 0
            if count == 0:
                with Session(conn) as session:
                    p1 = Product(
                        code="4008400401829",
                        name="Nutella Hazelnut Chocolate Spread",
                        brand="Ferrero",
                        quantity="400g",
                        categories=["en:spreads", "en:chocolate-spreads"],
                        ingredients_text="sugar, palm oil, hazelnuts (13%), skimmed milk powder (8.7%), fat-reduced cocoa (7.4%), emulsifier: lecithins (soya), vanillin.",
                        nutriscore="e",
                        nova=4,
                        ecoscore="d",
                        completeness=1.0,
                        quality_flags=[],
                        search_text="Nutella Hazelnut Chocolate Spread Ferrero sugar palm oil hazelnuts skimmed milk powder",
                    )
                    p2 = Product(
                        code="3017620422003",
                        name="Organic Wholemeal Bread",
                        brand="BioFarm",
                        quantity="500g",
                        categories=["en:breads"],
                        ingredients_text="wholemeal wheat flour, water, yeast, salt.",
                        nutriscore="a",
                        nova=1,
                        ecoscore="a",
                        completeness=1.0,
                        quality_flags=[],
                        search_text="Organic Wholemeal Bread BioFarm wholemeal wheat flour water yeast salt",
                    )
                    session.add_all([p1, p2])
                    session.flush()

                    session.add_all(
                        [
                            ProductDietFlag(code="4008400401829", diet="vegan", value="no"),
                            ProductDietFlag(code="3017620422003", diet="vegan", value="yes"),
                            Nutrition(
                                code="4008400401829",
                                energy_kcal=539.0,
                                fat_g=30.9,
                                sat_fat_g=10.6,
                                carbs_g=57.5,
                                sugars_g=56.3,
                                protein_g=6.3,
                                salt_g=0.107,
                            ),
                            Nutrition(
                                code="3017620422003",
                                energy_kcal=220.0,
                                fat_g=1.5,
                                sat_fat_g=0.3,
                                carbs_g=45.0,
                                sugars_g=2.0,
                                protein_g=9.0,
                                salt_g=0.8,
                            ),
                        ]
                    )
                    session.commit()
    except Exception:
        pass

    # 2. Setup Qdrant collections & seed points if empty
    try:
        from labellens.config import point_id
        from labellens.embeddings.sparse import Bm25SparseEmbedder
        from labellens.embeddings.text import BgeTextEmbedder
        from labellens.retrieval.qdrant_setup import (
            create_knowledge_collection,
            create_products_collection,
            get_client,
        )
        from qdrant_client import models

        client = get_client()
        client.get_collections()

        if not client.collection_exists(cfg.products_collection):
            create_products_collection(client)
        if not client.collection_exists(cfg.knowledge_collection):
            create_knowledge_collection(client)

        p_count = client.count(collection_name=cfg.products_collection).count
        if p_count == 0:
            text_emb = BgeTextEmbedder()
            sparse_emb = Bm25SparseEmbedder()

            test_items = [
                {
                    "code": "4008400401829",
                    "name": "Nutella Hazelnut Chocolate Spread",
                    "brands": "Ferrero",
                    "brand": "Ferrero",
                    "nutriscore": "e",
                    "nova": 4,
                    "diet_vegan": "no",
                    "has_image": False,
                    "categories": ["en:spreads", "en:chocolate-spreads"],
                    "search_text": "Nutella Hazelnut Chocolate Spread Ferrero",
                },
                {
                    "code": "3017620422003",
                    "name": "Organic Wholemeal Bread",
                    "brands": "BioFarm",
                    "brand": "BioFarm",
                    "nutriscore": "a",
                    "nova": 1,
                    "diet_vegan": "yes",
                    "has_image": False,
                    "categories": ["en:breads"],
                    "search_text": "Organic Wholemeal Bread BioFarm",
                },
            ]

            points = []
            for item in test_items:
                code_str = str(item["code"])
                search_str = str(item["search_text"])
                pid = point_id(code_str)
                dense_vec = text_emb.embed_query(search_str).tolist()
                sparse_vec = sparse_emb.embed_query(search_str)
                points.append(
                    models.PointStruct(
                        id=pid,
                        vector={"text_dense": dense_vec, "bm25": sparse_vec},
                        payload=item,
                    )
                )

            client.upsert(collection_name=cfg.products_collection, points=points)
    except Exception:
        pass
