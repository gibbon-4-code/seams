"""
Unit tests for T-Shirt Quality Evaluator.

Tests all 5 dimensions, edge cases, and research-backed findings:
- Cotton type hierarchy
- GSM sweet spot
- 65/35 blend red flag
- Cost-per-wear calculation
- Construction quality signals
"""

import pytest
from tools.tshirt_evaluator import evaluate_tshirt
from tests.fixtures.sample_tshirts import (
    BUDGET_CARDED_COTTON,
    PREMIUM_COMBED_RINGSPUN,
    LUXURY_SUPIMA,
    BLEND_65_35_RED_FLAG,
    BLEND_50_50,
    TRI_BLEND,
    HIGH_GSM_SWEET_SPOT,
    ULTRA_LIGHT_GSM,
    SIDE_SEAMED_TEE,
    TUBULAR_TEE,
    PRESHRUNK_TEE,
    GARMENT_DYED_TEE,
    HIGH_SINGLES_COUNT,
    PIMA_COTTON,
    MISSING_MATERIALS,
    NO_PRICE,
    RESEARCH_SWEET_SPOT,
    LOW_TRANSPARENCY_PREMIUM,
    PARTIAL_TRANSPARENCY,
    MEDIUM_TRANSPARENCY
)


class TestBasicEvaluation:
    """Test basic evaluation scenarios across quality tiers."""

    def test_budget_carded_cotton(self):
        """Budget carded cotton tee should score average tier with warnings."""
        result = evaluate_tshirt(BUDGET_CARDED_COTTON)

        assert result["quality_tier"] in ["average", "good"]  # Around tier boundary (updated thresholds)
        assert 3.0 <= result["scores"]["longevity"] <= 3.5  # Performance-based: 35-45 washes
        assert result["scores"]["shrinkage"] == 2.0  # High shrinkage (untreated cotton)
        assert result["scores"]["pilling"] >= 3.0  # Moderate pilling
        assert result["overall_score"] < 70  # Below "excellent" threshold (updated)
        assert "Tubular construction" in str(result["warnings"])
        assert 45 <= result["estimated_washes"] <= 55  # Budget tier (improved formula)

    def test_premium_combed_ringspun(self):
        """Premium combed ring-spun (Bella+Canvas style) should score excellent."""
        result = evaluate_tshirt(PREMIUM_COMBED_RINGSPUN)

        assert result["quality_tier"] == "excellent"
        assert result["scores"]["longevity"] >= 4.0  # High longevity
        assert result["scores"]["pilling"] == 5.0  # Combed = no pilling
        assert result["scores"]["value"] == 5.0  # Sweet spot price
        assert result["overall_score"] >= 80  # Excellent tier
        assert result["estimated_washes"] >= 80  # Premium durability
        assert result["cost_per_wear"] < 0.35  # Good value
        assert "combed" in result["explanations"]["pilling"].lower()

    def test_luxury_supima(self):
        """Luxury Supima cotton should score perfect or near-perfect."""
        result = evaluate_tshirt(LUXURY_SUPIMA)

        assert result["quality_tier"] == "excellent"
        assert result["scores"]["longevity"] >= 4.5  # Near-perfect longevity (capped at 5.0)
        assert result["scores"]["shrinkage"] == 5.0  # Garment-dyed = no shrinkage
        assert result["scores"]["pilling"] == 5.0  # Supima resistant
        assert result["scores"]["care"] == 5.0  # Garment-dyed
        assert result["overall_score"] >= 90  # Near perfect
        assert result["estimated_washes"] >= 135  # Luxury durability
        assert result["cost_per_wear"] <= 0.35  # Best value despite high price
        assert "supima" in result["metadata"]["cotton_type"].lower()


class TestPillingDetection:
    """Test pilling score calculation and 65/35 red flag."""

    def test_65_35_pilling_red_flag(self):
        """65/35 blend should trigger severe pilling warning."""
        result = evaluate_tshirt(BLEND_65_35_RED_FLAG)

        assert result["scores"]["pilling"] == 1.8  # Severe pilling (updated scoring)
        assert result["quality_tier"] in ["poor", "average"]  # Dragged down by severe pilling (updated tiers)
        assert any("BLEND" in w for w in result["warnings"])  # Updated warning text
        assert "pilling" in result["explanations"]["pilling"].lower()

    def test_50_50_blend_no_red_flag(self):
        """50/50 blend should NOT trigger 65/35 red flag."""
        result = evaluate_tshirt(BLEND_50_50)

        assert result["scores"]["pilling"] != 1.0  # Not the worst
        assert result["scores"]["shrinkage"] == 5.0  # Preshrunk
        assert not any("65/35" in w for w in result["warnings"])

    def test_tri_blend_pilling(self):
        """Tri-blend with 50% poly should have severe pilling (updated scoring)."""
        result = evaluate_tshirt(TRI_BLEND)

        # 50% polyester falls in 35-65% range → severe pilling (updated scoring)
        assert result["scores"]["pilling"] == 1.8  # Severe pilling for high poly content
        assert result["scores"]["longevity"] >= 1.5  # Light tri-blend has moderate durability


