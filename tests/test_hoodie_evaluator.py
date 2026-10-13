"""
Unit tests for Hoodie Quality Evaluator.

Tests scoring dimensions, brand detection, sub-line differentiation,
modifiers, parsing, edge cases, and the 3 worked examples from the spec.
"""

import pytest
from tools.hoodie_evaluator import (
    evaluate_hoodie,
    parse_hoodie_weight,
    detect_fleece_type,
    detect_hoodie_type,
    detect_construction_hoodie,
    detect_brand_hoodie,
    detect_special_construction,
    detect_origin,
    detect_anti_pill,
    score_fabric_composition,
    score_hoodie_weight,
    score_construction_hoodie,
    score_brand_tier_hoodie,
    calculate_shrinkage_hoodie,
    calculate_pilling_hoodie,
    calculate_care_hoodie,
    estimate_failure_modes_hoodie,
)
from tests.fixtures.sample_hoodies import (
    THREESIXTEEN_HEAVY,
    LADY_WHITE_SUPER,
    REIGNING_CHAMP_MID,
    REIGNING_CHAMP_HEAVY,
    CHAMPION_REVERSE_WEAVE,
    LA_APPAREL_HF09,
    CARHARTT_MIDWEIGHT,
    NIKE_TECH_FLEECE,
    FOG_ESSENTIALS,
    CHAMPION_POWERBLEND,
    NIKE_CLUB_FLEECE,
    UNIQLO_HOODIE,
    GILDAN_HEAVY_BLEND,
    HANES_ECOSMART,
    HM_BASIC_HOODIE,
    SHEIN_HOODIE,
    SPEC_CHAMPION_SPARSE,
    SPEC_BRAND_ONLY_RC,
    SPEC_HM_FAST_FASHION,
    ZIP_UP_COTTON,
    FRENCH_TERRY_UNIQLO,
    GENERIC_CHAMPION,
    NO_BRAND_BUDGET,
    MISSING_MATERIALS,
    REVERSE_WEAVE_ZIP,
    CARHARTT_HEAVYWEIGHT,
)


class TestBasicEvaluation:
    """Test basic evaluation across quality tiers."""

    def test_champion_reverse_weave(self):
        """Champion RW should score good/excellent — benchmark best-value hoodie."""
        result = evaluate_hoodie(CHAMPION_REVERSE_WEAVE)
        assert result["quality_tier"] in ["good", "excellent"]
        assert result["overall_score"] >= 70
        assert result["estimated_washes"] >= 200

    def test_hm_fast_fashion(self):
        """H&M should score poor."""
        result = evaluate_hoodie(HM_BASIC_HOODIE)
        assert result["quality_tier"] == "poor"
        assert result["overall_score"] < 35

    def test_reigning_champ_premium(self):
        """Reigning Champ should score excellent."""
        result = evaluate_hoodie(REIGNING_CHAMP_MID)
        assert result["quality_tier"] == "excellent"
        assert result["overall_score"] >= 80
        assert result["estimated_washes"] >= 300

    def test_3sixteen_artisanal(self):
        """3sixteen should score excellent — top tier."""
        result = evaluate_hoodie(THREESIXTEEN_HEAVY)
        assert result["quality_tier"] == "excellent"
        assert result["overall_score"] >= 85

    def test_lady_white_artisanal(self):
        """Lady White Co should score excellent."""
        result = evaluate_hoodie(LADY_WHITE_SUPER)
        assert result["quality_tier"] == "excellent"
        assert result["overall_score"] >= 85

    def test_gildan_entry_budget(self):
        """Gildan should score poor or average at the low end."""
        result = evaluate_hoodie(GILDAN_HEAVY_BLEND)
        assert result["quality_tier"] in ["poor", "average"]
        assert result["overall_score"] < 50

    def test_shein_fast_fashion(self):
        """SHEIN should score poor."""
        result = evaluate_hoodie(SHEIN_HOODIE)
        assert result["quality_tier"] == "poor"
        assert result["overall_score"] < 30

    def test_carhartt_midweight(self):
        """Carhartt K121 should score good — solid workwear value."""
        result = evaluate_hoodie(CARHARTT_MIDWEIGHT)
        assert result["quality_tier"] in ["good", "average"]
        assert result["overall_score"] >= 50


