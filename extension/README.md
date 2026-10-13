# Seams Browser Extension - Testing Guide

## Setup Instructions

### 1. Start the Backend API

First, make sure the FastAPI backend is running:

```bash
# From the repo root
python api/server.py
```

The API should be running at `http://localhost:8000`

Test the health endpoint:
```bash
curl http://localhost:8000/health
# Should return: {"status":"ok"}
```

### 2. Load the Extension in Chrome

1. Open Chrome and navigate to `chrome://extensions/`
2. Enable **Developer mode** (toggle in top-right corner)
3. Click **Load unpacked**
4. Select the `extension` directory from this repo
5. The "Seams - Clothing Quality Evaluator" extension should now appear

### 3. Test on Product Pages

Navigate to any t-shirt, hoodie, or jeans product page. The extension will:

1. **Auto-detect** if it's a product page (requires 2+ signals)
2. **Extract** HTML and send to backend API
3. **Evaluate** quality using the evaluator
4. **Display** floating overlay in top-right corner

#### Recommended Test Sites:

**High Transparency (9-10/10):**
- Bella+Canvas: https://www.bellacanvas.com/product/3001/Unisex-Jersey-Short-Sleeve-Tee.html
- Should show "Excellent" quality with full specs

**Low Transparency (2/10):**
- Generic brand sites with minimal product details
- Should show transparency warnings and "Ask CS" prompts

### 4. Debugging

**Check Console Logs:**
1. Right-click on page → **Inspect**
2. Go to **Console** tab
3. Look for `[Seams]` log messages

**Common Issues:**

- **No overlay appears**: Check console for `[Seams] Not a product page` message
  - Solution: Page needs 2+ product signals (price, add-to-cart, schema.org, etc.)

- **API connection failed**: Check if backend is running
  - Solution: Start `python api/server.py`

- **Extension not loading**: Check `chrome://extensions/` for errors
  - Solution: Make sure all files exist in extension directory

### 5. Extension Features

**Auto-Detection Signals:**
- Schema.org Product markup
- OpenGraph product tags
- "Add to Cart" buttons
- Price elements
- Product images
- URL patterns (/product/, /item/, /p/, etc.)

**UI Features:**
- ✅ Quality tier badge (Excellent/Good/Fair/Poor)
- ✅ Product info (name, price, image)
- ✅ Key specs chips (cotton type, construction, GSM)
- ✅ 6 metric sliders with expandable explanations:
  - 🔍 Transparency Score (1-10)
  - 💧 Shrinkage (1-5)
  - 🧶 Pilling (1-5)
  - ⏱️ Longevity (1-5)
  - 💰 Value (1-5)
  - 🧺 Care (1-5)
- ✅ Warnings (65/35 blend, tubular construction, etc.)
- ✅ "Ask Customer Service" questions for missing specs
- ✅ Cost-per-wear summary
- ✅ Close button (top-right X)

### 6. Known Limitations (MVP)

- **Three garment types**: T-shirts, hoodies, and jeans (anything else falls back to the t-shirt evaluator)
- **localhost API**: Requires local backend running
- **Chrome only**: Firefox/Edge not supported yet
- **Generic sites**: Works best on sites with Schema.org or OpenGraph markup
- **No caching**: Re-evaluates on every page load

### 7. Next Steps

After testing, consider:
- Adding proper extension icons
- Deploying backend API to cloud
- Adding browser storage caching
- Supporting more garment types (jackets, knitwear, activewear)
- Improving detection for specific retail sites
