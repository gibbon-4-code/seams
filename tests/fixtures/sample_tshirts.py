"""
Test fixtures for t-shirt evaluation tests.
Contains realistic product data for various quality tiers and edge cases.

Transparency Scoring Examples:
- PREMIUM_COMBED_RINGSPUN: Full transparency (10/10)
- MEDIUM_TRANSPARENCY: Good transparency (7/10)
- PARTIAL_TRANSPARENCY: Fair transparency (5/10)
- LOW_TRANSPARENCY_PREMIUM: Poor transparency (2/10)
"""

# Example 1: Budget Carded Cotton (Gildan G5000 style)
BUDGET_CARDED_COTTON = {
    "price": 8.50,
    "materials_structured": [{"material": "cotton", "percent": 100.0}],
    "materials_text": "100% Cotton. 5.3 oz/yd². Tubular construction."
}

# Example 2: Premium Combed Ring-Spun (Bella+Canvas 3001 style)
PREMIUM_COMBED_RINGSPUN = {
    "price": 28.00,
    "materials_structured": [{"material": "cotton", "percent": 100.0}],
    "materials_text": "100% Airlume combed and ring-spun cotton, 30 singles. 4.2 oz. Side-seamed. Double-needle stitching. Shoulder-to-shoulder taping."
}

# Example 3: Luxury Supima Cotton
LUXURY_SUPIMA = {
    "price": 45.00,
    "materials_structured": [{"material": "cotton", "percent": 100.0}],
    "materials_text": "100% Supima cotton. 180 GSM. Side-seamed. Garment-dyed."
}

# Example 4: The Dreaded 65/35 Blend (Pilling Red Flag)
BLEND_65_35_RED_FLAG = {
    "price": 18.00,
    "materials_structured": [
        {"material": "cotton", "percent": 65.0},
        {"material": "polyester", "percent": 35.0}
    ],
    "materials_text": "65% Cotton / 35% Polyester. 5.5 oz."
}

# Example 5: 50/50 Cotton-Poly Blend
BLEND_50_50 = {
    "price": 12.00,
    "materials_structured": [
        {"material": "cotton", "percent": 50.0},
        {"material": "polyester", "percent": 50.0}
    ],
    "materials_text": "50% Cotton / 50% Polyester. 5.0 oz. Preshrunk."
}

# Example 6: Tri-Blend (Soft Blend)
TRI_BLEND = {
    "price": 22.00,
    "materials_structured": [
        {"material": "polyester", "percent": 50.0},
        {"material": "cotton", "percent": 25.0},
        {"material": "rayon", "percent": 25.0}
    ],
    "materials_text": "50% Polyester / 25% Cotton / 25% Rayon. 3.8 oz. Side-seamed."
}

# Example 7: High GSM in Sweet Spot
HIGH_GSM_SWEET_SPOT = {
    "price": 32.00,
    "materials_structured": [{"material": "cotton", "percent": 100.0}],
    "materials_text": "100% Combed ring-spun cotton. 180 GSM. Side-seamed. Double-needle construction."
}

# Example 8: Ultra-Light GSM (Too Light)
ULTRA_LIGHT_GSM = {
    "price": 15.00,
    "materials_structured": [{"material": "cotton", "percent": 100.0}],
    "materials_text": "100% Cotton. 130 GSM. Tubular."
}

# Example 9: Side-Seamed Construction
SIDE_SEAMED_TEE = {
    "price": 25.00,
    "materials_structured": [{"material": "cotton", "percent": 100.0}],
    "materials_text": "100% Combed cotton. 4.5 oz. Side-seamed. Double-needle sleeves and hem."
}

# Example 10: Tubular Construction
TUBULAR_TEE = {
    "price": 10.00,
    "materials_structured": [{"material": "cotton", "percent": 100.0}],
    "materials_text": "100% Cotton. 5.0 oz. Tubular body."
}

# Example 11: Preshrunk Treatment
PRESHRUNK_TEE = {
    "price": 14.00,
    "materials_structured": [{"material": "cotton", "percent": 100.0}],
    "materials_text": "100% Cotton. 5.5 oz. Preshrunk. Tubular."
}

# Example 12: Garment-Dyed (Comfort Colors style)
GARMENT_DYED_TEE = {
    "price": 18.00,
    "materials_structured": [{"material": "cotton", "percent": 100.0}],
    "materials_text": "100% Ring-spun cotton. 6.1 oz. Garment-dyed. Tubular construction."
}

