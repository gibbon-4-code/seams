"""
FastAPI backend for Seams browser extension.

Wraps existing extraction + evaluation tools to provide a REST API
that the Chrome extension can call for real-time product evaluation.
"""

import logging
import sys
from pathlib import Path

# Add parent directory to path so we can import tools
sys.path.insert(0, str(Path(__file__).parent.parent))

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

from tools.product_extractor import extract_product
from tools.garment_detector import detect_garment_type
from tools.tshirt_evaluator import evaluate_tshirt
from tools.jeans_evaluator import evaluate_jeans
from tools.hoodie_evaluator import evaluate_hoodie

logger = logging.getLogger("seams.api")

app = FastAPI(
    title="Seams API",
    description="Clothing quality evaluation API (t-shirts, jeans, and hoodies)",
    version="0.1.0"
)

# CORS for browser extension
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # In production, restrict to specific extension ID
    allow_methods=["POST", "GET"],
    allow_headers=["*"],
)


class EvaluationRequest(BaseModel):
    html: str
    url: str


class EvaluationResponse(BaseModel):
    extraction: dict
    evaluation: dict
    error: Optional[str] = None


@app.get("/")
async def root():
    """Root endpoint with API info."""
    return {
        "name": "Seams API",
        "version": "0.1.0",
        "status": "running",
        "endpoints": {
            "health": "/health",
            "evaluate": "/api/evaluate (POST)"
        }
    }


@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {"status": "ok"}


@app.post("/api/evaluate", response_model=EvaluationResponse)
async def evaluate_product(request: EvaluationRequest):
    """
    Extract and evaluate product from HTML.

    Args:
        request: EvaluationRequest with html and url

    Returns:
        EvaluationResponse with extraction + evaluation data
    """
    try:
        # 1. Extract product data from HTML
        extraction_result = extract_product(request.html, request.url)

        # 2. Prepare data for evaluator (ensure all types are correct)
        evaluator_input = {
            "materials_structured": [],
            "materials_text": extraction_result.get("materials_text") or "",
            "price": None
        }

        # Convert price dict to float
        if extraction_result.get("price"):
            if isinstance(extraction_result["price"], dict):
                price_val = extraction_result["price"].get("amount")
                evaluator_input["price"] = float(price_val) if price_val is not None else None
            else:
                evaluator_input["price"] = float(extraction_result["price"])

        # Ensure materials_structured has proper format
        for material in extraction_result.get("materials_structured", []):
            material_item = {
                "material": str(material.get("material", "")),
                "percent": float(material.get("percent", 0)) if material.get("percent") is not None else None,
                "part": str(material.get("part", "unknown"))
            }
            evaluator_input["materials_structured"].append(material_item)

        # 3. Detect garment type
        product_name = extraction_result.get("product_name") or ""
        brand = extraction_result.get("brand") or ""
        materials_text = extraction_result.get("materials_text") or ""
        garment_info = detect_garment_type(product_name, materials_text, brand)
        logger.info("%s -> %s (%s)", request.url, garment_info["garment_type"], garment_info["confidence"])

        # 4. Route to correct evaluator
        if garment_info["garment_type"] == "jeans":
            evaluator_input["brand"] = brand
            evaluator_input["product_name"] = product_name
            evaluation_result = evaluate_jeans(evaluator_input)
        elif garment_info["garment_type"] == "hoodie":
            evaluator_input["brand"] = brand
            evaluator_input["product_name"] = product_name
            evaluation_result = evaluate_hoodie(evaluator_input)
        else:
            evaluation_result = evaluate_tshirt(evaluator_input)

        # 5. Prepare extraction metadata for frontend
        extraction_data = {
            "product_name": product_name,
            "brand": brand,
            "price": extraction_result.get("price"),
            "images": extraction_result.get("images", []),
            "materials_text": materials_text,
            "materials_structured": extraction_result.get("materials_structured", []),
            "confidence": extraction_result.get("extraction", {}).get("confidence"),
            "method": extraction_result.get("extraction", {}).get("method"),
            "garment_type": garment_info["garment_type"],
            "garment_confidence": garment_info["confidence"]
        }

        return EvaluationResponse(
            extraction=extraction_data,
            evaluation=evaluation_result
        )

    except Exception as e:
        logger.exception("Evaluation failed for %s", request.url)

        # Return partial response with error
        return EvaluationResponse(
            extraction={},
            evaluation={},
            error=f"Evaluation failed: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    logging.basicConfig(level=logging.INFO)
    uvicorn.run(app, host="127.0.0.1", port=8000, log_level="info")
