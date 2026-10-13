"""
Unit tests for Jeans Quality Evaluator.

Tests scoring dimensions, brand detection, modifiers, edge cases,
and the 3 worked examples from the specification.
"""

import pytest
from tools.jeans_evaluator import evaluate_jeans
from tests.fixtures.sample_jeans import (
    HERITAGE_RAW_SELVAGE,
    PURE_BLUE_JAPAN,
    THREE_SIXTEEN,
    NUDIE_LEAN_DEAN,
    MID_RANGE_LEVIS_511,
    LEVIS_501_ORIGINAL,
    LEVIS_MADE_CRAFTED,
    BUCK_MASON,
    UNIQLO_KAIHARA_SELVEDGE,
    WRANGLER_COWBOY_CUT,
    FAST_FASHION_SKINNY,
    HM_SKINNY,
    SHEIN_BUDGET,
    HIGH_STRETCH_FASHION,
    WOMENS_SKINNY,
    SPEC_RICH_UNKNOWN_BRAND,
    BRAND_ONLY_NUDIE,
    SHEIN_SURPRISE_COTTON,
    OUTLET_JEANS,
    NO_BRAND_NO_WEIGHT,
    RAW_UNSANFORIZED,
    MISSING_MATERIALS,
)


class TestBasicEvaluation:
    """Test basic evaluation across quality tiers."""

    def test_heritage_raw_selvage(self):
        """Iron Heart 21oz should score excellent."""
        result = evaluate_jeans(HERITAGE_RAW_SELVAGE)
        assert result["quality_tier"] == "excellent"
        assert result["overall_score"] >= 85
        assert result["scores"]["stretch_retention"] == 5.0
        assert result["scores"]["longevity"] == 5.0
        assert result["estimated_washes"] >= 300

    def test_mid_range_levis(self):
        """Levi's 511 should score average-good range."""
        result = evaluate_jeans(MID_RANGE_LEVIS_511)
        assert result["quality_tier"] in ["average", "good"]
        assert result["scores"]["longevity"] >= 2.5

    def test_fast_fashion_skinny(self):
        """ASOS distressed skinny should score poorly."""
        result = evaluate_jeans(FAST_FASHION_SKINNY)
        assert result["quality_tier"] == "poor"
        assert result["overall_score"] < 30
        assert result["scores"]["fade_quality"] <= 2.0

    def test_returns_garment_type(self):
        """All evaluations should include garment_type = jeans."""
        result = evaluate_jeans(MID_RANGE_LEVIS_511)
        assert result["garment_type"] == "jeans"

    def test_returns_metric_definitions(self):
        """All evaluations should include metric_definitions for UI."""
        result = evaluate_jeans(MID_RANGE_LEVIS_511)
        assert "metric_definitions" in result
        assert len(result["metric_definitions"]) == 5
        keys = [m["key"] for m in result["metric_definitions"]]
        assert "stretch_retention" in keys
        assert "longevity" in keys
        assert "fade_quality" in keys


class TestFabricComposition:
    """Test fabric composition scoring."""

    def test_pure_cotton(self):
        """100% cotton should score highest."""
        result = evaluate_jeans(HERITAGE_RAW_SELVAGE)
        assert result["scores"]["stretch_retention"] == 5.0

    def test_minimal_stretch(self):
        """98-99% cotton with 1-2% elastane should score well."""
        result = evaluate_jeans(MID_RANGE_LEVIS_511)
        assert result["scores"]["stretch_retention"] >= 3.5

    def test_high_polyester(self):
        """High polyester blend should trigger red flags."""
        result = evaluate_jeans(SHEIN_BUDGET)
        red_flag_text = " ".join(result["warnings"])
        assert "polyester" in red_flag_text.lower()

    def test_high_stretch(self):
        """High elastane content should lower stretch retention."""
        result = evaluate_jeans(HIGH_STRETCH_FASHION)
        assert result["scores"]["stretch_retention"] <= 3.0  # 3% elastane = moderate


class TestDenimWeight:
    """Test denim weight parsing and scoring."""

    def test_heavyweight_parsing(self):
        """21oz should be parsed and scored as ultra-heavy."""
        result = evaluate_jeans(HERITAGE_RAW_SELVAGE)
        assert result["metadata"]["denim_weight_oz"] == 21

    def test_weight_from_brand_inference(self):
        """When weight not stated, infer from brand defaults."""
        result = evaluate_jeans(BRAND_ONLY_NUDIE)
        assert result["metadata"]["denim_weight_oz"] is not None

    def test_no_weight_no_brand(self):
        """No weight + no brand = weight unknown."""
        result = evaluate_jeans(NO_BRAND_NO_WEIGHT)
        # Weight might still be None since brand is empty
        assert result["data_confidence"] in ["low", "medium"]


