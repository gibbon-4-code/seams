"""
Hoodie test fixtures for quality evaluation tests.

Covers: artisanal, premium, best-value, mid-range, budget, fast fashion,
sub-line differentiation, edge cases, and the 3 worked examples from the spec.
"""

# --- Artisanal (S tier) ---

THREESIXTEEN_HEAVY = {
    "price": 275.00,
    "brand": "3sixteen",
    "product_name": "3sixteen Heavyweight Hoodie - Black",
    "materials_structured": [{"material": "cotton", "percent": 100.0}],
    "materials_text": "100% Cotton. 500 GSM heavyweight fleece. Double-layer hood. "
                      "YKK double zipper. Flatlock seams. 2x2 rib cuffs with elastane. "
                      "Side-seamed. Metal aglets. Made in Canada."
}

LADY_WHITE_SUPER = {
    "price": 295.00,
    "brand": "Lady White Co",
    "product_name": "Lady White Co Super Weighted Hoodie",
    "materials_structured": [{"material": "cotton", "percent": 100.0}],
    "materials_text": "100% cotton. 610 GSM super heavyweight fleece. Garment-dyed. "
                      "Flatlock seams. Double-layer hood. 2x2 rib cuffs with elastane. "
                      "Side-seamed. Made in USA."
}

# --- Premium (A tier) ---

REIGNING_CHAMP_MID = {
    "price": 135.00,
    "brand": "Reigning Champ",
    "product_name": "Reigning Champ Midweight Terry Hoodie",
    "materials_structured": [{"material": "cotton", "percent": 100.0}],
    "materials_text": "100% cotton. French terry. 390 GSM. Flatlock seams. "
                      "YKK zipper. Double-layer hood. 2x2 rib cuffs with elastane. "
                      "Side-seamed. Made in Canada."
}

REIGNING_CHAMP_HEAVY = {
    "price": 160.00,
    "brand": "Reigning Champ",
    "product_name": "Reigning Champ Heavyweight Fleece Hoodie",
    "materials_structured": [{"material": "cotton", "percent": 100.0}],
    "materials_text": "100% cotton. Heavyweight brushed fleece. 420 GSM. "
                      "Flatlock seams. YKK zipper. Double-layer hood. "
                      "2x2 rib cuffs with elastane. Side-seamed. Made in Canada."
}

# --- Best Value (B+ tier) ---

CHAMPION_REVERSE_WEAVE = {
    "price": 68.00,
    "brand": "Champion",
    "product_name": "Champion Reverse Weave Hoodie",
    "materials_structured": [
        {"material": "cotton", "percent": 82.0},
        {"material": "polyester", "percent": 18.0}
    ],
    "materials_text": "82% Cotton, 18% Polyester. Reverse Weave cross-grain construction. "
                      "12oz (407 GSM). Double-layer hood. 2x2 rib cuffs with spandex. "
                      "Side-seamed. Metal grommets."
}

LA_APPAREL_HF09 = {
    "price": 78.00,
    "brand": "Los Angeles Apparel",
    "product_name": "Los Angeles Apparel HF09 14oz Heavy Fleece Hoodie",
    "materials_structured": [{"material": "cotton", "percent": 100.0}],
    "materials_text": "100% cotton. 14oz (475 GSM) heavy fleece. Pre-washed. "
                      "Double-layer hood. Rib cuffs with elastane. Side-seamed. "
                      "Made in USA."
}

CARHARTT_MIDWEIGHT = {
    "price": 64.99,
    "brand": "Carhartt",
    "product_name": "Carhartt K121 Midweight Hooded Sweatshirt",
    "materials_structured": [
        {"material": "cotton", "percent": 50.0},
        {"material": "polyester", "percent": 50.0}
    ],
    "materials_text": "50% Cotton, 50% Polyester. Midweight 10.5oz (356 GSM). "
                      "Brushed fleece. Triple-stitched seams. Double-layer hood. "
                      "Rib cuffs with spandex. Side-seamed."
}

# --- Mid-range (B tier) ---

NIKE_TECH_FLEECE = {
    "price": 110.00,
    "brand": "Nike",
    "product_name": "Nike Sportswear Tech Fleece Full-Zip Hoodie",
    "materials_structured": [
        {"material": "cotton", "percent": 64.0},
        {"material": "polyester", "percent": 36.0}
    ],
    "materials_text": "64% Cotton, 36% Polyester. Tech Fleece spacer construction. "
                      "Full-zip. Engineered hood."
}

FOG_ESSENTIALS = {
    "price": 90.00,
    "brand": "Fear of God Essentials",
    "product_name": "Fear of God Essentials Pullover Hoodie",
    "materials_structured": [
        {"material": "cotton", "percent": 80.0},
        {"material": "polyester", "percent": 20.0}
    ],
    "materials_text": "80% Cotton, 20% Polyester. 420 GSM. Double-layer hood. "
                      "Rib cuffs. Side-seamed."
}

# --- Budget / Mall (C tier) ---

CHAMPION_POWERBLEND = {
    "price": 35.00,
    "brand": "Champion",
    "product_name": "Champion Powerblend Hoodie",
    "materials_structured": [
        {"material": "cotton", "percent": 50.0},
        {"material": "polyester", "percent": 50.0}
    ],
    "materials_text": "50% Cotton, 50% Polyester. Powerblend fleece. "
                      "Double-layer hood. 1x1 rib cuffs."
}

