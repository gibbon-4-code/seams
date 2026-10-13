"""
Hoodie Quality Evaluation Engine

Evaluates hoodie quality using research-backed metrics including:
- Fabric composition (cotton %, polyester %, blend ratio)
- Fabric weight (GSM — recalibrated for hoodies, NOT t-shirt thresholds)
- Construction details (hood layers, zipper, cuffs, seams, pocket, drawstring)
- Brand/manufacturing tier with sub-line detection (Champion RW vs Powerblend)
- Price signal (capped — price != quality)

Post-score modifiers for hoodie type, fleece type, and special construction.

User-facing metrics (1-5 each, same keys as t-shirt evaluator):
1. Shrinkage — Will it shrink?
2. Pilling — Will it pill?
3. Longevity — How long will it last?
4. Value — Value for money
5. Care — Care difficulty
"""

import re
import json
import sys
from typing import Dict, List, Tuple, Optional


# ============================================================
# CONSTANTS
# ============================================================

# Brand default scores (0-100) for fallback when specs missing
BRAND_DEFAULT_SCORES = {
    # Artisanal (S tier, 90+)
    "3sixteen": 92, "lady white co": 90,
    # Premium (A tier, 85-89)
    "reigning champ": 88, "wings and horns": 85, "wings+horns": 85,
    # Best value (B+ tier, 78-82)
    "champion reverse weave": 82, "la apparel": 80,
    "los angeles apparel": 80, "carhartt heavyweight": 80,
    # Mid-range (B tier, 65-70)
    "carhartt": 70, "carhartt midweight": 70,
    "nike tech fleece": 68, "fog essentials": 65,
    "fear of god essentials": 65,
    # Budget/mall (C tier, 45-55)
    "nike": 52, "nike club fleece": 52, "adidas": 50,
    "gap": 48, "uniqlo": 50,
    "champion powerblend": 48, "champion": 55,
    "american eagle": 45, "abercrombie": 48,
    "abercrombie & fitch": 48, "north face": 55, "the north face": 55,
    # Entry budget (D tier, 28-35)
    "gildan": 32, "gildan heavy blend": 32,
    "hanes": 30, "fruit of the loom": 28,
    "jerzees": 30,
    # Fast fashion (F tier, 12-20)
    "h&m": 18, "hm": 18, "zara": 20, "shein": 12,
    "boohoo": 12, "forever 21": 14, "fashion nova": 14,
    "primark": 15,
}

# Brand default specs (inferred when listing lacks detail)
BRAND_DEFAULT_SPECS = {
    "champion reverse weave": {
        "gsm": 407, "composition": "82/18", "fleece_type": "brushed",
        "construction": "premium", "expected_washes": 300, "expected_wears": 900,
    },
    "champion powerblend": {
        "gsm": 305, "composition": "50/50", "fleece_type": "brushed",
        "construction": "standard", "expected_washes": 120, "expected_wears": 350,
    },
    "champion": {
        "gsm": 350, "composition": "80/20", "fleece_type": "brushed",
        "construction": "standard", "expected_washes": 150, "expected_wears": 450,
    },
    "gildan": {
        "gsm": 271, "composition": "50/50", "fleece_type": "brushed",
        "construction": "basic", "expected_washes": 70, "expected_wears": 200,
    },
    "gildan heavy blend": {
        "gsm": 271, "composition": "50/50", "fleece_type": "brushed",
        "construction": "basic", "expected_washes": 70, "expected_wears": 200,
    },
    "carhartt": {
        "gsm": 356, "composition": "50/50", "fleece_type": "brushed",
        "construction": "workwear", "expected_washes": 200, "expected_wears": 600,
    },
    "carhartt midweight": {
        "gsm": 356, "composition": "50/50", "fleece_type": "brushed",
        "construction": "workwear", "expected_washes": 200, "expected_wears": 600,
    },
    "carhartt heavyweight": {
        "gsm": 440, "composition": "50/50", "fleece_type": "brushed",
        "construction": "workwear", "expected_washes": 250, "expected_wears": 750,
    },
    "reigning champ": {
        "gsm": 390, "composition": "100/0", "fleece_type": "french_terry",
        "construction": "premium", "expected_washes": 450, "expected_wears": 1350,
    },
    "nike tech fleece": {
        "gsm": 260, "composition": "64/36", "fleece_type": "tech",
        "construction": "engineered", "expected_washes": 100, "expected_wears": 300,
    },
    "nike": {
        "gsm": 300, "composition": "80/20", "fleece_type": "brushed",
        "construction": "standard", "expected_washes": 100, "expected_wears": 300,
    },
    "nike club fleece": {
        "gsm": 300, "composition": "80/20", "fleece_type": "brushed",
        "construction": "standard", "expected_washes": 100, "expected_wears": 300,
    },
    "la apparel": {
        "gsm": 475, "composition": "100/0", "fleece_type": "brushed",
        "construction": "premium", "expected_washes": 300, "expected_wears": 900,
    },
    "los angeles apparel": {
        "gsm": 475, "composition": "100/0", "fleece_type": "brushed",
        "construction": "premium", "expected_washes": 300, "expected_wears": 900,
    },
    "lady white co": {
        "gsm": 441, "composition": "100/0", "fleece_type": "brushed",
        "construction": "artisanal", "expected_washes": 400, "expected_wears": 1200,
    },
    "3sixteen": {
        "gsm": 500, "composition": "100/0", "fleece_type": "brushed",
        "construction": "artisanal", "expected_washes": 500, "expected_wears": 1500,
    },
    "fog essentials": {
        "gsm": 420, "composition": "80/20", "fleece_type": "brushed",
        "construction": "premium", "expected_washes": 200, "expected_wears": 600,
    },
    "fear of god essentials": {
        "gsm": 420, "composition": "80/20", "fleece_type": "brushed",
        "construction": "premium", "expected_washes": 200, "expected_wears": 600,
    },
    "uniqlo": {
        "gsm": 290, "composition": "100/0", "fleece_type": "french_terry",
        "construction": "standard", "expected_washes": 120, "expected_wears": 350,
    },
    "gap": {
        "gsm": 280, "composition": "77/23", "fleece_type": "brushed",
        "construction": "standard", "expected_washes": 100, "expected_wears": 300,
    },
    "h&m": {
        "gsm": 230, "composition": "60/40", "fleece_type": "french_terry",
        "construction": "basic", "expected_washes": 15, "expected_wears": 45,
    },
    "hm": {
        "gsm": 230, "composition": "60/40", "fleece_type": "french_terry",
        "construction": "basic", "expected_washes": 15, "expected_wears": 45,
    },
    "hanes": {
        "gsm": 340, "composition": "50/50", "fleece_type": "brushed",
        "construction": "basic", "expected_washes": 70, "expected_wears": 200,
    },
    "shein": {
        "gsm": 200, "composition": "50/50", "fleece_type": "brushed",
        "construction": "basic", "expected_washes": 15, "expected_wears": 40,
    },
}

# Hoodie weight ranges (completely different from t-shirts)
HOODIE_WEIGHT_RANGES = {
    "ultra_heavy": (500, 9999, 10, "Ultra-heavyweight fleece (500+ GSM)"),
    "heavy": (400, 500, 8, "Heavyweight fleece (400-499 GSM)"),
    "upper_mid": (350, 400, 7, "Upper-midweight fleece (350-399 GSM)"),
    "mid": (280, 350, 5, "Midweight fleece (280-349 GSM)"),
    "light": (240, 280, 3, "Lightweight fleece (240-279 GSM)"),
    "ultra_light": (0, 240, 2, "Ultra-lightweight fleece (<240 GSM)"),
}

