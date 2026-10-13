"""
Jeans/Denim Quality Evaluation Engine

Evaluates jeans quality using research-backed metrics including:
- Fabric composition (cotton %, elastane %, polyester presence)
- Denim weight (oz/yd²)
- Construction details (selvage, chain stitch, rivets, bar tacks)
- Brand/manufacturing tier
- Price signal (capped — price ≠ quality)

Post-score modifiers for fit type, wash treatment, rise, and gender.

User-facing metrics (1-5 each):
1. Stretch retention — Will they stretch out?
2. Longevity — How long will they last?
3. Fade quality — Will they fade well?
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
    # Luxury heritage (90)
    "iron heart": 90, "pure blue japan": 90, "momotaro": 90,
    "samurai jeans": 90, "the real mccoys": 90, "oni denim": 90,
    "the flat head": 90, "studio dartisan": 90, "full count": 90,
    "sugar cane": 90,
    # Heritage premium top (82)
    "3sixteen": 82, "rogue territory": 82, "left field nyc": 82,
    # Heritage premium (75)
    "nudie jeans": 75, "nudie": 75, "naked and famous": 75,
    "naked & famous": 75, "apc": 75, "a.p.c.": 75, "edwin": 75,
    # Levi's sub-lines (70)
    "levis made and crafted": 70, "levis made & crafted": 70,
    "levis vintage clothing": 70, "levis lvc": 70,
    # Quality mainstream (58-60)
    "levis": 58, "levi's": 58, "wrangler": 60, "carhartt": 60,
    "dickies": 60, "lee": 58,
    # Mid-value (55)
    "buck mason": 55, "everlane": 55, "madewell": 55,
    # Budget standouts (48)
    "gap": 48, "uniqlo": 48, "abercrombie": 48,
    "abercrombie & fitch": 48,
    # Mall brands (42)
    "american eagle": 42, "banana republic": 42, "j crew": 42,
    "j.crew": 42,
    # Budget (30)
    "old navy": 30, "hollister": 30, "target": 30,
    "goodfellow": 30, "goodfellow & co": 30,
    # Fast fashion (25)
    "h&m": 25, "hm": 25, "zara": 25, "asos": 25,
    # Ultra fast fashion (18)
    "shein": 18, "boohoo": 18, "fashion nova": 18, "forever 21": 18,
    "prettylittlething": 18,
    # Fashion premium (comfort focus, 50-55)
    "ag": 52, "ag jeans": 52, "citizens of humanity": 52,
    "paige": 50, "7 for all mankind": 50, "rag & bone": 52,
    "rag and bone": 52, "frame": 50, "dl1961": 50, "joes jeans": 48,
    "joe's jeans": 48, "agolde": 52,
}

# Brand default specs (inferred when listing lacks detail)
BRAND_DEFAULT_SPECS = {
    "iron heart": {"weight_oz": 21, "stretch_pct": 0, "lifespan_years": 15},
    "pure blue japan": {"weight_oz": 14, "stretch_pct": 0, "lifespan_years": 10},
    "momotaro": {"weight_oz": 15, "stretch_pct": 0, "lifespan_years": 10},
    "samurai jeans": {"weight_oz": 19, "stretch_pct": 0, "lifespan_years": 15},
    "3sixteen": {"weight_oz": 14.5, "stretch_pct": 0, "lifespan_years": 8},
    "nudie jeans": {"weight_oz": 12.5, "stretch_pct": 0, "lifespan_years": 7},
    "nudie": {"weight_oz": 12.5, "stretch_pct": 0, "lifespan_years": 7},
    "naked and famous": {"weight_oz": 13, "stretch_pct": 0, "lifespan_years": 7},
    "naked & famous": {"weight_oz": 13, "stretch_pct": 0, "lifespan_years": 7},
    "apc": {"weight_oz": 13, "stretch_pct": 0, "lifespan_years": 5},
    "a.p.c.": {"weight_oz": 13, "stretch_pct": 0, "lifespan_years": 5},
    "levis": {"weight_oz": 12, "stretch_pct": 1, "lifespan_years": 2},
    "levi's": {"weight_oz": 12, "stretch_pct": 1, "lifespan_years": 2},
    "wrangler": {"weight_oz": 14, "stretch_pct": 0, "lifespan_years": 4},
    "uniqlo": {"weight_oz": 13, "stretch_pct": 0, "lifespan_years": 3},
    "gap": {"weight_oz": 12, "stretch_pct": 2, "lifespan_years": 2},
    "h&m": {"weight_oz": 10, "stretch_pct": 2, "lifespan_years": 1},
    "zara": {"weight_oz": 11, "stretch_pct": 2, "lifespan_years": 1.5},
    "shein": {"weight_oz": 9, "stretch_pct": 3, "lifespan_years": 0.5},
    "buck mason": {"weight_oz": 13.25, "stretch_pct": 0, "lifespan_years": 4},
}

DENIM_WEIGHT_RANGES = {
    "ultra_heavy": (16, 32, 10, "Ultra-heavyweight denim (16oz+)"),
    "heavy": (14, 16, 8, "Heavy denim (14-16oz)"),
    "mid": (12, 14, 6, "Mid-weight denim (12-14oz)"),
    "standard": (10, 12, 4, "Standard weight (10-12oz)"),
    "light": (8, 10, 3, "Lightweight denim (8-10oz)"),
    "ultra_light": (0, 8, 2, "Ultra-lightweight (<8oz)"),
}

CONSTRUCTION_SIGNALS_JEANS = {
    "selvage": {
        "boost": 2.0,
        "keywords": ["selvage", "selvedge", "self-edge", "self edge", "shuttle loom"],
    },
    "chain_stitch": {
        "boost": 1.0,
        "keywords": ["chain stitch", "chain-stitch", "chainstitch", "union special"],
    },
    "bar_tacks": {
        "boost": 0.5,
        "keywords": ["bar tack", "bar-tack", "bartack", "bar tacked", "reinforced stress"],
    },
    "rivets": {
        "boost": 0.5,
        "keywords": ["copper rivet", "brass rivet", "riveted", "rivet"],
    },
    "button_fly": {
        "boost": 0.3,
        "keywords": ["button fly", "button-fly"],
    },
    "ykk": {
        "boost": 0.2,
        "keywords": ["ykk"],
    },
}

FIT_MODIFIERS = {
    "super skinny": 0.65,
    "skinny": 0.70,
    "slim tapered": 0.87,
    "slim": 0.85,
    "tapered": 0.90,
    "straight": 1.00,
    "regular": 1.00,
    "bootcut": 1.00,
    "relaxed tapered": 1.10,
    "relaxed": 1.15,
    "loose": 1.10,
    "wide leg": 1.05,
    "wide": 1.05,
}

TREATMENT_MODIFIERS = {
    "raw": 1.10,
    "rigid": 1.10,
    "unwashed": 1.10,
    "dry": 1.08,
    "one wash": 1.05,
    "one-wash": 1.05,
    "rinsed": 1.00,
    "rinse wash": 1.00,
    "light wash": 1.00,
    "stone wash": 0.90,
    "stonewash": 0.90,
    "acid wash": 0.80,
    "distressed": 0.70,
    "destroyed": 0.60,
    "ripped": 0.65,
}

RISE_MODIFIERS = {
    "low": 0.90,
    "mid": 1.00,
    "regular": 1.00,
    "high": 1.05,
}

MILL_NAMES = [
    "kaihara", "kuroki", "collect", "nihon menpu",
    "candiani", "cone mills", "white oak", "vidalia mills",
    "kurabo", "toyoshima",
]

OUTLET_RETAILERS = [
    "nordstrom rack", "tj maxx", "marshalls", "ross",
    "off fifth", "last call", "outlet", "off-price",
]

LIFESPAN_BENCHMARKS = {
    # (min_washes, max_washes, min_wears, max_wears)
    "ultra_fast_fashion": (15, 30, 30, 80),
    "fast_fashion": (20, 50, 50, 150),
    "budget": (50, 120, 100, 250),
    "mid_range": (80, 200, 200, 400),
    "premium": (100, 300, 300, 600),
    "heritage": (200, 500, 500, 1000),
}

# Metric definitions for UI rendering
JEANS_METRIC_DEFINITIONS = [
    {
        "key": "stretch_retention",
        "icon": "💧",  # 💧
        "label": "Will they stretch out?",
        "left_label": "Stretch out fast",
        "right_label": "Holds shape",
        "max_score": 5
    },
    {
        "key": "longevity",
        "icon": "👖",  # 👖
        "label": "How long will they last?",
        "left_label": "6 months",
        "right_label": "10+ years",
        "max_score": 5
    },
    {
        "key": "fade_quality",
        "icon": "🎨",  # 🎨
        "label": "Will they fade well?",
        "left_label": "Patchy fading",
        "right_label": "Beautiful fades",
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

def parse_denim_weight(text: str) -> Optional[float]:
    """Parse denim weight in oz from text."""
    text_lower = text.lower()
    # Patterns: "14oz", "14 oz", "14oz/yd", "14 oz/yd²", "14-oz", "14 ounce"
    patterns = [
        r'(\d+(?:\.\d+)?)\s*(?:oz|ounce)',
        r'(\d+(?:\.\d+)?)\s*-\s*oz',
    ]
    for pattern in patterns:
        match = re.search(pattern, text_lower)
        if match:
            return float(match.group(1))
    return None


def detect_construction_jeans(text: str) -> Dict[str, bool]:
    """Detect jeans construction features from text."""
    text_lower = text.lower()
    features = {}
    for feature, config in CONSTRUCTION_SIGNALS_JEANS.items():
        features[feature] = any(kw in text_lower for kw in config["keywords"])
    return features


def detect_fit_type(text: str) -> str:
    """Detect fit type from product name/text. Returns fit name or 'unknown'."""
    text_lower = text.lower()
    # Check multi-word fits first (more specific)
    for fit in ["super skinny", "slim tapered", "relaxed tapered", "wide leg"]:
        if fit in text_lower:
            return fit
    # Then single-word fits
    for fit in ["skinny", "slim", "tapered", "straight", "regular",
                "bootcut", "relaxed", "loose", "wide"]:
        if fit in text_lower:
            return fit
    return "unknown"


def detect_treatment(text: str) -> str:
    """Detect wash/treatment type from text."""
    text_lower = text.lower()
    # Check multi-word treatments first
    for treatment in ["one wash", "one-wash", "light wash", "stone wash",
                      "stonewash", "acid wash", "rinse wash"]:
        if treatment in text_lower:
            return treatment.replace("-", " ")
    # Single-word treatments
    for treatment in ["raw", "rigid", "unwashed", "dry", "rinsed",
                      "distressed", "destroyed", "ripped"]:
        if treatment in text_lower:
            return treatment
    # Unsanforized/shrink-to-fit implies raw
    if re.search(r'shrink.to.fit|stf\b|unsanforized|loomstate', text_lower):
        return "raw"
    return "unknown"


def detect_rise(text: str) -> str:
    """Detect rise type from text."""
    text_lower = text.lower()
    if re.search(r'\blow[\s-]?rise\b', text_lower):
        return "low"
    if re.search(r'\bhigh[\s-]?rise\b|\bhigh[\s-]?waist\b', text_lower):
        return "high"
    if re.search(r'\bmid[\s-]?rise\b|\bregular[\s-]?rise\b', text_lower):
        return "mid"
    return "unknown"


def detect_brand(product_name: str, brand: str) -> Tuple[str, Optional[Dict]]:
    """
    Normalize brand name and look up in database.
    Returns (normalized_brand, brand_info_or_None).
    """
    # Combine sources, prefer explicit brand field
    raw = (brand or product_name or "").lower().strip()

    # Check for Levi's sub-lines FIRST (critical differentiation)
    combined = f"{product_name} {brand}".lower()
    if "levi" in combined:
        if any(sub in combined for sub in ["made & crafted", "made and crafted"]):
            return "levis made and crafted", {"default_score": 70}
        if any(sub in combined for sub in ["vintage clothing", "lvc"]):
            return "levis vintage clothing", {"default_score": 70}

    # Normalize common variations
    normalized = raw.replace("'", "").replace("'", "").replace(".", "").strip()

    # Direct lookup
    if normalized in BRAND_DEFAULT_SCORES:
        return normalized, {"default_score": BRAND_DEFAULT_SCORES[normalized]}

    # Partial match (brand name contained in lookup key or vice versa)
    for key, score in BRAND_DEFAULT_SCORES.items():
        if key in normalized or normalized in key:
            return key, {"default_score": score}

    # Try from product name if brand field was empty
    if not brand and product_name:
        name_lower = product_name.lower().replace("'", "").replace("'", "")
        for key, score in BRAND_DEFAULT_SCORES.items():
            if key in name_lower:
                return key, {"default_score": score}

    return normalized or "unknown", None


def detect_gender(product_name: str) -> Optional[str]:
    """Detect gender from product name."""
    text_lower = product_name.lower()
    if any(kw in text_lower for kw in ["women's", "womens", "women ", "ladies"]):
        return "women"
    if any(kw in text_lower for kw in ["men's", "mens", "men "]):
        return "men"
    return None


def detect_mill(text: str) -> Optional[str]:
    """Detect premium mill name from text."""
    text_lower = text.lower()
    for mill in MILL_NAMES:
        if mill in text_lower:
            return mill
    return None


def detect_outlet(text: str) -> bool:
    """Detect if purchase is from outlet/off-price retailer."""
    text_lower = text.lower()
    return any(retailer in text_lower for retailer in OUTLET_RETAILERS)


def detect_sanforization(text: str) -> Optional[str]:
    """Detect sanforization status."""
    text_lower = text.lower()
    if "unsanforized" in text_lower or "loomstate" in text_lower:
        return "unsanforized"
    if "sanforized" in text_lower:
        return "sanforized"
    if re.search(r'shrink.to.fit|stf\b', text_lower):
        return "unsanforized"
    return None


# ============================================================
# INTERNAL SCORING FUNCTIONS (0-10 each)
# ============================================================

def score_fabric_composition(
    materials_structured: List[Dict],
    materials_text: str,
    brand_score: Optional[float] = None
) -> Tuple[float, str]:
    """Score fabric composition (0-10). Weight: 30%."""
    cotton_pct = get_material_percent(materials_structured, "cotton")
    elastane_pct = get_material_percent(materials_structured, "spandex") + \
                   get_material_percent(materials_structured, "elastane")
    poly_pct = get_material_percent(materials_structured, "polyester")

    # No composition data — infer from brand reputation if available
    if not materials_structured or cotton_pct == 0:
        if brand_score is not None and brand_score >= 8.0:
            return 7.0, "Composition not disclosed — heritage brand typically uses 100% cotton"
        if brand_score is not None and brand_score >= 7.0:
            return 6.5, "Composition not disclosed — premium brand typically uses high cotton content"
        if brand_score is not None and brand_score >= 5.5:
            return 5.0, "Composition not disclosed — mainstream brand, likely cotton/elastane blend"
        return 3.0, "No fabric composition available"

    # 98-100% cotton (pure denim gold standard)
    if cotton_pct >= 98 and elastane_pct == 0:
        return 10.0, f"{cotton_pct:.0f}% cotton — pure denim, maximum durability and fade potential"

    # 95-99% cotton with minimal stretch (1-2% elastane)
    if cotton_pct >= 95 and elastane_pct <= 2:
        return 8.0, f"{cotton_pct:.0f}% cotton / {elastane_pct:.0f}% elastane — minimal stretch, good durability"

    # 90-97% cotton with moderate stretch
    if cotton_pct >= 90 and elastane_pct <= 3:
        score = 6.0
        if elastane_pct > 2:
            score = 5.5
            return score, f"{cotton_pct:.0f}% cotton / {elastane_pct:.0f}% elastane — moderate stretch, loses elasticity after ~50 washes at 40°C"
        return score, f"{cotton_pct:.0f}% cotton / {elastane_pct:.0f}% elastane — moderate stretch content"

    # High polyester (>10%)
    if poly_pct > 10:
        score = 3.0
        if poly_pct > 20:
            score = 2.0
        return score, f"{poly_pct:.0f}% polyester — fast-fashion construction, reduced breathability and fade character"

    # High stretch (>3% elastane)
    if elastane_pct > 3:
        score = 3.5
        if elastane_pct > 5:
            score = 2.0
        return score, f"{elastane_pct:.0f}% elastane — high stretch content, will lose shape over time"

    # Below 90% cotton
    if cotton_pct < 90:
        return 4.0, f"{cotton_pct:.0f}% cotton — below ideal cotton content for denim durability"

    return 5.0, f"{cotton_pct:.0f}% cotton blend"


def score_denim_weight(
    materials_text: str,
    brand_name: str = ""
) -> Tuple[float, str]:
    """Score denim weight (0-10). Weight: 25%."""
    weight = parse_denim_weight(materials_text)

    # Infer from brand if not stated
    if weight is None:
        brand_lower = brand_name.lower().replace("'", "").replace("'", "")
        specs = BRAND_DEFAULT_SPECS.get(brand_lower)
        if specs:
            weight = specs.get("weight_oz")
            if weight:
                return _score_weight(weight), f"~{weight}oz (inferred from {brand_name} defaults) — weight not disclosed"

        return 3.0, "Denim weight not disclosed — cannot assess fabric heft"

    return _score_weight(weight), f"{weight}oz denim"


def _score_weight(weight: float) -> float:
    """Convert oz weight to 0-10 score."""
    if weight >= 16:
        return 10.0
    elif weight >= 14:
        return 8.0
    elif weight >= 12:
        return 6.0
    elif weight >= 10:
        return 4.0
    elif weight >= 8:
        return 3.0
    else:
        return 2.0


def score_construction(materials_text: str, brand_score: Optional[float] = None) -> Tuple[float, str]:
    """Score construction details (0-10). Weight: 20%."""
    features = detect_construction_jeans(materials_text)
    found = [f for f, present in features.items() if present]

    if len(found) == 0:
        # Infer from brand reputation when no construction details disclosed
        if brand_score is not None and brand_score >= 8.0:
            return 6.0, "Construction not disclosed — heritage brand typically uses selvage/chain stitch"
        if brand_score is not None and brand_score >= 7.0:
            return 4.5, "Construction not disclosed — premium brand, likely quality construction"
        if brand_score is not None and brand_score >= 5.5:
            return 3.5, "Construction not disclosed — mainstream brand, standard construction assumed"
        return 2.0, "No construction details disclosed"

    # Score based on number + quality of features
    score = 2.0
    details = []

    if features.get("selvage"):
        score += 3.0
        details.append("selvage (shuttle loom)")
    if features.get("chain_stitch"):
        score += 2.0
        details.append("chain stitch hem")
    if features.get("bar_tacks"):
        score += 1.0
        details.append("bar-tacked stress points")
    if features.get("rivets"):
        score += 1.0
        details.append("riveted")
    if features.get("button_fly"):
        score += 0.5
        details.append("button fly")
    if features.get("ykk"):
        score += 0.5
        details.append("YKK zipper")

    score = min(10.0, score)
    explanation = f"Construction: {', '.join(details)}"
    return score, explanation


def score_brand_tier(brand_name: str, product_name: str) -> Tuple[float, str]:
    """Score brand/manufacturer tier (0-10). Weight: 15%."""
    normalized, brand_info = detect_brand(product_name, brand_name)

    if brand_info is None:
        return 4.0, f"Unknown brand '{brand_name or 'unspecified'}' — cannot assess manufacturing quality"

    default_score = brand_info["default_score"]
    # Convert 0-100 to 0-10
    score = default_score / 10.0

    # Determine tier description
    if default_score >= 85:
        tier_desc = "luxury heritage"
    elif default_score >= 70:
        tier_desc = "heritage premium"
    elif default_score >= 55:
        tier_desc = "quality mainstream"
    elif default_score >= 45:
        tier_desc = "mid-range"
    elif default_score >= 35:
        tier_desc = "budget"
    elif default_score >= 22:
        tier_desc = "fast fashion"
    else:
        tier_desc = "ultra fast fashion"

    return score, f"{normalized.title()} — {tier_desc} tier"


def score_price_signal(price: Optional[float]) -> Tuple[float, str]:
    """Score price signal (0-10, CAPPED at 8). Weight: 10%."""
    if price is None:
        return 4.0, "No price available"

    if price >= 200:
        return 8.0, f"${price:.0f} — premium price point (capped: price ≠ quality)"
    elif price >= 100:
        return 7.0, f"${price:.0f} — mid-premium price"
    elif price >= 60:
        return 5.0, f"${price:.0f} — mid-range price"
    elif price >= 30:
        return 3.0, f"${price:.0f} — budget price"
    else:
        return 2.0, f"${price:.0f} — ultra-budget price"


# ============================================================
# POST-SCORE MODIFIERS
# ============================================================

def apply_modifiers(
    base_score: float,
    fit: str,
    treatment: str,
    rise: str,
    gender: Optional[str]
) -> Tuple[float, List[str]]:
    """Apply fit, treatment, rise, and gender modifiers to base score."""
    modified = base_score
    notes = []

    # Fit modifier
    fit_mult = FIT_MODIFIERS.get(fit, 1.0)
    if fit_mult != 1.0:
        modified *= fit_mult
        if fit_mult < 1.0:
            notes.append(f"{fit} fit reduces lifespan ({fit_mult:.0%} of baseline)")
        else:
            notes.append(f"{fit} fit extends lifespan ({fit_mult:.0%} of baseline)")

    # Treatment modifier
    treatment_mult = TREATMENT_MODIFIERS.get(treatment, 1.0)
    if treatment_mult != 1.0:
        modified *= treatment_mult
        if treatment_mult > 1.0:
            notes.append(f"{treatment} denim starts stronger ({treatment_mult:.0%})")
        else:
            notes.append(f"{treatment} treatment weakens fabric ({treatment_mult:.0%})")

    # Rise modifier
    rise_mult = RISE_MODIFIERS.get(rise, 1.0)
    if rise_mult != 1.0:
        modified *= rise_mult
        if rise_mult < 1.0:
            notes.append(f"{rise}-rise increases crotch stress")

    # Women's jeans adjustment
    if gender == "women":
        modified *= 0.85
        notes.append("Women's jeans typically use thinner fabric and tighter fits (×0.85)")

    return modified, notes


# ============================================================
# USER-FACING METRIC FUNCTIONS (1-5 each)
# ============================================================

def calculate_stretch_retention(
    materials_structured: List[Dict],
    fit: str,
    construction: Dict[str, bool]
) -> Tuple[float, str]:
    """Calculate stretch retention score (1-5). Higher = holds shape better."""
    elastane_pct = get_material_percent(materials_structured, "spandex") + \
                   get_material_percent(materials_structured, "elastane")
    cotton_pct = get_material_percent(materials_structured, "cotton")
    poly_pct = get_material_percent(materials_structured, "polyester")

    # No stretch content — pure cotton holds shape perfectly
    if elastane_pct == 0 and cotton_pct >= 98:
        return 5.0, "100% cotton — no stretch to lose, holds shape permanently"

    # Minimal stretch (1-2%)
    if elastane_pct <= 2:
        score = 4.0
        explanation = f"{elastane_pct:.0f}% elastane — minimal stretch, good shape retention"
        # Tight fits stress stretch more
        if fit in ["skinny", "super skinny"]:
            score -= 0.5
            explanation += f". {fit} fit puts more stress on stretch fibers"
        return max(1.0, score), explanation

    # Moderate stretch (2-3%)
    if elastane_pct <= 3:
        score = 3.0
        explanation = f"{elastane_pct:.0f}% elastane — moderate stretch, loses elasticity after ~50 washes"
        if fit in ["skinny", "super skinny"]:
            score -= 0.5
        return max(1.0, score), explanation

    # High stretch (3-5%)
    if elastane_pct <= 5:
        score = 2.0
        explanation = f"{elastane_pct:.0f}% elastane — will stretch out noticeably, especially at knees and waist"
        return score, explanation

    # Extreme stretch (>5%)
    return 1.5, f"{elastane_pct:.0f}% elastane — extreme stretch content, expect significant bagging"


def calculate_longevity_jeans(
    overall_score: float,
    brand_name: str,
    fit: str,
    treatment: str,
    weight_oz: Optional[float],
    construction: Dict[str, bool]
) -> Tuple[float, str, int]:
    """
    Calculate longevity score (1-5) and estimated washes.
    Returns (score, explanation, estimated_washes).
    """
    # Base lifespan from overall score
    if overall_score >= 80:
        base_washes = 300
        tier = "heritage"
    elif overall_score >= 65:
        base_washes = 180
        tier = "premium"
    elif overall_score >= 50:
        base_washes = 100
        tier = "mid_range"
    elif overall_score >= 35:
        base_washes = 60
        tier = "budget"
    else:
        base_washes = 30
        tier = "fast_fashion"

    # Weight bonus
    if weight_oz and weight_oz >= 16:
        base_washes = int(base_washes * 1.3)
    elif weight_oz and weight_oz >= 14:
        base_washes = int(base_washes * 1.15)

    # Construction bonus
    if construction.get("selvage"):
        base_washes = int(base_washes * 1.1)

    # Fit penalty
    fit_mult = FIT_MODIFIERS.get(fit, 1.0)
    base_washes = int(base_washes * fit_mult)

    # Treatment modifier
    treatment_mult = TREATMENT_MODIFIERS.get(treatment, 1.0)
    base_washes = int(base_washes * treatment_mult)

    estimated_washes = max(15, base_washes)

    # Convert to 1-5 score
    if estimated_washes >= 250:
        score = 5.0
    elif estimated_washes >= 150:
        score = 4.0
    elif estimated_washes >= 80:
        score = 3.5
    elif estimated_washes >= 50:
        score = 3.0
    elif estimated_washes >= 30:
        score = 2.0
    else:
        score = 1.5

    # Build explanation
    parts = [f"~{estimated_washes} washes estimated"]
    if weight_oz:
        parts.append(f"{weight_oz}oz denim")
    if construction.get("selvage"):
        parts.append("selvage construction")
    if fit != "unknown":
        parts.append(f"{fit} fit")

    explanation = ". ".join(parts)
    return score, explanation, estimated_washes


def calculate_fade_quality(
    treatment: str,
    materials_structured: List[Dict],
    weight_oz: Optional[float],
    construction: Dict[str, bool],
    materials_text: str
) -> Tuple[float, str]:
    """Calculate fade quality score (1-5). Higher = better fade potential."""
    cotton_pct = get_material_percent(materials_structured, "cotton")
    poly_pct = get_material_percent(materials_structured, "polyester")

    # Base score from treatment
    if treatment in ["raw", "rigid", "unwashed", "dry"]:
        score = 5.0
        explanation = "Raw denim — develops unique personalized fades over time"
    elif treatment in ["one wash", "one-wash"]:
        score = 4.5
        explanation = "One-wash — retains most raw character with shrinkage removed"
    elif treatment in ["rinsed", "rinse wash", "light wash"]:
        score = 3.5
        explanation = "Lightly washed — some fade potential remains"
    elif treatment in ["stone wash", "stonewash"]:
        score = 2.5
        explanation = "Stone-washed — pre-faded, limited further evolution"
    elif treatment in ["distressed", "destroyed", "ripped"]:
        score = 1.5
        explanation = "Distressed — pre-damaged, minimal natural fade development"
    elif treatment in ["acid wash"]:
        score = 1.0
        explanation = "Acid-washed — chemically altered, no natural fade path"
    else:
        score = 3.0
        explanation = "Wash treatment unknown — moderate fade potential assumed"

    # Cotton percentage bonus/penalty
    if cotton_pct >= 98:
        score = min(5.0, score + 0.3)
        explanation += ". High cotton content absorbs indigo well"
    elif poly_pct > 10:
        score = max(1.0, score - 0.5)
        explanation += ". Polyester reduces indigo absorption and fade character"

    # Heavyweight denim fades differently
    if weight_oz and weight_oz >= 16:
        explanation += ". Heavyweight denim produces dramatic high-contrast fades"
    elif weight_oz and weight_oz >= 14:
        explanation += ". Mid-heavy weight gives good fade definition"

    # Selvage bonus (shuttle-loom character)
    if construction.get("selvage"):
        score = min(5.0, score + 0.2)
        explanation += ". Selvage weave adds natural texture variation"

    # Mill detection (premium indigo)
    mill = detect_mill(materials_text)
    if mill:
        score = min(5.0, score + 0.2)
        explanation += f". {mill.title()} mill denim known for quality indigo"

    return max(1.0, min(5.0, score)), explanation


def calculate_value_jeans(
    price: Optional[float],
    estimated_washes: int,
    brand_score: float,
    overall_score: float
) -> Tuple[Optional[float], str]:
    """Calculate value score (1-5). Detects outliers."""
    if price is None:
        return None, "No price available"

    cost_per_wear = price / max(1, estimated_washes)

    # Detect exceptional value
    if overall_score >= 45 and price < 50:
        return 5.0, f"Exceptional value: ${cost_per_wear:.2f}/wear at ${price:.0f} — quality exceeds price"

    if overall_score >= 60 and price < 100:
        return 4.5, f"Great value: ${cost_per_wear:.2f}/wear — ${price:.0f} for premium-tier quality"

    # Standard value calculation
    if cost_per_wear < 0.30:
        return 4.0, f"Excellent value: ${cost_per_wear:.2f}/wear (${price:.0f} for {estimated_washes} washes)"
    elif cost_per_wear < 0.60:
        return 3.5, f"Good value: ${cost_per_wear:.2f}/wear"
    elif cost_per_wear < 1.00:
        return 3.0, f"Fair value: ${cost_per_wear:.2f}/wear"
    elif cost_per_wear < 2.00:
        return 2.0, f"Below average value: ${cost_per_wear:.2f}/wear"
    else:
        return 1.5, f"Poor value: ${cost_per_wear:.2f}/wear (${price:.0f} for only {estimated_washes} estimated washes)"


def calculate_care_jeans(
    treatment: str,
    materials_structured: List[Dict],
    sanforization: Optional[str]
) -> Tuple[float, str]:
    """Calculate care difficulty score (1-5). Higher = easier care."""
    elastane_pct = get_material_percent(materials_structured, "spandex") + \
                   get_material_percent(materials_structured, "elastane")

    # Raw/rigid denim — high maintenance
    if treatment in ["raw", "rigid", "unwashed", "dry"]:
        score = 2.0
        explanation = "Raw denim requires patience: avoid washing for 3-6 months to develop fades"
        if sanforization == "unsanforized":
            score = 1.5
            explanation += ". Unsanforized — expect up to 10% shrinkage on first soak. Size up 1-2 sizes"
        return score, explanation

    # One-wash — moderate care
    if treatment in ["one wash", "one-wash"]:
        return 3.0, "One-wash: shrinkage already removed. Wash cold, hang dry every 5-10 wears"

    # Standard washed denim — easier
    if treatment in ["stone wash", "stonewash", "light wash", "rinsed", "rinse wash"]:
        score = 4.0
        explanation = "Pre-washed: standard machine wash cold, hang dry preferred"
        if elastane_pct > 2:
            score = 3.5
            explanation += f". {elastane_pct:.0f}% elastane — avoid tumble drying to preserve stretch"
        return score, explanation

    # Distressed — easy care but fragile
    if treatment in ["distressed", "destroyed", "ripped"]:
        return 3.5, "Distressed: machine washable but turn inside-out to prevent further damage"

    # Unknown treatment — assume standard
    score = 3.5
    explanation = "Standard care: machine wash cold, hang dry for best results"
    if elastane_pct > 2:
        score = 3.0
        explanation += f". {elastane_pct:.0f}% elastane — heat destroys stretch, always air dry"
    return score, explanation


# ============================================================
# TRANSPARENCY & RED FLAGS
# ============================================================

def calculate_transparency_jeans(
    weight_oz: Optional[float],
    construction: Dict[str, bool],
    treatment: str,
    mill: Optional[str],
    fit: str,
    materials_structured: List[Dict],
    brand_info: Optional[Dict]
) -> Tuple[int, str, str, List[str]]:
    """
    Calculate transparency score (1-10) for jeans.
    Returns (score, confidence, explanation, ask_cs).
    """
    score = 0
    data_points = []
    ask_cs = []

    # Fabric composition (+2)
    if materials_structured and len(materials_structured) > 0:
        score += 2
        data_points.append("Material composition disclosed")
    else:
        ask_cs.append("What is the fabric composition (cotton %, elastane %)?")

    # Denim weight (+2)
    if weight_oz is not None:
        score += 2
        data_points.append(f"Denim weight ({weight_oz}oz)")
    else:
        ask_cs.append("What is the denim weight in oz/yd²?")

    # Construction details (+2)
    construction_found = sum(1 for v in construction.values() if v)
    if construction_found >= 2:
        score += 2
        data_points.append("Construction details disclosed")
    elif construction_found == 1:
        score += 1
        data_points.append("Partial construction info")
    else:
        ask_cs.append("What construction features are used (selvage, chain stitch, rivets)?")

    # Treatment/wash (+1)
    if treatment != "unknown":
        score += 1
        data_points.append(f"Treatment: {treatment}")

    # Mill/fabric source (+1)
    if mill:
        score += 1
        data_points.append(f"Mill: {mill.title()}")

    # Fit type (+1)
    if fit != "unknown":
        score += 1
        data_points.append(f"Fit: {fit}")

    # Determine confidence
    if score >= 8:
        confidence = "high"
    elif score >= 5:
        confidence = "medium"
    else:
        confidence = "low"

    # Generate explanation
    if score >= 8:
        explanation = f"Excellent transparency ({score}/10): {', '.join(data_points)}"
    elif score >= 6:
        explanation = f"Good transparency ({score}/10): {', '.join(data_points)}"
    elif score >= 4:
        explanation = f"Fair transparency ({score}/10): Basic information disclosed"
    else:
        explanation = f"Poor transparency ({score}/10): Minimal quality information provided"

    return score, confidence, explanation, ask_cs


def detect_red_flags_jeans(
    materials_structured: List[Dict],
    weight_oz: Optional[float],
    price: Optional[float],
    treatment: str,
    construction: Dict[str, bool],
    materials_text: str
) -> List[str]:
    """Detect jeans-specific red flags."""
    red_flags = []
    poly_pct = get_material_percent(materials_structured, "polyester")
    elastane_pct = get_material_percent(materials_structured, "spandex") + \
                   get_material_percent(materials_structured, "elastane")
    cotton_pct = get_material_percent(materials_structured, "cotton")

    # High polyester
    if poly_pct > 20:
        red_flags.append(f"⛔ {poly_pct:.0f}% polyester — not real denim, fast-fashion construction")
    elif poly_pct > 10:
        red_flags.append(f"⚠️ {poly_pct:.0f}% polyester — reduces breathability and fade quality")

    # Extreme stretch
    if elastane_pct > 5:
        red_flags.append(f"⛔ {elastane_pct:.0f}% elastane — will stretch out and bag significantly")
    elif elastane_pct > 3:
        red_flags.append(f"⚠️ {elastane_pct:.0f}% elastane — loses elasticity after ~50 washes")

    # Very lightweight
    if weight_oz and weight_oz < 8:
        red_flags.append(f"⛔ Ultra-lightweight denim ({weight_oz}oz) — expect rapid wear-through")

    # Overpriced for quality
    if price and price > 150 and cotton_pct < 90:
        red_flags.append(f"⚠️ Premium price (${price:.0f}) with budget composition ({cotton_pct:.0f}% cotton)")

    # Pre-distressed at premium price
    if treatment in ["distressed", "destroyed", "ripped"] and price and price > 100:
        red_flags.append(f"⚠️ Pre-distressed at ${price:.0f} — paying premium for pre-damaged fabric")

    # Outlet warning
    if detect_outlet(materials_text):
        red_flags.append("⚠️ Outlet/off-price retailer — fabric composition may differ from mainline version")

    return red_flags


def detect_value_outliers(
    brand_name: str,
    price: Optional[float],
    overall_score: float
) -> List[str]:
    """Detect exceptional value or overpriced products."""
    notes = []
    normalized = brand_name.lower().replace("'", "").replace("'", "")

    # Exceptional value brands
    if "uniqlo" in normalized and price and price < 60:
        notes.append("💎 Uniqlo Kaihara denim at budget price — competes with 3-5× priced alternatives")
    if "wrangler" in normalized and price and price < 30:
        notes.append("💎 Wrangler Cowboy Cut — 14oz raw denim at extraordinary value ($25 for 3-5 years)")
    if ("goodfellow" in normalized or "target" in normalized) and price and price < 40:
        notes.append("💎 Target Goodfellow selvedge at budget price — surprisingly good construction")

    # Potentially overpriced (fashion-premium with light denim)
    fashion_premium = ["ag", "ag jeans", "paige", "7 for all mankind", "frame", "dl1961"]
    if any(fp in normalized for fp in fashion_premium) and price and price > 150:
        notes.append("⚠️ Fashion-premium brand — often uses lighter/stretchier denim than heritage brands at similar prices")

    return notes


# ============================================================
# CARE IMPACT
# ============================================================

def calculate_care_impact_jeans(
    estimated_washes: int,
    materials_structured: List[Dict],
    treatment: str,
    price: Optional[float]
) -> Dict:
    """Calculate how care methods affect jeans longevity."""
    elastane_pct = get_material_percent(materials_structured, "spandex") + \
                   get_material_percent(materials_structured, "elastane")

    # Multipliers for denim
    best_mult = 1.5  # Cold infrequent + air dry
    good_mult = 1.2  # Cold regular + air dry
    worst_mult = 0.65  # Hot frequent + tumble dry

    if elastane_pct > 2:
        # Stretch denim is more sensitive to heat
        worst_mult = 0.55
        best_mult = 1.4

    best_washes = int(estimated_washes * best_mult)
    good_washes = int(estimated_washes * good_mult)
    worst_washes = int(estimated_washes * worst_mult)

    scenarios = []
    if price:
        scenarios = [
            {"method": "Cold wash every 5-10 wears + air dry", "impact": "Best",
             "washes": best_washes, "cost_per_wear": round(price / best_washes, 2),
             "description": "Optimal for denim — preserves indigo and structure"},
            {"method": "Cold wash monthly + air dry", "impact": "Good",
             "washes": good_washes, "cost_per_wear": round(price / good_washes, 2),
             "description": "Good balance of hygiene and longevity"},
            {"method": "Warm wash weekly + tumble dry low", "impact": "Standard",
             "washes": estimated_washes, "cost_per_wear": round(price / estimated_washes, 2),
             "description": "Standard care — baseline estimate"},
            {"method": "Hot wash frequent + tumble dry high", "impact": "Worst",
             "washes": worst_washes, "cost_per_wear": round(price / worst_washes, 2),
             "description": "Harsh — rapidly degrades denim fibers and stretch"},
        ]
    else:
        scenarios = [
            {"method": "Cold wash every 5-10 wears + air dry", "impact": "Best",
             "washes": best_washes, "description": "Optimal for denim"},
            {"method": "Cold wash monthly + air dry", "impact": "Good",
             "washes": good_washes, "description": "Good balance"},
            {"method": "Warm wash weekly + tumble dry low", "impact": "Standard",
             "washes": estimated_washes, "description": "Baseline"},
            {"method": "Hot wash frequent + tumble dry high", "impact": "Worst",
             "washes": worst_washes, "description": "Harsh method"},
        ]

    # Recommendations
    recommendations = [
        "Turn inside-out before washing to preserve surface color",
        "Avoid fabric softener — it breaks down fibers and stretch",
    ]

    if treatment in ["raw", "rigid", "unwashed", "dry"]:
        recommendations.insert(0, "Raw denim: wait 3-6 months before first wash for best fades")
        recommendations.append("Spot-clean stains instead of full washing when possible")
        recommendations.append("When ready, soak in cold water in bathtub for 45 min, hang dry")
    elif elastane_pct > 2:
        recommendations.insert(0, f"{elastane_pct:.0f}% elastane — NEVER tumble dry, heat destroys stretch")

    recommendations.append("Wash in cold water only — hot water accelerates indigo loss and shrinkage")

    # Savings
    savings = None
    if price:
        standard_cpw = price / estimated_washes
        best_cpw = price / best_washes
        savings = {
            "cost_per_wear_reduction": round(standard_cpw - best_cpw, 2),
            "additional_washes": best_washes - estimated_washes,
            "total_value_gained": round((standard_cpw - best_cpw) * best_washes, 2),
            "summary": f"Proper denim care adds {best_washes - estimated_washes} washes and saves ${standard_cpw - best_cpw:.2f}/wear"
        }

    return {
        "scenarios": scenarios,
        "recommendations": recommendations,
        "savings": savings,
        "baseline_method": "Warm wash weekly + tumble dry low",
        "best_method": "Cold wash every 5-10 wears + air dry"
    }


# ============================================================
# FAILURE MODES
# ============================================================

def estimate_failure_modes(
    fit: str,
    weight_oz: Optional[float],
    materials_structured: List[Dict],
    treatment: str,
    construction: Dict[str, bool]
) -> List[Dict]:
    """Estimate primary failure modes and risks."""
    modes = []
    elastane_pct = get_material_percent(materials_structured, "spandex") + \
                   get_material_percent(materials_structured, "elastane")

    # Crotch blowout (#1 cause of jean death)
    crotch_risk = "medium"
    crotch_note = "Thigh friction + moisture weakening fibers"
    if fit in ["skinny", "super skinny"]:
        crotch_risk = "high"
        crotch_note = "Tight fit increases thigh friction significantly"
    elif fit in ["relaxed", "loose", "wide"]:
        crotch_risk = "low"
        crotch_note = "Relaxed fit reduces thigh contact"
    if weight_oz and weight_oz >= 14:
        if crotch_risk == "high":
            crotch_risk = "medium"
        crotch_note += f". {weight_oz}oz denim provides extra resistance"

    modes.append({"mode": "Crotch blowout", "risk": crotch_risk, "note": crotch_note})

    # Knee wear
    knee_risk = "medium"
    knee_note = "Bending stress creates honeycomb fractures over time"
    if weight_oz and weight_oz >= 14:
        knee_risk = "low"
        knee_note = f"Heavy denim ({weight_oz}oz) resists knee bags well"
    modes.append({"mode": "Knee wear", "risk": knee_risk, "note": knee_note})

    # Stretch loss (for stretch denim only)
    if elastane_pct > 0:
        stretch_risk = "low" if elastane_pct <= 2 else ("medium" if elastane_pct <= 4 else "high")
        modes.append({
            "mode": "Stretch loss",
            "risk": stretch_risk,
            "note": f"{elastane_pct:.0f}% elastane — heat and time degrade stretch fibers"
        })

    return modes


# ============================================================
# OVERALL SCORE
# ============================================================

def calculate_overall_score_jeans(
    internal_scores: Dict[str, float],
    modifiers_mult: float
) -> Tuple[float, str]:
    """
    Calculate overall score (0-100) from weighted internal scores.
    Internal scores are 0-10, weights sum to 1.0.
    """
    weights = {
        "composition": 0.30,
        "weight": 0.25,
        "construction": 0.20,
        "brand": 0.15,
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

    # Convert 0-10 to 0-100 and apply modifiers
    overall = (weighted_sum / total_weight) * 10 * modifiers_mult
    overall = max(0, min(100, overall))

    # Quality tiers
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

def evaluate_jeans(product_data: Dict) -> Dict:
    """
    Evaluate jeans quality.

    Args:
        product_data: {
            "materials_structured": [...],
            "materials_text": str,
            "price": float or None,
            "brand": str,
            "product_name": str
        }

    Returns:
        Evaluation dict matching t-shirt evaluator shape.
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
    weight_oz = parse_denim_weight(materials_text)
    construction = detect_construction_jeans(materials_text)
    fit = detect_fit_type(combined_text)
    treatment = detect_treatment(combined_text)
    rise = detect_rise(combined_text)
    gender = detect_gender(product_name)
    mill = detect_mill(materials_text)
    sanforization = detect_sanforization(materials_text)
    brand_normalized, brand_info = detect_brand(product_name, brand)

    # Infer weight from brand if not stated
    if weight_oz is None and brand_normalized:
        specs = BRAND_DEFAULT_SPECS.get(brand_normalized)
        if specs:
            weight_oz = specs.get("weight_oz")

    # --- Internal scoring (0-10 each) ---
    # Score brand first so we can use it for inference when specs are missing
    brand_score, brand_exp = score_brand_tier(brand, product_name)
    comp_score, comp_exp = score_fabric_composition(materials_structured, materials_text, brand_score)
    weight_score, weight_exp = score_denim_weight(materials_text, brand)
    const_score, const_exp = score_construction(materials_text, brand_score)
    price_score, price_exp = score_price_signal(price)

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

    fit_mult = FIT_MODIFIERS.get(fit, 1.0)
    if fit_mult != 1.0:
        modifiers_mult *= fit_mult
        modifier_notes.append(f"Fit ({fit}): ×{fit_mult}")

    treatment_mult = TREATMENT_MODIFIERS.get(treatment, 1.0)
    if treatment_mult != 1.0:
        modifiers_mult *= treatment_mult
        modifier_notes.append(f"Treatment ({treatment}): ×{treatment_mult}")

    rise_mult = RISE_MODIFIERS.get(rise, 1.0)
    if rise_mult != 1.0:
        modifiers_mult *= rise_mult
        modifier_notes.append(f"Rise ({rise}): ×{rise_mult}")

    if gender == "women":
        modifiers_mult *= 0.85
        modifier_notes.append("Women's jeans adjustment: ×0.85")

    # --- Overall score ---
    overall_score, quality_tier = calculate_overall_score_jeans(internal_scores, modifiers_mult)

    # --- User-facing metrics (1-5) ---
    stretch_score, stretch_exp = calculate_stretch_retention(
        materials_structured, fit, construction
    )
    longevity_score, longevity_exp, estimated_washes = calculate_longevity_jeans(
        overall_score, brand, fit, treatment, weight_oz, construction
    )
    fade_score, fade_exp = calculate_fade_quality(
        treatment, materials_structured, weight_oz, construction, materials_text
    )
    value_score, value_exp = calculate_value_jeans(
        price, estimated_washes, brand_score, overall_score
    )
    care_score, care_exp = calculate_care_jeans(treatment, materials_structured, sanforization)

    scores = {
        "stretch_retention": stretch_score,
        "longevity": longevity_score,
        "fade_quality": fade_score,
        "value": value_score,
        "care": care_score,
    }

    # Cost per wear
    cost_per_wear = None
    if price and estimated_washes:
        cost_per_wear = round(price / estimated_washes, 2)

    # Transparency
    transparency_score, data_confidence, transparency_exp, ask_cs = calculate_transparency_jeans(
        weight_oz, construction, treatment, mill, fit, materials_structured, brand_info
    )

    # Red flags
    red_flags = detect_red_flags_jeans(
        materials_structured, weight_oz, price, treatment, construction, materials_text
    )

    # Value outliers
    value_notes = detect_value_outliers(brand, price, overall_score)

    # Failure modes
    failure_modes = estimate_failure_modes(
        fit, weight_oz, materials_structured, treatment, construction
    )

    # Care impact
    care_impact = calculate_care_impact_jeans(
        estimated_washes, materials_structured, treatment, price
    )

    # Compile warnings
    warnings = red_flags.copy()
    warnings.extend(value_notes)

    if sanforization == "unsanforized":
        warnings.append("⚠️ Unsanforized denim — expect up to 10% shrinkage. Size up 1-2 sizes")

    if transparency_score <= 3:
        warnings.append(
            f"⚠️ TRANSPARENCY: {transparency_score}/10 — "
            "Brand provides minimal quality information"
        )

    return {
        "garment_type": "jeans",
        "metric_definitions": JEANS_METRIC_DEFINITIONS,
        "scores": scores,
        "overall_score": overall_score,
        "quality_tier": quality_tier,
        "transparency_score": transparency_score,
        "data_confidence": data_confidence,
        "cost_per_wear": cost_per_wear,
        "estimated_washes": estimated_washes,
        "explanations": {
            "stretch_retention": stretch_exp,
            "longevity": longevity_exp,
            "fade_quality": fade_exp,
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
            "denim_weight_oz": weight_oz,
            "construction_features": construction,
            "fit_type": fit,
            "treatment": treatment,
            "rise": rise,
            "gender": gender,
            "mill": mill,
            "sanforization": sanforization,
            "modifiers_applied": {
                "fit": fit_mult if fit_mult != 1.0 else None,
                "treatment": treatment_mult if treatment_mult != 1.0 else None,
                "rise": rise_mult if rise_mult != 1.0 else None,
                "gender": 0.85 if gender == "women" else None,
                "combined": round(modifiers_mult, 3) if modifiers_mult != 1.0 else None,
            },
        },
    }


def _empty_evaluation() -> Dict:
    """Return evaluation for products with no usable data."""
    return {
        "garment_type": "jeans",
        "metric_definitions": JEANS_METRIC_DEFINITIONS,
        "scores": {
            "stretch_retention": None,
            "longevity": None,
            "fade_quality": None,
            "value": None,
            "care": None,
        },
        "overall_score": None,
        "quality_tier": "unknown",
        "transparency_score": 0,
        "data_confidence": "none",
        "cost_per_wear": None,
        "estimated_washes": None,
        "explanations": {
            "error": "Insufficient data: No materials or brand information available",
            "transparency": "No data: Cannot evaluate without material composition or brand",
        },
        "warnings": ["Unable to evaluate: missing materials and brand data"],
        "ask_customer_service": [
            "What is the fabric composition?",
            "What is the denim weight in oz?",
        ],
        "failure_modes": [],
        "care_impact": {},
        "metadata": {},
    }


def main():
    """CLI entry point."""
    import argparse

    parser = argparse.ArgumentParser(description="Evaluate jeans/denim quality")
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

    result = evaluate_jeans(product_data)
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
