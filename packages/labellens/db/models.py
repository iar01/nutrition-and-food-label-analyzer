"""SQLAlchemy 2 models for LabelLens structured PostgreSQL store."""

import uuid
from datetime import datetime
from typing import Any

from sqlalchemy import (
    DateTime,
    Float,
    ForeignKey,
    Index,
    Integer,
    String,
    Text,
    func,
)
from sqlalchemy.dialects.postgresql import ARRAY, JSONB, UUID
from sqlalchemy.orm import Mapped, mapped_column, relationship

from labellens.db.base import Base


class Product(Base):
    """Normalized core product entity."""

    __tablename__ = "products"

    code: Mapped[str] = mapped_column(String(14), primary_key=True)
    name: Mapped[str] = mapped_column(Text, nullable=False)
    brand: Mapped[str | None] = mapped_column(Text, nullable=True)
    quantity: Mapped[str | None] = mapped_column(Text, nullable=True)
    categories: Mapped[list[str] | None] = mapped_column(ARRAY(String), nullable=True)
    ingredients_text: Mapped[str] = mapped_column(Text, nullable=False)
    nutriscore: Mapped[str | None] = mapped_column(String(30), nullable=True)
    nova: Mapped[int | None] = mapped_column(Integer, nullable=True)
    ecoscore: Mapped[str | None] = mapped_column(String(30), nullable=True)
    completeness: Mapped[float] = mapped_column(Float, nullable=False)
    image_path: Mapped[str | None] = mapped_column(Text, nullable=True)
    off_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    quality_flags: Mapped[list[str]] = mapped_column(ARRAY(String), nullable=False, default=list)
    search_text: Mapped[str] = mapped_column(Text, nullable=False)

    # Relationships
    nutrition: Mapped["Nutrition | None"] = relationship(
        "Nutrition",
        back_populates="product",
        uselist=False,
        cascade="all, delete-orphan",
    )
    product_additives: Mapped[list["ProductAdditive"]] = relationship(
        "ProductAdditive",
        back_populates="product",
        cascade="all, delete-orphan",
    )
    additives: Mapped[list["Additive"]] = relationship(
        "Additive",
        secondary="product_additives",
        viewonly=True,
    )
    allergens: Mapped[list["ProductAllergen"]] = relationship(
        "ProductAllergen",
        back_populates="product",
        cascade="all, delete-orphan",
    )
    diet_flags: Mapped[list["ProductDietFlag"]] = relationship(
        "ProductDietFlag",
        back_populates="product",
        cascade="all, delete-orphan",
    )

    __table_args__ = (
        # Trigram GIN indexes for typo-tolerant fuzzy searching
        Index(
            "ix_products_name_trgm",
            "name",
            postgresql_using="gin",
            postgresql_ops={"name": "gin_trgm_ops"},
        ),
        Index(
            "ix_products_brand_trgm",
            "brand",
            postgresql_using="gin",
            postgresql_ops={"brand": "gin_trgm_ops"},
        ),
        # GIN index for category array membership
        Index("ix_products_categories_gin", "categories", postgresql_using="gin"),
        # B-tree indexes for analytical and filter lookups
        Index("ix_products_nutriscore", "nutriscore"),
        Index("ix_products_nova", "nova"),
    )


class Nutrition(Base):
    """Nutritional profile per 100g."""

    __tablename__ = "nutrition"

    code: Mapped[str] = mapped_column(
        String(14),
        ForeignKey("products.code", ondelete="CASCADE"),
        primary_key=True,
    )
    energy_kcal: Mapped[float | None] = mapped_column(Float, nullable=True)
    fat_g: Mapped[float | None] = mapped_column(Float, nullable=True)
    sat_fat_g: Mapped[float | None] = mapped_column(Float, nullable=True)
    carbs_g: Mapped[float | None] = mapped_column(Float, nullable=True)
    sugars_g: Mapped[float | None] = mapped_column(Float, nullable=True)
    fiber_g: Mapped[float | None] = mapped_column(Float, nullable=True)
    protein_g: Mapped[float | None] = mapped_column(Float, nullable=True)
    salt_g: Mapped[float | None] = mapped_column(Float, nullable=True)
    sodium_g: Mapped[float | None] = mapped_column(Float, nullable=True)

    product: Mapped["Product"] = relationship("Product", back_populates="nutrition")


