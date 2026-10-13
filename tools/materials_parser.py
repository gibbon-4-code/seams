"""
Materials Parser - Parse raw materials text into structured format.
"""

import re
from typing import List, Dict, Tuple, Optional


# Material normalization mappings
MATERIAL_SYNONYMS = {
    "viscose": "rayon",
    "polyamide": "nylon",
    "elastane": "spandex",
}

# Part label patterns (case-insensitive)
PART_PATTERNS = [
    r"shell\s*:",
    r"outer\s*:",
    r"lining\s*:",
    r"inner\s*:",
    r"fill(?:ing)?\s*:",
    r"padding\s*:",
    r"insulation\s*:",
]


def normalize_material(material: str) -> str:
    """
    Normalize material names using synonym mappings.

    Args:
        material: Raw material name

    Returns:
        Normalized material name (lowercase)
    """
    material_lower = material.lower().strip()

    # Apply synonym mappings
    for synonym, normalized in MATERIAL_SYNONYMS.items():
        if synonym in material_lower:
            material_lower = material_lower.replace(synonym, normalized)

    return material_lower


def extract_percentages(text: str) -> List[Tuple[str, Optional[float]]]:
    """
    Extract material and percentage pairs from text.

    Handles formats like:
    - "60% wool, 40% polyester"
    - "wool 60%, polyester 40%"
    - "wool (60%), polyester (40%)"

    Args:
        text: Text containing materials and percentages

    Returns:
        List of (material, percent) tuples
    """
    results = []

    # Pattern 1: "60% wool" or "60 % wool"
    pattern1 = r"(\d+)\s*%\s+([a-zA-Z\s]+?)(?=\d+\s*%|$|,|\.|\(|;)"
    matches1 = re.finditer(pattern1, text)
    for match in matches1:
        percent = float(match.group(1))
        material = match.group(2).strip()
        if material:
            results.append((material, percent))

    # Pattern 2: "wool 60%" or "wool (60%)"
    pattern2 = r"([a-zA-Z\s]+?)\s+\(?(\d+)\s*%\)?"
    if not results:  # Only try pattern 2 if pattern 1 didn't match
        matches2 = re.finditer(pattern2, text)
        for match in matches2:
            material = match.group(1).strip()
            percent = float(match.group(2))
            if material and material.lower() not in ["lining", "shell", "fill", "filling", "outer", "inner"]:
                results.append((material, percent))

    # Pattern 3: Just material names without percentages
    if not results:
        # Extract material names (common fabrics)
        common_materials = [
            "cotton", "polyester", "wool", "silk", "linen", "nylon", "rayon",
            "spandex", "elastane", "acrylic", "cashmere", "leather", "suede",
            "viscose", "polyamide", "modal", "lyocell", "tencel"
        ]
        for material in common_materials:
            if material in text.lower():
                results.append((material, None))

    return results


def parse_materials(materials_text: str) -> Tuple[List[Dict], List[str]]:
    """
    Parse raw materials text into structured format.

    Args:
        materials_text: Raw materials composition text

    Returns:
        Tuple of (structured_materials, notes)
        - structured_materials: List of dicts with part, material, percent
        - notes: List of parsing notes/warnings
    """
    if not materials_text:
        return [], []

    structured = []
    notes = []

    # Split by part labels - combine all patterns
    parts = []

    # Combine all patterns into one with capturing groups
    combined_pattern = "|".join(f"({p})" for p in PART_PATTERNS)

    # Find all part labels in the text
    matches = list(re.finditer(combined_pattern, materials_text, re.IGNORECASE))

    if matches:
        for i, match in enumerate(matches):
            part_label = match.group(0).rstrip(":").strip().lower()

            # Normalize part name
            if "shell" in part_label or "outer" in part_label:
                part_name = "shell"
            elif "lining" in part_label or "inner" in part_label:
                part_name = "lining"
            elif "fill" in part_label or "padding" in part_label or "insulation" in part_label:
                part_name = "fill"
            else:
                part_name = "other"

            # Get text between this label and the next (or end of string)
            start_pos = match.end()
            if i + 1 < len(matches):
                end_pos = matches[i + 1].start()
            else:
                end_pos = len(materials_text)

            part_text = materials_text[start_pos:end_pos].strip()
            if part_text:
                parts.append((part_name, part_text))

    # If no parts found, treat entire text as unknown part
    if not parts:
        parts = [("unknown", materials_text)]

    # Parse each part
    for part_name, part_text in parts:
        materials = extract_percentages(part_text)

        if not materials:
            notes.append(f"Could not parse materials for {part_name}")
            continue

        # Calculate percentage sum for validation
        percentages_sum = sum(p for _, p in materials if p is not None)
        if percentages_sum > 0 and abs(percentages_sum - 100) > 1:  # Allow 1% tolerance
            notes.append(f"{part_name.capitalize()} percentages sum to {percentages_sum}%")

        # Add to structured list
        for material, percent in materials:
            structured.append({
                "part": part_name,
                "material": normalize_material(material),
                "percent": percent
            })

    return structured, notes


def validate_materials_structured(materials: List[Dict]) -> bool:
    """
    Validate structured materials format.

    Args:
        materials: List of material dicts

    Returns:
        True if valid format, False otherwise
    """
    if not isinstance(materials, list):
        return False

    for item in materials:
        if not isinstance(item, dict):
            return False
        if "part" not in item or "material" not in item:
            return False
        if not isinstance(item.get("part"), str):
            return False
        if not isinstance(item.get("material"), str):
            return False
        if "percent" in item and item["percent"] is not None:
            if not isinstance(item["percent"], (int, float)):
                return False

    return True
