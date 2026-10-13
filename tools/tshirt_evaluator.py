"""
T-Shirt Quality Evaluation Engine

Based on 2025 University of Leeds/WRAP research that tested 47 t-shirts and found:
- Price ≠ Durability (£4 shirt outperformed £395 shirt; most durable was £28)
- Specific, measurable attributes predict quality better than price
- Sweet spot: $20-$45 retail for optimal cost-per-wear

Evaluates t-shirts on 5 dimensions:
1. Longevity (1-5): Predicts wash cycles based on cotton type, GSM, construction
2. Shrinkage (1-5): Based on blend ratio and preshrunk treatment
3. Pilling (1-5): Research-backed red flag detection (65/35 blend)
4. Value (1-5): Cost-per-wear calculation
5. Care (1-5): Ease of maintenance
"""

import re
import json
import sys
from typing import Dict, List, Tuple, Optional


# Cotton Type Hierarchy (most critical quality factor)
COTTON_TYPES = {
    "supima": {
        "score_boost": 2.0,
        "wash_multiplier": 1.5,
        "keywords": ["supima"],
        "description": "Extra-long staple, 30-45% stronger than regular cotton"
    },
    "pima": {
        "score_boost": 2.0,
        "wash_multiplier": 1.5,
        "keywords": ["pima", "pima cotton"],
        "description": "Extra-long staple, nearly identical to Supima"
    },
    "combed_ringspun": {
        "score_boost": 1.0,
        "wash_multiplier": 1.2,
        "keywords": ["combed and ring-spun", "combed & ring-spun", "combed ring-spun", "combed ringspun", "airlume"],
        "description": "Combing removes short fibers, ring-spinning creates dense yarn"
    },
    "ringspun": {
        "score_boost": 0.5,
        "wash_multiplier": 1.1,
        "keywords": ["ring-spun", "ringspun", "ring spun"],
        "description": "Better than carded but not combed"
    },
    "carded": {
        "score_boost": 0.0,
        "wash_multiplier": 1.0,
        "keywords": ["carded", "open-end", "open end"],
        "description": "Short-staple fibers, minimal processing"
    }
}

# GSM (Grams per Square Meter) Sweet Spot Detection
GSM_RANGES = {
    "ultra_light": (120, 140, 0.5, "Ultra-lightweight"),
    "light": (140, 160, 0.3, "Lightweight"),
    "sweet_spot": (165, 185, 1.0, "Optimal sweet spot"),
    "premium": (190, 220, 0.8, "Premium weight"),
    "heavyweight": (220, 300, 0.5, "Heavyweight")
}

# Construction Detection Keywords
CONSTRUCTION_SIGNALS = {
    "side_seamed": {
        "boost": 0.5,
        "keywords": ["side-seam", "side seam", "not tubular", "side-stitched"],
        "description": "Prevents torquing/twisting"
    },
    "tubular": {
        "boost": 0.0,
        "keywords": ["tubular"],
        "warning": "May torque/twist after washing"
    },
    "double_needle": {
        "boost": 0.5,
        "keywords": ["double-needle", "double needle", "double stitched"],
        "description": "Reinforced hems"
    },
    "shoulder_tape": {
        "boost": 0.5,
        "keywords": ["shoulder-to-shoulder", "taped shoulders", "shoulder tape", "shoulder taping"],
        "description": "Prevents collar/shoulder stretching"
    },
    "preshrunk": {
        "boost": 0.0,
        "keywords": ["preshrunk", "pre-shrunk", "pre shrunk", "sanforized"],
        "affects": "shrinkage"
    },
    "garment_dyed": {
        "boost": 0.0,
        "keywords": ["garment-dyed", "garment dyed", "pigment dyed"],
        "affects": "shrinkage_and_care"
    }
}


def detect_cotton_type(materials_text: str) -> Tuple[str, str]:
    """
    Detect cotton type from materials text.
    Returns: (type_key, description)
    """
    if not materials_text:
        return "carded", "Unspecified cotton type (assumed carded)"

    text_lower = materials_text.lower()

    # Check in order of priority (most specific first)
    for type_key, type_info in COTTON_TYPES.items():
        for keyword in type_info["keywords"]:
            if keyword in text_lower:
                return type_key, type_info["description"]

    # If contains "cotton" but no type specified → carded (red flag)
    if "cotton" in text_lower:
        return "carded", "Unspecified cotton type (assumed carded - lowest quality)"

    return "carded", "No cotton type specified"


