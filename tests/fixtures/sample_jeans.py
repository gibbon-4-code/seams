"""
Jeans/Denim test fixtures for quality evaluation tests.

Covers: heritage raw, mid-range, fast fashion, value outliers,
edge cases, and the 3 worked examples from the spec.
"""

# --- Heritage / Premium ---

HERITAGE_RAW_SELVAGE = {
    "price": 350.00,
    "brand": "Iron Heart",
    "product_name": "Iron Heart IH-888S 21oz Selvage Denim - Relaxed Tapered",
    "materials_structured": [{"material": "cotton", "percent": 100.0}],
    "materials_text": "100% Cotton. 21oz selvage denim. Unsanforized. Chain stitch hem. "
                      "Copper rivets. Bar tacked at all stress points. Button fly. Made in Japan."
}

PURE_BLUE_JAPAN = {
    "price": 295.00,
    "brand": "Pure Blue Japan",
    "product_name": "Pure Blue Japan XX-019 14oz Relaxed Tapered",
    "materials_structured": [{"material": "cotton", "percent": 100.0}],
    "materials_text": "100% cotton. 14oz slubby selvedge denim. One wash. "
                      "Chain stitch hem. Hidden copper rivets. Made in Japan."
}

THREE_SIXTEEN = {
    "price": 265.00,
    "brand": "3sixteen",
    "product_name": "3sixteen ST-100x Slim Tapered - 14.5oz",
    "materials_structured": [{"material": "cotton", "percent": 100.0}],
    "materials_text": "100% cotton. 14.5oz Kuroki selvedge denim. Raw/rigid. "
                      "Chain stitch hem by Union Special. YKK zipper. Made in USA."
}

# --- Heritage-Premium ---

NUDIE_LEAN_DEAN = {
    "price": 180.00,
    "brand": "Nudie Jeans",
    "product_name": "Nudie Jeans Lean Dean Dry 16 Dips Selvage",
    "materials_structured": [{"material": "cotton", "percent": 100.0}],
    "materials_text": "100% organic cotton. 13.75oz Kaihara selvedge denim. Raw. "
                      "Chain stitch hem. Free lifetime repairs."
}

NAKED_AND_FAMOUS = {
    "price": 168.00,
    "brand": "Naked & Famous",
    "product_name": "Naked & Famous Super Guy - Elephant 8 Supima Soft Selvedge",
    "materials_structured": [{"material": "cotton", "percent": 100.0}],
    "materials_text": "100% Supima cotton. 14oz selvedge denim. Button fly. Made in Canada."
}

# --- Mid-Range ---

MID_RANGE_LEVIS_511 = {
    "price": 69.50,
    "brand": "Levi's",
    "product_name": "Levi's 511 Slim Fit Men's Jeans",
    "materials_structured": [
        {"material": "cotton", "percent": 99.0},
        {"material": "spandex", "percent": 1.0}
    ],
    "materials_text": "99% Cotton, 1% Elastane. Slim fit. Mid rise. Zip fly."
}

LEVIS_501_ORIGINAL = {
    "price": 59.50,
    "brand": "Levi's",
    "product_name": "Levi's 501 Original Fit Men's Jeans - Rigid STF",
    "materials_structured": [{"material": "cotton", "percent": 100.0}],
    "materials_text": "100% cotton. Shrink-To-Fit. Straight leg. Button fly."
}

LEVIS_MADE_CRAFTED = {
    "price": 198.00,
    "brand": "Levi's Made & Crafted",
    "product_name": "Levi's Made & Crafted 502 Taper Selvedge",
    "materials_structured": [{"material": "cotton", "percent": 100.0}],
    "materials_text": "100% cotton. 14oz Japanese selvedge denim. One wash. Tapered fit."
}

BUCK_MASON = {
    "price": 128.00,
    "brand": "Buck Mason",
    "product_name": "Buck Mason Ford Standard Jean",
    "materials_structured": [{"material": "cotton", "percent": 100.0}],
    "materials_text": "100% cotton. 13.25oz Kaihara denim. Straight fit. "
                      "Chain stitch hem. Copper rivets."
}

# --- Value Outliers ---

UNIQLO_KAIHARA_SELVEDGE = {
    "price": 49.90,
    "brand": "Uniqlo",
    "product_name": "Uniqlo Selvedge Slim Fit Jeans",
    "materials_structured": [{"material": "cotton", "percent": 100.0}],
    "materials_text": "100% cotton. Kaihara denim. Selvedge. Slim fit. Regular rise."
}

WRANGLER_COWBOY_CUT = {
    "price": 24.99,
    "brand": "Wrangler",
    "product_name": "Wrangler Cowboy Cut Original Fit Jean",
    "materials_structured": [{"material": "cotton", "percent": 100.0}],
    "materials_text": "100% cotton. 14oz denim. Regular fit. High rise. Straight leg."
}

TARGET_GOODFELLOW_SELVEDGE = {
    "price": 34.99,
    "brand": "Goodfellow & Co",
    "product_name": "Goodfellow & Co Slim Fit Selvedge Jeans",
    "materials_structured": [{"material": "cotton", "percent": 100.0}],
    "materials_text": "100% cotton. 14oz selvedge denim. Slim fit."
}

# --- Fast Fashion ---

