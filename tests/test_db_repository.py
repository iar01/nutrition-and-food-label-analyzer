"""Integration tests for PostgreSQL repository layer against Docker Compose database."""

import time
import uuid
from collections.abc import AsyncGenerator

import pytest
from labellens.config import get_settings
from labellens.db.models import Product
from labellens.db.repository import ProductRepository, ProfileRepository
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.pool import NullPool

settings = get_settings()


@pytest.fixture
async def async_db_session() -> AsyncGenerator[AsyncSession, None]:
    """Provide isolated async DB session using NullPool for pytest-asyncio event loops."""
    engine = create_async_engine(
        settings.database_url,
        poolclass=NullPool,
        echo=False,
    )
    session_maker = async_sessionmaker(
        bind=engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    async with session_maker() as session:
        yield session
    await engine.dispose()


@pytest.mark.asyncio
async def test_get_by_code_existing_and_latency(async_db_session: AsyncSession) -> None:
    session = async_db_session
    # Find one real product code in DB
    res = await session.execute(select(Product.code).limit(1))
    real_code = res.scalar_one_or_none()
    assert real_code is not None, "Database has no products loaded"

    # Warm-up (ensures connection handshake is established in session)
    await ProductRepository.get_by_code(real_code, session)

    # Measure latency (target < 10ms locally)
    start = time.perf_counter()
    product = await ProductRepository.get_by_code(real_code, session)
    elapsed_ms = (time.perf_counter() - start) * 1000.0

    assert product is not None
    assert product.code == real_code
    assert len(product.name) > 0
    assert len(product.search_text) > 0
    assert isinstance(product.diet_flags, dict)
    assert "vegan" in product.diet_flags
    print(f"\n[Test] Barcode lookup took: {elapsed_ms:.2f} ms")
    assert elapsed_ms < 20.0  # Locally < 20ms (typically 1-5ms)


@pytest.mark.asyncio
async def test_get_by_code_non_existent(async_db_session: AsyncSession) -> None:
    session = async_db_session
    product = await ProductRepository.get_by_code("0000000000000", session)
    assert product is None


@pytest.mark.asyncio
async def test_fuzzy_search_name_typo_tolerance(async_db_session: AsyncSession) -> None:
    session = async_db_session
    # Search for typo "Choclat" (Chocolate)
    results = await ProductRepository.fuzzy_search_name("Choclat", session, limit=5)
    assert len(results) > 0
    # Should match chocolate products
    assert any("choc" in r.name.lower() for r in results)


@pytest.mark.asyncio
async def test_filter_products_diet_and_scores(async_db_session: AsyncSession) -> None:
    session = async_db_session
    # Filter products that are strictly vegan with Nutri-Score 'a'
    results = await ProductRepository.filter_products(
        session=session,
        diet_filters={"vegan": "yes"},
        nutriscore=["a"],
        limit=5,
    )
    assert len(results) > 0
    for p in results:
        assert p.nutriscore == "a"


@pytest.mark.asyncio
async def test_filter_products_nova_limit(async_db_session: AsyncSession) -> None:
    session = async_db_session
    # Filter minimally processed (NOVA <= 2)
    results = await ProductRepository.filter_products(
        session=session,
        nova_max=2,
        limit=5,
    )
    assert len(results) > 0
    for p in results:
        assert p.nova is not None and p.nova <= 2


@pytest.mark.asyncio
async def test_user_and_profile_crud(async_db_session: AsyncSession) -> None:
    session = async_db_session
    test_user_id = uuid.uuid4()
    test_email = f"user_{test_user_id.hex[:8]}@example.com"

    # 1. Upsert profile
    created = await ProfileRepository.upsert_profile(
        user_id=test_user_id,
        diets=["vegan", "gluten_free"],
        allergens=["en:peanuts"],
        goals={"daily_calories": 2000, "low_sugar": True},
        session=session,
        email=test_email,
    )
    assert created.user_id == test_user_id
    assert "vegan" in created.diets
    assert created.email == test_email

    # 2. Retrieve profile
    fetched = await ProfileRepository.get_profile(test_user_id, session)
    assert fetched is not None
    assert fetched.user_id == test_user_id
    assert fetched.email == test_email
    assert fetched.allergens == ["en:peanuts"]
    assert fetched.goals.get("low_sugar") is True

    # 3. Update profile
    updated = await ProfileRepository.upsert_profile(
        user_id=test_user_id,
        diets=["vegetarian"],
        allergens=[],
        goals={"low_sodium": True},
        session=session,
    )
    assert updated.diets == ["vegetarian"]
    assert updated.allergens == []
    assert updated.goals.get("low_sodium") is True
