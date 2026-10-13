"""
Garment Type Detector

Detects whether a product is jeans, a t-shirt, a hoodie, or unknown
based on product name, materials text, and brand signals.
"""

import re
from typing import Dict, List


# Strong signals (high confidence when matched)
JEANS_STRONG = [
    r"\bjeans?\b", r"\bdenim\s+jeans\b", r"\bselvedge\b", r"\bselvage\b",
    r"\braw\s+denim\b", r"\b501\b", r"\b511\b", r"\b505\b", r"\b514\b",
    r"\b5-pocket\b", r"\bfive.pocket\b",
]

TSHIRT_STRONG = [
    r"\bt-?shirt\b", r"\btee\b", r"\btshirt\b", r"\bjersey\s+tee\b",
    r"\bcrew\s+neck\s+t", r"\bv-?neck\s+t",
]

HOODIE_STRONG = [
    r"\bhoodie\b", r"\bhooded\s+(?:sweatshirt|pullover|top|fleece)\b",
    r"\bzip[\s-]?up\s+hood", r"\bfull[\s-]?zip\s+hood",
    r"\bpullover\s+hood", r"\bhalf[\s-]?zip\s+hood",
    r"\bquarter[\s-]?zip\s+hood",
]

# Medium signals (need 2+ or combined with other context)
JEANS_MEDIUM = [
    r"\bdenim\b", r"\bindigo\b", r"\bshrink.to.fit\b",
    r"\bchain.stitch\b", r"\bbar.tack\b",
]

TSHIRT_MEDIUM = [
    r"\bjersey\b", r"\bcrew\s+neck\b", r"\bgsm\b",
    r"\bring.spun\b", r"\bcarded\b", r"\bcombed\b",
]

HOODIE_MEDIUM = [
    r"\bsweatshirt\b", r"\bfleece\b", r"\bdrawstring\b",
    r"\bkangaroo\s+pocket\b", r"\breverse\s+weave\b",
]

# Exclusion signals (prevent false matches)
JEANS_EXCLUDE = [
    r"\bjacket\b", r"\bshirt\b(?!\s*jeans)", r"\bcoat\b", r"\bvest\b",
    r"\bbag\b", r"\bskirt\b",
]

HOODIE_EXCLUDE = [
    r"\bjacket\b(?!\s*hoodie)", r"\bcoat\b",
    r"\bvest\b(?!\s*hoodie)", r"\bblanket\b",
]


def detect_garment_type(
    product_name: str = "",
    materials_text: str = "",
    brand: str = ""
) -> Dict:
    """
    Detect garment type from product listing text.

    Args:
        product_name: Product title/name
        materials_text: Raw materials description
        brand: Brand name

    Returns:
        {
            "garment_type": "jeans" | "tshirt" | "hoodie" | "unknown",
            "confidence": "high" | "medium" | "low",
            "signals": ["matched signal descriptions"]
        }
    """
    combined = f"{product_name} {materials_text} {brand}".lower()
    signals = []

    # Check for exclusions first
    has_jeans_exclusion = any(re.search(p, combined) for p in JEANS_EXCLUDE)
    has_hoodie_exclusion = any(re.search(p, combined) for p in HOODIE_EXCLUDE)

    # Count jeans signals
    jeans_strong = 0
    for pattern in JEANS_STRONG:
        if re.search(pattern, combined):
            jeans_strong += 1
            signals.append(f"jeans_strong: {pattern}")

    jeans_medium = 0
    if not has_jeans_exclusion:
        for pattern in JEANS_MEDIUM:
            if re.search(pattern, combined):
                jeans_medium += 1
                signals.append(f"jeans_medium: {pattern}")

    # Count hoodie signals
    hoodie_strong = 0
    for pattern in HOODIE_STRONG:
        if re.search(pattern, combined):
            hoodie_strong += 1
            signals.append(f"hoodie_strong: {pattern}")

    hoodie_medium = 0
    if not has_hoodie_exclusion:
        for pattern in HOODIE_MEDIUM:
            if re.search(pattern, combined):
                hoodie_medium += 1
                signals.append(f"hoodie_medium: {pattern}")

    # Count t-shirt signals
    tshirt_strong = 0
    for pattern in TSHIRT_STRONG:
        if re.search(pattern, combined):
            tshirt_strong += 1
            signals.append(f"tshirt_strong: {pattern}")

    tshirt_medium = 0
    for pattern in TSHIRT_MEDIUM:
        if re.search(pattern, combined):
            tshirt_medium += 1
            signals.append(f"tshirt_medium: {pattern}")

    # Decision logic
    # Jeans with exclusion (e.g., "denim jacket") -> not jeans
    if has_jeans_exclusion and jeans_strong == 0:
        jeans_strong = 0
        jeans_medium = 0

    # Hoodie with exclusion (e.g., "fleece jacket") -> not hoodie
    if has_hoodie_exclusion and hoodie_strong == 0:
        hoodie_strong = 0
        hoodie_medium = 0

    # Strong signal = high confidence
    if jeans_strong >= 1 and not has_jeans_exclusion:
        return {
            "garment_type": "jeans",
            "confidence": "high",
            "signals": signals
        }

    if hoodie_strong >= 1 and not has_hoodie_exclusion:
        return {
            "garment_type": "hoodie",
            "confidence": "high",
            "signals": signals
        }

    if tshirt_strong >= 1:
        return {
            "garment_type": "tshirt",
            "confidence": "high",
            "signals": signals
        }

    # Medium signals only
    if jeans_medium >= 2 and not has_jeans_exclusion:
        return {
            "garment_type": "jeans",
            "confidence": "medium",
            "signals": signals
        }

    # Hoodie medium signals (sweatshirt + fleece, etc.)
    if hoodie_medium >= 2 and not has_hoodie_exclusion:
        return {
            "garment_type": "hoodie",
            "confidence": "medium",
            "signals": signals
        }

    if tshirt_medium >= 2:
        return {
            "garment_type": "tshirt",
            "confidence": "medium",
            "signals": signals
        }

    # Fallback
    return {
        "garment_type": "unknown",
        "confidence": "low",
        "signals": signals
    }