FAST_FASHION_SKINNY = {
    "price": 25.00,
    "brand": "ASOS",
    "product_name": "ASOS DESIGN skinny jeans in mid wash with heavy distressing",
    "materials_structured": [
        {"material": "cotton", "percent": 85.0},
        {"material": "polyester", "percent": 13.0},
        {"material": "spandex", "percent": 2.0}
    ],
    "materials_text": "85% Cotton, 13% Polyester, 2% Elastane. Skinny fit. "
                      "Low rise. Distressed. Zip fly."
}

HM_SKINNY = {
    "price": 19.99,
    "brand": "H&M",
    "product_name": "H&M Skinny Jeans",
    "materials_structured": [
        {"material": "cotton", "percent": 86.0},
        {"material": "polyester", "percent": 12.0},
        {"material": "spandex", "percent": 2.0}
    ],
    "materials_text": "86% Cotton, 12% Polyester, 2% Elastane."
}

SHEIN_BUDGET = {
    "price": 15.00,
    "brand": "SHEIN",
    "product_name": "SHEIN High Waist Skinny Jeans",
    "materials_structured": [
        {"material": "cotton", "percent": 72.0},
        {"material": "polyester", "percent": 25.0},
        {"material": "spandex", "percent": 3.0}
    ],
    "materials_text": "72% Cotton, 25% Polyester, 3% Spandex. Skinny. High rise."
}

ZARA_SLIM = {
    "price": 39.90,
    "brand": "Zara",
    "product_name": "Zara Slim Fit Jeans",
    "materials_structured": [
        {"material": "cotton", "percent": 92.0},
        {"material": "polyester", "percent": 6.0},
        {"material": "spandex", "percent": 2.0}
    ],
    "materials_text": "92% Cotton, 6% Polyester, 2% Elastane. Slim fit."
}

# --- Fashion-Premium (stretch/comfort focus) ---

HIGH_STRETCH_FASHION = {
    "price": 228.00,
    "brand": "AG",
    "product_name": "AG The Tellis Modern Slim Jean",
    "materials_structured": [
        {"material": "cotton", "percent": 55.0},
        {"material": "modal", "percent": 22.0},
        {"material": "polyester", "percent": 20.0},
        {"material": "spandex", "percent": 3.0}
    ],
    "materials_text": "55% Cotton, 22% Modal, 20% Polyester, 3% Elastane. Slim fit."
}

CITIZENS_HUMANITY = {
    "price": 218.00,
    "brand": "Citizens of Humanity",
    "product_name": "Citizens of Humanity Gage Straight Leg Jean",
    "materials_structured": [
        {"material": "cotton", "percent": 98.0},
        {"material": "spandex", "percent": 2.0}
    ],
    "materials_text": "98% Cotton, 2% Elastane. Straight leg. Mid rise."
}

# --- Women's ---

WOMENS_SKINNY = {
    "price": 89.00,
    "brand": "Madewell",
    "product_name": "Madewell 10\" High-Rise Skinny Jeans in Women's Pure White",
    "materials_structured": [
        {"material": "cotton", "percent": 93.0},
        {"material": "polyester", "percent": 5.0},
        {"material": "spandex", "percent": 2.0}
    ],
    "materials_text": "93% Cotton, 5% Polyester, 2% Elastane. Skinny fit. High rise."
}

# --- Worked Examples from Spec ---

SPEC_RICH_UNKNOWN_BRAND = {
    "price": 79.00,
    "brand": "",
    "product_name": "Straight Leg Jeans - Indigo",
    "materials_structured": [
        {"material": "cotton", "percent": 98.0},
        {"material": "spandex", "percent": 2.0}
    ],
    "materials_text": "98% cotton, 2% elastane, 13oz denim"
}

BRAND_ONLY_NUDIE = {
    "price": 120.00,
    "brand": "Nudie Jeans",
    "product_name": "Nudie Jeans Gritty Jackson",
    "materials_structured": [],
    "materials_text": ""
}

SHEIN_SURPRISE_COTTON = {
    "price": 18.00,
    "brand": "SHEIN",
    "product_name": "SHEIN Straight Leg Jeans",
    "materials_structured": [{"material": "cotton", "percent": 100.0}],
    "materials_text": "100% Cotton"
}

# --- Edge Cases ---

OUTLET_JEANS = {
    "price": 49.99,
    "brand": "Levi's",
    "product_name": "Levi's 511 Slim Fit Jeans",
    "materials_structured": [
        {"material": "cotton", "percent": 79.0},
        {"material": "polyester", "percent": 18.0},
        {"material": "spandex", "percent": 3.0}
    ],
    "materials_text": "79% Cotton, 18% Polyester, 3% Elastane. Nordstrom Rack.",
    "retailer": "Nordstrom Rack"
}

NO_BRAND_NO_WEIGHT = {
    "price": 45.00,
    "brand": "",
    "product_name": "Slim Fit Jeans - Dark Blue",
    "materials_structured": [
        {"material": "cotton", "percent": 98.0},
        {"material": "spandex", "percent": 2.0}
    ],
    "materials_text": "98% Cotton, 2% Elastane"
}

RAW_UNSANFORIZED = {
    "price": 220.00,
    "brand": "Samurai Jeans",
    "product_name": "Samurai Jeans S510XX 19oz Unsanforized Denim",
    "materials_structured": [{"material": "cotton", "percent": 100.0}],
    "materials_text": "100% cotton. 19oz unsanforized denim. Chain stitch. "
                      "Copper rivets. Button fly. Made in Japan."
}

MISSING_MATERIALS = {
    "price": 60.00,
    "brand": "Gap",
    "product_name": "Gap '90s Original Straight Jeans",
    "materials_structured": [],
    "materials_text": ""
}