# Construction signals with boost points
CONSTRUCTION_SIGNALS_HOODIE = {
    "hood_double_layer": {
        "boost": 2.0,
        "keywords": ["double-layer hood", "double layer hood", "lined hood",
                     "3-panel hood", "three-panel hood", "jersey-lined hood",
                     "three panel"],
    },
    "zipper_ykk": {
        "boost": 2.0,
        "keywords": ["ykk", "metal zipper", "brass zipper", "two-way zipper",
                     "zipper garage"],
    },
    "cuffs_quality": {
        "boost": 1.5,
        "keywords": ["2x2 rib", "2x2 ribbed", "ribbed cuffs", "rib cuffs",
                     "rib knit cuff", "elastane", "spandex", "lycra"],
    },
    "seams_quality": {
        "boost": 1.5,
        "keywords": ["flatlock", "flat-lock", "double-needle", "double needle",
                     "triple-stitch", "triple stitch", "triple-stitched",
                     "reinforced seams"],
    },
    "pocket_reinforced": {
        "boost": 1.0,
        "keywords": ["bar-tack", "bar tack", "bartack", "reinforced pocket",
                     "kangaroo pocket"],
    },
    "side_seamed": {
        "boost": 1.0,
        "keywords": ["side-seamed", "side seam", "side seamed"],
    },
    "drawstring_metal": {
        "boost": 0.5,
        "keywords": ["metal aglet", "metal eyelet", "metal grommet",
                     "waxed drawstring"],
    },
    "neck_tape": {
        "boost": 0.5,
        "keywords": ["neck tape", "taped neck", "taped shoulder"],
    },
}

# Hoodie type modifiers (multiply against final score)
HOODIE_TYPE_MODIFIERS = {
    "pullover": 1.00,
    "quarter_zip": 0.95,
    "half_zip": 0.95,
    "full_zip": 0.90,
    "sleeveless": 0.90,
}

# Fleece type modifiers
FLEECE_TYPE_MODIFIERS = {
    "french_terry": 1.05,
    "brushed": 1.00,
    "tech": 0.95,
}

# Special construction modifiers
SPECIAL_CONSTRUCTION_MODIFIERS = {
    "reverse_weave": 1.10,
    "garment_dyed": 1.05,
}

LIFESPAN_BENCHMARKS = {
    # (min_washes, max_washes, min_wears, max_wears)
    "fast_fashion": (10, 20, 30, 60),
    "entry_budget": (50, 80, 150, 250),
    "budget_mall": (80, 150, 250, 450),
    "mid_range": (100, 200, 300, 600),
    "best_value": (200, 400, 600, 1200),
    "premium": (300, 600, 900, 1800),
    "artisanal": (400, 700, 1200, 2100),
}

# Metric definitions for UI rendering (same 5 keys as t-shirt)
HOODIE_METRIC_DEFINITIONS = [
    {
        "key": "shrinkage",
        "icon": "💧",  # 💧
        "label": "Will it shrink?",
        "left_label": "High risk",
        "right_label": "Low risk",
        "max_score": 5
    },
    {
        "key": "pilling",
        "icon": "🧶",  # 🧶
        "label": "Will it pill?",
        "left_label": "High pilling",
        "right_label": "No pilling",
        "max_score": 5
    },
    {
        "key": "longevity",
        "icon": "\u23f1\ufe0f",  # ⏱️
        "label": "How long will it last?",
        "left_label": "3 months",
        "right_label": "5+ years",
        "max_score": 5
    },
    {
        "key": "value",
        "icon": "💰",  # 💰
        "label": "Value for money",
        "left_label": "Poor value",
        "right_label": "Excellent value",
        "max_score": 5
    },
    {
        "key": "care",
        "icon": "🧺",  # 🧺
        "label": "Care difficulty",
        "left_label": "High maintenance",
        "right_label": "Easy care",
        "max_score": 5
    },
]


# ============================================================
# HELPER FUNCTIONS
# ============================================================

def get_material_percent(materials_structured: List[Dict], material_name: str) -> float:
    """Get total percentage of a specific material (case-insensitive)."""
    total = 0.0
    for item in materials_structured:
        mat = item.get("material", "").lower()
        if material_name.lower() in mat:
            pct = item.get("percent")
            if pct is not None:
                total += float(pct)
    return total


# ============================================================
# PARSING FUNCTIONS
# ============================================================

def parse_hoodie_weight(text: str) -> Optional[float]:
    """Parse hoodie weight as GSM from text. Converts oz to GSM."""
    text_lower = text.lower()

    # Parse GSM directly
    gsm_patterns = [
        r'(\d+(?:\.\d+)?)\s*(?:gsm|g/m)',
    ]
    for pattern in gsm_patterns:
        match = re.search(pattern, text_lower)
        if match:
            return float(match.group(1))

    # Parse oz and convert to GSM
    oz_patterns = [
        r'(\d+(?:\.\d+)?)\s*(?:oz|ounce)',
        r'(\d+(?:\.\d+)?)\s*-\s*oz',
    ]
    for pattern in oz_patterns:
        match = re.search(pattern, text_lower)
        if match:
            oz = float(match.group(1))
            return round(oz * 33.906, 0)

    # Weight descriptors
    if "ultra-heavyweight" in text_lower or "ultra heavyweight" in text_lower:
        return 500.0
    if "super weighted" in text_lower or "super heavy" in text_lower:
        return 550.0
    if re.search(r'\bheavyweight\b', text_lower):
        return 400.0
    if re.search(r'\bmidweight\b', text_lower):
        return 315.0
    if re.search(r'\blightweight\b', text_lower):
        return 240.0

    return None


def detect_fleece_type(text: str) -> str:
    """Detect fleece type from text. Default: brushed."""
    text_lower = text.lower()

    # French terry (check first — more specific)
    if any(kw in text_lower for kw in [
        "french terry", "loopback", "loop-back", "loop back",
        "terry interior", "unfinished interior", "loop interior"
    ]):
        return "french_terry"

    # Tech fleece
    if any(kw in text_lower for kw in [
        "tech fleece", "spacer", "tri-layer", "engineered fleece",
        "spacer construction"
    ]):
        return "tech"

    # Brushed fleece (explicit)
    if any(kw in text_lower for kw in [
        "brushed fleece", "brushed interior", "fleece-lined",
        "napped", "soft interior"
    ]):
        return "brushed"

    return "unknown"


def detect_hoodie_type(text: str) -> str:
    """Detect hoodie type from text. Default: pullover."""
    text_lower = text.lower()

    # Check more-specific types BEFORE generic full_zip
    if any(kw in text_lower for kw in ["quarter zip", "quarter-zip", "1/4 zip"]):
        return "quarter_zip"
    if any(kw in text_lower for kw in ["half zip", "half-zip", "1/2 zip"]):
        return "half_zip"
    if any(kw in text_lower for kw in ["full zip", "full-zip", "zip-up", "zip up",
                                        "zip hoodie", "zip through"]):
        return "full_zip"
    if any(kw in text_lower for kw in ["sleeveless", "vest hoodie", "hoodie vest"]):
        return "sleeveless"
    if any(kw in text_lower for kw in ["pullover", "overhead", "pull-over"]):
        return "pullover"

    return "unknown"