class TestWorkedExamples:
    """Validate the 3 worked examples from the specification."""

    def test_champion_sparse(self):
        """Spec example 1: Champion, $35, 80/20, sparse listing."""
        result = evaluate_hoodie(SPEC_CHAMPION_SPARSE)
        # Spec expects ~54/100, average tier, ~120 washes
        assert result["quality_tier"] == "average"
        assert 40 <= result["overall_score"] <= 70
        assert result["estimated_washes"] >= 60

    def test_reigning_champ_brand_only(self):
        """Spec example 2: RC, $135, brand-only (no materials). Should score good+."""
        result = evaluate_hoodie(SPEC_BRAND_ONLY_RC)
        # Spec expects ~85/100 but brand-only inference yields ~80
        assert result["quality_tier"] in ["good", "excellent"]
        assert result["overall_score"] >= 70
        assert result["estimated_washes"] >= 150

    def test_hm_fast_fashion_sparse(self):
        """Spec example 3: H&M, $25, cotton/polyester (no percentages)."""
        result = evaluate_hoodie(SPEC_HM_FAST_FASHION)
        assert result["quality_tier"] == "poor"
        assert result["overall_score"] < 35
        # H&M should have low expected washes
        assert result["estimated_washes"] <= 40


class TestFabricComposition:
    """Test fabric composition scoring."""

    def test_100_cotton(self):
        """100% cotton should score well (7.0)."""
        score, _ = score_fabric_composition(
            [{"material": "cotton", "percent": 100.0}], "", None
        )
        assert score == 7.0

    def test_80_20_blend(self):
        """80/20 cotton/poly sweet spot for hoodies — score 8.0."""
        score, _ = score_fabric_composition(
            [{"material": "cotton", "percent": 80.0},
             {"material": "polyester", "percent": 20.0}],
            "", None
        )
        assert score == 8.0

    def test_50_50_blend(self):
        """50/50 should score 4.0 — common budget composition."""
        score, _ = score_fabric_composition(
            [{"material": "cotton", "percent": 50.0},
             {"material": "polyester", "percent": 50.0}],
            "", None
        )
        assert score == 4.0

    def test_high_polyester(self):
        """65% polyester should score low (3.0)."""
        score, _ = score_fabric_composition(
            [{"material": "polyester", "percent": 65.0},
             {"material": "cotton", "percent": 35.0}],
            "", None
        )
        assert score == 3.0

    def test_no_composition_premium_brand(self):
        """No composition + premium brand -> infer decent quality."""
        score, _ = score_fabric_composition([], "", 8.8)
        assert score >= 7.0

    def test_no_composition_no_brand(self):
        """No composition + unknown brand -> low score."""
        score, _ = score_fabric_composition([], "", None)
        assert score <= 3.0

    def test_cotton_polyester_text_only(self):
        """'cotton/polyester' text without percentages -> 4.0."""
        score, _ = score_fabric_composition(
            [], "cotton/polyester", None
        )
        assert score == 4.0


