Objective: Parse raw materials text into structured format.

When to use: After extracting raw materials_text from product page.

Input: materials_text string (e.g., "Shell: 60% Wool, 40% Polyester. Lining: 100% Polyester")

Tool: tools/materials_parser.py

Output: materials_structured list with part, material, percent

Behavior:
- Identifies parts: shell, lining, fill, outer, inner (else "unknown")
- Extracts material names and percentages
- Normalizes synonyms: viscose→rayon, polyamide→nylon, elastane→spandex
- Keeps percentages as-is even if sum ≠ 100% (notes discrepancy)
- Returns empty list + note if parsing fails

Edge cases:
- No part labels → part="unknown"
- No percentages → percent=null
- Percentages don't sum to 100% → note in extraction.notes
- Unrecognized materials → kept as-is (no over-normalization)

Example structured output:
```json
[
  { "part": "shell", "material": "wool", "percent": 60 },
  { "part": "shell", "material": "polyester", "percent": 40 },
  { "part": "lining", "material": "polyester", "percent": 100 }
]
```