def detect_construction_hoodie(text: str) -> Dict[str, bool]:
    """Detect hoodie construction features from text."""
    text_lower = text.lower()
    features = {}
    for feature, config in CONSTRUCTION_SIGNALS_HOODIE.items():
        features[feature] = any(kw in text_lower for kw in config["keywords"])
    return features


def detect_brand_hoodie(product_name: str, brand: str) -> Tuple[str, Optional[Dict]]:
    """
    Normalize brand name and look up in database.
    Critical: detect sub-lines (Champion RW vs Powerblend, Carhartt mid/heavy, Nike Club/Tech).
    """
    combined = f"{product_name} {brand}".lower()

    # Champion sub-line detection (CRITICAL)
    if "champion" in combined:
        if "reverse weave" in combined:
            return "champion reverse weave", {"default_score": 82}
        if "powerblend" in combined:
            return "champion powerblend", {"default_score": 48}
        if "eco fleece" in combined:
            return "champion powerblend", {"default_score": 48}

    # Carhartt sub-line detection
    if "carhartt" in combined:
        if any(kw in combined for kw in ["heavyweight", "k185", "heavy weight"]):
            return "carhartt heavyweight", {"default_score": 80}
        if any(kw in combined for kw in ["midweight", "k121", "mid weight"]):
            return "carhartt midweight", {"default_score": 70}

    # Nike sub-line detection
    if "nike" in combined:
        if "tech fleece" in combined:
            return "nike tech fleece", {"default_score": 68}
        if "club fleece" in combined or "club" in combined:
            return "nike club fleece", {"default_score": 52}

    # FOG / Essentials detection
    if "fear of god" in combined or "fog essentials" in combined or "essentials" in combined:
        if "fear of god" in combined or "essentials" in combined:
            return "fear of god essentials", {"default_score": 65}

    # Normalize brand
    raw = (brand or "").lower().strip()
    normalized = raw.replace("'", "").replace("\u2019", "").replace(".", "").strip()

    # Direct lookup
    if normalized in BRAND_DEFAULT_SCORES:
        return normalized, {"default_score": BRAND_DEFAULT_SCORES[normalized]}

    # Partial match (skip empty strings)
    if normalized:
        for key, score in BRAND_DEFAULT_SCORES.items():
            if key in normalized or normalized in key:
                return key, {"default_score": score}

    # Try from product name if brand field empty
    if not brand and product_name:
        name_lower = product_name.lower().replace("'", "").replace("\u2019", "")
        for key, score in BRAND_DEFAULT_SCORES.items():
            if key in name_lower:
                return key, {"default_score": score}

    return normalized or "unknown", None


def detect_special_construction(text: str) -> Dict[str, bool]:
    """Detect special construction features."""
    text_lower = text.lower()
    return {
        "reverse_weave": any(kw in text_lower for kw in [
            "reverse weave", "cross-grain", "cross grain"
        ]),
        "garment_dyed": any(kw in text_lower for kw in [
            "garment-dyed", "garment dyed"
        ]),
        "preshrunk": any(kw in text_lower for kw in [
            "preshrunk", "pre-shrunk", "pre-washed", "pre washed",
            "sanforized"
        ]),
    }


def detect_origin(text: str) -> Optional[str]:
    """Detect manufacturing origin."""
    text_lower = text.lower()
    if any(kw in text_lower for kw in ["made in canada"]):
        return "canada"
    if any(kw in text_lower for kw in ["made in usa", "made in la",
                                        "made in los angeles", "made in america"]):
        return "usa"
    if "made in japan" in text_lower:
        return "japan"
    if "made in portugal" in text_lower:
        return "portugal"
    return None


def detect_anti_pill(text: str) -> bool:
    """Detect anti-pilling treatment keywords."""
    text_lower = text.lower()
    return any(kw in text_lower for kw in [
        "anti-pill", "anti pill", "pill-resistant", "pill resistant",
        "air-jet yarn", "air jet", "nublend"
    ])


def detect_cotton_type(text: str) -> str:
    """Detect cotton quality type from text."""
    text_lower = text.lower()
    if "supima" in text_lower:
        return "supima"
    if "pima" in text_lower:
        return "pima"
    if any(kw in text_lower for kw in ["combed and ring-spun", "combed & ring-spun",
                                        "combed ring-spun", "combed ringspun"]):
        return "combed_ringspun"
    if any(kw in text_lower for kw in ["ring-spun", "ringspun", "ring spun"]):
        return "ringspun"
    return "unknown"


# ============================================================
# INTERNAL SCORING FUNCTIONS (0-10 each)
# ============================================================

def score_fabric_composition(
    materials_structured: List[Dict],
    materials_text: str,
    brand_score: Optional[float] = None
) -> Tuple[float, str]:
    """Score fabric composition (0-10). Weight: 25%."""
    cotton_pct = get_material_percent(materials_structured, "cotton")
    poly_pct = get_material_percent(materials_structured, "polyester")

    # No composition data
    if not materials_structured or (cotton_pct == 0 and poly_pct == 0):
        # Check for "cotton/polyester" text without percentages
        text_lower = materials_text.lower()
        if "cotton" in text_lower and "polyester" in text_lower:
            return 4.0, "Cotton/polyester blend (no percentages) — assume 50/50 or worse"
        if brand_score is not None and brand_score >= 8.0:
            return 7.0, "Composition not disclosed — premium brand typically uses high-quality fabric"
        if brand_score is not None and brand_score >= 7.0:
            return 6.0, "Composition not disclosed — quality brand, likely cotton-dominant blend"
        if brand_score is not None and brand_score >= 5.0:
            return 4.5, "Composition not disclosed — mid-range brand"
        return 2.0, "No fabric composition available"

    cotton_type = detect_cotton_type(materials_text)

    # 100% premium cotton (Supima/Pima)
    if cotton_pct >= 98 and cotton_type in ["supima", "pima"]:
        return 10.0, f"100% {cotton_type.title()} cotton — extra-long staple, maximum durability"

    # 100% combed ringspun cotton
    if cotton_pct >= 98 and cotton_type == "combed_ringspun":
        return 9.0, "100% combed ringspun cotton — premium yarn quality"

    # 80-90% cotton / 10-20% poly (sweet spot for hoodies)
    if 80 <= cotton_pct <= 90 and 10 <= poly_pct <= 20:
        return 8.0, f"{cotton_pct:.0f}/{poly_pct:.0f} cotton/poly — sweet spot for shape retention + cotton feel"

    # 100% regular cotton
    if cotton_pct >= 98:
        return 7.0, "100% cotton — excellent quality, may shrink more than blends"

    # 60-79% cotton
    if 60 <= cotton_pct <= 79:
        return 5.0, f"{cotton_pct:.0f}% cotton / {poly_pct:.0f}% polyester — moderate blend"

    # 50/50 cotton/poly
    if 45 <= cotton_pct <= 55 and 45 <= poly_pct <= 55:
        return 4.0, "50/50 cotton/polyester — common budget blend, prone to pilling"

    # High polyester (>60%)
    if poly_pct > 60:
        return 3.0, f"{poly_pct:.0f}% polyester — synthetic-dominant, reduced breathability"

    # Below 50% cotton
    if cotton_pct < 50:
        return 3.5, f"{cotton_pct:.0f}% cotton — low cotton content"

    return 5.0, f"{cotton_pct:.0f}% cotton blend"