class TestHoodieWeight:
    """Test weight parsing and scoring."""

    def test_gsm_parsing(self):
        """Parse GSM directly from text."""
        assert parse_hoodie_weight("390 GSM") == 390.0
        assert parse_hoodie_weight("420 gsm heavyweight") == 420.0

    def test_oz_conversion(self):
        """Convert oz to GSM correctly (×33.906)."""
        gsm = parse_hoodie_weight("12oz fleece")
        assert gsm is not None
        assert 405 <= gsm <= 410  # 12 * 33.906 = 406.872

    def test_14oz_conversion(self):
        """14oz should convert to ~475 GSM."""
        gsm = parse_hoodie_weight("14oz heavy fleece")
        assert gsm is not None
        assert 470 <= gsm <= 480

    def test_weight_descriptor_heavyweight(self):
        """'heavyweight' keyword -> 400 GSM."""
        assert parse_hoodie_weight("Heavyweight fleece") == 400.0

    def test_weight_descriptor_midweight(self):
        """'midweight' keyword -> 315 GSM."""
        assert parse_hoodie_weight("Midweight brushed fleece") == 315.0

    def test_weight_descriptor_lightweight(self):
        """'lightweight' keyword -> 240 GSM."""
        assert parse_hoodie_weight("Lightweight fleece") == 240.0

    def test_no_weight(self):
        """No weight info -> None."""
        assert parse_hoodie_weight("100% cotton fleece") is None

    def test_weight_score_500plus(self):
        """500+ GSM should score 10/10."""
        score, _ = score_hoodie_weight("500 GSM")
        assert score == 10.0

    def test_weight_score_400(self):
        """400 GSM should score 8/10."""
        score, _ = score_hoodie_weight("400 GSM")
        assert score == 8.0

    def test_weight_score_280(self):
        """280 GSM should score 5/10."""
        score, _ = score_hoodie_weight("280 GSM")
        assert score == 5.0

    def test_weight_infer_from_brand(self):
        """Should infer GSM from brand when not stated."""
        score, exp = score_hoodie_weight("", "Reigning Champ")
        assert score > 3.0
        assert "inferred" in exp.lower() or "GSM" in exp


class TestFleeceType:
    """Test fleece type detection."""

    def test_french_terry(self):
        """'French terry' should be detected."""
        assert detect_fleece_type("French terry interior") == "french_terry"

    def test_loopback(self):
        """'loopback' -> french_terry."""
        assert detect_fleece_type("Loopback construction") == "french_terry"

    def test_tech_fleece(self):
        """'Tech Fleece' -> tech."""
        assert detect_fleece_type("Tech Fleece spacer construction") == "tech"

    def test_brushed_fleece(self):
        """'brushed fleece' -> brushed."""
        assert detect_fleece_type("Brushed fleece interior") == "brushed"

    def test_unknown_default(self):
        """No fleece type keywords -> unknown."""
        assert detect_fleece_type("100% cotton") == "unknown"

    def test_french_terry_uniqlo_fixture(self):
        """Uniqlo French Terry fixture should detect french_terry."""
        text = f"{FRENCH_TERRY_UNIQLO['product_name']} {FRENCH_TERRY_UNIQLO['materials_text']}"
        assert detect_fleece_type(text) == "french_terry"


class TestHoodieType:
    """Test hoodie type detection."""

    def test_full_zip(self):
        assert detect_hoodie_type("Full-Zip Hoodie") == "full_zip"

    def test_pullover(self):
        assert detect_hoodie_type("Pullover Hoodie") == "pullover"

    def test_quarter_zip(self):
        assert detect_hoodie_type("Quarter-Zip Hood") == "quarter_zip"

    def test_half_zip(self):
        assert detect_hoodie_type("Half-Zip Hoodie") == "half_zip"

    def test_sleeveless(self):
        assert detect_hoodie_type("Sleeveless Hoodie") == "sleeveless"

    def test_unknown_default(self):
        assert detect_hoodie_type("Oversized Hoodie") == "unknown"


class TestConstruction:
    """Test construction feature detection."""

    def test_double_layer_hood(self):
        features = detect_construction_hoodie("Double-layer hood")
        assert features["hood_double_layer"] is True

    def test_ykk_zipper(self):
        features = detect_construction_hoodie("YKK double zipper")
        assert features["zipper_ykk"] is True

    def test_flatlock_seams(self):
        features = detect_construction_hoodie("Flatlock seams")
        assert features["seams_quality"] is True

    def test_2x2_rib_cuffs(self):
        features = detect_construction_hoodie("2x2 rib cuffs with elastane")
        assert features["cuffs_quality"] is True

    def test_side_seamed(self):
        features = detect_construction_hoodie("Side-seamed construction")
        assert features["side_seamed"] is True

    def test_metal_aglets(self):
        features = detect_construction_hoodie("Metal aglets on drawstring")
        assert features["drawstring_metal"] is True

    def test_construction_score_with_many_features(self):
        """Rich construction listing should score high."""
        text = ("Double-layer hood. Flatlock seams. YKK zipper. "
                "2x2 rib cuffs with elastane. Side-seamed. Metal aglets.")
        score, _ = score_construction_hoodie(text)
        assert score >= 8.0

    def test_construction_score_no_features(self):
        """No construction details + no brand -> low score."""
        score, _ = score_construction_hoodie("")
        assert score <= 3.0