class TestConstruction:
    """Test construction feature detection."""

    def test_selvage_detected(self):
        result = evaluate_jeans(HERITAGE_RAW_SELVAGE)
        assert result["metadata"]["construction_features"]["selvage"] is True

    def test_chain_stitch_detected(self):
        result = evaluate_jeans(HERITAGE_RAW_SELVAGE)
        assert result["metadata"]["construction_features"]["chain_stitch"] is True

    def test_rivets_detected(self):
        result = evaluate_jeans(HERITAGE_RAW_SELVAGE)
        assert result["metadata"]["construction_features"]["rivets"] is True

    def test_button_fly_detected(self):
        result = evaluate_jeans(HERITAGE_RAW_SELVAGE)
        assert result["metadata"]["construction_features"]["button_fly"] is True


class TestBrandTier:
    """Test brand detection and tier scoring."""

    def test_luxury_heritage_brand(self):
        result = evaluate_jeans(HERITAGE_RAW_SELVAGE)
        assert result["metadata"]["brand_tier_score"] >= 8.0

    def test_fast_fashion_brand(self):
        result = evaluate_jeans(SHEIN_BUDGET)
        assert result["metadata"]["brand_tier_score"] < 3.0

    def test_levis_subline_differentiation(self):
        """Levi's Made & Crafted should score higher than mainline."""
        mainline = evaluate_jeans(MID_RANGE_LEVIS_511)
        premium = evaluate_jeans(LEVIS_MADE_CRAFTED)
        assert premium["metadata"]["brand_tier_score"] > mainline["metadata"]["brand_tier_score"]

    def test_unknown_brand(self):
        result = evaluate_jeans(SPEC_RICH_UNKNOWN_BRAND)
        assert result["metadata"]["brand_tier_score"] <= 5.0


class TestModifiers:
    """Test fit, treatment, rise, and gender modifiers."""

    def test_skinny_fit_detected(self):
        result = evaluate_jeans(FAST_FASHION_SKINNY)
        assert result["metadata"]["fit_type"] == "skinny"

    def test_slim_fit_detected(self):
        result = evaluate_jeans(MID_RANGE_LEVIS_511)
        assert result["metadata"]["fit_type"] == "slim"

    def test_raw_treatment_detected(self):
        result = evaluate_jeans(RAW_UNSANFORIZED)
        assert result["metadata"]["treatment"] == "raw"

    def test_distressed_treatment_detected(self):
        result = evaluate_jeans(FAST_FASHION_SKINNY)
        assert result["metadata"]["treatment"] == "distressed"

    def test_rise_detected(self):
        result = evaluate_jeans(FAST_FASHION_SKINNY)
        assert result["metadata"]["rise"] == "low"

    def test_womens_adjustment(self):
        """Women's jeans should get ×0.85 modifier."""
        result = evaluate_jeans(WOMENS_SKINNY)
        assert result["metadata"]["gender"] == "women"
        assert result["metadata"]["modifiers_applied"]["gender"] == 0.85


class TestFadeQuality:
    """Test fade quality scoring."""

    def test_raw_denim_high_fade(self):
        """Raw denim should have high fade potential."""
        result = evaluate_jeans(HERITAGE_RAW_SELVAGE)
        assert result["scores"]["fade_quality"] >= 4.5

    def test_distressed_low_fade(self):
        """Distressed denim has minimal fade potential."""
        result = evaluate_jeans(FAST_FASHION_SKINNY)
        assert result["scores"]["fade_quality"] <= 2.0


class TestValueOutliers:
    """Test value outlier detection."""

    def test_uniqlo_exceptional_value(self):
        """Uniqlo Kaihara selvedge should be flagged as exceptional value."""
        result = evaluate_jeans(UNIQLO_KAIHARA_SELVEDGE)
        warnings_text = " ".join(result["warnings"])
        assert "uniqlo" in warnings_text.lower() or result["scores"]["value"] >= 4.0

    def test_wrangler_value(self):
        """Wrangler Cowboy Cut should be excellent value."""
        result = evaluate_jeans(WRANGLER_COWBOY_CUT)
        assert result["scores"]["value"] >= 4.0