class TestGSMDetection:
    """Test GSM parsing and sweet spot detection."""

    def test_gsm_sweet_spot(self):
        """180 GSM should get longevity boost (sweet spot)."""
        result = evaluate_tshirt(HIGH_GSM_SWEET_SPOT)

        assert result["metadata"]["gsm"] == 180.0
        assert result["scores"]["longevity"] >= 4.0  # Boosted
        assert "sweet spot" in result["explanations"]["longevity"].lower() or "180" in result["explanations"]["longevity"]

    def test_gsm_too_light(self):
        """130 GSM (ultra-light) should get lower longevity."""
        result = evaluate_tshirt(ULTRA_LIGHT_GSM)

        assert result["metadata"]["gsm"] == 130.0
        assert result["scores"]["longevity"] <= 3.0  # Penalized (performance-based)
        assert result["quality_tier"] in ["poor", "average"]  # Updated tier names


class TestConstructionDetection:
    """Test construction feature detection."""

    def test_side_seamed_vs_tubular(self):
        """Side-seamed should score higher than tubular."""
        side_seamed = evaluate_tshirt(SIDE_SEAMED_TEE)
        tubular = evaluate_tshirt(TUBULAR_TEE)

        assert side_seamed["scores"]["longevity"] > tubular["scores"]["longevity"]
        assert side_seamed["metadata"]["construction_features"].get("side_seamed") == True
        assert tubular["metadata"]["construction_features"].get("tubular") == True
        assert any("torque" in w.lower() or "twist" in w.lower() for w in tubular["warnings"])

    def test_preshrunk_detection(self):
        """Preshrunk treatment should boost shrinkage score."""
        result = evaluate_tshirt(PRESHRUNK_TEE)

        assert result["scores"]["shrinkage"] == 5.0  # Minimal shrinkage
        assert result["metadata"]["construction_features"].get("preshrunk") == True
        assert "preshrunk" in result["explanations"]["shrinkage"].lower()

    def test_garment_dyed_detection(self):
        """Garment-dyed should boost both shrinkage and care scores."""
        result = evaluate_tshirt(GARMENT_DYED_TEE)

        assert result["scores"]["shrinkage"] == 5.0  # Zero additional shrinkage
        assert result["scores"]["care"] == 5.0  # More stable
        assert result["metadata"]["construction_features"].get("garment_dyed") == True
        assert "garment-dyed" in result["explanations"]["shrinkage"].lower()


class TestSinglesCount:
    """Test singles count parsing and boost."""

    def test_singles_count_boost(self):
        """30+ singles should boost longevity."""
        result = evaluate_tshirt(HIGH_SINGLES_COUNT)

        assert result["metadata"]["singles_count"] == 32
        assert result["scores"]["longevity"] >= 3.5  # Good score with all boosts
        assert "32 singles" in result["explanations"]["longevity"]


class TestValueCalculation:
    """Test cost-per-wear and value scoring."""

    def test_cost_per_wear_sweet_spot(self):
        """$28 tee at 90 washes should get perfect value score."""
        result = evaluate_tshirt(RESEARCH_SWEET_SPOT)

        assert result["scores"]["value"] == 5.0  # Perfect value
        assert 20 <= RESEARCH_SWEET_SPOT["price"] <= 45  # In sweet spot
        assert result["cost_per_wear"] <= 0.35  # Good cost per wear
        assert "sweet spot" in result["explanations"]["value"].lower()

    def test_value_without_price(self):
        """Missing price should return None for value score."""
        result = evaluate_tshirt(NO_PRICE)

        assert result["scores"]["value"] is None
        assert result["cost_per_wear"] is None
        assert "no price" in result["explanations"]["value"].lower()


class TestCottonTypeHierarchy:
    """Test cotton type detection and hierarchy."""

    def test_pima_cotton_detection(self):
        """Pima cotton should be detected and scored high."""
        result = evaluate_tshirt(PIMA_COTTON)

        assert result["metadata"]["cotton_type"] == "pima"
        assert result["scores"]["longevity"] >= 4.5  # High boost
        assert result["estimated_washes"] >= 120  # Premium multiplier