def score_hoodie_weight(
    materials_text: str,
    brand_name: str = "",
    price: Optional[float] = None
) -> Tuple[float, str]:
    """Score hoodie weight (0-10). Weight: 20%. Uses hoodie-specific thresholds."""
    gsm = parse_hoodie_weight(materials_text)

    # Infer from brand defaults if not stated
    if gsm is None:
        brand_lower = brand_name.lower().replace("'", "").replace("\u2019", "")
        specs = BRAND_DEFAULT_SPECS.get(brand_lower)
        if specs:
            gsm = specs.get("gsm")
            if gsm:
                return _score_gsm(gsm), f"~{gsm:.0f} GSM (inferred from {brand_name} defaults) — weight not disclosed"

        # Infer from price when brand unknown
        if price is not None:
            if price >= 100:
                inferred = 380
            elif price >= 60:
                inferred = 320
            elif price >= 30:
                inferred = 280
            else:
                inferred = 240
            return _score_gsm(inferred), f"~{inferred} GSM (estimated from ${price:.0f} price point) — weight not disclosed"

        return 3.0, "Hoodie weight not disclosed — cannot assess fabric heft"

    return _score_gsm(gsm), f"{gsm:.0f} GSM"


def _score_gsm(gsm: float) -> float:
    """Convert GSM weight to 0-10 score using hoodie thresholds."""
    if gsm >= 500:
        return 10.0
    elif gsm >= 400:
        return 8.0
    elif gsm >= 350:
        return 7.0
    elif gsm >= 280:
        return 5.0
    elif gsm >= 240:
        return 3.0
    else:
        return 2.0


def score_construction_hoodie(
    materials_text: str,
    brand_score: Optional[float] = None
) -> Tuple[float, str]:
    """Score construction details (0-10). Weight: 25%."""
    features = detect_construction_hoodie(materials_text)
    found = [f for f, present in features.items() if present]

    if len(found) == 0:
        # Infer from brand reputation
        if brand_score is not None and brand_score >= 8.5:
            return 8.0, "Construction not disclosed — artisanal brand, premium construction assumed"
        if brand_score is not None and brand_score >= 7.5:
            return 6.5, "Construction not disclosed — premium brand, quality construction assumed"
        if brand_score is not None and brand_score >= 6.0:
            return 5.0, "Construction not disclosed — mid-range brand, standard construction"
        if brand_score is not None and brand_score >= 4.0:
            return 3.5, "Construction not disclosed — budget brand"
        return 2.0, "No construction details disclosed"

    # Sum boost points
    total_boost = 0.0
    details = []

    for feature, config in CONSTRUCTION_SIGNALS_HOODIE.items():
        if features.get(feature):
            total_boost += config["boost"]
            details.append(feature.replace("_", " "))

    # Base 2.0 + boosts, max 10.0
    score = min(10.0, 2.0 + total_boost)
    explanation = f"Construction: {', '.join(details)}"
    return score, explanation


def score_brand_tier_hoodie(brand_name: str, product_name: str) -> Tuple[float, str]:
    """Score brand/manufacturer tier (0-10). Weight: 20%."""
    normalized, brand_info = detect_brand_hoodie(product_name, brand_name)

    if brand_info is None:
        return 4.0, f"Unknown brand '{brand_name or 'unspecified'}' — cannot assess manufacturing quality"

    default_score = brand_info["default_score"]
    score = default_score / 10.0

    if default_score >= 90:
        tier_desc = "artisanal"
    elif default_score >= 80:
        tier_desc = "premium / best value"
    elif default_score >= 65:
        tier_desc = "mid-range"
    elif default_score >= 45:
        tier_desc = "budget / mall"
    elif default_score >= 28:
        tier_desc = "entry budget"
    else:
        tier_desc = "fast fashion"

    return score, f"{normalized.title()} — {tier_desc} tier"


def score_price_signal_hoodie(price: Optional[float]) -> Tuple[float, str]:
    """Score price signal (0-10, CAPPED at 8). Weight: 10%."""
    if price is None:
        return 4.0, "No price available"

    if price >= 150:
        return 8.0, f"${price:.0f} — premium price point (capped: price \u2260 quality)"
    elif price >= 100:
        return 7.0, f"${price:.0f} — mid-premium price"
    elif price >= 60:
        return 6.0, f"${price:.0f} — mid-range price"
    elif price >= 30:
        return 4.0, f"${price:.0f} — budget price"
    else:
        return 2.0, f"${price:.0f} — ultra-budget price"


# ============================================================
# USER-FACING METRIC FUNCTIONS (1-5 each)
# ============================================================

def calculate_shrinkage_hoodie(
    materials_structured: List[Dict],
    hoodie_type: str,
    special: Dict[str, bool],
    gsm: Optional[float]
) -> Tuple[float, str]:
    """Calculate shrinkage risk (1-5). Higher = lower shrinkage risk."""
    cotton_pct = get_material_percent(materials_structured, "cotton")
    poly_pct = get_material_percent(materials_structured, "polyester")

    # Composition base (on 1-10 scale, then map to 1-5)
    if poly_pct >= 90:
        base = 9.0
        explanation = "Nearly all polyester — minimal shrinkage"
    elif 45 <= cotton_pct <= 55 and 45 <= poly_pct <= 55:
        base = 7.0
        explanation = "50/50 blend — moderate shrinkage resistance"
    elif 80 <= cotton_pct <= 90:
        base = 5.0
        explanation = f"{cotton_pct:.0f}% cotton — expect 3-5% shrinkage on first hot wash"
    elif cotton_pct >= 95:
        base = 3.0
        explanation = "100% cotton — expect 5-10% shrinkage on first hot wash"
    elif cotton_pct > 0:
        base = 5.5
        explanation = f"{cotton_pct:.0f}/{poly_pct:.0f} blend — moderate shrinkage"
    else:
        base = 5.0
        explanation = "Composition unknown — moderate shrinkage risk assumed"

    # Modifiers
    if special.get("preshrunk"):
        base += 1.5
        explanation += ". Preshrunk — shrinkage already removed"
    if special.get("garment_dyed"):
        base += 2.0
        explanation += ". Garment-dyed — removes ~99% of shrinkage"
    if special.get("reverse_weave"):
        base += 2.0
        explanation += ". Reverse Weave cross-grain — reduces vertical shrinkage 50-70%"
    if gsm and gsm >= 400:
        base += 0.5
        explanation += ". Dense knit resists deformation"

    # Zip-up penalty
    if hoodie_type == "full_zip":
        base -= 0.5
        explanation += ". Zip-up risk: cotton body shrinks around non-shrinking polyester zipper tape, causing buckling"
    elif hoodie_type in ["quarter_zip", "half_zip"]:
        base -= 0.3

    # Clamp and convert to 1-5
    score = max(1.0, min(5.0, base / 2.0))
    return round(score, 1), explanation


