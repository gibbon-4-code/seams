"""
HTML Fetcher - Fetch HTML from URLs with polite delays and error handling.
"""

import time
import requests
from typing import Tuple, Dict, Optional


def fetch_html(url: str, timeout: int = 15, delay: float = 0.5) -> Tuple[str, Dict]:
    """
    Fetch HTML from a URL with proper error handling.

    Args:
        url: The URL to fetch
        timeout: Request timeout in seconds (default: 15)
        delay: Polite delay before making request in seconds (default: 0.5)

    Returns:
        Tuple of (html_content, metadata)
        metadata includes: final_url, status_code, warnings (list)

    Never crashes - always returns something with notes in metadata.
    """
    metadata = {
        "final_url": url,
        "status_code": None,
        "warnings": []
    }

    # Polite delay before making request
    if delay > 0:
        time.sleep(delay)

    # Sensible headers to identify ourselves
    headers = {
        "User-Agent": "Seams/1.0 (Product Data Extraction Bot; Educational/Research Purpose)",
        "Accept": "text/html,application/xhtml+xml,application/xml;q=0.9,*/*;q=0.8",
        "Accept-Language": "en-US,en;q=0.9",
        "Accept-Encoding": "gzip, deflate",
        "DNT": "1",
        "Connection": "keep-alive",
        "Upgrade-Insecure-Requests": "1"
    }

    try:
        response = requests.get(
            url,
            headers=headers,
            timeout=timeout,
            allow_redirects=True
        )

        metadata["status_code"] = response.status_code
        metadata["final_url"] = response.url

        # Handle redirects
        if response.history:
            metadata["warnings"].append(
                f"Redirected {len(response.history)} time(s). Final URL: {response.url}"
            )

        # Check for common bot-detection status codes
        if response.status_code == 403:
            metadata["warnings"].append(
                "403 Forbidden - Site may have bot detection. Try HTML-file mode instead."
            )
            return response.text, metadata

        elif response.status_code == 429:
            metadata["warnings"].append(
                "429 Too Many Requests - Rate limited. Try HTML-file mode or wait before retrying."
            )
            return response.text, metadata

        elif response.status_code >= 400:
            metadata["warnings"].append(
                f"HTTP {response.status_code} error. Returning partial content if available."
            )
            return response.text, metadata

        # Success
        return response.text, metadata

    except requests.exceptions.Timeout:
        metadata["warnings"].append(
            f"Request timeout after {timeout}s. Try HTML-file mode or increase timeout."
        )
        return "", metadata

    except requests.exceptions.ConnectionError as e:
        metadata["warnings"].append(
            f"Connection error: {str(e)}. Check URL and network connection."
        )
        return "", metadata

    except requests.exceptions.TooManyRedirects:
        metadata["warnings"].append(
            "Too many redirects. URL may be broken or redirecting in a loop."
        )
        return "", metadata

    except requests.exceptions.RequestException as e:
        metadata["warnings"].append(
            f"Request error: {str(e)}. Try HTML-file mode."
        )
        return "", metadata

    except Exception as e:
        metadata["warnings"].append(
            f"Unexpected error: {str(e)}. Try HTML-file mode."
        )
        return "", metadata


def validate_url(url: str) -> bool:
    """
    Basic URL validation.

    Args:
        url: URL string to validate

    Returns:
        True if URL appears valid, False otherwise
    """
    if not url:
        return False

    url_lower = url.lower()
    if not (url_lower.startswith("http://") or url_lower.startswith("https://")):
        return False

    return True