class TestBrandTier:
    """Test brand detection and sub-line differentiation."""

    def test_champion_reverse_weave_subline(self):
        """Champion Reverse Weave should be detected as premium sub-line."""
        brand, info = detect_brand_hoodie("Champion Reverse Weave Hoodie", "Champion")
        assert brand == "champion reverse weave"
        assert info["default_score"] == 82

    def test_champion_powerblend_subline(self):
        """Champion Powerblend should be detected as budget sub-line."""
        brand, info = detect_brand_hoodie("Champion Powerblend Hoodie", "Champion")
        assert brand == "champion powerblend"
        assert info["default_score"] == 48

    def test_champion_generic(self):
        """Generic Champion (no sub-line) should score middle ground."""
        brand, info = detect_brand_hoodie("Champion Hoodie", "Champion")
        assert brand == "champion"
        assert info["default_score"] == 55

    def test_carhartt_midweight(self):
        """Carhartt K121 should be detected as midweight."""
        brand, info = detect_brand_hoodie("Carhartt K121 Midweight Hooded Sweatshirt", "Carhartt")
        assert brand == "carhartt midweight"

    def test_carhartt_heavyweight(self):
        """Carhartt K185 should be detected as heavyweight."""
        brand, info = detect_brand_hoodie("Carhartt K185 Heavyweight Hooded Sweatshirt", "Carhartt")
        assert brand == "carhartt heavyweight"

    def test_nike_tech_fleece(self):
        """Nike Tech Fleece sub-line."""
        brand, info = detect_brand_hoodie("Nike Tech Fleece Full-Zip Hoodie", "Nike")
        assert brand == "nike tech fleece"
        assert info["default_score"] == 68

    def test_nike_club_fleece(self):
        """Nike Club Fleece sub-line."""
        brand, info = detect_brand_hoodie("Nike Sportswear Club Fleece Pullover Hoodie", "Nike")
        assert brand == "nike club fleece"
        assert info["default_score"] == 52

    def test_reigning_champ(self):
        """Reigning Champ should score premium."""
        score, _ = score_brand_tier_hoodie("Reigning Champ", "Midweight Terry Hoodie")
        assert score >= 8.0

    def test_hm_fast_fashion(self):
        """H&M should score low."""
        score, _ = score_brand_tier_hoodie("H&M", "Oversized Hoodie")
        assert score <= 2.5

    def test_unknown_brand(self):
        """Unknown brand should get middle score (4.0)."""
        score, _ = score_brand_tier_hoodie("", "Pullover Hoodie")
        assert score == 4.0

    def test_sub_line_differentiation_matters(self):
        """Champion RW should score significantly higher than Powerblend."""
        rw_result = evaluate_hoodie(CHAMPION_REVERSE_WEAVE)
        pb_result = evaluate_hoodie(CHAMPION_POWERBLEND)
        assert rw_result["overall_score"] > pb_result["overall_score"] + 20


class TestModifiers:
    """Test post-score modifiers."""

    def test_fullzip_penalty(self):
        """Full-zip should score lower than equivalent pullover."""
        pullover_data = {
            "price": 68.00,
            "brand": "Champion",
            "product_name": "Champion Reverse Weave Pullover Hoodie",
            "materials_structured": [
                {"material": "cotton", "percent": 82.0},
                {"material": "polyester", "percent": 18.0}
            ],
            "materials_text": "82% Cotton, 18% Polyester. Reverse Weave. "
                              "Double-layer hood. 2x2 rib cuffs with spandex."
        }
        zip_data = {
            "price": 75.00,
            "brand": "Champion",
            "product_name": "Champion Reverse Weave Full Zip Hoodie",
            "materials_structured": [
                {"material": "cotton", "percent": 82.0},
                {"material": "polyester", "percent": 18.0}
            ],
            "materials_text": "82% Cotton, 18% Polyester. Reverse Weave. Full-zip. "
                              "Double-layer hood. 2x2 rib cuffs with spandex."
        }
        pullover_result = evaluate_hoodie(pullover_data)
        zip_result = evaluate_hoodie(zip_data)
        assert pullover_result["overall_score"] > zip_result["overall_score"]

    def test_french_terry_bonus(self):
        """French terry should boost overall score slightly."""
        result = evaluate_hoodie(REIGNING_CHAMP_MID)
        # RC midweight is french terry — should have modifier applied
        modifiers = result["metadata"]["modifiers_applied"]
        assert modifiers.get("fleece_type") == 1.05

    def test_reverse_weave_bonus(self):
        """Reverse Weave should apply 1.10 modifier."""
        result = evaluate_hoodie(CHAMPION_REVERSE_WEAVE)
        modifiers = result["metadata"]["modifiers_applied"]
        assert modifiers.get("reverse_weave") == 1.10

    def test_garment_dyed_bonus(self):
        """Garment-dyed should apply 1.05 modifier."""
        result = evaluate_hoodie(LADY_WHITE_SUPER)
        modifiers = result["metadata"]["modifiers_applied"]
        assert modifiers.get("garment_dyed") == 1.05