class TestEdgeCases:
    """Test edge cases and missing data handling."""

    def test_missing_materials_data(self):
        """No materials data should return unknown tier with warnings."""
        result = evaluate_tshirt(MISSING_MATERIALS)

        assert result["quality_tier"] == "unknown"
        assert result["overall_score"] is None
        assert all(score is None for score in result["scores"].values())
        assert "Insufficient data" in result["explanations"]["error"]
        assert len(result["warnings"]) > 0


class TestOverallScoring:
    """Test overall score calculation and tier assignment."""

    def test_overall_score_calculation(self):
        """Overall score should be weighted average of dimension scores."""
        result = evaluate_tshirt(PREMIUM_COMBED_RINGSPUN)

        # Check that overall score is in 0-100 range
        assert 0 <= result["overall_score"] <= 100

        # Check tier matches score
        if result["overall_score"] >= 80:
            assert result["quality_tier"] == "excellent"
        elif result["overall_score"] >= 60:
            assert result["quality_tier"] == "good"
        elif result["overall_score"] >= 40:
            assert result["quality_tier"] == "fair"
        else:
            assert result["quality_tier"] == "poor"

    def test_longevity_and_pilling_weighted_most(self):
        """Longevity and pilling should have most weight in overall score."""
        # This is implicit in the algorithm (35% + 30% = 65% of total weight)
        # Test with poor pilling (65/35 blend)
        poor_pilling = evaluate_tshirt(BLEND_65_35_RED_FLAG)

        # Despite decent longevity, poor pilling should drag down overall score
        assert poor_pilling["quality_tier"] in ["average", "poor"]  # Updated tier expectations
        assert poor_pilling["overall_score"] < 60


class TestExplanations:
    """Test that explanations are generated for all scores."""

    def test_all_explanations_present(self):
        """All dimension scores should have explanations."""
        result = evaluate_tshirt(PREMIUM_COMBED_RINGSPUN)

        assert "longevity" in result["explanations"]
        assert "shrinkage" in result["explanations"]
        assert "pilling" in result["explanations"]
        assert "value" in result["explanations"]
        assert "care" in result["explanations"]

        # Explanations should not be empty
        for explanation in result["explanations"].values():
            assert len(explanation) > 0


class TestTransparencyScoring:
    """Test transparency scorecard (1-10) and data confidence."""

    def test_full_transparency(self):
        """Bella+Canvas with all specs should score 9/10 transparency (missing treatment)."""
        result = evaluate_tshirt(PREMIUM_COMBED_RINGSPUN)

        assert result["transparency_score"] == 9  # Near-perfect disclosure (missing treatment)
        assert result["data_confidence"] == "high"
        assert "transparency" in result["explanations"]
        assert "Excellent" in result["explanations"]["transparency"]
        assert len(result["ask_customer_service"]) == 0  # No critical missing specs

    def test_low_transparency(self):
        """'100% Cotton' only should score 2/10 with warnings."""
        result = evaluate_tshirt(LOW_TRANSPARENCY_PREMIUM)

        assert result["transparency_score"] == 2  # Only composition disclosed
        assert result["data_confidence"] == "low"
        assert any("TRANSPARENCY" in w for w in result["warnings"])
        assert len(result["ask_customer_service"]) >= 2  # Should prompt for missing specs
        assert any("type of cotton" in q.lower() for q in result["ask_customer_service"])
        assert any("weight" in q.lower() or "gsm" in q.lower() for q in result["ask_customer_service"])

    def test_partial_transparency(self):
        """Some specs missing should score 6/10 with medium confidence."""
        result = evaluate_tshirt(PARTIAL_TRANSPARENCY)

        assert result["transparency_score"] == 6  # Cotton type + GSM + composition
        assert result["data_confidence"] == "medium"
        assert "transparency" in result["explanations"]
        assert len(result["ask_customer_service"]) > 0  # Some specs missing

    def test_medium_transparency(self):
        """Good disclosure but missing singles/reinforcement should score 7-8/10."""
        result = evaluate_tshirt(MEDIUM_TRANSPARENCY)

        assert 7 <= result["transparency_score"] <= 8  # Good transparency
        assert result["data_confidence"] == "high"
        assert "transparency" in result["explanations"]
        # May or may not have ask_cs prompts depending on what's missing

    def test_ask_customer_service_prompts(self):
        """Missing specs should generate actionable customer service questions."""
        result = evaluate_tshirt(LOW_TRANSPARENCY_PREMIUM)

        ask_cs = result["ask_customer_service"]
        assert len(ask_cs) >= 2

        # Should prompt for critical missing specs
        ask_cs_text = " ".join(ask_cs).lower()
        assert "cotton" in ask_cs_text  # Cotton type question
        assert "gsm" in ask_cs_text or "weight" in ask_cs_text  # Weight question
        assert "construction" in ask_cs_text or "seam" in ask_cs_text  # Construction question

    def test_transparency_affects_confidence(self):
        """Verify data_confidence levels match transparency score ranges."""
        # High confidence (8-10)
        high_result = evaluate_tshirt(PREMIUM_COMBED_RINGSPUN)
        assert high_result["transparency_score"] >= 8
        assert high_result["data_confidence"] == "high"

        # Low confidence (1-4)
        low_result = evaluate_tshirt(LOW_TRANSPARENCY_PREMIUM)
        assert low_result["transparency_score"] <= 4
        assert low_result["data_confidence"] == "low"

        # Medium confidence (5-7)
        medium_result = evaluate_tshirt(PARTIAL_TRANSPARENCY)
        assert medium_result["transparency_score"] == 6  # Cotton type + GSM + composition
        assert medium_result["data_confidence"] == "medium"


