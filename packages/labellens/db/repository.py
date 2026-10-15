"""Repository data-access layer for products, dietary filters, and user profiles."""

import uuid
from typing import Any

from sqlalchemy import func, or_, select
from sqlalchemy.dialects.postgresql import insert as pg_insert
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload

from labellens.db.models import (
    Additive,
    Product,
    ProductAdditive,
    ProductAllergen,
    ProductDietFlag,
    Profile,
    User,
)
from labellens.db.schemas import (
    AdditiveDetails,
    NutritionDetails,
    ProductDetail,
    ProductSummary,
    UserProfile,
)


class ProductRepository:
    """Data access repository for product retrieval, fuzzy searching, and filtering."""

    @staticmethod
    async def get_by_code(code: str, session: AsyncSession) -> ProductDetail | None:
        """Retrieve a product by exact GS1 barcode with all nutritional and dietary relations."""
        stmt = (
            select(Product)
            .where(Product.code == code)
            .options(
                selectinload(Product.nutrition),
                selectinload(Product.product_additives).selectinload(ProductAdditive.additive),
                selectinload(Product.allergens),
                selectinload(Product.diet_flags),
            )
        )
        result = await session.execute(stmt)
        product = result.scalar_one_or_none()
        if not product:
            return None

        # Build nutrition DTO
        nutr_dto = None
        if product.nutrition:
            nutr_dto = NutritionDetails(
                energy_kcal=product.nutrition.energy_kcal,
                fat_g=product.nutrition.fat_g,
                sat_fat_g=product.nutrition.sat_fat_g,
                carbs_g=product.nutrition.carbs_g,
                sugars_g=product.nutrition.sugars_g,
                fiber_g=product.nutrition.fiber_g,
                protein_g=product.nutrition.protein_g,
                salt_g=product.nutrition.salt_g,
                sodium_g=product.nutrition.sodium_g,
            )

        # Build additives DTO
        additives_dto = [
            AdditiveDetails(
                id=pa.additive.id,
                name=pa.additive.name,
                e_number=pa.additive.e_number,
                short_description=pa.additive.short_description,
            )
            for pa in product.product_additives
            if pa.additive
        ]

        # Build allergens list
        allergens_list = [{"allergen": a.allergen, "kind": a.kind} for a in product.allergens]

        # Build diet flags dict
        diet_dict = {df.diet: df.value for df in product.diet_flags}

        return ProductDetail(
            code=product.code,
            name=product.name,
            brand=product.brand,
            quantity=product.quantity,
            categories=product.categories,
            ingredients_text=product.ingredients_text,
            nutriscore=product.nutriscore,
            nova=product.nova,
            ecoscore=product.ecoscore,
            completeness=product.completeness,
            off_url=product.off_url,
            quality_flags=product.quality_flags,
            search_text=product.search_text,
            nutrition=nutr_dto,
            additives=additives_dto,
            allergens=allergens_list,
            diet_flags=diet_dict,
        )

    @staticmethod
    async def fuzzy_search_name(
        query: str,
        session: AsyncSession,
        limit: int = 20,
        similarity_threshold: float = 0.2,
    ) -> list[ProductSummary]:
        """Typo-tolerant fuzzy product search using PostgreSQL pg_trgm GIN index."""
        clean_q = query.strip()
        if not clean_q:
            return []

        # 1. Trigram similarity query leveraging ix_products_name_trgm (both whole string and word similarity)
        sim_col = func.similarity(Product.name, clean_q)
        wsim_col = func.word_similarity(clean_q, Product.name)
        stmt = (
            select(Product)
            .where(
                or_(
                    Product.name.op("%")(clean_q),
                    sim_col >= similarity_threshold,
                    wsim_col >= similarity_threshold,
                )
            )
            .order_by(func.greatest(sim_col, wsim_col).desc())
            .limit(limit)
        )
        result = await session.execute(stmt)
        products = list(result.scalars().all())

        # 2. Fallback to ILIKE if trigram similarity threshold returned empty (e.g. short words)
        if not products:
            fallback_stmt = (
                select(Product)
                .where(Product.name.ilike(f"%{clean_q}%"))
                .order_by(Product.completeness.desc())
                .limit(limit)
            )
            fallback_res = await session.execute(fallback_stmt)
            products = list(fallback_res.scalars().all())

        return [ProductSummary.model_validate(p) for p in products]

    @staticmethod
    async def filter_products(
        session: AsyncSession,
        diet_filters: dict[str, str] | None = None,
        exclude_allergens: list[str] | None = None,
        nutriscore: list[str] | None = None,
        nova_max: int | None = None,
        categories: list[str] | None = None,
        limit: int = 20,
        offset: int = 0,
    ) -> list[ProductSummary]:
        """Filtered product query answering exact questions using relational indexes."""
        stmt = select(Product)

        # Diet flags filtering (e.g. {"vegan": "yes", "gluten_free": "yes"})
        if diet_filters:
            for diet_name, flag_val in diet_filters.items():
                subq = select(ProductDietFlag.code).where(
                    (ProductDietFlag.diet == diet_name) & (ProductDietFlag.value == flag_val)
                )
                stmt = stmt.where(Product.code.in_(subq))

        # Allergen exclusion
        if exclude_allergens:
            allergen_subq = select(ProductAllergen.code).where(
                ProductAllergen.allergen.in_(exclude_allergens)
            )
            stmt = stmt.where(Product.code.not_in(allergen_subq))

        # Nutri-Score filter (e.g. ["a", "b"])
        if nutriscore:
            clean_scores = [s.lower() for s in nutriscore]
            stmt = stmt.where(Product.nutriscore.in_(clean_scores))

        # NOVA group maximum threshold (e.g. nova_max = 2 for minimally processed)
        if nova_max is not None:
            stmt = stmt.where((Product.nova.is_not(None)) & (Product.nova <= nova_max))

        # Category array overlap using GIN index
        if categories:
            stmt = stmt.where(Product.categories.overlap(categories))

        stmt = stmt.order_by(Product.completeness.desc()).limit(limit).offset(offset)
        result = await session.execute(stmt)
        products = result.scalars().all()
        return [ProductSummary.model_validate(p) for p in products]

    @staticmethod
    async def get_additives(code: str, session: AsyncSession) -> list[AdditiveDetails]:
        """Fetch all additives associated with a specific product barcode."""
        stmt = (
            select(Additive)
            .join(ProductAdditive, ProductAdditive.additive_id == Additive.id)
            .where(ProductAdditive.code == code)
        )
        result = await session.execute(stmt)
        additives = result.scalars().all()
        return [AdditiveDetails.model_validate(a) for a in additives]