def calculate_pilling_hoodie(
    materials_structured: List[Dict],
    fleece_type: str,
    gsm: Optional[float],
    anti_pill: bool
) -> Tuple[float, str]:
    """Calculate pilling resistance (1-5). Higher = less pilling."""
    cotton_pct = get_material_percent(materials_structured, "cotton")
    poly_pct = get_material_percent(materials_structured, "polyester")
    cotton_type = "unknown"

    # Composition base (on 1-10 scale)
    if poly_pct >= 90 and anti_pill:
        base = 9.0
        explanation = "100% polyester with anti-pill treatment — maximum pill resistance"
    elif cotton_pct >= 95:
        cotton_type_text = "cotton"
        base = 5.0
        explanation = f"100% {cotton_type_text} — moderate pilling, but pills self-release as fibers break off"
    elif 80 <= cotton_pct <= 90:
        base = 5.0
        explanation = f"{cotton_pct:.0f}/{poly_pct:.0f} cotton/poly — moderate pilling tendency"
    elif poly_pct >= 60:
        base = 6.0
        explanation = f"High polyester ({poly_pct:.0f}%) — synthetic fibers anchor pills firmly"
    elif 45 <= cotton_pct <= 55 and 45 <= poly_pct <= 55:
        base = 3.0
        explanation = "50/50 cotton/poly — WORST for pilling (cotton fibers break, poly fibers anchor them)"
    elif cotton_pct > 0:
        base = 4.5
        explanation = f"{cotton_pct:.0f}/{poly_pct:.0f} blend"
    else:
        base = 4.0
        explanation = "Composition unknown — moderate pilling risk assumed"

    # Fleece type modifier (most important hoodie-specific factor)
    if fleece_type == "french_terry":
        base += 1.0
        explanation += ". French terry interior — loops are structurally anchored, pills significantly less"
    elif fleece_type == "brushed":
        explanation += ". Brushed fleece interior — millions of free fiber ends prone to pilling"
        if gsm and gsm < 280:
            base -= 1.0
            explanation += " (lightweight + brushed = rapid pilling)"

    # Weight modifier
    if gsm and gsm >= 400:
        base += 1.0
        explanation += f". {gsm:.0f} GSM — tighter, heavier knit holds fibers more securely"
    elif gsm and gsm >= 350:
        base += 0.5

    # Anti-pill treatment
    if anti_pill and poly_pct < 90:
        base += 0.5
        explanation += ". Anti-pill treatment detected (lasts 5-30 washes before diminishing)"

    # Always mention backpack strap risk
    explanation += ". Watch for pilling under backpack straps (severe localized abrasion)"

    # Clamp to 1-5
    score = max(1.0, min(5.0, base / 2.0))
    return round(score, 1), explanation


def calculate_longevity_hoodie(
    overall_score: float,
    hoodie_type: str,
    fleece_type: str,
    gsm: Optional[float],
    construction: Dict[str, bool]
) -> Tuple[float, str, int, int]:
    """
    Calculate longevity (1-5) and estimated washes/wears.
    Returns (score, explanation, estimated_washes, estimated_wears).
    """
    # Base lifespan from overall score
    if overall_score >= 80:
        base_washes = 400
        base_wears = 1200
    elif overall_score >= 65:
        base_washes = 200
        base_wears = 600
    elif overall_score >= 50:
        base_washes = 120
        base_wears = 350
    elif overall_score >= 35:
        base_washes = 70
        base_wears = 200
    else:
        base_washes = 20
        base_wears = 50

    # GSM bonus
    if gsm and gsm >= 500:
        base_washes = int(base_washes * 1.3)
        base_wears = int(base_wears * 1.3)
    elif gsm and gsm >= 400:
        base_washes = int(base_washes * 1.15)
        base_wears = int(base_wears * 1.15)

    # Hoodie type modifier
    type_mult = HOODIE_TYPE_MODIFIERS.get(hoodie_type, 1.0)
    base_washes = int(base_washes * type_mult)
    base_wears = int(base_wears * type_mult)

    estimated_washes = max(10, base_washes)
    estimated_wears = max(30, base_wears)

    # Convert to 1-5
    if estimated_washes >= 300:
        score = 5.0
    elif estimated_washes >= 180:
        score = 4.0
    elif estimated_washes >= 100:
        score = 3.5
    elif estimated_washes >= 60:
        score = 3.0
    elif estimated_washes >= 30:
        score = 2.0
    else:
        score = 1.5

    # Build explanation
    parts = [f"~{estimated_washes} washes / ~{estimated_wears} wears estimated"]
    if gsm:
        parts.append(f"{gsm:.0f} GSM")
    if fleece_type != "unknown":
        parts.append(f"{fleece_type.replace('_', ' ')} fleece")
    if hoodie_type != "unknown" and hoodie_type != "pullover":
        parts.append(f"{hoodie_type.replace('_', ' ')}")

    explanation = ". ".join(parts)
    return score, explanation, estimated_washes, estimated_wears


def calculate_value_hoodie(
    price: Optional[float],
    estimated_washes: int,
    brand_score: float,
    overall_score: float
) -> Tuple[Optional[float], str]:
    """Calculate value (1-5). Champion RW at $55-75 is the benchmark."""
    if price is None:
        return None, "No price available"

    estimated_wears = max(30, estimated_washes * 3)
    cost_per_wear = price / max(1, estimated_wears)

    # Exceptional value detection
    if overall_score >= 55 and price < 80:
        return 5.0, f"Exceptional value: ${cost_per_wear:.2f}/wear at ${price:.0f} — quality exceeds price"

    if overall_score >= 70 and price < 120:
        return 4.5, f"Great value: ${cost_per_wear:.2f}/wear — ${price:.0f} for premium-tier quality"

    # Standard value calculation
    if cost_per_wear < 0.20:
        return 4.5, f"Excellent value: ${cost_per_wear:.2f}/wear (${price:.0f} for ~{estimated_wears} wears)"
    elif cost_per_wear < 0.40:
        return 3.5, f"Good value: ${cost_per_wear:.2f}/wear"
    elif cost_per_wear < 0.75:
        return 3.0, f"Fair value: ${cost_per_wear:.2f}/wear"
    elif cost_per_wear < 1.50:
        return 2.0, f"Below average value: ${cost_per_wear:.2f}/wear"
    else:
        return 1.5, f"Poor value: ${cost_per_wear:.2f}/wear (${price:.0f} for only ~{estimated_wears} estimated wears)"


def calculate_care_hoodie(
    materials_structured: List[Dict],
    hoodie_type: str,
    fleece_type: str,
    special: Dict[str, bool]
) -> Tuple[float, str]:
    """Calculate care difficulty (1-5). Higher = easier. Always includes fabric softener warning."""
    cotton_pct = get_material_percent(materials_structured, "cotton")
    poly_pct = get_material_percent(materials_structured, "polyester")

    # Composition base (on 1-10 scale)
    if 45 <= cotton_pct <= 55 and 45 <= poly_pct <= 55:
        base = 9.0
        explanation = "50/50 blend — easy care, wash cold, hang dry preferred"
    elif 80 <= cotton_pct <= 90:
        base = 7.0
        explanation = "80/20 cotton/poly — machine wash cold, air dry for best results"
    elif poly_pct >= 90:
        base = 7.0
        explanation = "Synthetic — easy wash, but no fabric softener"
    elif cotton_pct >= 95:
        base = 5.0
        explanation = "100% cotton — air dry only to avoid shrinkage, no tumble dry"
    elif cotton_pct > 0:
        base = 6.5
        explanation = f"{cotton_pct:.0f}/{poly_pct:.0f} blend — standard machine wash care"
    else:
        base = 6.0
        explanation = "Standard care assumed"

    # Zipper penalty
    if hoodie_type == "full_zip":
        base -= 1.0
        explanation += ". Always zip up before washing to prevent zipper damage and snagging"
    elif hoodie_type in ["quarter_zip", "half_zip"]:
        base -= 0.5

    # Tech fleece penalty
    if fleece_type == "tech":
        base -= 0.5
        explanation += ". Tech fleece: must air-dry (heat damages adhesive bond between layers)"

    # Special lining penalty
    if special.get("garment_dyed"):
        base -= 0.5
        explanation += ". Garment-dyed: wash separately first few times (color may bleed)"

    # Preshrunk bonus
    if special.get("preshrunk"):
        base += 1.0
        explanation += ". Preshrunk — less worry about sizing changes"

    # ALWAYS include fabric softener warning
    explanation += ". NEVER use fabric softener on fleece — it coats fibers, reduces warmth, kills moisture-wicking. Use vinegar in rinse cycle instead"

    # Hoodies can go longer between washes
    explanation += ". Hoodies can go 4-6 wears between washes (outerwear doesn't touch skin directly)"

    # Clamp to 1-5
    score = max(1.0, min(5.0, base / 2.0))
    return round(score, 1), explanation