class Additive(Base):
    """Standardized food additive catalog entity."""

    __tablename__ = "additives"

    id: Mapped[str] = mapped_column(Text, primary_key=True)  # e.g. "en:e322"
    name: Mapped[str | None] = mapped_column(Text, nullable=True)
    e_number: Mapped[str | None] = mapped_column(Text, nullable=True)
    short_description: Mapped[str | None] = mapped_column(Text, nullable=True)


class ProductAdditive(Base):
    """Many-to-many junction table between products and additives."""

    __tablename__ = "product_additives"

    code: Mapped[str] = mapped_column(
        String(14),
        ForeignKey("products.code", ondelete="CASCADE"),
        primary_key=True,
    )
    additive_id: Mapped[str] = mapped_column(
        Text,
        ForeignKey("additives.id", ondelete="CASCADE"),
        primary_key=True,
    )

    product: Mapped["Product"] = relationship("Product", back_populates="product_additives")
    additive: Mapped["Additive"] = relationship("Additive")


class ProductAllergen(Base):
    """Allergens declared in products (contains or traces)."""

    __tablename__ = "product_allergens"

    code: Mapped[str] = mapped_column(
        String(14),
        ForeignKey("products.code", ondelete="CASCADE"),
        primary_key=True,
    )
    allergen: Mapped[str] = mapped_column(Text, primary_key=True)
    kind: Mapped[str] = mapped_column(String(20), primary_key=True)  # 'contains' | 'traces'

    product: Mapped["Product"] = relationship("Product", back_populates="allergens")

    __table_args__ = (Index("ix_product_allergens_allergen_kind", "allergen", "kind"),)


class ProductDietFlag(Base):
    """Three-valued dietary compliance flags (yes / no / unknown)."""

    __tablename__ = "diet_flags"

    code: Mapped[str] = mapped_column(
        String(14),
        ForeignKey("products.code", ondelete="CASCADE"),
        primary_key=True,
    )
    diet: Mapped[str] = mapped_column(String(50), primary_key=True)  # 'vegan', 'vegetarian', etc.
    value: Mapped[str] = mapped_column(String(10), nullable=False)  # 'yes', 'no', 'unknown'

    product: Mapped["Product"] = relationship("Product", back_populates="diet_flags")

    __table_args__ = (Index("ix_diet_flags_diet_value", "diet", "value"),)


class User(Base):
    """Application user entity."""

    __tablename__ = "users"

    id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        primary_key=True,
        default=uuid.uuid4,
    )
    email: Mapped[str | None] = mapped_column(String(255), unique=True, nullable=True)
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    profile: Mapped["Profile | None"] = relationship(
        "Profile",
        back_populates="user",
        uselist=False,
        cascade="all, delete-orphan",
    )
    chat_sessions: Mapped[list["ChatSession"]] = relationship(
        "ChatSession",
        back_populates="user",
        cascade="all, delete-orphan",
    )


class Profile(Base):
    """User dietary preferences, allergen exclusions, and wellness goals."""

    __tablename__ = "profiles"

    user_id: Mapped[uuid.UUID] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="CASCADE"),
        primary_key=True,
    )
    diets: Mapped[list[str]] = mapped_column(ARRAY(String), nullable=False, default=list)
    allergens: Mapped[list[str]] = mapped_column(ARRAY(String), nullable=False, default=list)
    goals: Mapped[dict[str, Any]] = mapped_column(JSONB, nullable=False, default=dict)

    user: Mapped["User"] = relationship("User", back_populates="profile")


class ChatSession(Base):
    """Conversation thread tracking entity."""

    __tablename__ = "chat_sessions"

    thread_id: Mapped[str] = mapped_column(String(100), primary_key=True)
    user_id: Mapped[uuid.UUID | None] = mapped_column(
        UUID(as_uuid=True),
        ForeignKey("users.id", ondelete="SET NULL"),
        nullable=True,
    )
    created_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True),
        server_default=func.now(),
        nullable=False,
    )

    user: Mapped["User | None"] = relationship("User", back_populates="chat_sessions")
