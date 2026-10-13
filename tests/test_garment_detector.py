"""
Tests for garment type detection.
"""

import pytest
from tools.garment_detector import detect_garment_type


class TestJeansDetection:
    def test_explicit_jeans(self):
        result = detect_garment_type("Levi's 501 Original Fit Jeans", "")
        assert result["garment_type"] == "jeans"
        assert result["confidence"] == "high"

    def test_slim_jeans(self):
        result = detect_garment_type("ASOS DESIGN slim jeans in mid wash", "")
        assert result["garment_type"] == "jeans"

    def test_selvedge_denim(self):
        result = detect_garment_type("Slim Selvedge Jean", "14oz selvedge denim")
        assert result["garment_type"] == "jeans"

    def test_raw_denim(self):
        result = detect_garment_type("", "Raw denim, 100% cotton, 14oz")
        assert result["garment_type"] == "jeans"

    def test_denim_jacket_not_jeans(self):
        result = detect_garment_type("Denim Jacket - Indigo", "100% cotton denim")
        assert result["garment_type"] != "jeans"

    def test_501_model_number(self):
        result = detect_garment_type("Levi's 501 Shrink-to-Fit", "")
        assert result["garment_type"] == "jeans"


class TestTshirtDetection:
    def test_explicit_tshirt(self):
        result = detect_garment_type("Bella+Canvas 3001 Unisex Jersey Tee", "")
        assert result["garment_type"] == "tshirt"
        assert result["confidence"] == "high"

    def test_t_shirt_hyphenated(self):
        result = detect_garment_type("Cotton T-Shirt", "")
        assert result["garment_type"] == "tshirt"

    def test_tshirt_no_space(self):
        result = detect_garment_type("Premium Tshirt", "")
        assert result["garment_type"] == "tshirt"


class TestUnknown:
    def test_ambiguous_pants(self):
        result = detect_garment_type("Cotton stretch pants", "")
        assert result["garment_type"] == "unknown"

    def test_empty_input(self):
        result = detect_garment_type("", "", "")
        assert result["garment_type"] == "unknown"

    def test_jacket(self):
        result = detect_garment_type("Wool Blend Jacket", "60% wool, 40% polyester")
        assert result["garment_type"] != "jeans"


class TestHoodieDetection:
    def test_explicit_hoodie(self):
        result = detect_garment_type("Champion Reverse Weave Hoodie", "")
        assert result["garment_type"] == "hoodie"
        assert result["confidence"] == "high"

    def test_hooded_sweatshirt(self):
        result = detect_garment_type("Men's Hooded Sweatshirt", "80% cotton, 20% polyester")
        assert result["garment_type"] == "hoodie"
        assert result["confidence"] == "high"

    def test_zip_up_hoodie(self):
        result = detect_garment_type("Full-Zip Hoodie - Black", "")
        assert result["garment_type"] == "hoodie"

    def test_sweatshirt_with_fleece(self):
        """Sweatshirt + fleece = medium hoodie signal."""
        result = detect_garment_type("Fleece Sweatshirt", "brushed fleece interior")
        assert result["garment_type"] == "hoodie"

    def test_fleece_jacket_not_hoodie(self):
        """Fleece jacket should not be detected as hoodie."""
        result = detect_garment_type("Fleece Jacket - Quarter Zip", "")
        assert result["garment_type"] != "hoodie"

    def test_pullover_hoodie(self):
        result = detect_garment_type("Pullover Hoodie with Kangaroo Pocket", "")
        assert result["garment_type"] == "hoodie"


class TestSignals:
    def test_signals_populated(self):
        result = detect_garment_type("Levi's 501 Jeans", "selvedge denim")
        assert len(result["signals"]) > 0


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