def parse_gsm(materials_text: str) -> Optional[float]:
    """
    Parse GSM from materials text.
    Handles: "180 GSM", "180gsm", "5.3 oz/yd²", "5.3 oz"
    """
    if not materials_text:
        return None

    # Direct GSM mention
    gsm_match = re.search(r'(\d+(?:\.\d+)?)\s*g?s?m', materials_text, re.IGNORECASE)
    if gsm_match:
        return float(gsm_match.group(1))

    # oz/yd² conversion (oz * 33.9 = GSM)
    oz_match = re.search(r'(\d+(?:\.\d+)?)\s*oz(?:/yd²|/yd2)?', materials_text, re.IGNORECASE)
    if oz_match:
        oz = float(oz_match.group(1))
        return oz * 33.9

    return None


def parse_singles_count(materials_text: str) -> Optional[int]:
    """
    Parse singles count from materials text.
    Handles: "30 singles", "18s", "combed 30s ring-spun"
    """
    if not materials_text:
        return None

    # Pattern: number followed by "singles" or "s"
    singles_match = re.search(r'(\d+)\s*(?:singles|s)\b', materials_text, re.IGNORECASE)
    if singles_match:
        return int(singles_match.group(1))

    return None


def detect_construction(materials_text: str) -> Dict[str, bool]:
    """
    Detect construction features from materials text.
    Returns dict with boolean flags for each feature.
    """
    if not materials_text:
        return {}

    text_lower = materials_text.lower()
    detected = {}

    for feature, info in CONSTRUCTION_SIGNALS.items():
        for keyword in info["keywords"]:
            if keyword in text_lower:
                detected[feature] = True
                break

    return detected


def get_material_percent(materials_structured: List[Dict], material_name: str) -> float:
    """
    Get total percentage of a specific material from materials_structured.
    """
    total = 0.0
    for item in materials_structured:
        if item.get("material", "").lower() == material_name.lower():
            percent = item.get("percent", 0)
            if percent is not None:
                total += percent
    return total


def calculate_longevity(
    cotton_type: str,
    gsm: Optional[float],
    singles: Optional[int],
    construction: Dict[str, bool],
    materials_structured: List[Dict]
) -> Tuple[float, str, int]:
    """
    Calculate longevity score (1-5) and explanation.
    Updated wash estimates (less pessimistic):
    - Combed ringspun: 60-85 washes (2-3 years)
    - Ringspun: 45-65 washes (1.5-2 years)
    - Heavyweight bonus: +20% washes
    """
    base_score = 1.0
    explanation_parts = []

    # Cotton type (most important factor)
    cotton_info = COTTON_TYPES.get(cotton_type, COTTON_TYPES["carded"])
    base_score += cotton_info["score_boost"]
    explanation_parts.append(f"{cotton_type.replace('_', ' ').title()} cotton")

    # GSM sweet spot
    if gsm:
        for range_name, (min_gsm, max_gsm, boost, desc) in GSM_RANGES.items():
            if min_gsm <= gsm <= max_gsm:
                base_score += boost
                explanation_parts.append(f"{int(gsm)} GSM ({desc})")
                break

    # Singles count (more nuanced)
    if singles:
        if singles >= 30:
            base_score += 0.5
            explanation_parts.append(f"{singles} singles (premium yarn)")
        elif singles >= 24:
            base_score += 0.2
            explanation_parts.append(f"{singles} singles (medium yarn)")
        elif singles <= 18:
            base_score -= 0.2
            explanation_parts.append(f"{singles} singles (coarse yarn)")

    # Construction boosts
    if construction.get("side_seamed"):
        base_score += 0.5
        explanation_parts.append("side-seamed")

    if construction.get("double_needle"):
        base_score += 0.5
        explanation_parts.append("double-needle")

    if construction.get("shoulder_tape"):
        base_score += 0.5
        explanation_parts.append("shoulder taping")

    # Calculate base estimated washes with improved formula
    wash_multiplier = cotton_info["wash_multiplier"]
    # Use base_score (not capped) to calculate washes
    estimated_washes = base_score * 25 * wash_multiplier

    # Add weight bonus (heavyweight lasts longer)
    if gsm:
        if gsm >= 220:  # Heavyweight
            estimated_washes *= 1.2
            explanation_parts.append("+20% heavyweight bonus")
        elif gsm >= 180:  # Mid-weight
            estimated_washes *= 1.1
            explanation_parts.append("+10% mid-weight bonus")

    estimated_washes = int(estimated_washes)

    # Convert wash count to performance-based score (FIX: was using feature score)
    # This makes the score reflect actual durability, not just feature detection
    if estimated_washes >= 70:
        longevity_score = 5.0
    elif estimated_washes >= 55:
        longevity_score = 4.0
    elif estimated_washes >= 45:
        longevity_score = 3.5
    elif estimated_washes >= 35:
        longevity_score = 3.0
    elif estimated_washes >= 25:
        longevity_score = 2.5
    else:
        longevity_score = 2.0

    explanation = f"{', '.join(explanation_parts)} → ~{estimated_washes} washes"

    return longevity_score, explanation, estimated_washes