class ProfileRepository:
    """Data access repository for managing user profiles and preferences."""

    @staticmethod
    async def get_profile(user_id: uuid.UUID, session: AsyncSession) -> UserProfile | None:
        """Fetch a user's dietary profile and wellness goals."""
        stmt = select(Profile).where(Profile.user_id == user_id).options(selectinload(Profile.user))
        result = await session.execute(stmt)
        profile = result.scalar_one_or_none()
        if not profile:
            return None

        email = profile.user.email if profile.user else None
        return UserProfile(
            user_id=profile.user_id,
            email=email,
            diets=profile.diets,
            allergens=profile.allergens,
            goals=profile.goals,
        )

    @staticmethod
    async def upsert_profile(
        user_id: uuid.UUID,
        diets: list[str],
        allergens: list[str],
        goals: dict[str, Any],
        session: AsyncSession,
        email: str | None = None,
    ) -> UserProfile:
        """Insert or update user and dietary profile idempotently."""
        # Ensure user exists
        if email:
            user_insert = (
                pg_insert(User)
                .values(id=user_id, email=email)
                .on_conflict_do_update(
                    index_elements=[User.id],
                    set_={"email": email},
                )
            )
        else:
            user_insert = (
                pg_insert(User)
                .values(id=user_id, email=email)
                .on_conflict_do_nothing(index_elements=[User.id])
            )
        await session.execute(user_insert)

        # Upsert profile
        profile_insert = (
            pg_insert(Profile)
            .values(
                user_id=user_id,
                diets=diets,
                allergens=allergens,
                goals=goals,
            )
            .on_conflict_do_update(
                index_elements=[Profile.user_id],
                set_={
                    "diets": diets,
                    "allergens": allergens,
                    "goals": goals,
                },
            )
        )
        await session.execute(profile_insert)
        await session.commit()

        return UserProfile(
            user_id=user_id,
            email=email,
            diets=diets,
            allergens=allergens,
            goals=goals,
        )
