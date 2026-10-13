# T-Shirt Quality Evaluation Workflow

## Objective
Evaluate t-shirt quality using research-backed durability predictors from the 2025 University of Leeds/WRAP study.

## When to Use
After extracting product data from a t-shirt listing. This workflow takes extracted JSON and produces a comprehensive quality evaluation with 5-dimension scores, cost-per-wear analysis, and actionable warnings.

## Input
Product JSON with:
- `materials_structured`: List of materials with percentages (e.g., `[{"material": "cotton", "percent": 100}]`)
- `price`: Float (USD or other currency)
- `materials_text`: Raw materials/product description text

**Minimum required**: `materials_structured`
**Optional**: `price` (needed for value scoring), `materials_text` (enables cotton type, GSM, construction detection)

## Tool
`tools/tshirt_evaluator.py`

## Output
Comprehensive evaluation JSON:

```json
{
  "scores": {
    "longevity": 4.5,      // 1-5 (predicts wash cycles)
    "shrinkage": 2.0,      // 1-5 (lower = more shrinkage)
    "pilling": 5.0,        // 1-5 (1 = severe pilling)
    "value": 5.0,          // 1-5 (cost-per-wear)
    "care": 4.0            // 1-5 (ease of care)
  },
  "overall_score": 82.5,   // 0-100 (weighted average)
  "quality_tier": "excellent",  // excellent/good/fair/poor/unknown
  "transparency_score": 9,  // 1-10 (data disclosure scorecard)
  "data_confidence": "high", // high/medium/low (based on transparency)
  "cost_per_wear": 0.28,   // Estimated $/wear
  "estimated_washes": 90,  // Predicted lifespan in wash cycles
  "explanations": {
    "longevity": "Combed ring-spun cotton (30 singles) + side-seamed + reinforced = ~90 washes",
    "shrinkage": "Untreated cotton. Expect 8-10% shrinkage; size up recommended",
    "pilling": "Combed fibers remove short ends that cause pilling",
    "value": "Peak sweet spot: $28 for 90 wears = $0.31/wear",
    "care": "Standard machine wash",
    "transparency": "Excellent transparency (9/10): Cotton type, weight, singles, construction, reinforcement all disclosed"
  },
  "warnings": [
    "Tubular construction: may torque/twist after washing"
  ],
  "ask_customer_service": [],  // Questions for missing specs
  "metadata": {
    "cotton_type": "combed_ringspun",
    "cotton_description": "Combing removes short fibers, ring-spinning creates dense yarn",
    "gsm": 142.38,
    "singles_count": 30,
    "construction_features": {
      "side_seamed": true,
      "double_needle": true,
      "shoulder_tape": true
    }
  }
}
```

## Evaluation Logic

Based on 2025 Leeds/WRAP study findings:

### 1. Cotton Type Hierarchy (Most Critical)
- **Supima**: Extra-long staple, 30-45% stronger → longevity +2.0, wash multiplier 1.5×
- **Pima**: Nearly identical to Supima → longevity +2.0, wash multiplier 1.5×
- **Combed ring-spun**: Removes short fibers, dense yarn → longevity +1.0, wash multiplier 1.2×
- **Ring-spun**: Better than carded → longevity +0.5, wash multiplier 1.1×
- **Carded/Unspecified**: Lowest quality → no boost

**If cotton type not specified → assumed carded (red flag)**

### 2. GSM Sweet Spot (Not "Heavier = Better")
- **165-185 GSM**: Optimal sweet spot → longevity +1.0
- **190-220 GSM**: Premium weight → longevity +0.8
- **<140 GSM**: Ultra-light → longevity +0.5
- **>220 GSM**: Heavyweight → longevity +0.5

**Key insight**: A 4.2oz (142 GSM) combed ring-spun tee can outlast a 6.0oz (203 GSM) carded tee.

### 3. Construction Features
- **Side-seamed** (vs tubular): Prevents torquing → longevity +0.5
- **Double-needle**: Reinforced hems → longevity +0.5
- **Shoulder taping**: Prevents stretching → longevity +0.5
- **30+ singles**: Premium yarn fineness → longevity +0.5

### 4. The 65/35 Blend Red Flag
**65% cotton / 35% polyester = worst pilling combination**
Research shows polyester "hairiness" wraps around breaking cotton fibers, anchoring pills permanently to fabric surface. Unlike pure cotton (pills eventually detach), 65/35 blends retain pills forever.

**Detection**: If 60% ≤ cotton ≤ 70% AND 30% ≤ polyester ≤ 40% → pilling score = 1.0 + warning

### 5. Cost-Per-Wear (Value Truth-Teller)
- **Sweet spot**: $20-$45 retail → value score = 5.0
- **CPW < $0.30**: Excellent value → score = 4.0
- **CPW > $0.50**: Poor value → score = 2.0

**Research validation**: £28 tee at 90 washes (£0.31/wear) outperforms £4 tee at 20 washes (£0.20/wear) AND £395 tee at 100 washes (£3.95/wear) on **total value**.

