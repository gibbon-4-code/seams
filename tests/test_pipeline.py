"""Tests for the shared evaluation pipeline (used by the API and web demo)."""

from tools.pipeline import evaluate_details, evaluate_extraction


def test_evaluate_details_routes_hoodie():
    result = evaluate_details("Heavyweight Pullover Hoodie", "80% cotton, 20% polyester. 400 GSM fleece.", 65.0)
    assert result["extraction"]["garment_type"] == "hoodie"
    assert result["extraction"]["method"] == "manual"
    assert result["evaluation"]["garment_type"] == "hoodie"


def test_evaluate_details_flags_65_35_blend():
    result = evaluate_details("Basic Crew Tee", "65% polyester, 35% cotton", 8.0)
    assert result["extraction"]["garment_type"] == "tshirt"
    assert result["evaluation"]["scores"]["pilling"] <= 2


def test_evaluate_details_without_materials_or_price():
    result = evaluate_details("Slim Fit Jeans", "", None)
    assert result["extraction"]["garment_type"] == "jeans"
    assert result["extraction"]["materials_structured"] == []


def test_evaluate_extraction_tolerates_missing_fields():
    result = evaluate_extraction({})
    assert result["extraction"]["product_name"] == ""
    assert "scores" in result["evaluation"]
