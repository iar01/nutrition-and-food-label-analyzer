"""Unit tests for barcode and nutrition validators."""

from labellens.data.validators import gs1_valid, validate_nutrition


class TestGS1Validation:
    def test_valid_ean13(self) -> None:
        # 3017620422003 is Nutella EAN-13
        assert gs1_valid("3017620422003") is True

    def test_valid_upc_a(self) -> None:
        # Standard UPC-A: 012345678905
        # Digits: 0,1,2,3,4,5,6,7,8,9,0. Reversed: 0,9,8,7,6,5,4,3,2,1,0
        # Odds (idx 0,2,4,6,8,10): 0,8,6,4,2,0 -> sum = 20 * 3 = 60
        # Evens (idx 1,3,5,7,9): 9,7,5,3,1 -> sum = 25 * 1 = 25
        # Total = 85 -> (10 - 85%10)%10 = 5
        assert gs1_valid("012345678905") is True

    def test_valid_gtin8(self) -> None:
        # GTIN-8: 96385074
        # 9,6,3,8,5,0,7, 4
        # Reversed: 7,0,5,8,3,6,9
        # idx 0,2,4,6: 7+5+3+9 = 24 * 3 = 72
        # idx 1,3,5: 0+8+6 = 14
        # Total = 86 -> (10 - 86%10)%10 = 4
        assert gs1_valid("96385074") is True

    def test_valid_gtin14(self) -> None:
        # GTIN-14: 10012345678902
        assert gs1_valid("10012345678902") is True

    def test_invalid_checksum(self) -> None:
        assert gs1_valid("3017620422004") is False
        assert gs1_valid("012345678906") is False

    def test_invalid_lengths(self) -> None:
        assert gs1_valid("1234567") is False  # 7 digits
        assert gs1_valid("123456789") is False  # 9 digits
        assert gs1_valid("12345678901") is False  # 11 digits
        assert gs1_valid("123456789012345") is False  # 15 digits

    def test_invalid_non_numeric(self) -> None:
        assert gs1_valid("301762042200A") is False
        assert gs1_valid("abc") is False
        assert gs1_valid("") is False
        assert gs1_valid("   ") is False


class TestNutritionValidation:
    def test_clean_nutritional_profile(self) -> None:
        nut = {
            "energy_kcal": 250.0,
            "fat_g": 10.0,
            "sat_fat_g": 2.0,
            "carbs_g": 30.0,
            "sugars_g": 5.0,
            "fiber_g": 3.0,
            "protein_g": 8.0,
            "salt_g": 0.51,
            "sodium_g": 0.20,
        }
        cleaned, flags = validate_nutrition(nut)
        assert len(flags) == 0
        assert cleaned["fat_g"] == 10.0
        assert cleaned["energy_kcal"] == 250.0

    def test_negative_macro_flagged_and_nulled(self) -> None:
        nut = {"fat_g": -5.0, "energy_kcal": 100.0}
        cleaned, flags = validate_nutrition(nut)
        assert "fat_g_negative" in flags
        assert cleaned["fat_g"] is None

    def test_macro_exceeds_100g(self) -> None:
        nut = {"carbs_g": 105.0}
        cleaned, flags = validate_nutrition(nut)
        assert "carbs_g_exceeds_100g" in flags
        assert cleaned["carbs_g"] is None

    def test_sat_fat_exceeds_fat(self) -> None:
        nut = {"fat_g": 5.0, "sat_fat_g": 10.0}
        cleaned, flags = validate_nutrition(nut)
        assert "sat_fat_exceeds_total_fat" in flags

    def test_sugars_exceed_carbs(self) -> None:
        nut = {"carbs_g": 12.0, "sugars_g": 25.0}
        cleaned, flags = validate_nutrition(nut)
        assert "sugars_exceed_carbs" in flags

    def test_salt_sodium_discrepancy(self) -> None:
        # salt should be approx 2.54 * sodium -> 0.1 * 2.54 = ~0.254g, not 5.0g
        nut = {"sodium_g": 0.1, "salt_g": 5.0}
        cleaned, flags = validate_nutrition(nut)
        assert "salt_sodium_discrepancy" in flags

    def test_macro_sum_exceeds_105g(self) -> None:
        nut = {
            "fat_g": 40.0,
            "carbs_g": 40.0,
            "protein_g": 30.0,  # sum = 110g > 105g
        }
        cleaned, flags = validate_nutrition(nut)
        assert "macro_sum_exceeds_100g" in flags

    def test_energy_macro_discrepancy(self) -> None:
        # Expected: 10*4 (carbs) + 10*4 (protein) + 10*9 (fat) = 170 kcal
        # Listed: 800 kcal -> discrepancy > 300 kcal
        nut = {
            "energy_kcal": 800.0,
            "fat_g": 10.0,
            "carbs_g": 10.0,
            "protein_g": 10.0,
        }
        cleaned, flags = validate_nutrition(nut)
        assert "energy_macro_discrepancy" in flags
