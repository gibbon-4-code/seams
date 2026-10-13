"""
Evaluation Pipeline - extraction result -> garment detection -> evaluator.

Shared by the API (api/server.py) and the in-browser web demo (web/),
so both produce identical results.
"""

from typing import Dict, Optional

from .product_extractor import extract_product
from .materials_parser import parse_materials
from .garment_detector import detect_garment_type
from .tshirt_evaluator import evaluate_tshirt
from .jeans_evaluator import evaluate_jeans
from .hoodie_evaluator import evaluate_hoodie


def evaluate_extraction(extraction_result: Dict) -> Dict:
    """
    Detect garment type and run the matching evaluator.

    Args:
        extraction_result: Output of extract_product (or an equivalent dict)

    Returns:
        {"extraction": {...summary for the UI...}, "evaluation": {...}}
    """
    product_name = extraction_result.get("product_name") or ""
    brand = extraction_result.get("brand") or ""
    materials_text = extraction_result.get("materials_text") or ""

    # Evaluators expect a float price and clean material entries
    price = extraction_result.get("price")
    if isinstance(price, dict):
        price = price.get("amount")
    price = float(price) if price is not None else None

    materials_structured = [
        {
            "material": str(m.get("material", "")),
            "percent": float(m["percent"]) if m.get("percent") is not None else None,
            "part": str(m.get("part", "unknown")),
        }
        for m in extraction_result.get("materials_structured") or []
    ]

    evaluator_input = {
        "materials_structured": materials_structured,
        "materials_text": materials_text,
        "price": price,
    }

    garment_info = detect_garment_type(product_name, materials_text, brand)

    if garment_info["garment_type"] == "jeans":
        evaluation = evaluate_jeans({**evaluator_input, "brand": brand, "product_name": product_name})
    elif garment_info["garment_type"] == "hoodie":
        evaluation = evaluate_hoodie({**evaluator_input, "brand": brand, "product_name": product_name})
    else:
        evaluation = evaluate_tshirt(evaluator_input)

    extraction_meta = extraction_result.get("extraction") or {}
    extraction = {
        "product_name": product_name,
        "brand": brand,
        "price": extraction_result.get("price"),
        "images": extraction_result.get("images") or [],
        "materials_text": materials_text,
        "materials_structured": extraction_result.get("materials_structured") or [],
        "confidence": extraction_meta.get("confidence"),
        "method": extraction_meta.get("method"),
        "notes": extraction_meta.get("notes") or [],
        "garment_type": garment_info["garment_type"],
        "garment_confidence": garment_info["confidence"],
    }

    return {"extraction": extraction, "evaluation": evaluation}


def evaluate_html(html: str, url: Optional[str] = None) -> Dict:
    """Extract product data from page HTML, then evaluate it."""
    return evaluate_extraction(extract_product(html, url))


def evaluate_details(
    product_name: str,
    materials_text: str,
    price: Optional[float] = None,
    currency: str = "USD",
    brand: str = "",
) -> Dict:
    """
    Evaluate a product from details typed in by hand (no page HTML).

    Args:
        product_name: e.g. "Heavyweight Pullover Hoodie" (used to detect garment type)
        materials_text: Composition and description, e.g. "80% cotton, 20% polyester, 400 GSM"
        price: Retail price, if known
        currency: Price currency code
        brand: Brand name, if known
    """
    structured, notes = parse_materials(materials_text) if materials_text else ([], [])
    return evaluate_extraction({
        "product_name": product_name,
        "brand": brand,
        "price": {"amount": price, "currency": currency} if price is not None else None,
        "materials_text": materials_text,
        "materials_structured": structured,
        "extraction": {"method": "manual", "confidence": None, "notes": notes},
    })