def calculate_shrinkage(
    materials_structured: List[Dict],
    construction: Dict[str, bool]
) -> Tuple[float, str]:
    """
    Calculate shrinkage score (1-5).
    5 = <3% shrinkage, 2 = 8-10% shrinkage
    """
    poly_percent = get_material_percent(materials_structured, "polyester")
    cotton_percent = get_material_percent(materials_structured, "cotton")

    # Preshrunk or garment-dyed = minimal shrinkage
    if construction.get("preshrunk") or construction.get("garment_dyed"):
        if construction.get("garment_dyed"):
            return 5.0, "Garment-dyed (already preshrunk, zero additional shrinkage)"
        else:
            return 5.0, "Preshrunk treatment reduces shrinkage to <3%"

    # High polyester content = minimal shrinkage
    if poly_percent > 30:
        return 5.0, f"{int(poly_percent)}% polyester reduces shrinkage to <3%"

    # 100% untreated cotton = high shrinkage
    if cotton_percent >= 90:
        return 2.0, "Untreated 100% cotton. Expect 8-10% shrinkage; size up recommended"

    # Mid-range blend
    return 3.5, "Moderate shrinkage expected (5-7%)"


def calculate_pilling(
    materials_structured: List[Dict],
    cotton_type: str,
    singles: Optional[int] = None,
    gsm: Optional[float] = None
) -> Tuple[float, str, List[str]]:
    """
    Calculate pilling score (1-5) and warnings.
    1 = severe permanent pilling, 5 = highly resistant
    Improved: differentiates poly-cotton ratios and adds singles impact
    """
    cotton_percent = get_material_percent(materials_structured, "cotton")
    poly_percent = get_material_percent(materials_structured, "polyester")
    warnings = []
    score = 3.0
    explanation = ""

    # Premium cotton types (Supima, Pima) = inherently combed, best pilling resistance
    if cotton_type in ["supima", "pima"]:
        score = 5.0
        explanation = f"{cotton_type.title()} cotton (extra-long staple) is highly pilling-resistant"

    # Combed cotton = best pilling resistance
    elif "combed" in cotton_type:
        score = 5.0
        explanation = "Combed fibers remove short ends that cause pilling"

    # Poly-cotton blends (nuanced scoring)
    elif poly_percent > 0:
        if 35 <= poly_percent <= 65:
            # 50/50 and similar blends - WORST for pilling
            score = 1.8
            explanation = f"High polyester content ({int(poly_percent)}%) creates severe pilling issues. Polyester fibers anchor pills permanently to fabric. Expect pilling within 8-12 washes."
            warnings.append(f"⚠️ {int(cotton_percent)}/{int(poly_percent)} BLEND: Permanent pilling expected (worst ratio for pilling)")
        elif poly_percent >= 80:
            # Mostly poly - better than blends
            score = 3.2
            explanation = f"High polyester content ({int(poly_percent)}%) reduces pilling vs blends. Expect moderate pilling after 30-40 washes."
        elif poly_percent <= 25:
            # Mostly cotton with poly for strength
            score = 3.5
            explanation = f"Low polyester content ({int(poly_percent)}%) primarily for durability. Minimal pilling impact. Expect performance similar to pure cotton."
        else:
            # Mid-range blend
            score = 2.5
            explanation = f"{int(poly_percent)}% polyester may cause moderate pilling"
            warnings.append(f"⚠️ Poly-cotton blend ({int(cotton_percent)}/{int(poly_percent)}): Moderate pilling risk")

    # Standard cotton
    elif cotton_percent >= 80:
        score = 3.5
        explanation = "Standard cotton (pills may form but eventually detach)"

    # Singles count impact (if provided and score isn't already at extremes)
    if singles and 2.0 < score < 5.0:
        if singles >= 30:  # Fine yarn (premium)
            score += 0.3
            explanation += f" + fine {singles}s yarn"
        elif singles >= 24:  # Medium yarn
            score += 0.1
        elif singles <= 18:  # Coarse yarn (budget)
            score -= 0.2
            explanation += f" + coarse {singles}s yarn"

    # Heavyweight bonus (dense fabric pills less)
    if gsm and gsm >= 220 and score < 5.0:
        score += 0.3
        explanation += " Heavyweight fabric (220+ GSM) reduces pilling."

    # Cap score at 5.0
    score = min(5.0, score)

    return score, explanation, warnings