# Example 13: Singles Count Boost (30+ Singles)
HIGH_SINGLES_COUNT = {
    "price": 30.00,
    "materials_structured": [{"material": "cotton", "percent": 100.0}],
    "materials_text": "100% Combed and ring-spun cotton, 32 singles. 4.3 oz. Side-seamed. Double-needle."
}

# Example 14: Low Singles Count (Budget)
LOW_SINGLES_COUNT = {
    "price": 9.00,
    "materials_structured": [{"material": "cotton", "percent": 100.0}],
    "materials_text": "100% Cotton, 18 singles. 6.0 oz. Tubular."
}

# Example 15: Pima Cotton
PIMA_COTTON = {
    "price": 40.00,
    "materials_structured": [{"material": "cotton", "percent": 100.0}],
    "materials_text": "100% Pima cotton. 5.0 oz. Side-seamed. Double-needle construction."
}

# Example 16: Missing Materials Data (Edge Case)
MISSING_MATERIALS = {
    "price": 20.00,
    "materials_structured": [],
    "materials_text": ""
}

# Example 17: No Price Data (Edge Case)
NO_PRICE = {
    "materials_structured": [{"material": "cotton", "percent": 100.0}],
    "materials_text": "100% Combed cotton. 4.5 oz. Side-seamed."
}

# Example 18: Minimal Data (Only Composition)
MINIMAL_DATA = {
    "price": 15.00,
    "materials_structured": [{"material": "cotton", "percent": 100.0}],
    "materials_text": "100% Cotton"
}

# Example 19: Heavyweight Cotton (6+ oz)
HEAVYWEIGHT_COTTON = {
    "price": 16.00,
    "materials_structured": [{"material": "cotton", "percent": 100.0}],
    "materials_text": "100% Cotton. 6.5 oz/yd². Tubular."
}

# Example 20: Perfect Construction (All Features)
PERFECT_CONSTRUCTION = {
    "price": 35.00,
    "materials_structured": [{"material": "cotton", "percent": 100.0}],
    "materials_text": "100% Supima cotton, 30 singles. 180 GSM. Side-seamed. Double-needle sleeves and hem. Shoulder-to-shoulder taping. Garment-dyed."
}

# Example 21: Cost-Per-Wear Sweet Spot Validation (£28 tee from research)
RESEARCH_SWEET_SPOT = {
    "price": 28.00,
    "materials_structured": [{"material": "cotton", "percent": 100.0}],
    "materials_text": "100% Combed and ring-spun cotton. 4.5 oz. Side-seamed. Double-needle."
}

# Example 22: Overpriced Budget Quality (High price, low quality)
OVERPRICED_BUDGET = {
    "price": 60.00,
    "materials_structured": [{"material": "cotton", "percent": 100.0}],
    "materials_text": "100% Cotton. 5.0 oz. Tubular."
}

# Example 23: Excellent Value Budget (Low price, decent quality)
EXCELLENT_VALUE_BUDGET = {
    "price": 12.00,
    "materials_structured": [{"material": "cotton", "percent": 100.0}],
    "materials_text": "100% Ring-spun cotton. 5.0 oz. Side-seamed."
}

# Example 24: High Polyester (Not 65/35)
HIGH_POLYESTER = {
    "price": 16.00,
    "materials_structured": [
        {"material": "polyester", "percent": 80.0},
        {"material": "cotton", "percent": 20.0}
    ],
    "materials_text": "80% Polyester / 20% Cotton. 4.5 oz. Moisture-wicking."
}

# Example 25: Nearly 100% Cotton with Spandex
COTTON_WITH_SPANDEX = {
    "price": 24.00,
    "materials_structured": [
        {"material": "cotton", "percent": 95.0},
        {"material": "spandex", "percent": 5.0}
    ],
    "materials_text": "95% Combed cotton / 5% Spandex. 5.5 oz. Side-seamed. Stretch fit."
}

# Example 26: Low Transparency Premium Brand (AllSaints style)
LOW_TRANSPARENCY_PREMIUM = {
    "price": 59.00,
    "materials_structured": [{"material": "cotton", "percent": 100.0}],
    "materials_text": "100% Cotton"
}

# Example 27: Partial Transparency (Some specs but not all)
PARTIAL_TRANSPARENCY = {
    "price": 35.00,
    "materials_structured": [{"material": "cotton", "percent": 100.0}],
    "materials_text": "100% Combed ring-spun cotton. 4.5 oz."
}

# Example 28: Medium Transparency (Good but missing a few details)
MEDIUM_TRANSPARENCY = {
    "price": 32.00,
    "materials_structured": [{"material": "cotton", "percent": 100.0}],
    "materials_text": "100% Ring-spun cotton. 5.0 oz. Side-seamed. Preshrunk."
}