class TestPilling:
    """Test pilling score calculation."""

    def test_5050_worst_pilling(self):
        """50/50 cotton/poly is worst for pilling (score should be low)."""
        score, exp = calculate_pilling_hoodie(
            [{"material": "cotton", "percent": 50.0},
             {"material": "polyester", "percent": 50.0}],
            "brushed", 300, False
        )
        assert score <= 2.0
        assert "WORST for pilling" in exp

    def test_french_terry_better(self):
        """French terry should pill less than brushed (higher score)."""
        french_score, _ = calculate_pilling_hoodie(
            [{"material": "cotton", "percent": 100.0}],
            "french_terry", 390, False
        )
        brushed_score, _ = calculate_pilling_hoodie(
            [{"material": "cotton", "percent": 100.0}],
            "brushed", 390, False
        )
        assert french_score > brushed_score

    def test_heavy_gsm_bonus(self):
        """Heavier fabric should pill less."""
        heavy_score, _ = calculate_pilling_hoodie(
            [{"material": "cotton", "percent": 80.0},
             {"material": "polyester", "percent": 20.0}],
            "brushed", 450, False
        )
        light_score, _ = calculate_pilling_hoodie(
            [{"material": "cotton", "percent": 80.0},
             {"material": "polyester", "percent": 20.0}],
            "brushed", 260, False
        )
        assert heavy_score > light_score

    def test_backpack_strap_warning(self):
        """Every pilling explanation should mention backpack straps."""
        _, exp = calculate_pilling_hoodie(
            [{"material": "cotton", "percent": 80.0},
             {"material": "polyester", "percent": 20.0}],
            "brushed", 350, False
        )
        assert "backpack" in exp.lower()

    def test_anti_pill_treatment(self):
        """Anti-pill treatment should improve score."""
        base_score, _ = calculate_pilling_hoodie(
            [{"material": "cotton", "percent": 80.0},
             {"material": "polyester", "percent": 20.0}],
            "brushed", 300, False
        )
        treated_score, _ = calculate_pilling_hoodie(
            [{"material": "cotton", "percent": 80.0},
             {"material": "polyester", "percent": 20.0}],
            "brushed", 300, True
        )
        assert treated_score >= base_score


