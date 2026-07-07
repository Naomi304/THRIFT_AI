import os
from urllib.parse import urlparse

import requests
from dotenv import load_dotenv

# THRIFT_AI / Google Search API via RapidAPI
# Uses the same API_KEY from apikeys.env as your other API files.
#
# RapidAPI endpoint from your snippet:
# GET https://google-search74.p.rapidapi.com/?query=Nike&limit=10&related_keywords=true

load_dotenv("apikeys.env")

api_key = os.getenv("API_KEY")

GOOGLE_API_HOST = "google-search74.p.rapidapi.com"
GOOGLE_API_URL = f"https://{GOOGLE_API_HOST}/"


def build_google_query(brand, item_type, size, color, material, condition):
    """
    Build a search query from the THRIFT AI form.
    Add sale/thrift keywords so Google is more likely to return marketplace-style results.
    """

    query_parts = [brand, color, material, item_type, size, condition, "used", "for sale", "price"]

    return " ".join([
        str(part).strip()
        for part in query_parts
        if part and str(part).strip() and str(part).strip().lower() != "n/a"
    ])


def get_domain(url):
    """
    Convert a URL into a clean source/domain name.
    Example: https://www.ebay.com/item/... -> ebay.com
    """

    if not url:
        return "Google Result"

    try:
        parsed = urlparse(url)
        domain = parsed.netloc.replace("www.", "")
        return domain or "Google Result"
    except Exception:
        return "Google Result"


def extract_results_list(api_response):
    """
    Different Google Search APIs use different keys. This checks common response shapes.
    """

    if not isinstance(api_response, dict):
        return []

    possible_keys = [
        "results",
        "organic_results",
        "organic",
        "items",
        "data"
    ]

    for key in possible_keys:
        value = api_response.get(key)

        if isinstance(value, list):
            return value

        if isinstance(value, dict):
            for nested_key in possible_keys:
                nested_value = value.get(nested_key)
                if isinstance(nested_value, list):
                    return nested_value

    return []


def clean_google_results(api_response):
    """
    Convert Google search results into the same product-card format used by results.html.
    Regular Google search results may not include price or image, so those are optional.
    """

    products = []
    raw_results = extract_results_list(api_response)

    for item in raw_results[:10]:
        if not isinstance(item, dict):
            continue

        url = (
            item.get("url")
            or item.get("link")
            or item.get("href")
            or item.get("result_url")
            or "#"
        )

        title = (
            item.get("title")
            or item.get("name")
            or item.get("heading")
            or "No title"
        )

        snippet = (
            item.get("description")
            or item.get("snippet")
            or item.get("text")
            or ""
        )

        source_site = (
            item.get("source")
            or item.get("displayed_link")
            or item.get("domain")
            or get_domain(url)
        )

        image = (
            item.get("image")
            or item.get("thumbnail")
            or item.get("thumbnail_url")
            or ""
        )

        price = (
            item.get("price")
            or item.get("extracted_price")
            or item.get("sale_price")
            or ""
        )

        products.append({
            "title": title,
            "price": price if price else "Price unavailable",
            "location": "",
            "url": url,
            "image": image,
            "source": source_site,
            "snippet": snippet
        })

    return products


def get_google_data(brand, item_type, size, color, material, condition):
    """
    Search Google through RapidAPI and return normalized result cards.

    Returns:
    {
        "status": "Success" or "Error",
        "message": "...",
        "products": [...]
    }
    """

    if not api_key:
        return {
            "status": "Error",
            "message": "API_KEY is missing. Check apikeys.env.",
            "products": []
        }

    query = build_google_query(brand, item_type, size, color, material, condition)

    headers = {
        "Content-Type": "application/json",
        "X-RapidAPI-Host": GOOGLE_API_HOST,
        "X-RapidAPI-Key": api_key
    }

    params = {
        "query": query,
        "limit": "10",
        "related_keywords": "true"
    }

    try:
        response = requests.get(
            GOOGLE_API_URL,
            headers=headers,
            params=params,
            timeout=20
        )

        if response.status_code == 429:
            return {
                "status": "Error",
                "message": "Google API rate limit exceeded on RapidAPI. Wait a moment or upgrade the plan.",
                "products": []
            }

        if response.status_code != 200:
            return {
                "status": "Error",
                "message": f"HTTP {response.status_code}: {response.text[:200]}",
                "products": []
            }

        api_response = response.json()
        products = clean_google_results(api_response)

        return {
            "status": "Success",
            "message": f"Found {len(products)} Google results.",
            "products": products,
            "query": query
        }

    except requests.exceptions.Timeout:
        return {
            "status": "Error",
            "message": "Google API timed out. Try again.",
            "products": []
        }

    except Exception as e:
        return {
            "status": "Error",
            "message": str(e),
            "products": []
        }


if __name__ == "__main__":
    # Standalone test:
    result = get_google_data(
        brand="Nike",
        item_type="hoodie",
        size="M",
        color="black",
        material="cotton",
        condition="used"
    )

    print(result)