# ============================================================
# TRANSPARENCY & RED FLAGS
# ============================================================

def calculate_transparency_hoodie(
    gsm: Optional[float],
    construction: Dict[str, bool],
    fleece_type: str,
    hoodie_type: str,
    materials_structured: List[Dict],
    brand_info: Optional[Dict],
    origin: Optional[str]
) -> Tuple[int, str, str, List[str]]:
    """Calculate transparency score (1-10)."""
    score = 0
    data_points = []
    ask_cs = []

    # Fabric composition (+2)
    if materials_structured and len(materials_structured) > 0:
        score += 2
        data_points.append("Material composition disclosed")
    else:
        ask_cs.append("What is the fabric composition (cotton %, polyester %)?")

    # Fabric weight (+2)
    if gsm is not None:
        score += 2
        data_points.append(f"Fabric weight ({gsm:.0f} GSM)")
    else:
        ask_cs.append("What is the fabric weight in GSM or oz?")

    # Construction details (+2)
    construction_found = sum(1 for v in construction.values() if v)
    if construction_found >= 3:
        score += 2
        data_points.append("Detailed construction info")
    elif construction_found >= 1:
        score += 1
        data_points.append("Partial construction info")
    else:
        ask_cs.append("What construction details? (hood layers, seam type, cuff ribbing)")

    # Fleece type (+1)
    if fleece_type != "unknown":
        score += 1
        data_points.append(f"Fleece type: {fleece_type.replace('_', ' ')}")

    # Hoodie type (+0.5 — usually obvious)
    if hoodie_type != "unknown":
        score += 1

    # Origin (+1)
    if origin:
        score += 1
        data_points.append(f"Origin: {origin}")

    # Confidence
    if score >= 8:
        confidence = "high"
    elif score >= 5:
        confidence = "medium"
    else:
        confidence = "low"

    if score >= 8:
        explanation = f"Excellent transparency ({score}/10): {', '.join(data_points)}"
    elif score >= 6:
        explanation = f"Good transparency ({score}/10): {', '.join(data_points)}"
    elif score >= 4:
        explanation = f"Fair transparency ({score}/10): Basic information disclosed"
    else:
        explanation = f"Poor transparency ({score}/10): Minimal quality information provided"

    return score, confidence, explanation, ask_cs


def detect_red_flags_hoodie(
    materials_structured: List[Dict],
    gsm: Optional[float],
    price: Optional[float],
    fleece_type: str,
    construction: Dict[str, bool]
) -> List[str]:
    """Detect hoodie-specific red flags."""
    red_flags = []
    poly_pct = get_material_percent(materials_structured, "polyester")
    cotton_pct = get_material_percent(materials_structured, "cotton")

    # High polyester
    if poly_pct > 60 and fleece_type != "tech":
        red_flags.append(f"\u26d4 {poly_pct:.0f}% polyester — synthetic-dominant, reduced breathability")

    # Ultra-lightweight
    if gsm and gsm < 240:
        red_flags.append(f"\u26d4 Ultra-lightweight ({gsm:.0f} GSM) — expect rapid surface degradation")

    # Lightweight at premium price
    if gsm and gsm < 280 and price and price > 60:
        red_flags.append(f"\u26a0\ufe0f Lightweight ({gsm:.0f} GSM) at ${price:.0f} — fabric weight doesn't match price point")

    # 50/50 at premium price
    if 45 <= cotton_pct <= 55 and 45 <= poly_pct <= 55 and price and price > 80:
        red_flags.append(f"\u26a0\ufe0f 50/50 blend at ${price:.0f} — budget composition at premium pricing")

    # No construction info + high price
    construction_found = sum(1 for v in construction.values() if v)
    if construction_found == 0 and price and price > 100:
        red_flags.append(f"\u26a0\ufe0f ${price:.0f} with no construction details disclosed — low transparency")

    return red_flags


def detect_value_outliers_hoodie(
    brand_name: str,
    price: Optional[float],
    overall_score: float
) -> List[str]:
    """Detect exceptional value or overpriced products."""
    notes = []
    normalized = brand_name.lower().replace("'", "").replace("\u2019", "")

    # Exceptional value
    if "champion reverse weave" in normalized and price and 55 <= price <= 80:
        notes.append("💎 Champion Reverse Weave at $" + f"{price:.0f}" +
                     " — lowest cost-per-wear of any tier (~$0.08-0.12/wear)")
    if "carhartt" in normalized and "midweight" in normalized and price and price < 75:
        notes.append("💎 Carhartt K121 — workwear durability at mall pricing")
    if ("la apparel" in normalized or "los angeles apparel" in normalized) and price and price < 90:
        notes.append("💎 LA Apparel 14oz — premium 100% cotton, made in USA, at mid-range pricing")

    # Potentially overpriced
    if "fog essentials" in normalized or "fear of god" in normalized:
        if price and price > 90:
            notes.append("\u26a0\ufe0f Fashion-premium pricing — construction doesn't fully justify premium over Champion Reverse Weave")

    return notes


# ============================================================
# CARE IMPACT
# ============================================================

