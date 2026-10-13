"""
Assemble the static web demo into _site/ (used by GitHub Pages).

    python web/build.py
    python -m http.server -d _site 8080
"""

import shutil
from pathlib import Path

ROOT = Path(__file__).resolve().parent.parent
SITE = ROOT / "_site"

# Engine modules that run in the browser (html_fetcher needs network access, so it's left out)
TOOL_MODULES = [
    "__init__", "pipeline", "product_extractor", "materials_parser",
    "garment_detector", "tshirt_evaluator", "hoodie_evaluator", "jeans_evaluator",
]


def build():
    if SITE.exists():
        shutil.rmtree(SITE)
    (SITE / "tools").mkdir(parents=True)

    for name in ["index.html", "app.js", "style.css"]:
        shutil.copy(ROOT / "web" / name, SITE / name)

    # Reuse the browser extension's overlay UI as-is
    for name in ["overlay.js", "overlay.css"]:
        shutil.copy(ROOT / "extension" / "content" / name, SITE / name)

    for name in TOOL_MODULES:
        shutil.copy(ROOT / "tools" / f"{name}.py", SITE / "tools" / f"{name}.py")

    (SITE / ".nojekyll").touch()
    print(f"Built {SITE}")


if __name__ == "__main__":
    build()
