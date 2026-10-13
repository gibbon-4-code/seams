"""
Product Extractor - Extract structured product data from HTML.
"""

import json
import re
from typing import Dict, List, Optional
from urllib.parse import urljoin, urlparse

from bs4 import BeautifulSoup
try:
    from price_parser import Price
    PRICE_PARSER_AVAILABLE = True
except ImportError:
    PRICE_PARSER_AVAILABLE = False

from .materials_parser import parse_materials

# Words that suggest a product description contains fabric/composition details
FABRIC_HINT_RE = re.compile(
    r"\b(materials?|composition|cotton|polyester|wool|nylon|polyamide|viscose|"
    r"rayon|elastane|spandex|linen|denim|fleece|gsm)\b",
    re.IGNORECASE,
)


def extract_product(html: str, source_url: Optional[str] = None) -> Dict:
    """
    Main orchestrator - extract product data from HTML.

    Args:
        html: HTML content
        source_url: Original URL (optional)

    Returns:
        Dictionary with product data following the schema
    """
    if not html:
        return _empty_result(source_url, notes=["Empty HTML provided"])

    soup = BeautifulSoup(html, "lxml")

    # Try extraction strategies in order
    data = {}
    method = "none"
    notes = []

    # Strategy 1: JSON-LD
    jsonld_data, jsonld_notes = extract_jsonld(soup)
    if jsonld_data and jsonld_data.get("product_name"):
        data.update(jsonld_data)
        method = "jsonld"
        notes.extend(jsonld_notes)

    # Strategy 1.5: JavaScript Config (fill in missing fields, especially materials)
    # Try if materials not found in JSON-LD
    if not data.get("materials_text"):
        js_config_data, js_config_notes = extract_js_config(soup)
        if js_config_data:
            # Fill missing fields from JS config
            for key, value in js_config_data.items():
                if key not in data or data[key] is None:
                    data[key] = value
            notes.extend(js_config_notes)
            # Update method if JS config provided the primary data
            if method == "none" and js_config_data.get("materials_text"):
                method = "js_config"

    # Strategy 2: OpenGraph (fill in missing fields)
    og_data = extract_opengraph(soup)
    if og_data:
        for key, value in og_data.items():
            if key not in data or data[key] is None:
                data[key] = value
        if method == "none" and og_data.get("product_name"):
            method = "opengraph"

    # Strategy 3: Heuristics (fill in remaining missing fields)
    heuristic_data = extract_heuristic(soup)
    if heuristic_data:
        for key, value in heuristic_data.items():
            if key not in data or data[key] is None:
                data[key] = value
        if method == "none":
            method = "heuristic"

    # Title tag fallback: if no product name found (or placeholder from client-side render)
    _bad_names = {"product not available", "loading...", "untitled", ""}
    if not data.get("product_name") or data.get("product_name", "").strip().lower() in _bad_names:
        title_tag = soup.find("title")
        if title_tag and title_tag.string:
            # Strip common suffixes like "| Brand Name" or "- Site Name"
            title = title_tag.string.strip()
            for sep in [" | ", " - ", " – ", " — "]:
                if sep in title:
                    title = title.split(sep)[0].strip()
                    break
            if title and title.upper() != "PRODUCT NOT AVAILABLE":
                data["product_name"] = title
                notes.append("product_name from <title> tag (client-side rendered page)")

    # Extract images (only if not already extracted from JSON-LD)
    if not data.get("images"):
        if source_url:
            data["images"] = extract_images(soup, source_url)
        else:
            data["images"] = extract_images(soup, "")

    # Parse materials if materials_text is present
    if data.get("materials_text"):
        structured, material_notes = parse_materials(data["materials_text"])
        data["materials_structured"] = structured
        notes.extend(material_notes)
    else:
        data["materials_structured"] = []

    # Determine confidence
    confidence = determine_confidence(data, method)

    # Build final result
    result = {
        "source_url": source_url or None,
        "product_name": data.get("product_name"),
        "brand": data.get("brand"),
        "price": data.get("price"),
        "materials_text": data.get("materials_text"),
        "materials_structured": data.get("materials_structured", []),
        "country_of_origin": data.get("country_of_origin"),
        "care_instructions": data.get("care_instructions"),
        "images": data.get("images", []),
        "extraction": {
            "method": method,
            "confidence": confidence,
            "notes": notes
        }
    }

    return result