def calculate_value(
    price: Optional[float],
    estimated_washes: int
) -> Tuple[Optional[float], str]:
    """
    Calculate value score (1-5) based on cost-per-wear.
    Sweet spot: $20-$45 retail
    """
    if price is None or price <= 0:
        return None, "No price available"

    cost_per_wear = price / estimated_washes

    # The sweet spot (research finding)
    if 20 <= price <= 45:
        explanation = f"Peak sweet spot: ${price:.2f} for {estimated_washes} wears = ${cost_per_wear:.2f}/wear"
        return 5.0, explanation

    # Excellent cost-per-wear regardless of price
    if cost_per_wear < 0.30:
        explanation = f"Excellent value: ${cost_per_wear:.2f}/wear (${price:.2f} for {estimated_washes} washes)"
        return 4.0, explanation

    # Acceptable value
    if cost_per_wear < 0.50:
        explanation = f"Fair value: ${cost_per_wear:.2f}/wear"
        return 3.0, explanation

    # Poor value
    explanation = f"Poor value: ${cost_per_wear:.2f}/wear (${price:.2f} for only {estimated_washes} washes)"
    return 2.0, explanation


def calculate_care(construction: Dict[str, bool]) -> Tuple[float, str]:
    """
    Calculate care score (1-5).
    5 = very easy care, 3 = standard machine wash
    """
    if construction.get("garment_dyed"):
        return 5.0, "Garment-dyed fabric is more stable and color-fast"

    return 4.0, "Standard machine wash"


def calculate_overall_score(scores: Dict[str, Optional[float]]) -> Tuple[float, str]:
    """
    Calculate overall score (0-100) from 5-dimension scores.
    Weighted average with longevity and pilling most important.
    """
    # Weights (must sum to 1.0)
    weights = {
        "longevity": 0.35,
        "pilling": 0.30,
        "value": 0.20,
        "shrinkage": 0.10,
        "care": 0.05
    }

    # Skip value if not available
    if scores.get("value") is None:
        # Redistribute value weight proportionally
        weights = {
            "longevity": 0.40,
            "pilling": 0.35,
            "shrinkage": 0.15,
            "care": 0.10
        }

    # Calculate weighted average (convert 1-5 scale to 0-100)
    weighted_sum = 0.0
    total_weight = 0.0

    for dimension, weight in weights.items():
        score = scores.get(dimension)
        if score is not None:
            weighted_sum += score * weight
            total_weight += weight

    if total_weight == 0:
        return 0.0, "unknown"

    # Convert 1-5 scale to 0-100
    overall = (weighted_sum / total_weight) * 20

    # Determine quality tier (recalibrated - less harsh)
    # excellent = top 10% of products, good = solid quality recommended
    if overall >= 86:  # 4.3/5 average
        tier = "excellent"
    elif overall >= 66:  # 3.3/5 average
        tier = "good"
    elif overall >= 46:  # 2.3/5 average
        tier = "average"
    else:
        tier = "poor"

    return overall, tier


