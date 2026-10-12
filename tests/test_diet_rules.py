"""Unit tests for dietary profile derivation rules (three-valued logic)."""

from labellens.data.diet_rules import derive_diet_flags


class TestDietRules:
    def test_empty_data_yields_all_unknown(self) -> None:
        flags = derive_diet_flags(
            analysis_tags=None,
            allergens=None,
            traces=None,
            labels=None,
            palm_oil_count=None,
        )
        assert flags["vegan"] == "unknown"
        assert flags["vegetarian"] == "unknown"
        assert flags["palm_oil_free"] == "unknown"
        assert flags["gluten_free"] == "unknown"
        assert flags["lactose_free"] == "unknown"
        assert flags["nut_free"] == "unknown"

    def test_explicit_vegan_and_vegetarian(self) -> None:
        flags = derive_diet_flags(
            analysis_tags=["en:vegan", "en:palm-oil-free"],
            allergens=[],
            traces=[],
            labels=["en:vegan"],
            palm_oil_count=0,
        )
        assert flags["vegan"] == "yes"
        # A vegan product is inherently vegetarian and lactose-free
        assert flags["vegetarian"] == "yes"
        assert flags["lactose_free"] == "yes"
        assert flags["palm_oil_free"] == "yes"

    def test_dairy_product_is_not_vegan_and_not_lactose_free(self) -> None:
        flags = derive_diet_flags(
            analysis_tags=["en:non-vegan", "en:vegetarian"],
            allergens=["en:milk"],
            traces=[],
        )
        assert flags["vegan"] == "no"
        assert flags["vegetarian"] == "yes"
        assert flags["lactose_free"] == "no"

    def test_meat_or_fish_product_is_not_vegetarian(self) -> None:
        flags = derive_diet_flags(
            analysis_tags=["en:non-vegetarian"],
            allergens=["en:fish"],
            traces=[],
        )
        assert flags["vegan"] == "no"
        assert flags["vegetarian"] == "no"

    def test_palm_oil_detection(self) -> None:
        # Flagged by analysis tag
        f1 = derive_diet_flags(
            analysis_tags=["en:palm-oil"],
            allergens=[],
            traces=[],
        )
        assert f1["palm_oil_free"] == "no"

        # Flagged by ingredient count
        f2 = derive_diet_flags(
            analysis_tags=[],
            allergens=[],
            traces=[],
            palm_oil_count=1,
        )
        assert f2["palm_oil_free"] == "no"

    def test_gluten_free_certification_and_allergens(self) -> None:
        # Product with wheat is not gluten free
        f_wheat = derive_diet_flags(
            analysis_tags=[],
            allergens=["en:wheat"],
            traces=[],
        )
        assert f_wheat["gluten_free"] == "no"

        # Product with gluten trace is not gluten free
        f_trace = derive_diet_flags(
            analysis_tags=[],
            allergens=[],
            traces=["en:gluten"],
        )
        assert f_trace["gluten_free"] == "no"

        # Certified gluten-free label
        f_cert = derive_diet_flags(
            analysis_tags=[],
            allergens=[],
            traces=[],
            labels=["en:gluten-free"],
        )
        assert f_cert["gluten_free"] == "yes"

    def test_nut_free_detection(self) -> None:
        f_nuts = derive_diet_flags(
            analysis_tags=[],
            allergens=["en:peanuts"],
            traces=[],
        )
        assert f_nuts["nut_free"] == "no"

        f_cert = derive_diet_flags(
            analysis_tags=[],
            allergens=[],
            traces=[],
            labels=["en:nut-free"],
        )
        assert f_cert["nut_free"] == "yes"