class TestCareImpact:
    """Test care impact calculator showing how washing methods affect longevity."""

    def test_care_impact_scenarios_present(self):
        """All evaluations should include care impact with 4 scenarios."""
        result = evaluate_tshirt(PREMIUM_COMBED_RINGSPUN)

        assert "care_impact" in result
        assert "scenarios" in result["care_impact"]
        assert len(result["care_impact"]["scenarios"]) == 4

        # Check scenario structure
        for scenario in result["care_impact"]["scenarios"]:
            assert "method" in scenario
            assert "impact" in scenario
            assert "washes" in scenario
            assert "description" in scenario

    def test_care_impact_wash_progression(self):
        """Best care method should give most washes, worst should give least."""
        result = evaluate_tshirt(PREMIUM_COMBED_RINGSPUN)

        scenarios = result["care_impact"]["scenarios"]
        best = next(s for s in scenarios if s["impact"] == "Best")
        standard = next(s for s in scenarios if s["impact"] == "Standard")
        worst = next(s for s in scenarios if s["impact"] == "Worst")

        # Best should extend life
        assert best["washes"] > standard["washes"]
        # Worst should reduce life
        assert worst["washes"] < standard["washes"]
        # Standard should be baseline
        assert standard["washes"] == result["estimated_washes"]

    def test_care_impact_with_price(self):
        """When price available, scenarios should include cost-per-wear."""
        result = evaluate_tshirt(PREMIUM_COMBED_RINGSPUN)  # Has price

        scenarios = result["care_impact"]["scenarios"]
        for scenario in scenarios:
            assert "cost_per_wear" in scenario
            assert scenario["cost_per_wear"] > 0

    def test_care_impact_without_price(self):
        """When price unavailable, scenarios should work without cost-per-wear."""
        result = evaluate_tshirt(NO_PRICE)

        scenarios = result["care_impact"]["scenarios"]
        for scenario in scenarios:
            assert "cost_per_wear" not in scenario or scenario.get("cost_per_wear") is None
            assert "washes" in scenario  # Wash counts still available

    def test_care_impact_pure_cotton_recommendations(self):
        """100% cotton should get specific care recommendations."""
        result = evaluate_tshirt(PREMIUM_COMBED_RINGSPUN)  # 100% cotton

        recommendations = result["care_impact"]["recommendations"]
        assert len(recommendations) > 0

        recs_text = " ".join(recommendations).lower()
        assert "cotton" in recs_text or "cold" in recs_text

    def test_care_impact_poly_blend_recommendations(self):
        """Poly-cotton blends should get different recommendations."""
        result = evaluate_tshirt(BLEND_65_35_RED_FLAG)  # 65% cotton, 35% poly

        recommendations = result["care_impact"]["recommendations"]
        assert len(recommendations) > 0

        recs_text = " ".join(recommendations).lower()
        assert "polyester" in recs_text or "blend" in recs_text

    def test_care_impact_savings_calculation(self):
        """Savings should show value of better care methods."""
        result = evaluate_tshirt(PREMIUM_COMBED_RINGSPUN)  # Has price

        savings = result["care_impact"].get("savings")
        if savings:
            assert "cost_per_wear_reduction" in savings
            assert "additional_washes" in savings
            assert savings["additional_washes"] > 0
            assert "summary" in savings

    def test_care_impact_baseline_method(self):
        """Care impact should clearly identify baseline method."""
        result = evaluate_tshirt(PREMIUM_COMBED_RINGSPUN)

        assert "baseline_method" in result["care_impact"]
        assert "best_method" in result["care_impact"]
        assert result["care_impact"]["baseline_method"] != result["care_impact"]["best_method"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