def calculate_transparency(
    cotton_type: str,
    cotton_desc: str,
    gsm: Optional[float],
    singles: Optional[int],
    construction: Dict[str, bool]
) -> Tuple[int, str, str, List[str]]:
    """
    Calculate transparency score (1-10) based on data disclosure.

    Returns:
        (transparency_score, data_confidence, explanation, ask_customer_service)
    """
    transparency_score = 0
    data_points = []
    ask_cs = []

    # Cotton type specified (+2)
    if cotton_type != "carded" or "unspecified" not in cotton_desc.lower():
        transparency_score += 2
        data_points.append("Cotton type specified")
    else:
        ask_cs.append("What type of cotton is used? (combed, ring-spun, Supima, etc.)")

    # GSM or oz/yd² specified (+2)
    if gsm is not None:
        transparency_score += 2
        data_points.append(f"Weight specified ({int(gsm)} GSM)")
    else:
        ask_cs.append("What is the fabric weight in GSM or oz/yd²?")

    # Singles count specified (+1)
    if singles is not None:
        transparency_score += 1
        data_points.append(f"Singles count ({singles}s)")

    # Construction method (+1)
    if construction.get("side_seamed") or construction.get("tubular"):
        transparency_score += 1
        data_points.append("Construction method disclosed")
    else:
        ask_cs.append("Is this side-seamed or tubular construction?")

    # Preshrunk/garment-dyed (+1)
    if construction.get("preshrunk") or construction.get("garment_dyed"):
        transparency_score += 1
        data_points.append("Treatment disclosed")

    # Reinforcement details (+1)
    if construction.get("double_needle") or construction.get("shoulder_tape"):
        transparency_score += 1
        data_points.append("Reinforcement details")

    # Material composition (+2) - always present if we got this far
    transparency_score += 2
    data_points.append("Material composition disclosed")

    # Determine data confidence
    if transparency_score >= 8:
        data_confidence = "high"
    elif transparency_score >= 5:
        data_confidence = "medium"
    else:
        data_confidence = "low"

    # Generate explanation
    if transparency_score >= 9:
        explanation = f"Excellent transparency ({transparency_score}/10): {', '.join(data_points)}"
    elif transparency_score >= 7:
        explanation = f"Good transparency ({transparency_score}/10): {', '.join(data_points)}"
    elif transparency_score >= 5:
        explanation = f"Fair transparency ({transparency_score}/10): Basic composition disclosed"
    else:
        explanation = f"Poor transparency ({transparency_score}/10): Minimal quality information provided"

    return transparency_score, data_confidence, explanation, ask_cs


def detect_red_flags(
    materials_structured: List[Dict],
    cotton_type: str,
    cotton_desc: str,
    gsm: Optional[float],
    price: Optional[float]
) -> List[str]:
    """
    Detect quality-killing red flags that warrant explicit warnings.

    Returns:
        List of red flag warnings
    """
    red_flags = []
    cotton_percent = get_material_percent(materials_structured, "cotton")
    poly_percent = get_material_percent(materials_structured, "polyester")

    # Red Flag 1: Very thin fabric
    if gsm and gsm < 130:
        red_flags.append("⛔ Very thin fabric (<130 GSM) - expect see-through and rapid wear")

    # Red Flag 2: Unknown cheap cotton
    if (cotton_type == "carded" and
        "unspecified" in cotton_desc.lower() and
        cotton_percent >= 90 and
        price and price < 12):
        red_flags.append("⛔ Unspecified cotton at budget price - likely lowest quality carded cotton")

    # Red Flag 3: Extreme blend (40-60% poly)
    if 40 <= poly_percent <= 60:
        red_flags.append("⛔ 50/50 poly-cotton blend - worst pilling of any composition")

    # Red Flag 4: Very low GSM for price
    if gsm and price and gsm < 140 and price > 30:
        red_flags.append("⛔ Overpriced for fabric weight - thin fabric (<140 GSM) at premium price point")

    return red_flags