def extract_jsonld(soup: BeautifulSoup) -> tuple[Dict, List[str]]:
    """
    Extract product data from JSON-LD structured data.

    Args:
        soup: BeautifulSoup object

    Returns:
        Tuple of (data dict, notes list)
    """
    data = {}
    notes = []

    try:
        # Get all script tags with type="application/ld+json"
        scripts = soup.find_all("script", {"type": "application/ld+json"})
        for script in scripts:
            try:
                jsonld = json.loads(script.string)

                # Handle @graph arrays
                items = []
                if isinstance(jsonld, dict):
                    if "@graph" in jsonld:
                        items = jsonld["@graph"]
                    else:
                        items = [jsonld]
                elif isinstance(jsonld, list):
                    items = jsonld

                # Look for Product type
                for item in items:
                    if not isinstance(item, dict):
                        continue

                    item_type = item.get("@type", "")
                    if isinstance(item_type, list):
                        item_type = " ".join(item_type)

                    if "Product" in item_type:
                        # Extract fields
                        if "name" in item:
                            data["product_name"] = item["name"]

                        if "brand" in item:
                            brand = item["brand"]
                            if isinstance(brand, dict):
                                data["brand"] = brand.get("name")
                            else:
                                data["brand"] = str(brand)

                        # Extract offers
                        if "offers" in item:
                            offers = item["offers"]
                            if isinstance(offers, dict):
                                offers = [offers]

                            if isinstance(offers, list) and len(offers) > 0:
                                # Use first offer
                                offer = offers[0]

                                if len(offers) > 1:
                                    notes.append(f"Multiple offers found ({len(offers)} variants)")

                                if "price" in offer:
                                    try:
                                        price_amount = float(offer["price"])
                                        currency = offer.get("priceCurrency", "GBP")
                                        data["price"] = {
                                            "amount": price_amount,
                                            "currency": currency
                                        }
                                    except (ValueError, TypeError):
                                        pass

                        # Extract materials: schema.org "material" property first,
                        # then the description if it talks about fabric (evaluators
                        # read GSM, cotton type, construction from it)
                        materials_parts = []
                        material = item.get("material")
                        if isinstance(material, list):
                            material = ", ".join(str(m) for m in material)
                        if isinstance(material, str) and material.strip():
                            materials_parts.append(material.strip())

                        desc = item.get("description")
                        if isinstance(desc, str) and FABRIC_HINT_RE.search(desc):
                            materials_parts.append(desc.strip())

                        if materials_parts:
                            data["materials_text"] = ". ".join(materials_parts)

                        # Extract images
                        if "image" in item:
                            images = item["image"]
                            if isinstance(images, str):
                                data["images"] = [images]
                            elif isinstance(images, list):
                                data["images"] = images

                        # Country of origin
                        if "countryOfOrigin" in item:
                            origin = item["countryOfOrigin"]
                            if isinstance(origin, dict):
                                data["country_of_origin"] = origin.get("name")
                            else:
                                data["country_of_origin"] = str(origin)

                        break  # Use first Product found

            except (json.JSONDecodeError, TypeError):
                continue

    except Exception as e:
        notes.append(f"JSON-LD parsing error: {str(e)}")

    return data, notes