def calculate_care_impact_hoodie(
    estimated_washes: int,
    materials_structured: List[Dict],
    fleece_type: str,
    price: Optional[float]
) -> Dict:
    """Calculate how care methods affect hoodie longevity."""
    cotton_pct = get_material_percent(materials_structured, "cotton")

    # Multipliers
    best_mult = 1.5
    good_mult = 1.2
    worst_mult = 0.6

    if cotton_pct >= 90:
        worst_mult = 0.55  # 100% cotton more sensitive to heat

    if fleece_type == "tech":
        worst_mult = 0.5  # Tech fleece very sensitive to heat

    best_washes = int(estimated_washes * best_mult)
    good_washes = int(estimated_washes * good_mult)
    worst_washes = int(estimated_washes * worst_mult)

    scenarios = []
    if price:
        best_wears = best_washes * 3
        good_wears = good_washes * 3
        base_wears = estimated_washes * 3
        worst_wears = worst_washes * 3
        scenarios = [
            {"method": "Cold wash every 4-6 wears + air dry", "impact": "Best",
             "washes": best_washes, "cost_per_wear": round(price / best_wears, 2),
             "description": "Optimal for fleece — preserves structure and surface"},
            {"method": "Cold wash bi-weekly + air dry", "impact": "Good",
             "washes": good_washes, "cost_per_wear": round(price / good_wears, 2),
             "description": "Good balance of hygiene and longevity"},
            {"method": "Warm wash weekly + tumble dry low", "impact": "Standard",
             "washes": estimated_washes, "cost_per_wear": round(price / base_wears, 2),
             "description": "Standard care — baseline estimate"},
            {"method": "Hot wash frequent + tumble dry high", "impact": "Worst",
             "washes": worst_washes, "cost_per_wear": round(price / worst_wears, 2),
             "description": "Destroys fleece surface, shrinks cotton, kills cuff elasticity"},
        ]
    else:
        scenarios = [
            {"method": "Cold wash every 4-6 wears + air dry", "impact": "Best",
             "washes": best_washes, "description": "Optimal for fleece"},
            {"method": "Cold wash bi-weekly + air dry", "impact": "Good",
             "washes": good_washes, "description": "Good balance"},
            {"method": "Warm wash weekly + tumble dry low", "impact": "Standard",
             "washes": estimated_washes, "description": "Baseline"},
            {"method": "Hot wash frequent + tumble dry high", "impact": "Worst",
             "washes": worst_washes, "description": "Harsh — destroys fleece rapidly"},
        ]

    # Recommendations — ALWAYS include softener warning
    recommendations = [
        "NEVER use fabric softener on fleece — it coats fibers, kills insulation and wicking. Use vinegar instead",
        "Turn inside-out before washing to protect fleece surface",
        "Wash in cold water only — hot water shrinks cotton and degrades elastane in cuffs",
        "Air dry flat or on a drying rack — hanging causes permanent shoulder stretching",
    ]

    if fleece_type == "tech":
        recommendations.insert(1, "Tech fleece: ALWAYS air dry — heat destroys the adhesive bond between layers")

    # Savings
    savings = None
    if price:
        base_wears = estimated_washes * 3
        best_wears = best_washes * 3
        standard_cpw = price / base_wears
        best_cpw = price / best_wears
        savings = {
            "cost_per_wear_reduction": round(standard_cpw - best_cpw, 2),
            "additional_washes": best_washes - estimated_washes,
            "total_value_gained": round((standard_cpw - best_cpw) * best_wears, 2),
            "summary": f"Proper care adds ~{best_washes - estimated_washes} washes and saves ${standard_cpw - best_cpw:.2f}/wear"
        }

    return {
        "scenarios": scenarios,
        "recommendations": recommendations,
        "savings": savings,
        "baseline_method": "Warm wash weekly + tumble dry low",
        "best_method": "Cold wash every 4-6 wears + air dry"
    }


# ============================================================
# FAILURE MODES
# ============================================================

def estimate_failure_modes_hoodie(
    hoodie_type: str,
    fleece_type: str,
    gsm: Optional[float],
    materials_structured: List[Dict],
    construction: Dict[str, bool]
) -> List[Dict]:
    """Estimate primary failure modes and risks."""
    modes = []
    cotton_pct = get_material_percent(materials_structured, "cotton")
    poly_pct = get_material_percent(materials_structured, "polyester")

    # 1. Pilling/surface degradation (most common)
    pill_risk = "medium"
    pill_note = "Fleece surface degrades from abrasion (especially under backpack straps)"
    if 45 <= cotton_pct <= 55 and 45 <= poly_pct <= 55:
        pill_risk = "high"
        pill_note = "50/50 blend + fleece = maximum pilling risk"
    elif fleece_type == "french_terry":
        pill_risk = "low"
        pill_note = "French terry loops resist pilling better than brushed fleece"
    if gsm and gsm < 280 and fleece_type == "brushed":
        pill_risk = "high"
        pill_note = "Lightweight brushed fleece — expect visible pilling within 10-15 wears"
    modes.append({"mode": "Pilling/surface degradation", "risk": pill_risk, "note": pill_note})

    # 2. Cuff/hem elastic failure
    cuff_risk = "medium"
    cuff_note = "Ribbing stretches out over time, heat accelerates this"
    if construction.get("cuffs_quality"):
        cuff_risk = "low"
        cuff_note = "Quality ribbing with elastane — good shape retention"
    modes.append({"mode": "Cuff elastic failure", "risk": cuff_risk, "note": cuff_note})

    # 3. Zipper failure (zip-ups only)
    if hoodie_type in ["full_zip", "quarter_zip", "half_zip"]:
        zip_risk = "medium"
        zip_note = "Zipper is the terminal failure point for zip-up hoodies"
        if construction.get("zipper_ykk"):
            zip_risk = "low"
            zip_note = "YKK zipper — reliable hardware, low failure rate"
        if cotton_pct >= 90 and hoodie_type == "full_zip":
            zip_risk = "high"
            zip_note = "100% cotton + full zip — cotton body shrinks around non-shrinking zipper tape, causing buckling"
        modes.append({"mode": "Zipper failure", "risk": zip_risk, "note": zip_note})

    # 4. Neckline/hood stretching (pullovers)
    if hoodie_type == "pullover":
        neck_risk = "medium"
        neck_note = "Repeated pulling over head stretches neckline and hood opening"
        if gsm and gsm >= 400:
            neck_risk = "low"
            neck_note = "Heavyweight fabric resists neckline stretching"
        modes.append({"mode": "Neckline stretching", "risk": neck_risk, "note": neck_note})

    # 5. Pocket tearing
    pocket_risk = "medium"
    pocket_note = "Kangaroo pocket stitching separates at stress corners (smartphone weight)"
    if construction.get("pocket_reinforced"):
        pocket_risk = "low"
        pocket_note = "Reinforced pocket construction — bar-tacked stress points"
    modes.append({"mode": "Pocket tearing", "risk": pocket_risk, "note": pocket_note})

    return modes


# ============================================================
# OVERALL SCORE
# ============================================================

def calculate_overall_score_hoodie(
    internal_scores: Dict[str, float],
    modifiers_mult: float
) -> Tuple[float, str]:
    """Calculate overall score (0-100) from weighted internal scores."""
    weights = {
        "composition": 0.25,
        "weight": 0.20,
        "construction": 0.25,
        "brand": 0.20,
        "price": 0.10,
    }

    weighted_sum = 0.0
    total_weight = 0.0
    for key, weight in weights.items():
        score = internal_scores.get(key)
        if score is not None:
            weighted_sum += score * weight
            total_weight += weight

    if total_weight == 0:
        return 0.0, "unknown"

    overall = (weighted_sum / total_weight) * 10 * modifiers_mult
    overall = max(0, min(100, overall))

    if overall >= 80:
        tier = "excellent"
    elif overall >= 60:
        tier = "good"
    elif overall >= 40:
        tier = "average"
    else:
        tier = "poor"

    return round(overall, 1), tier


# ============================================================
# MAIN ENTRY POINT
# ============================================================

