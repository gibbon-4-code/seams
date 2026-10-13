"""Guards for the in-browser web demo (web/), which runs tools/ under Pyodide."""

import ast
import sys
import re
from pathlib import Path

from web.build import TOOL_MODULES

ROOT = Path(__file__).resolve().parent.parent

# Third-party packages usable in the browser (app.js loads bs4 + lxml; price_parser is an optional import)
BROWSER_PACKAGES = {"bs4", "lxml", "price_parser"}


def test_app_js_loads_same_modules_as_build():
    app_js = (ROOT / "web" / "app.js").read_text(encoding="utf-8")
    block = re.search(r"TOOL_MODULES = \[(.*?)\]", app_js, re.S).group(1)
    assert re.findall(r"'([\w]+)'", block) == TOOL_MODULES


def test_browser_modules_only_import_available_packages():
    stdlib = set(sys.stdlib_module_names)
    for name in TOOL_MODULES:
        tree = ast.parse((ROOT / "tools" / f"{name}.py").read_text(encoding="utf-8"))
        for node in ast.walk(tree):
            if isinstance(node, ast.Import):
                roots = [a.name.split(".")[0] for a in node.names]
            elif isinstance(node, ast.ImportFrom) and node.level == 0:
                roots = [node.module.split(".")[0]]
            else:
                continue
            for root in roots:
                assert root in stdlib | BROWSER_PACKAGES, f"tools/{name}.py imports {root}, unavailable in the web demo"

    # Relative imports must stay within the shipped modules
    for name in TOOL_MODULES:
        src = (ROOT / "tools" / f"{name}.py").read_text(encoding="utf-8")
        for mod in re.findall(r"^from \.(\w+) import", src, re.M):
            assert mod in TOOL_MODULES, f"tools/{name}.py needs tools/{mod}.py, which isn't shipped"