def calculate_care_impact(
    estimated_washes: int,
    materials_structured: List[Dict],
    cotton_type: str,
    construction: Dict[str, bool],
    price: Optional[float]
) -> Dict:
    """
    Calculate how different washing methods affect t-shirt longevity.

    Based on research showing washing method significantly impacts lifespan:
    - Hot water + tumble dry high = baseline (what most people do)
    - Cold water + air dry = extends life 2-3x

    Args:
        estimated_washes: Baseline wash count
        materials_structured: Material composition
        cotton_type: Detected cotton type
        construction: Construction features
        price: Product price (for CPW calculations)

    Returns:
        Dict with care scenarios and recommendations
    """
    cotton_percent = get_material_percent(materials_structured, "cotton")
    poly_percent = get_material_percent(materials_structured, "polyester")

    # Baseline is "typical consumer behavior" (warm wash, medium tumble dry)
    baseline_washes = estimated_washes

    # Calculate multipliers for different care methods
    # Based on research: heat is the #1 destroyer of fabric

    # Best case: Cold wash + air dry
    best_multiplier = 1.5  # Base improvement
    if cotton_percent >= 95:
        best_multiplier = 1.8  # Pure cotton benefits most from gentle care
    elif poly_percent >= 50:
        best_multiplier = 1.3  # Poly-cotton less sensitive to heat

    # Good case: Cold wash + tumble dry low
    good_multiplier = 1.25
    if cotton_percent >= 95:
        good_multiplier = 1.4

    # Worst case: Hot wash + tumble dry high
    worst_multiplier = 0.7  # Reduces lifespan by 30%
    if cotton_percent >= 95 and not construction.get("preshrunk"):
        worst_multiplier = 0.6  # Untreated cotton suffers most

    # Calculate scenarios
    best_washes = int(baseline_washes * best_multiplier)
    good_washes = int(baseline_washes * good_multiplier)
    worst_washes = int(baseline_washes * worst_multiplier)

    # Cost per wear for each scenario
    scenarios = []

    if price:
        scenarios.append({
            "method": "Cold wash + air dry",
            "impact": "Best",
            "washes": best_washes,
            "cost_per_wear": round(price / best_washes, 2),
            "description": "Gentlest method - extends life significantly"
        })

        scenarios.append({
            "method": "Cold wash + tumble dry low",
            "impact": "Good",
            "washes": good_washes,
            "cost_per_wear": round(price / good_washes, 2),
            "description": "Balanced approach - convenient with longevity benefit"
        })

        scenarios.append({
            "method": "Warm wash + tumble dry medium",
            "impact": "Standard",
            "washes": baseline_washes,
            "cost_per_wear": round(price / baseline_washes, 2),
            "description": "Typical consumer behavior - baseline estimate"
        })

        scenarios.append({
            "method": "Hot wash + tumble dry high",
            "impact": "Worst",
            "washes": worst_washes,
            "cost_per_wear": round(price / worst_washes, 2),
            "description": "Harsh method - significantly reduces lifespan"
        })
    else:
        # Price not available, show wash counts only
        scenarios.append({
            "method": "Cold wash + air dry",
            "impact": "Best",
            "washes": best_washes,
            "description": "Gentlest method - extends life significantly"
        })

        scenarios.append({
            "method": "Cold wash + tumble dry low",
            "impact": "Good",
            "washes": good_washes,
            "description": "Balanced approach - convenient with longevity benefit"
        })

        scenarios.append({
            "method": "Warm wash + tumble dry medium",
            "impact": "Standard",
            "washes": baseline_washes,
            "description": "Typical consumer behavior - baseline estimate"
        })

        scenarios.append({
            "method": "Hot wash + tumble dry high",
            "impact": "Worst",
            "washes": worst_washes,
            "description": "Harsh method - significantly reduces lifespan"
        })

    # Generate personalized recommendations
    recommendations = []

    if cotton_percent >= 95:
        recommendations.append("100% cotton benefits most from cold water and air drying")
        if not construction.get("preshrunk"):
            recommendations.append("First wash: cold water to minimize shrinkage")

    if poly_percent >= 30:
        recommendations.append("Polyester blend handles heat better but still ages faster with high temperatures")

    if cotton_type in ["supima", "pima", "combed_ringspun"]:
        recommendations.append(f"{cotton_type.replace('_', ' ').title()} cotton deserves gentle care to maximize its premium durability")

    # Universal recommendations
    recommendations.append("Turn inside out before washing to reduce pilling")
    recommendations.append("Avoid fabric softener - it breaks down fibers over time")

    if construction.get("garment_dyed"):
        recommendations.append("Garment-dyed: already preshrunk, safe to use warm water if needed")

    # Calculate potential savings
    savings = None
    if price:
        standard_cpw = price / baseline_washes
        best_cpw = price / best_washes
        cost_savings = round(standard_cpw - best_cpw, 2)
        washes_gained = best_washes - baseline_washes

        savings = {
            "cost_per_wear_reduction": cost_savings,
            "additional_washes": washes_gained,
            "total_value_gained": round(cost_savings * best_washes, 2),
            "summary": f"Switching to cold wash + air dry saves ${cost_savings}/wear and adds {washes_gained} washes"
        }

    return {
        "scenarios": scenarios,
        "recommendations": recommendations,
        "savings": savings,
        "baseline_method": "Warm wash + tumble dry medium",
        "best_method": "Cold wash + air dry"
    }