def evaluate_hoodie(product_data: Dict) -> Dict:
    """
    Evaluate hoodie quality.

    Args:
        product_data: {
            "materials_structured": [...],
            "materials_text": str,
            "price": float or None,
            "brand": str,
            "product_name": str
        }

    Returns:
        Evaluation dict matching t-shirt/jeans evaluator shape.
    """
    materials_structured = product_data.get("materials_structured", [])
    materials_text = product_data.get("materials_text", "")
    price = product_data.get("price")
    brand = product_data.get("brand", "")
    product_name = product_data.get("product_name", "")

    combined_text = f"{product_name} {materials_text}"

    # Handle missing data
    if not materials_structured and not brand:
        return _empty_evaluation()

    # --- Parse all attributes ---
    gsm = parse_hoodie_weight(materials_text)
    construction = detect_construction_hoodie(materials_text)
    fleece_type = detect_fleece_type(combined_text)
    hoodie_type = detect_hoodie_type(combined_text)
    special = detect_special_construction(combined_text)
    origin = detect_origin(materials_text)
    anti_pill = detect_anti_pill(materials_text)
    brand_normalized, brand_info = detect_brand_hoodie(product_name, brand)

    # Infer fleece type from brand if not detected
    if fleece_type == "unknown" and brand_normalized:
        specs = BRAND_DEFAULT_SPECS.get(brand_normalized)
        if specs:
            fleece_type = specs.get("fleece_type", "brushed")

    # Default fleece type to brushed if still unknown
    if fleece_type == "unknown":
        fleece_type = "brushed"

    # Default hoodie type to pullover if unknown
    if hoodie_type == "unknown":
        hoodie_type = "pullover"

    # Infer GSM from brand defaults
    if gsm is None and brand_normalized:
        specs = BRAND_DEFAULT_SPECS.get(brand_normalized)
        if specs:
            gsm = specs.get("gsm")

    # --- Internal scoring (0-10 each) ---
    brand_score, brand_exp = score_brand_tier_hoodie(brand, product_name)
    comp_score, comp_exp = score_fabric_composition(materials_structured, materials_text, brand_score)
    weight_score, weight_exp = score_hoodie_weight(materials_text, brand, price)
    const_score, const_exp = score_construction_hoodie(materials_text, brand_score)
    price_score, price_exp = score_price_signal_hoodie(price)

    internal_scores = {
        "composition": comp_score,
        "weight": weight_score,
        "construction": const_score,
        "brand": brand_score,
        "price": price_score,
    }

    # --- Apply modifiers ---
    modifiers_mult = 1.0
    modifier_notes = []

    type_mult = HOODIE_TYPE_MODIFIERS.get(hoodie_type, 1.0)
    if type_mult != 1.0:
        modifiers_mult *= type_mult
        modifier_notes.append(f"Type ({hoodie_type.replace('_', ' ')}): \u00d7{type_mult}")

    fleece_mult = FLEECE_TYPE_MODIFIERS.get(fleece_type, 1.0)
    if fleece_mult != 1.0:
        modifiers_mult *= fleece_mult
        modifier_notes.append(f"Fleece ({fleece_type.replace('_', ' ')}): \u00d7{fleece_mult}")

    if special.get("reverse_weave"):
        modifiers_mult *= 1.10
        modifier_notes.append("Reverse Weave: \u00d71.10")
    if special.get("garment_dyed"):
        modifiers_mult *= 1.05
        modifier_notes.append("Garment-dyed: \u00d71.05")

    # --- Overall score ---
    overall_score, quality_tier = calculate_overall_score_hoodie(internal_scores, modifiers_mult)

    # --- User-facing metrics (1-5) ---
    shrinkage_score, shrinkage_exp = calculate_shrinkage_hoodie(
        materials_structured, hoodie_type, special, gsm
    )
    pilling_score, pilling_exp = calculate_pilling_hoodie(
        materials_structured, fleece_type, gsm, anti_pill
    )
    longevity_score, longevity_exp, estimated_washes, estimated_wears = calculate_longevity_hoodie(
        overall_score, hoodie_type, fleece_type, gsm, construction
    )
    value_score, value_exp = calculate_value_hoodie(
        price, estimated_washes, brand_score, overall_score
    )
    care_score, care_exp = calculate_care_hoodie(
        materials_structured, hoodie_type, fleece_type, special
    )

    scores = {
        "shrinkage": shrinkage_score,
        "pilling": pilling_score,
        "longevity": longevity_score,
        "value": value_score,
        "care": care_score,
    }

    # Cost per wear
    cost_per_wear = None
    if price and estimated_wears:
        cost_per_wear = round(price / estimated_wears, 2)

    # Transparency
    transparency_score, data_confidence, transparency_exp, ask_cs = calculate_transparency_hoodie(
        gsm, construction, fleece_type, hoodie_type, materials_structured, brand_info, origin
    )

    # Red flags
    red_flags = detect_red_flags_hoodie(
        materials_structured, gsm, price, fleece_type, construction
    )

    # Value outliers (use normalized brand name for sub-line matching)
    value_notes = detect_value_outliers_hoodie(brand_normalized, price, overall_score)

    # Failure modes
    failure_modes = estimate_failure_modes_hoodie(
        hoodie_type, fleece_type, gsm, materials_structured, construction
    )

    # Care impact
    care_impact = calculate_care_impact_hoodie(
        estimated_washes, materials_structured, fleece_type, price
    )

    # Compile warnings
    warnings = red_flags.copy()
    warnings.extend(value_notes)

    if transparency_score <= 3:
        warnings.append(
            f"\u26a0\ufe0f TRANSPARENCY: {transparency_score}/10 \u2014 "
            "Brand provides minimal quality information"
        )

    return {
        "garment_type": "hoodie",
        "metric_definitions": HOODIE_METRIC_DEFINITIONS,
        "scores": scores,
        "overall_score": overall_score,
        "quality_tier": quality_tier,
        "transparency_score": transparency_score,
        "data_confidence": data_confidence,
        "cost_per_wear": cost_per_wear,
        "estimated_washes": estimated_washes,
        "estimated_wears": estimated_wears,
        "explanations": {
            "shrinkage": shrinkage_exp,
            "pilling": pilling_exp,
            "longevity": longevity_exp,
            "value": value_exp,
            "care": care_exp,
            "transparency": transparency_exp,
        },
        "warnings": warnings,
        "ask_customer_service": ask_cs,
        "failure_modes": failure_modes,
        "care_impact": care_impact,
        "metadata": {
            "brand_name": brand_normalized,
            "brand_tier_score": brand_score,
            "gsm": gsm,
            "fleece_type": fleece_type,
            "hoodie_type": hoodie_type,
            "construction_features": construction,
            "special_construction": special,
            "origin": origin,
            "anti_pill": anti_pill,
            "modifiers_applied": {
                "hoodie_type": type_mult if type_mult != 1.0 else None,
                "fleece_type": fleece_mult if fleece_mult != 1.0 else None,
                "reverse_weave": 1.10 if special.get("reverse_weave") else None,
                "garment_dyed": 1.05 if special.get("garment_dyed") else None,
                "combined": round(modifiers_mult, 3) if modifiers_mult != 1.0 else None,
            },
        },
    }


def _empty_evaluation() -> Dict:
    """Return evaluation for products with no usable data."""
    return {
        "garment_type": "hoodie",
        "metric_definitions": HOODIE_METRIC_DEFINITIONS,
        "scores": {
            "shrinkage": None,
            "pilling": None,
            "longevity": None,
            "value": None,
            "care": None,
        },
        "overall_score": None,
        "quality_tier": "unknown",
        "transparency_score": 0,
        "data_confidence": "none",
        "cost_per_wear": None,
        "estimated_washes": None,
        "estimated_wears": None,
        "explanations": {
            "error": "Insufficient data: No materials or brand information available",
            "transparency": "No data: Cannot evaluate without material composition or brand",
        },
        "warnings": ["Unable to evaluate: missing materials and brand data"],
        "ask_customer_service": [
            "What is the fabric composition?",
            "What is the fabric weight in GSM or oz?",
            "Is it French terry or brushed fleece?",
        ],
        "failure_modes": [],
        "care_impact": {},
        "metadata": {},
    }


def main():
    """CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Evaluate hoodie quality")
    parser.add_argument("--json-file", help="Path to product JSON file")
    parser.add_argument("--stdin", action="store_true", help="Read JSON from stdin")

    args = parser.parse_args()

    if args.json_file:
        with open(args.json_file, 'r', encoding='utf-8') as f:
            product_data = json.load(f)
    elif args.stdin:
        product_data = json.load(sys.stdin)
    else:
        print("Error: Specify --json-file or --stdin")
        sys.exit(1)

    result = evaluate_hoodie(product_data)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
