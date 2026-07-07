import os
from dotenv import load_dotenv
import requests

load_dotenv("apikeys.env")

api_key = os.getenv("API_KEY")


def clean_craigslist_results(api_response):
    products = []

    raw_items = api_response.get("data", [])

    for item in raw_items[:10]:
        products.append({
            "title": item.get("title", "No title"),
            "price": item.get("price", "Price unavailable"),
            "location": item.get("location", "Location unavailable"),
            "url": item.get("url", "#"),
            "source": "Craigslist"
        })

    return products


def get_craigslist_data(brand, item_type, size, color, material, condition):
    if not api_key:
        return {
            "status": "Error",
            "message": "API_KEY is missing. Check apikeys.env.",
            "products": []
        }

    craigslist_url = "https://craigslist-data.p.rapidapi.com/search"

    headers = {
        "X-RapidAPI-Key": api_key,
        "X-RapidAPI-Host": "craigslist-data.p.rapidapi.com",
        "Content-Type": "application/json"
    }

    query_parts = [brand, color, material, item_type, size, condition]
    query = " ".join([str(part) for part in query_parts if part])

    payload = {
        "query": query,
        "gl": "newyork",
        "hl": "en",
        "has_pic": False,
        "posted_today": False,
        "show_duplicates": False,
        "search_title_only": False,
        "search_distance": 0,
        "page": 0
    }

    try:
        response = requests.post(
            craigslist_url,
            headers=headers,
            json=payload,
            timeout=15
        )

        print("Craigslist status:", response.status_code)
        print("Craigslist response:", response.text)

        if response.status_code != 200:
            return {
                "status": "Error",
                "message": response.text,
                "products": []
            }

        api_response = response.json()
        products = clean_craigslist_results(api_response)

        return {
            "status": "Success",
            "message": f"Found {len(products)} Craigslist listings.",
            "products": products
        }

    except Exception as e:
        return {
            "status": "Error",
            "message": str(e),
            "products": []
        }