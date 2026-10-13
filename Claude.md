# Seams — Agent Instructions (WAT)

You are working inside the WAT framework (Workflows, Agents, Tools).
- Workflows = markdown SOPs in /workflows
- Tools = deterministic Python scripts in /tools
- You (the agent) coordinate workflows and call tools in the right order.

## Goal of this repo
Build an MVP engine to extract structured product data for clothing listings (starting with jackets).
Inputs: product URL OR raw HTML.
Output: best-effort normalized JSON (name, brand, price, currency, materials text, parsed materials, etc.).
No UI in MVP. No scoring in MVP (yet).

## Operating rules
1) Prefer deterministic tools over "doing it in chat".
2) Before writing new code, check /tools and /workflows for something existing.
3) Make a plan first (5–8 bullets), then implement.
4) Add tests (no live network calls in tests).
5) Never bypass paywalls/auth, do not bulk crawl. One URL at a time with polite timeouts and delays.
6) If extraction fails, return partial output + "notes" explaining what happened (don't crash).

## Where things go
- /workflows: step-by-step SOPs
- /tools: python scripts that execute steps
- /.tmp: saved html, extracted json, logs (disposable)
- /tests: unit tests with embedded HTML strings

## MVP workflows to support
- workflows/extract_product.md
- workflows/parse_materials.md
- workflows/test_extraction.md