class TestCareImpact:
    """Test care impact scenarios."""

    def test_care_impact_present(self):
        result = evaluate_jeans(MID_RANGE_LEVIS_511)
        assert "care_impact" in result
        assert "scenarios" in result["care_impact"]
        assert len(result["care_impact"]["scenarios"]) == 4

    def test_raw_denim_care(self):
        """Raw denim should get low care score (high maintenance)."""
        result = evaluate_jeans(HERITAGE_RAW_SELVAGE)
        assert result["scores"]["care"] <= 2.0

    def test_care_recommendations_for_raw(self):
        """Raw denim should get specific care recommendations."""
        result = evaluate_jeans(HERITAGE_RAW_SELVAGE)
        recs = result["care_impact"].get("recommendations", [])
        recs_text = " ".join(recs).lower()
        assert "raw" in recs_text or "wash" in recs_text


class TestFailureModes:
    """Test failure mode estimation."""

    def test_failure_modes_present(self):
        result = evaluate_jeans(MID_RANGE_LEVIS_511)
        assert "failure_modes" in result
        assert len(result["failure_modes"]) >= 2

    def test_skinny_crotch_blowout_risk(self):
        """Skinny fit should have high crotch blowout risk."""
        result = evaluate_jeans(FAST_FASHION_SKINNY)
        crotch = next((m for m in result["failure_modes"] if m["mode"] == "Crotch blowout"), None)
        assert crotch is not None
        assert crotch["risk"] == "high"


class TestTransparency:
    """Test transparency scoring."""

    def test_full_transparency(self):
        """Heritage denim with all specs should score high."""
        result = evaluate_jeans(HERITAGE_RAW_SELVAGE)
        assert result["transparency_score"] >= 7

    def test_low_transparency(self):
        """Brand-only listing should score low."""
        result = evaluate_jeans(BRAND_ONLY_NUDIE)
        assert result["transparency_score"] <= 3

    def test_ask_cs_prompts(self):
        """Low transparency should generate CS questions."""
        result = evaluate_jeans(BRAND_ONLY_NUDIE)
        assert len(result["ask_customer_service"]) > 0


class TestEdgeCases:
    """Test edge cases and graceful degradation."""

    def test_missing_materials(self):
        """Missing materials should still return valid result."""
        result = evaluate_jeans(MISSING_MATERIALS)
        # Gap is known brand, so should still produce some evaluation
        assert result["garment_type"] == "jeans"
        assert result["quality_tier"] in ["average", "poor", "unknown"]

    def test_all_explanations_present(self):
        """All score dimensions should have explanations."""
        result = evaluate_jeans(MID_RANGE_LEVIS_511)
        assert "stretch_retention" in result["explanations"]
        assert "longevity" in result["explanations"]
        assert "fade_quality" in result["explanations"]
        assert "value" in result["explanations"]
        assert "care" in result["explanations"]
        assert "transparency" in result["explanations"]

    def test_no_data_at_all(self):
        """No materials + no brand = unknown tier."""
        empty = {
            "price": None, "brand": "", "product_name": "",
            "materials_structured": [], "materials_text": ""
        }
        result = evaluate_jeans(empty)
        assert result["quality_tier"] == "unknown"


class TestWorkedExamples:
    """Validate against the 3 spec worked examples."""

    def test_spec_rich_unknown_brand(self):
        """98% cotton, 2% elastane, 13oz, $79 → mid-range tier."""
        result = evaluate_jeans(SPEC_RICH_UNKNOWN_BRAND)
        assert result["quality_tier"] in ["average", "good"]
        assert 40 <= result["overall_score"] <= 70
        assert result["estimated_washes"] >= 50

    def test_brand_only_nudie(self):
        """Nudie $120, no specs → uses brand defaults."""
        result = evaluate_jeans(BRAND_ONLY_NUDIE)
        assert result["quality_tier"] in ["good", "excellent"]
        assert result["estimated_washes"] >= 100

    def test_shein_surprise_cotton(self):
        """SHEIN 100% cotton $18 → still poor due to brand/construction."""
        result = evaluate_jeans(SHEIN_SURPRISE_COTTON)
        assert result["quality_tier"] in ["poor", "average"]
        assert result["overall_score"] < 50


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