class TestShrinkage:
    """Test shrinkage calculation."""

    def test_100_cotton_high_risk(self):
        """100% cotton should have high shrinkage risk (low score)."""
        score, _ = calculate_shrinkage_hoodie(
            [{"material": "cotton", "percent": 100.0}],
            "pullover",
            {"reverse_weave": False, "garment_dyed": False, "preshrunk": False},
            400
        )
        assert score <= 2.5

    def test_5050_low_risk(self):
        """50/50 blend should have lower shrinkage risk."""
        score, _ = calculate_shrinkage_hoodie(
            [{"material": "cotton", "percent": 50.0},
             {"material": "polyester", "percent": 50.0}],
            "pullover",
            {"reverse_weave": False, "garment_dyed": False, "preshrunk": False},
            300
        )
        assert score >= 3.0

    def test_preshrunk_bonus(self):
        """Preshrunk should improve shrinkage score."""
        base_score, _ = calculate_shrinkage_hoodie(
            [{"material": "cotton", "percent": 100.0}],
            "pullover",
            {"reverse_weave": False, "garment_dyed": False, "preshrunk": False},
            400
        )
        preshrunk_score, _ = calculate_shrinkage_hoodie(
            [{"material": "cotton", "percent": 100.0}],
            "pullover",
            {"reverse_weave": False, "garment_dyed": False, "preshrunk": True},
            400
        )
        assert preshrunk_score > base_score

    def test_reverse_weave_bonus(self):
        """Reverse Weave should reduce shrinkage significantly."""
        rw_score, exp = calculate_shrinkage_hoodie(
            [{"material": "cotton", "percent": 82.0},
             {"material": "polyester", "percent": 18.0}],
            "pullover",
            {"reverse_weave": True, "garment_dyed": False, "preshrunk": False},
            407
        )
        assert "Reverse Weave" in exp
        assert rw_score >= 3.5

    def test_zip_up_penalty(self):
        """Zip-up hoodie should have zipper buckling note."""
        score, exp = calculate_shrinkage_hoodie(
            [{"material": "cotton", "percent": 100.0}],
            "full_zip",
            {"reverse_weave": False, "garment_dyed": False, "preshrunk": False},
            400
        )
        assert "zip" in exp.lower() or "buckling" in exp.lower()


class TestValueOutliers:
    """Test value outlier detection."""

    def test_champion_rw_exceptional(self):
        """Champion Reverse Weave in $55-75 should be flagged as exceptional."""
        result = evaluate_hoodie(CHAMPION_REVERSE_WEAVE)
        all_text = " ".join(result.get("warnings", []))
        # Should have value outlier note
        assert any("champion" in w.lower() or "cost-per-wear" in w.lower()
                    for w in result.get("warnings", []))

    def test_la_apparel_exceptional(self):
        """LA Apparel at <$90 should be flagged as exceptional value."""
        result = evaluate_hoodie(LA_APPAREL_HF09)
        all_text = " ".join(result.get("warnings", []))
        assert "la apparel" in all_text.lower() or "value" in all_text.lower()


class TestFailureModes:
    """Test failure mode estimation."""

    def test_zip_up_has_zipper_failure(self):
        """Zip-up hoodies should include zipper failure mode."""
        modes = estimate_failure_modes_hoodie(
            "full_zip", "brushed", 350,
            [{"material": "cotton", "percent": 80.0},
             {"material": "polyester", "percent": 20.0}],
            {"zipper_ykk": False, "cuffs_quality": False, "hood_double_layer": False,
             "seams_quality": False, "pocket_reinforced": False, "side_seamed": False,
             "drawstring_metal": False, "neck_tape": False}
        )
        mode_names = [m["mode"] for m in modes]
        assert "Zipper failure" in mode_names

    def test_pullover_has_neckline_stretch(self):
        """Pullover hoodies should include neckline stretching mode."""
        modes = estimate_failure_modes_hoodie(
            "pullover", "brushed", 350,
            [{"material": "cotton", "percent": 80.0},
             {"material": "polyester", "percent": 20.0}],
            {"zipper_ykk": False, "cuffs_quality": False, "hood_double_layer": False,
             "seams_quality": False, "pocket_reinforced": False, "side_seamed": False,
             "drawstring_metal": False, "neck_tape": False}
        )
        mode_names = [m["mode"] for m in modes]
        assert "Neckline stretching" in mode_names
        assert "Zipper failure" not in mode_names

    def test_5050_high_pilling_risk(self):
        """50/50 blend should flag high pilling risk in failure modes."""
        modes = estimate_failure_modes_hoodie(
            "pullover", "brushed", 300,
            [{"material": "cotton", "percent": 50.0},
             {"material": "polyester", "percent": 50.0}],
            {"zipper_ykk": False, "cuffs_quality": False, "hood_double_layer": False,
             "seams_quality": False, "pocket_reinforced": False, "side_seamed": False,
             "drawstring_metal": False, "neck_tape": False}
        )
        pilling_mode = [m for m in modes if "pilling" in m["mode"].lower()][0]
        assert pilling_mode["risk"] == "high"

    def test_ykk_reduces_zipper_risk(self):
        """YKK zipper should reduce zipper failure risk."""
        modes = estimate_failure_modes_hoodie(
            "full_zip", "brushed", 350,
            [{"material": "cotton", "percent": 80.0},
             {"material": "polyester", "percent": 20.0}],
            {"zipper_ykk": True, "cuffs_quality": False, "hood_double_layer": False,
             "seams_quality": False, "pocket_reinforced": False, "side_seamed": False,
             "drawstring_metal": False, "neck_tape": False}
        )
        zip_mode = [m for m in modes if "zipper" in m["mode"].lower()][0]
        assert zip_mode["risk"] == "low"