def extract_js_config(soup: BeautifulSoup) -> tuple[Dict, List[str]]:
    """
    Extract product data from JavaScript config variables.

    Targets patterns like:
    - window.asos.pdp.config.productDescription = {...}
    - window.site.product.config = {...}

    Args:
        soup: BeautifulSoup object

    Returns:
        Tuple of (data dict, notes list)
    """
    data = {}
    notes = []

    # Find all script tags (exclude JSON-LD)
    scripts = soup.find_all("script")

    for script in scripts:
        # Skip JSON-LD scripts
        if script.get("type") == "application/ld+json":
            continue

        if not script.string:
            continue

        script_content = script.string

        # Pattern 1: ASOS productDescription
        asos_pattern = r'window\.asos\.pdp\.config\.productDescription\s*=\s*(\{[^;]+\});'
        match = re.search(asos_pattern, script_content, re.DOTALL)

        if match:
            try:
                json_str = match.group(1)
                config = json.loads(json_str)

                # Map ASOS-specific fields to standard schema
                if "aboutMe" in config:
                    # aboutMe contains materials composition
                    materials = config["aboutMe"]
                    # Strip HTML tags like <br>
                    materials = re.sub(r'<[^>]+>', ' ', materials)
                    materials = re.sub(r'\s+', ' ', materials).strip()
                    if materials and len(materials) > 10:
                        data["materials_text"] = materials

                if "careInfo" in config:
                    care = config["careInfo"]
                    care = re.sub(r'<[^>]+>', ' ', care)
                    care = re.sub(r'\s+', ' ', care).strip()
                    if care and len(care) > 5:
                        data["care_instructions"] = care

                if "sizeAndFit" in config:
                    size_info = config["sizeAndFit"]
                    size_info = re.sub(r'<[^>]+>', ' ', size_info)
                    size_info = re.sub(r'\s+', ' ', size_info).strip()
                    if size_info:
                        notes.append(f"Size info: {size_info}")

                if data:
                    notes.append("Extracted from ASOS JavaScript config")

            except json.JSONDecodeError as e:
                notes.append(f"Failed to parse ASOS config JSON: {str(e)}")
            except Exception as e:
                notes.append(f"Error extracting ASOS config: {str(e)}")

            # Stop after first match
            break

    return data, notes


def extract_opengraph(soup: BeautifulSoup) -> Dict:
    """
    Extract product data from OpenGraph and meta tags.

    Args:
        soup: BeautifulSoup object

    Returns:
        Dictionary with extracted data
    """
    data = {}

    # OpenGraph tags
    og_title = soup.find("meta", property="og:title")
    if og_title and og_title.get("content"):
        data["product_name"] = og_title["content"]

    og_image = soup.find("meta", property="og:image")
    if og_image and og_image.get("content"):
        data["images"] = [og_image["content"]]

    # Product-specific meta tags
    meta_brand = soup.find("meta", property="product:brand")
    if meta_brand and meta_brand.get("content"):
        data["brand"] = meta_brand["content"]

    meta_price = soup.find("meta", property="product:price:amount")
    if meta_price and meta_price.get("content"):
        try:
            price_amount = float(meta_price["content"])
            meta_currency = soup.find("meta", property="product:price:currency")
            currency = meta_currency["content"] if meta_currency else "GBP"
            data["price"] = {
                "amount": price_amount,
                "currency": currency
            }
        except (ValueError, TypeError):
            pass

    # Description
    og_desc = soup.find("meta", property="og:description")
    if og_desc and og_desc.get("content"):
        desc = og_desc["content"]
        if "material" in desc.lower() or "composition" in desc.lower():
            data["materials_text"] = desc

    return data


