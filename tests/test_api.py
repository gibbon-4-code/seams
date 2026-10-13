"""
End-to-end tests for the FastAPI backend (extract -> detect -> evaluate).
Uses FastAPI's TestClient, so no server or network is needed.
"""

import pytest
from fastapi.testclient import TestClient

from api.server import app


client = TestClient(app)


def product_page(name, material=None, description=None, price="30.00"):
    """Build a minimal product page with schema.org JSON-LD."""
    fields = [f'"@type": "Product"', f'"name": "{name}"',
              '"brand": {"@type": "Brand", "name": "Example Basics"}',
              f'"offers": {{"@type": "Offer", "price": "{price}", "priceCurrency": "USD"}}']
    if material:
        fields.append(f'"material": "{material}"')
    if description:
        fields.append(f'"description": "{description}"')
    return f"""<html><head><script type="application/ld+json">
    {{"@context": "https://schema.org", {", ".join(fields)}}}
    </script></head><body><h1>{name}</h1></body></html>"""


def evaluate(html):
    response = client.post("/api/evaluate", json={"html": html, "url": "https://shop.example.com/p/1"})
    assert response.status_code == 200
    return response.json()


def test_health():
    assert client.get("/health").json() == {"status": "ok"}


def test_page_without_materials_does_not_error():
    """Regression: a missing materials_text used to crash the request."""
    data = evaluate(product_page("Classic Crew T-Shirt"))
    assert data["error"] is None
    assert data["extraction"]["product_name"] == "Classic Crew T-Shirt"
    assert data["evaluation"]["quality_tier"] is not None


def test_tshirt_full_pipeline():
    data = evaluate(product_page(
        "Heavyweight Crew T-Shirt",
        material="100% Cotton",
        description="Combed and ring-spun cotton, 200 GSM, side-seamed, preshrunk.",
    ))
    assert data["error"] is None
    assert data["extraction"]["garment_type"] == "tshirt"
    assert data["extraction"]["materials_structured"][0]["material"] == "cotton"
    assert set(data["evaluation"]["scores"]) >= {"longevity", "shrinkage", "pilling", "value", "care"}


@pytest.mark.parametrize("name,expected", [
    ("Slim Fit Selvedge Jeans", "jeans"),
    ("Heavyweight Pullover Hoodie", "hoodie"),
])
def test_routes_to_correct_evaluator(name, expected):
    data = evaluate(product_page(name, material="100% Cotton"))
    assert data["error"] is None
    assert data["extraction"]["garment_type"] == expected
    assert data["evaluation"]["garment_type"] == expected
