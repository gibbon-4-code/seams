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

from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel
from typing import Optional

from tools.pipeline import evaluate_html

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
        result = evaluate_html(request.html, request.url)
        logger.info("%s -> %s (%s)", request.url,
                    result["extraction"]["garment_type"], result["extraction"]["garment_confidence"])
        return EvaluationResponse(**result)

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
