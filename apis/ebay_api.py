import os
from dotenv import load_dotenv
import requests

# THRIFT_AI / eBay Average Selling Price API via RapidAPI
# This file uses the same API_KEY from apikeys.env as your other API files.

load_dotenv("apikeys.env")

api_key = os.getenv("API_KEY")

EBAY_API_HOST = "ebay-average-selling-price.p.rapidapi.com"
EBAY_API_URL = f"https://{EBAY_API_HOST}/findCompletedItems"


def build_ebay_query(brand, item_type, size, color, material, condition):
    """
    Build a clean eBay sold-items search query from the THRIFT AI form.
    Keep it not-too-specific so eBay can actually find matches.
    """

    query_parts = [brand, color, material, item_type, size]

    # eBay sold data usually uses "pre-owned" language instead of "thrifted"
    if condition and str(condition).lower() in ["used", "used/thrifted", "thrifted", "pre-owned", "preowned"]:
        query_parts.append("pre-owned")
    elif condition:
        query_parts.append(str(condition))

    return " ".join([str(part).strip() for part in query_parts if part and str(part).strip()])


def clean_ebay_products(api_response):
    """
    Convert the eBay API response into the same product-card format
    your results.html already understands.
    """

    products = []

    raw_products = api_response.get("products", [])

    for item in raw_products[:10]:
        sale_price = item.get("sale_price")
        currency = item.get("currency", "$")
        shipping_price = item.get("shipping_price")

        if sale_price is not None:
            price = f"{currency}{sale_price}"
        else:
            price = "Price unavailable"

        products.append({
            "title": item.get("title", "No title"),
            "price": price,
            "location": "",
            "url": item.get("link", "#"),
            "image": item.get("image_url", ""),
            "source": "eBay Sold",
            "condition": item.get("condition", ""),
            "date_sold": item.get("date_sold", ""),
            "buying_format": item.get("buying_format", ""),
            "shipping": f"{currency}{shipping_price}" if shipping_price is not None else ""
        })

    return products


def get_ebay_data(brand, item_type, size, color, material, condition):
    """
    Search eBay sold listings and return normalized product data for THRIFT AI.

    Returns:
    {
        "status": "Success" or "Error",
        "message": "...",
        "products": [...],
        "average_price": 0,
        "median_price": 0,
        "min_price": 0,
        "max_price": 0,
        "total_results": 0,
        "response_url": "..."
    }
    """

    if not api_key:
        return {
            "status": "Error",
            "message": "API_KEY is missing. Check apikeys.env.",
            "products": []
        }

    query = build_ebay_query(brand, item_type, size, color, material, condition)

    headers = {
        "X-RapidAPI-Key": api_key,
        "X-RapidAPI-Host": EBAY_API_HOST,
        "Content-Type": "application/json"
    }

    payload = {
        "keywords": query,
        "max_search_results": "60",
        "remove_outliers": "true"
    }

    try:
        response = requests.post(
            EBAY_API_URL,
            headers=headers,
            json=payload,
            timeout=20
        )

        if response.status_code == 429:
            return {
                "status": "Error",
                "message": "eBay API rate limit exceeded on RapidAPI. Wait a moment or upgrade the plan.",
                "products": []
            }

        if response.status_code != 200:
            return {
                "status": "Error",
                "message": f"HTTP {response.status_code}: {response.text[:200]}",
                "products": []
            }

        api_response = response.json()

        if api_response.get("success") is False:
            return {
                "status": "Error",
                "message": api_response.get("warning") or api_response.get("message") or "eBay API returned success=false.",
                "products": []
            }

        products = clean_ebay_products(api_response)

        avg = api_response.get("average_price")
        median = api_response.get("median_price")
        total = api_response.get("total_results") or api_response.get("results")

        message_parts = [f"Found {len(products)} eBay sold listings."]
        if median:
            message_parts.append(f"Median sold price: ${median}.")
        elif avg:
            message_parts.append(f"Average sold price: ${avg}.")

        return {
            "status": "Success",
            "message": " ".join(message_parts),
            "products": products,
            "average_price": avg,
            "median_price": median,
            "min_price": api_response.get("min_price"),
            "max_price": api_response.get("max_price"),
            "total_results": total,
            "response_url": api_response.get("response_url", "")
        }

    except requests.exceptions.Timeout:
        return {
            "status": "Error",
            "message": "eBay API timed out. Try again.",
            "products": []
        }

    except Exception as e:
        return {
            "status": "Error",
            "message": str(e),
            "products": []
        }


if __name__ == "__main__":
    # Quick standalone test:
    result = get_ebay_data(
        brand="Nike",
        item_type="hoodie",
        size="M",
        color="black",
        material="cotton",
        condition="used"
    )

    print(result)