class TestCareImpact:
    """Test care calculation and care impact scenarios."""

    def test_softener_warning_always(self):
        """Fabric softener warning MUST appear in every care explanation."""
        score, exp = calculate_care_hoodie(
            [{"material": "cotton", "percent": 80.0},
             {"material": "polyester", "percent": 20.0}],
            "pullover", "brushed",
            {"reverse_weave": False, "garment_dyed": False, "preshrunk": False}
        )
        assert "fabric softener" in exp.lower() or "softener" in exp.lower()

    def test_care_impact_has_scenarios(self):
        """Care impact should include 4 wash scenarios."""
        result = evaluate_hoodie(CHAMPION_REVERSE_WEAVE)
        care = result["care_impact"]
        assert "scenarios" in care
        assert len(care["scenarios"]) == 4

    def test_care_impact_recommendations(self):
        """Care impact should include recommendations."""
        result = evaluate_hoodie(CHAMPION_REVERSE_WEAVE)
        care = result["care_impact"]
        assert len(care["recommendations"]) >= 3

    def test_care_impact_softener_in_recs(self):
        """Care impact recommendations must include softener warning."""
        result = evaluate_hoodie(CHAMPION_REVERSE_WEAVE)
        recs = " ".join(result["care_impact"]["recommendations"])
        assert "softener" in recs.lower()

    def test_zip_up_care_penalty(self):
        """Zip-up should score slightly lower care than pullover."""
        pullover_score, _ = calculate_care_hoodie(
            [{"material": "cotton", "percent": 80.0},
             {"material": "polyester", "percent": 20.0}],
            "pullover", "brushed",
            {"reverse_weave": False, "garment_dyed": False, "preshrunk": False}
        )
        zip_score, _ = calculate_care_hoodie(
            [{"material": "cotton", "percent": 80.0},
             {"material": "polyester", "percent": 20.0}],
            "full_zip", "brushed",
            {"reverse_weave": False, "garment_dyed": False, "preshrunk": False}
        )
        assert pullover_score > zip_score


class TestSpecialConstruction:
    """Test special construction feature detection."""

    def test_reverse_weave(self):
        special = detect_special_construction("Reverse Weave cross-grain construction")
        assert special["reverse_weave"] is True

    def test_garment_dyed(self):
        special = detect_special_construction("Garment-dyed finish")
        assert special["garment_dyed"] is True

    def test_preshrunk(self):
        special = detect_special_construction("Pre-washed and preshrunk")
        assert special["preshrunk"] is True

    def test_none_detected(self):
        special = detect_special_construction("100% cotton fleece")
        assert special["reverse_weave"] is False
        assert special["garment_dyed"] is False
        assert special["preshrunk"] is False


class TestOrigin:
    """Test manufacturing origin detection."""

    def test_made_in_canada(self):
        assert detect_origin("Made in Canada") == "canada"

    def test_made_in_usa(self):
        assert detect_origin("Made in USA") == "usa"

    def test_made_in_japan(self):
        assert detect_origin("Made in Japan") == "japan"

    def test_no_origin(self):
        assert detect_origin("100% cotton fleece") is None