NIKE_CLUB_FLEECE = {
    "price": 60.00,
    "brand": "Nike",
    "product_name": "Nike Sportswear Club Fleece Pullover Hoodie",
    "materials_structured": [
        {"material": "cotton", "percent": 80.0},
        {"material": "polyester", "percent": 20.0}
    ],
    "materials_text": "80% Cotton, 20% Polyester. Brushed fleece. "
                      "Double-layer hood. Rib cuffs. Side-seamed."
}

UNIQLO_HOODIE = {
    "price": 39.90,
    "brand": "Uniqlo",
    "product_name": "Uniqlo Sweat Pullover Hoodie",
    "materials_structured": [{"material": "cotton", "percent": 100.0}],
    "materials_text": "100% cotton. French terry. Side-seamed."
}

# --- Entry Budget (D tier) ---

GILDAN_HEAVY_BLEND = {
    "price": 18.00,
    "brand": "Gildan",
    "product_name": "Gildan Heavy Blend Hooded Sweatshirt",
    "materials_structured": [
        {"material": "cotton", "percent": 50.0},
        {"material": "polyester", "percent": 50.0}
    ],
    "materials_text": "50% Cotton, 50% Polyester. 8oz (271 GSM). "
                      "Air-jet yarn for pill resistance. 1x1 rib cuffs."
}

HANES_ECOSMART = {
    "price": 15.00,
    "brand": "Hanes",
    "product_name": "Hanes EcoSmart Hoodie",
    "materials_structured": [
        {"material": "cotton", "percent": 50.0},
        {"material": "polyester", "percent": 50.0}
    ],
    "materials_text": "50% Cotton, 50% Polyester. Fleece. 1x1 rib cuffs."
}

# --- Fast Fashion (F tier) ---

HM_BASIC_HOODIE = {
    "price": 24.99,
    "brand": "H&M",
    "product_name": "H&M Oversized Hoodie",
    "materials_structured": [],
    "materials_text": "cotton/polyester"
}

SHEIN_HOODIE = {
    "price": 18.00,
    "brand": "SHEIN",
    "product_name": "SHEIN Oversized Drawstring Hoodie",
    "materials_structured": [
        {"material": "polyester", "percent": 65.0},
        {"material": "cotton", "percent": 35.0}
    ],
    "materials_text": "65% Polyester, 35% Cotton."
}

# --- Worked Examples from Spec ---

SPEC_CHAMPION_SPARSE = {
    "price": 34.99,
    "brand": "Champion",
    "product_name": "Men's Hoodie",
    "materials_structured": [
        {"material": "cotton", "percent": 80.0},
        {"material": "polyester", "percent": 20.0}
    ],
    "materials_text": "80% cotton, 20% polyester"
}

SPEC_BRAND_ONLY_RC = {
    "price": 135.00,
    "brand": "Reigning Champ",
    "product_name": "Hoodie",
    "materials_structured": [],
    "materials_text": ""
}

SPEC_HM_FAST_FASHION = {
    "price": 24.99,
    "brand": "H&M",
    "product_name": "Oversized Hoodie",
    "materials_structured": [],
    "materials_text": "cotton/polyester"
}

# --- Edge Cases ---

ZIP_UP_COTTON = {
    "price": 55.00,
    "brand": "",
    "product_name": "Full-Zip Hoodie - Black",
    "materials_structured": [{"material": "cotton", "percent": 100.0}],
    "materials_text": "100% Cotton. Full-zip. Zip fly."
}

FRENCH_TERRY_UNIQLO = {
    "price": 39.90,
    "brand": "Uniqlo",
    "product_name": "Uniqlo French Terry Pullover Hoodie",
    "materials_structured": [{"material": "cotton", "percent": 100.0}],
    "materials_text": "100% cotton. French terry interior. Side-seamed."
}

GENERIC_CHAMPION = {
    "price": 45.00,
    "brand": "Champion",
    "product_name": "Champion Hoodie",
    "materials_structured": [
        {"material": "cotton", "percent": 80.0},
        {"material": "polyester", "percent": 20.0}
    ],
    "materials_text": "80% Cotton, 20% Polyester."
}

NO_BRAND_BUDGET = {
    "price": 25.00,
    "brand": "",
    "product_name": "Pullover Hoodie",
    "materials_structured": [
        {"material": "cotton", "percent": 60.0},
        {"material": "polyester", "percent": 40.0}
    ],
    "materials_text": "60% Cotton, 40% Polyester"
}

MISSING_MATERIALS = {
    "price": 55.00,
    "brand": "Gap",
    "product_name": "Gap Vintage Soft Hoodie",
    "materials_structured": [],
    "materials_text": ""
}

REVERSE_WEAVE_ZIP = {
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

CARHARTT_HEAVYWEIGHT = {
    "price": 79.99,
    "brand": "Carhartt",
    "product_name": "Carhartt K185 Heavyweight Hooded Sweatshirt",
    "materials_structured": [
        {"material": "cotton", "percent": 50.0},
        {"material": "polyester", "percent": 50.0}
    ],
    "materials_text": "50% Cotton, 50% Polyester. Heavyweight 13oz. "
                      "Brushed fleece. Triple-stitched seams. Double-layer hood. "
                      "Rain Defender water-repellent. Side-seamed."
}
