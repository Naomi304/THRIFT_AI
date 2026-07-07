import os
from urllib.parse import quote
from dotenv import load_dotenv
import requests

load_dotenv("apikeys.env")

api_key = os.getenv("API_KEY")

KIJIJI_HOST = "kijiji.p.rapidapi.com"
# /searchByKeyword on this provider is broken and returns
# {"error":"Error Searching By Keyword"} for any input. Use /searchByURL and
# feed it a Kijiji search URL built from the user's query.
SEARCH_BY_URL_ENDPOINT = f"https://{KIJIJI_HOST}/searchByURL"


def build_kijiji_search_url(keyword):
    """Build a Kijiji Canada-wide search URL from a keyword string.

    Kijiji search paths look like: /b-canada/<slug>/k0l0
    """
    slug = quote(keyword.strip().lower().replace(" ", "-"), safe="-")
    return f"https://www.kijiji.ca/b-canada/{slug}/k0l0"


def clean_kijiji_results(api_response):
    products = []

    raw_items = (
        api_response.get("results")
        or api_response.get("data")
        or api_response.get("listings")
        or api_response.get("ads")
        or []
    )

    for item in raw_items[:10]:
        products.append({
            "title": item.get("title", "No title"),
            "price": item.get("price", "Price unavailable"),
            "location": item.get("location", "Location unavailable"),
            "url": item.get("url") or item.get("link") or "#",
            "image": item.get("image") or item.get("thumbnail") or "",
            "source": "Kijiji"
        })

    return products


def get_kijiji_data(brand, item_type, size, color, material, condition):
    if not api_key:
        return {
            "status": "Error",
            "message": "API_KEY is missing. Check apikeys.env.",
            "products": []
        }

    query_parts = [brand, color, material, item_type, size, condition]
    keyword = " ".join([str(part) for part in query_parts if part]).strip()

    if not keyword:
        return {
            "status": "Error",
            "message": "No search terms provided.",
            "products": []
        }

    search_url = build_kijiji_search_url(keyword)

    headers = {
        "X-RapidAPI-Key": api_key,
        "X-RapidAPI-Host": KIJIJI_HOST
    }

    try:
        response = requests.get(
            SEARCH_BY_URL_ENDPOINT,
            headers=headers,
            params={"URL": search_url},
            timeout=15
        )

        if response.status_code == 429:
            return {
                "status": "Error",
                "message": "Kijiji API monthly quota exceeded on RapidAPI. Upgrade the plan or wait for reset.",
                "products": []
            }

        if response.status_code != 200:
            return {
                "status": "Error",
                "message": f"HTTP {response.status_code}: {response.text[:200]}",
                "products": []
            }

        try:
            api_response = response.json()
        except ValueError:
            return {
                "status": "Error",
                "message": f"Non-JSON response: {response.text[:200]}",
                "products": []
            }

        # Provider returns 200 with an error body for known failure modes.
        if isinstance(api_response, dict):
            if api_response.get("error"):
                return {
                    "status": "Error",
                    "message": f"Kijiji provider error: {api_response['error']}",
                    "products": []
                }
            if api_response.get("message") == "Invalid URL":
                return {
                    "status": "Error",
                    "message": f"Kijiji rejected search URL: {search_url}",
                    "products": []
                }

        products = clean_kijiji_results(api_response)

        return {
            "status": "Success",
            "message": f"Found {len(products)} Kijiji listings.",
            "products": products
        }

    except requests.Timeout:
        return {
            "status": "Error",
            "message": "Kijiji API request timed out.",
            "products": []
        }
    except Exception as e:
        return {
            "status": "Error",
            "message": str(e),
            "products": []
        }


if __name__ == "__main__":
    result = get_kijiji_data(
        brand="Nike",
        item_type="shirt",
        size="M",
        color="black",
        material="cotton",
        condition="used"
    )

    print(result)