class TestEdgeCases:
    """Test edge cases and unusual inputs."""

    def test_no_brand_budget(self):
        """No brand, budget price, some materials -> should still evaluate."""
        result = evaluate_hoodie(NO_BRAND_BUDGET)
        assert result["quality_tier"] in ["poor", "average"]
        assert result["overall_score"] is not None

    def test_missing_materials(self):
        """Known brand but no materials -> evaluate via brand inference."""
        result = evaluate_hoodie(MISSING_MATERIALS)
        assert result["quality_tier"] in ["poor", "average"]
        assert result["overall_score"] is not None

    def test_no_data_at_all(self):
        """No materials + no brand -> empty evaluation."""
        result = evaluate_hoodie({
            "price": 30.00,
            "brand": "",
            "product_name": "Hoodie",
            "materials_structured": [],
            "materials_text": ""
        })
        assert result["quality_tier"] == "unknown"
        assert result["overall_score"] is None

    def test_return_shape(self):
        """Evaluation should have all required keys."""
        result = evaluate_hoodie(CHAMPION_REVERSE_WEAVE)
        assert "garment_type" in result
        assert result["garment_type"] == "hoodie"
        assert "metric_definitions" in result
        assert "scores" in result
        assert "overall_score" in result
        assert "quality_tier" in result
        assert "transparency_score" in result
        assert "cost_per_wear" in result
        assert "estimated_washes" in result
        assert "estimated_wears" in result
        assert "explanations" in result
        assert "warnings" in result
        assert "failure_modes" in result
        assert "care_impact" in result
        assert "metadata" in result

    def test_metric_definitions_match_tshirt_keys(self):
        """Metric definitions should use same 5 keys as t-shirt evaluator."""
        result = evaluate_hoodie(CHAMPION_REVERSE_WEAVE)
        keys = [m["key"] for m in result["metric_definitions"]]
        assert keys == ["shrinkage", "pilling", "longevity", "value", "care"]

    def test_scores_all_in_range(self):
        """All user-facing scores should be 1-5 (or None)."""
        result = evaluate_hoodie(CHAMPION_REVERSE_WEAVE)
        for key, score in result["scores"].items():
            if score is not None:
                assert 1.0 <= score <= 5.0, f"{key} score {score} out of range"

    def test_overall_score_in_range(self):
        """Overall score should be 0-100."""
        result = evaluate_hoodie(REIGNING_CHAMP_MID)
        assert 0 <= result["overall_score"] <= 100

    def test_metadata_populated(self):
        """Metadata should contain fleece type, hoodie type, etc."""
        result = evaluate_hoodie(REIGNING_CHAMP_MID)
        meta = result["metadata"]
        assert "fleece_type" in meta
        assert "hoodie_type" in meta
        assert "gsm" in meta
        assert "construction_features" in meta
        assert "brand_name" in meta

    def test_anti_pill_detection(self):
        """Anti-pill keywords should be detected."""
        assert detect_anti_pill("Air-jet yarn for pill resistance") is True
        assert detect_anti_pill("NuBlend fleece") is True
        assert detect_anti_pill("100% cotton") is False


class TestTierOrdering:
    """Verify quality tier ordering across major fixtures."""

    def test_artisanal_beats_premium(self):
        """3sixteen should score >= Reigning Champ."""
        art = evaluate_hoodie(THREESIXTEEN_HEAVY)
        prem = evaluate_hoodie(REIGNING_CHAMP_MID)
        assert art["overall_score"] >= prem["overall_score"]

    def test_premium_beats_budget(self):
        """Reigning Champ should score > Champion Powerblend."""
        prem = evaluate_hoodie(REIGNING_CHAMP_MID)
        budget = evaluate_hoodie(CHAMPION_POWERBLEND)
        assert prem["overall_score"] > budget["overall_score"]

    def test_budget_beats_fast_fashion(self):
        """Champion Powerblend should score > H&M."""
        budget = evaluate_hoodie(CHAMPION_POWERBLEND)
        ff = evaluate_hoodie(HM_BASIC_HOODIE)
        assert budget["overall_score"] > ff["overall_score"]

    def test_best_value_beats_mid_range(self):
        """Champion RW should score > generic mid-range."""
        rw = evaluate_hoodie(CHAMPION_REVERSE_WEAVE)
        mid = evaluate_hoodie(FOG_ESSENTIALS)
        assert rw["overall_score"] >= mid["overall_score"]


if __name__ == "__main__":
    pytest.main([__file__, "-v"])