def extract_heuristic(soup: BeautifulSoup) -> Dict:
    """
    Extract product data using heuristics (text-based patterns).

    Args:
        soup: BeautifulSoup object

    Returns:
        Dictionary with extracted data
    """
    data = {}

    # Extract product name from h1 or title (prefer h1)
    if not data.get("product_name"):
        h1 = soup.find("h1")
        if h1:
            data["product_name"] = h1.get_text().strip()
        else:
            title = soup.find("title")
            if title:
                data["product_name"] = title.get_text().strip()

    # Extract brand (look for common class names and patterns)
    if not data.get("brand"):
        # Try class containing "brand"
        brand_elem = soup.find(class_=re.compile(r"brand", re.I))
        if brand_elem:
            data["brand"] = brand_elem.get_text().strip()
        else:
            # Try itemprop
            brand_elem = soup.find(attrs={"itemprop": "brand"})
            if brand_elem:
                data["brand"] = brand_elem.get_text().strip()
            else:
                # Try data-testid
                brand_elem = soup.find(attrs={"data-testid": re.compile(r"brand", re.I)})
                if brand_elem:
                    data["brand"] = brand_elem.get_text().strip()

    # Extract price using price-parser if available
    if not data.get("price") and PRICE_PARSER_AVAILABLE:
        price_selectors = [
            {"class_": re.compile(r"price", re.I)},
            {"itemprop": "price"},
            {"data-testid": re.compile(r"price", re.I)}
        ]
        for selector in price_selectors:
            price_elem = soup.find(attrs=selector)
            if price_elem:
                price_text = price_elem.get_text().strip()
                parsed = Price.fromstring(price_text)
                if parsed.amount:
                    data["price"] = {
                        "amount": float(parsed.amount),
                        "currency": parsed.currency or "GBP"
                    }
                    break

    # Extract materials/composition
    if not data.get("materials_text"):
        material_keywords = ["composition", "materials", "fabric", "shell", "lining", "fill"]
        for keyword in material_keywords:
            # Look for elements containing the keyword
            elements = soup.find_all(string=re.compile(keyword, re.I))
            for elem in elements:
                parent = elem.parent
                if parent:
                    # Try to get the parent's parent (containing div) first
                    grandparent = parent.parent
                    if grandparent:
                        text = grandparent.get_text().strip()
                        if len(text) > 20 and len(text) < 500 and ("%" in text or "cotton" in text.lower() or "wool" in text.lower()):
                            data["materials_text"] = text
                            break
                    # Fallback to parent
                    text = parent.get_text().strip()
                    if len(text) > 20 and len(text) < 500 and ("%" in text or "cotton" in text.lower() or "wool" in text.lower()):
                        data["materials_text"] = text
                        break
            if data.get("materials_text"):
                break

    # Extract care instructions
    care_keywords = ["care", "washing", "wash", "dry clean"]
    for keyword in care_keywords:
        elements = soup.find_all(string=re.compile(keyword, re.I))
        for elem in elements:
            parent = elem.parent
            if parent:
                text = parent.get_text().strip()
                if len(text) > 10 and len(text) < 300:
                    data["care_instructions"] = text
                    break
        if data.get("care_instructions"):
            break

    # Extract country of origin
    if not data.get("country_of_origin"):
        origin_keywords = ["made in", "origin", "country"]
        for keyword in origin_keywords:
            elements = soup.find_all(string=re.compile(keyword, re.I))
            for elem in elements:
                parent = elem.parent
                if parent:
                    text = parent.get_text().strip()
                    # Look for country names in the text
                    if len(text) > 5 and len(text) < 100:
                        data["country_of_origin"] = text
                        break
            if data.get("country_of_origin"):
                break

    return data


def extract_images(soup: BeautifulSoup, base_url: str) -> List[str]:
    """
    Extract product image URLs.

    Args:
        soup: BeautifulSoup object
        base_url: Base URL for resolving relative URLs

    Returns:
        List of image URLs
    """
    images = []

    # Look for product images
    img_selectors = [
        {"class_": re.compile(r"product.*image", re.I)},
        {"itemprop": "image"},
        {"data-testid": re.compile(r"image", re.I)},
    ]

    for selector in img_selectors:
        img_elems = soup.find_all("img", attrs=selector, limit=10)
        for img in img_elems:
            src = img.get("src") or img.get("data-src")
            if src:
                # Resolve relative URLs
                if base_url:
                    src = urljoin(base_url, src)
                if src not in images:
                    images.append(src)

    # If no images found, get any product-related images
    if not images:
        all_imgs = soup.find_all("img", limit=20)
        for img in all_imgs:
            src = img.get("src") or img.get("data-src")
            alt = img.get("alt", "")
            if src and ("product" in alt.lower() or "image" in alt.lower()):
                if base_url:
                    src = urljoin(base_url, src)
                if src not in images:
                    images.append(src)

    return images[:10]  # Limit to 10 images


def determine_confidence(data: Dict, method: str) -> str:
    """
    Calculate confidence level based on extracted data.

    Args:
        data: Extracted data dictionary
        method: Extraction method used

    Returns:
        Confidence level: "high", "medium", or "low"
    """
    # Count present fields
    required_fields = ["product_name", "price", "materials_text"]
    present = sum(1 for field in required_fields if data.get(field))

    # High confidence: all required fields + structured data source
    if present == 3 and method in ["jsonld", "js_config"]:
        return "high"

    # Medium confidence: name + price present
    if data.get("product_name") and data.get("price"):
        return "medium"

    # Low confidence: partial data only
    return "low"


def _empty_result(source_url: Optional[str], notes: List[str] = None) -> Dict:
    """
    Create an empty result with notes.

    Args:
        source_url: Source URL
        notes: List of notes

    Returns:
        Empty result dictionary
    """
    return {
        "source_url": source_url,
        "product_name": None,
        "brand": None,
        "price": None,
        "materials_text": None,
        "materials_structured": [],
        "country_of_origin": None,
        "care_instructions": None,
        "images": [],
        "extraction": {
            "method": "none",
            "confidence": "low",
            "notes": notes or []
        }
    }
