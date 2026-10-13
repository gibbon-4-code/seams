"""
CLI - Command-line interface for product extraction.

Usage:
    python cli.py --url "https://example.com/product"
    python cli.py --html-file "saved.html"
    echo "<html>...</html>" | python cli.py --html-stdin
"""

import argparse
import json
import sys
import os
from datetime import datetime
from pathlib import Path
from urllib.parse import urlparse

from tools.html_fetcher import fetch_html, validate_url
from tools.product_extractor import extract_product


def ensure_tmp_dirs():
    """Create .tmp/ directory structure if it doesn't exist."""
    tmp_dir = Path(".tmp")
    tmp_dir.mkdir(exist_ok=True)
    (tmp_dir / "html").mkdir(exist_ok=True)
    (tmp_dir / "json").mkdir(exist_ok=True)
    (tmp_dir / "logs").mkdir(exist_ok=True)


def get_timestamp_filename(url_or_name: str, extension: str) -> str:
    """
    Generate a timestamped filename.

    Args:
        url_or_name: URL or name to extract identifier from
        extension: File extension (e.g., 'html', 'json')

    Returns:
        Timestamped filename
    """
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")

    # Extract a short identifier from URL or name
    if url_or_name.startswith("http"):
        parsed = urlparse(url_or_name)
        # Use domain + path
        identifier = parsed.netloc.replace("www.", "").split(".")[0]
    else:
        identifier = "file"

    return f"{timestamp}_{identifier}.{extension}"


def save_html(html: str, source_identifier: str) -> Path:
    """
    Save HTML to .tmp/html/ with timestamp.

    Args:
        html: HTML content
        source_identifier: URL or filename identifier

    Returns:
        Path to saved file
    """
    filename = get_timestamp_filename(source_identifier, "html")
    filepath = Path(".tmp") / "html" / filename

    with open(filepath, "w", encoding="utf-8") as f:
        f.write(html)

    return filepath


def save_json(data: dict, source_identifier: str) -> Path:
    """
    Save JSON to .tmp/json/ with timestamp.

    Args:
        data: Data dictionary
        source_identifier: URL or filename identifier

    Returns:
        Path to saved file
    """
    filename = get_timestamp_filename(source_identifier, "json")
    filepath = Path(".tmp") / "json" / filename

    with open(filepath, "w", encoding="utf-8") as f:
        json.dump(data, f, indent=2, ensure_ascii=False)

    return filepath


def main():
    """Main CLI entry point."""
    parser = argparse.ArgumentParser(
        description="Extract structured product data from clothing listings",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  python cli.py --url "https://www.asos.com/product/123"
  python cli.py --html-file "saved_page.html"
  echo "<html>...</html>" | python cli.py --html-stdin

Output is printed to stdout and automatically saved to .tmp/
        """
    )

    # Input mode arguments (mutually exclusive)
    input_group = parser.add_mutually_exclusive_group(required=True)
    input_group.add_argument(
        "--url",
        type=str,
        help="Product URL to fetch and extract"
    )
    input_group.add_argument(
        "--html-file",
        type=str,
        help="Path to HTML file to extract from"
    )
    input_group.add_argument(
        "--html-stdin",
        action="store_true",
        help="Read HTML from stdin"
    )

    args = parser.parse_args()

    # Ensure .tmp/ directories exist
    ensure_tmp_dirs()

    html = ""
    source_url = None
    source_identifier = "unknown"
    fetch_metadata = {}

    try:
        # URL mode
        if args.url:
            if not validate_url(args.url):
                print("Error: Invalid URL format", file=sys.stderr)
                sys.exit(1)

            print(f"Fetching URL: {args.url}", file=sys.stderr)
            html, fetch_metadata = fetch_html(args.url)

            if fetch_metadata.get("warnings"):
                for warning in fetch_metadata["warnings"]:
                    print(f"Warning: {warning}", file=sys.stderr)

            if not html:
                print("Error: Failed to fetch HTML", file=sys.stderr)
                sys.exit(1)

            source_url = args.url
            source_identifier = args.url

        # HTML file mode
        elif args.html_file:
            filepath = Path(args.html_file)
            if not filepath.exists():
                print(f"Error: File not found: {args.html_file}", file=sys.stderr)
                sys.exit(1)

            print(f"Reading HTML from: {args.html_file}", file=sys.stderr)
            with open(filepath, "r", encoding="utf-8") as f:
                html = f.read()

            source_identifier = filepath.stem

        # Stdin mode
        elif args.html_stdin:
            print("Reading HTML from stdin...", file=sys.stderr)
            html = sys.stdin.read()
            source_identifier = "stdin"

        # Validate HTML
        if not html or len(html) < 100:
            print("Error: HTML too short or empty", file=sys.stderr)
            sys.exit(1)

        # Save HTML to .tmp/
        html_path = save_html(html, source_identifier)
        print(f"Saved HTML to: {html_path}", file=sys.stderr)

        # Extract product data
        print("Extracting product data...", file=sys.stderr)
        result = extract_product(html, source_url)

        # Add fetch metadata to extraction notes if present
        if fetch_metadata.get("warnings"):
            result["extraction"]["notes"].extend(fetch_metadata["warnings"])

        # Save JSON to .tmp/
        json_path = save_json(result, source_identifier)
        print(f"Saved JSON to: {json_path}", file=sys.stderr)

        # Print JSON to stdout (pretty-printed)
        print(json.dumps(result, indent=2, ensure_ascii=False))

        # Print summary to stderr
        print("\n" + "="*60, file=sys.stderr)
        print(f"Extraction complete!", file=sys.stderr)
        print(f"  Method: {result['extraction']['method']}", file=sys.stderr)
        print(f"  Confidence: {result['extraction']['confidence']}", file=sys.stderr)
        print(f"  Product: {result['product_name'] or 'N/A'}", file=sys.stderr)
        print(f"  Brand: {result['brand'] or 'N/A'}", file=sys.stderr)
        if result['price']:
            print(f"  Price: {result['price']['amount']} {result['price']['currency']}", file=sys.stderr)
        else:
            print(f"  Price: N/A", file=sys.stderr)
        print("="*60, file=sys.stderr)

        sys.exit(0)

    except KeyboardInterrupt:
        print("\nInterrupted by user", file=sys.stderr)
        sys.exit(1)

    except Exception as e:
        print(f"Error: {str(e)}", file=sys.stderr)
        import traceback
        traceback.print_exc(file=sys.stderr)
        sys.exit(1)


if __name__ == "__main__":
    main()
