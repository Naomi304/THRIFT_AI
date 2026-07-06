import os
from dotenv import load_dotenv
import requests

load_dotenv("apikeys.env")

api_key = os.getenv("API_KEY")


def clean_amazon_products(api_response):
    """
    Converts the huge Amazon API JSON into a simple list of products
    your results page can actually display.
    """

    products = []

    try:
        raw_products = api_response.get("data", {}).get("products", [])

        for item in raw_products[:10]:
            product = {
                "title": item.get("product_title", "No title"),
                "price": item.get("product_price", "Price unavailable"),
                "rating": item.get("product_star_rating", "No rating"),
                "reviews": item.get("product_num_ratings", "No reviews"),
                "image": item.get("product_photo", ""),
                "url": item.get("product_url", "#"),
                "source": "Amazon"
            }

            products.append(product)

    except Exception as e:
        print("Error cleaning Amazon data:", e)

    return products


def get_amazon_data(brand, item_type, size, color, material, condition):
    if not api_key:
        return {
            "status": "Error",
            "message": "API_KEY is missing.",
            "products": []
        }

    query_parts = [brand, color, material, item_type, size, condition]
    query = " ".join([str(part) for part in query_parts if part])

    amazon_url = "https://real-time-amazon-data.p.rapidapi.com/search"

    headers = {
        "X-RapidAPI-Key": api_key,
        "X-RapidAPI-Host": "real-time-amazon-data.p.rapidapi.com"
    }

    params = {
        "query": query,
        "country": "US",
        "page": "1",
        "sort_by": "RELEVANCE",
        "is_prime": "false",
        "language": "en_US"
    }

    try:
        response = requests.get(
            amazon_url,
            headers=headers,
            params=params,
            timeout=15
        )

        print("Amazon status:", response.status_code)

        if response.status_code != 200:
            return {
                "status": "Error",
                "message": response.text,
                "products": []
            }

        api_response = response.json()
        products = clean_amazon_products(api_response)

        return {
            "status": "Success",
            "message": f"Found {len(products)} Amazon products.",
            "products": products
        }

    except Exception as e:
        return {
            "status": "Error",
            "message": str(e),
            "products": []
        }