def evaluate_tshirt(product_data: Dict) -> Dict:
    """
    Evaluate t-shirt quality using Leeds/WRAP research-backed metrics.

    Args:
        product_data: Extracted product JSON with:
            - materials_structured: [{"material": "cotton", "percent": 100}]
            - price: float
            - materials_text: str (for parsing cotton_type, gsm, construction)

    Returns:
        {
            "scores": {
                "longevity": 4.5,      # 1-5 (predicts wash cycles)
                "shrinkage": 2,        # 1-5 (lower = more shrinkage)
                "pilling": 5,          # 1-5 (1 = severe pilling)
                "value": 5,            # 1-5 (cost-per-wear)
                "care": 4              # 1-5 (ease of care)
            },
            "overall_score": 82,       # 0-100 (weighted average)
            "quality_tier": "excellent",  # excellent/good/fair/poor
            "cost_per_wear": 0.28,     # Estimated $/wear
            "estimated_washes": 90,    # Predicted lifespan
            "explanations": {...},     # Per-score explanations
            "warnings": [...]          # Red flags (e.g., "65/35 blend")
        }
    """
    materials_structured = product_data.get("materials_structured", [])
    price = product_data.get("price")
    materials_text = product_data.get("materials_text", "")

    # Check for missing data
    if not materials_structured:
        return {
            "scores": {
                "longevity": None,
                "shrinkage": None,
                "pilling": None,
                "value": None,
                "care": None
            },
            "overall_score": None,
            "quality_tier": "unknown",
            "transparency_score": 0,
            "data_confidence": "none",
            "cost_per_wear": None,
            "estimated_washes": None,
            "explanations": {
                "error": "Insufficient data: No materials information available",
                "transparency": "No data: Cannot evaluate without material composition"
            },
            "warnings": ["Unable to evaluate: missing materials data"],
            "ask_customer_service": ["What materials is this product made from?"]
        }

    # Parse text for quality signals
    cotton_type, cotton_desc = detect_cotton_type(materials_text)
    gsm = parse_gsm(materials_text)
    singles = parse_singles_count(materials_text)
    construction = detect_construction(materials_text)

    # Calculate 5 dimension scores
    longevity_score, longevity_exp, estimated_washes = calculate_longevity(
        cotton_type, gsm, singles, construction, materials_structured
    )

    shrinkage_score, shrinkage_exp = calculate_shrinkage(
        materials_structured, construction
    )

    pilling_score, pilling_exp, pilling_warnings = calculate_pilling(
        materials_structured, cotton_type, singles, gsm
    )

    # Use estimated_washes from longevity calculation (FIX: was recalculating with old formula)

    value_score, value_exp = calculate_value(price, estimated_washes)

    care_score, care_exp = calculate_care(construction)

    # Compile scores
    scores = {
        "longevity": longevity_score,
        "shrinkage": shrinkage_score,
        "pilling": pilling_score,
        "value": value_score,
        "care": care_score
    }

    # Calculate overall score
    overall_score, quality_tier = calculate_overall_score(scores)

    # Calculate cost per wear
    cost_per_wear = None
    if price and estimated_washes:
        cost_per_wear = round(price / estimated_washes, 2)

    # Calculate transparency score
    transparency_score, data_confidence, transparency_exp, ask_cs = calculate_transparency(
        cotton_type, cotton_desc, gsm, singles, construction
    )

    # Detect red flags
    red_flags = detect_red_flags(materials_structured, cotton_type, cotton_desc, gsm, price)

    # Compile warnings (red flags first, then other warnings)
    warnings = red_flags.copy()
    warnings.extend(pilling_warnings)

    if construction.get("tubular"):
        warnings.append("Tubular construction: may torque/twist after washing")

    if cotton_type == "carded" and "unspecified" in cotton_desc.lower() and not any("⛔" in w for w in warnings):
        # Only add if not already flagged by red flag detector
        warnings.append("Cotton type not specified in listing (assumed lowest quality)")

    # Add transparency warning if score is low
    if transparency_score <= 4:
        warnings.append(f"⚠️ TRANSPARENCY: {transparency_score}/10 - Brand provides minimal quality information. Why won't they disclose cotton type, weight, or construction?")

    # Calculate care impact scenarios
    care_impact = calculate_care_impact(
        estimated_washes, materials_structured, cotton_type, construction, price
    )

    # Return full evaluation
    return {
        "garment_type": "tshirt",
        "metric_definitions": [
            {"key": "shrinkage", "icon": "💧", "label": "Will it shrink?",
             "left_label": "High risk", "right_label": "Low risk", "max_score": 5},
            {"key": "pilling", "icon": "🧶", "label": "Will it pill?",
             "left_label": "High pilling", "right_label": "No pilling", "max_score": 5},
            {"key": "longevity", "icon": "\u23f1\ufe0f", "label": "How long will it last?",
             "left_label": "6 months", "right_label": "3+ years", "max_score": 5},
            {"key": "value", "icon": "💰", "label": "Value for money",
             "left_label": "Poor value", "right_label": "Excellent value", "max_score": 5},
            {"key": "care", "icon": "🧺", "label": "Care difficulty",
             "left_label": "High maintenance", "right_label": "Easy care", "max_score": 5},
        ],
        "scores": scores,
        "overall_score": round(overall_score, 1) if overall_score else None,
        "quality_tier": quality_tier,
        "transparency_score": transparency_score,
        "data_confidence": data_confidence,
        "cost_per_wear": cost_per_wear,
        "estimated_washes": estimated_washes,
        "explanations": {
            "longevity": longevity_exp,
            "shrinkage": shrinkage_exp,
            "pilling": pilling_exp,
            "value": value_exp,
            "care": care_exp,
            "transparency": transparency_exp
        },
        "warnings": warnings,
        "ask_customer_service": ask_cs,
        "care_impact": care_impact,
        "metadata": {
            "cotton_type": cotton_type,
            "cotton_description": cotton_desc,
            "gsm": gsm,
            "singles_count": singles,
            "construction_features": construction
        }
    }


def main():
    """
    CLI entry point for standalone usage.
    """
    import argparse

    parser = argparse.ArgumentParser(description="Evaluate t-shirt quality")
    parser.add_argument("--json-file", help="Path to product JSON file")
    parser.add_argument("--stdin", action="store_true", help="Read JSON from stdin")

    args = parser.parse_args()

    # Read input
    if args.json_file:
        with open(args.json_file, 'r', encoding='utf-8') as f:
            product_data = json.load(f)
    elif args.stdin:
        product_data = json.load(sys.stdin)
    else:
        print("Error: Specify --json-file or --stdin")
        sys.exit(1)

    # Evaluate
    result = evaluate_tshirt(product_data)

    # Output
    print(json.dumps(result, indent=2))


if __name__ == "__main__":
    main()