### 6. Shrinkage Prediction
- **Garment-dyed**: Zero additional shrinkage → score = 5.0
- **Preshrunk OR >30% polyester**: <3% shrinkage → score = 5.0
- **Untreated 100% cotton**: 8-10% shrinkage → score = 2.0

### 7. Transparency Scorecard (1-10) **NEW**

**Core Feature**: Tracks how much quality information the brand discloses

**Scoring breakdown**:
- Cotton type specified (+2 points)
- GSM or oz/yd² specified (+2 points)
- Singles count specified (+1 point)
- Construction method disclosed (+1 point)
- Treatment disclosed (preshrunk/garment-dyed) (+1 point)
- Reinforcement details (double-needle/shoulder tape) (+1 point)
- Material composition disclosed (+2 points)

**Transparency tiers**:
- **9-10: Excellent** - Full specs disclosed (e.g., Bella+Canvas)
- **7-8: Good** - Most key specs provided
- **5-6: Fair** - Basic composition + some details
- **3-4: Poor** - Minimal info, red flag
- **1-2: Very poor** - Hiding quality details

**Data confidence**:
- **High (8-10)**: Reliable evaluation, all critical specs present
- **Medium (5-7)**: Partial evaluation, some assumptions made
- **Low (1-4)**: Unreliable evaluation, worst-case assumptions

**"Ask Customer Service" prompts**: When critical specs are missing, the evaluator generates specific questions to ask the brand's customer service team.

**Real-world impact**:
- £59 AllSaints tee (transparency=2) scores 42/100 "fair"
- £28 Bella+Canvas (transparency=9) scores 82/100 "excellent"
- Transparency score exposes brands hiding behind price

## Usage Examples

### Standalone CLI
```bash
# From extracted JSON file
python -m tools.tshirt_evaluator --json-file .tmp/json/20260207_123456_product.json

# From stdin (quick test)
echo '{
  "price": 28.00,
  "materials_structured": [{"material": "cotton", "percent": 100}],
  "materials_text": "100% Combed and ring-spun cotton. 4.2 oz. Side-seamed."
}' | python -m tools.tshirt_evaluator --stdin
```

### Python Integration
```python
from tools.tshirt_evaluator import evaluate_tshirt

product_data = {
    "price": 28.00,
    "materials_structured": [{"material": "cotton", "percent": 100}],
    "materials_text": "100% Combed and ring-spun cotton. 4.2 oz. Side-seamed."
}

result = evaluate_tshirt(product_data)
print(f"Quality tier: {result['quality_tier']}")
print(f"Cost per wear: ${result['cost_per_wear']}")
print(f"Warnings: {result['warnings']}")
```

## Edge Cases

### Missing Materials Data
**Input**: Empty `materials_structured`
**Output**: All scores = null, tier = "unknown", warning generated

### No Price Data
**Input**: Price missing or null
**Output**: Value score = null, all other scores calculated normally

### No GSM/Construction Details
**Input**: Only "100% Cotton" with no additional details
**Output**: Assumes carded cotton (worst case), calculates scores with lower confidence, adds warning

### Mixed Blends
**Input**: Multiple materials (e.g., tri-blend)
**Output**: Evaluates based on composition percentages, applies blend-specific rules

### Low Transparency (Brand Hiding Specs)
**Input**: "100% Cotton" with no other details
**Output**:
- Transparency score = 2/10
- Data confidence = "low"
- Worst-case assumptions (carded cotton, 20 washes)
- Warning: "⚠️ TRANSPARENCY: 2/10 - Brand provides minimal quality information"
- Ask Customer Service prompts generated for missing specs

## Quality Tier Definitions

- **Excellent (80-100)**: Premium construction, long lifespan (80+ washes), excellent value
- **Good (60-79)**: Solid quality, decent durability (50-80 washes), fair value
- **Fair (40-59)**: Budget quality, moderate lifespan (30-50 washes), acceptable value
- **Poor (0-39)**: Low quality, short lifespan (<30 washes), poor value or severe red flags
- **Unknown**: Insufficient data to evaluate

## Next Steps

After evaluation:
1. **For browser extension**: Display scores in overlay badge with explanations
2. **For decision-making**: Compare cost-per-wear across options
3. **For warnings**: Alert user to red flags (65/35 blend, tubular construction, etc.)
4. **For confidence**: Use metadata to assess reliability of evaluation

## Research References

- **2025 University of Leeds/WRAP Study**: Tested 47 t-shirts, found zero price-durability correlation
- **Key Finding**: £4 tee outperformed £395 tee; most durable was £28
- **Cotton Staple Length Research**: Supima/Pima 30-45% stronger than regular cotton
- **65/35 Blend Pilling**: Academic research on polyester fiber "hairiness" anchoring pills
- **GSM Sweet Spot**: Industry consensus on 165-185 GSM optimal range
