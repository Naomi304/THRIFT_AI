import os
from dotenv import load_dotenv
import requests

# Load environment variables from .env file
load_dotenv(dotenv_path="C:/Users/naomi/THRIFT_AI/apikeys.env")

# Get the API key from .env
api_key = os.getenv('API_KEY') 

def get_amazon_data(api_key, asin="B07ZPKBL9V"):
    amazon_url = "https://real-time-amazon-data.p.rapidapi.com/product-details"
    headers = {
        "X-RapidAPI-Key": api_key,
        "X-RapidAPI-Host": "real-time-amazon-data.p.rapidapi.com"
    }
    params = {
        "asin": asin,
        "country": "US"
    }
    
    # request to API
    response = requests.get(amazon_url, headers=headers, params=params)
    
    if response.status_code == 200:
        return response.json()
    else:
        return {"Error": response.status_code, "Message": response.text}

# test
amazon_data = get_amazon_data(api_key)
print("Amazon Data:", amazon_data)

'''

def get_amazon_data(product_name):
    headers = {"X-RapidAPI-Key": API_KEY}
    params = {"search": product_name}
    response = requests.get("https://amazon-scraper.p.rapidapi.com", headers=headers, params=params)
    return response.json()

def get_kijiji_data(product_name):
    headers = {"X-RapidAPI-Key": API_KEY}
    params = {"search": product_name}
    response = requests.get("https://kijiji-scraper.p.rapidapi.com", headers=headers, params=params)
    return response.json()

def get_craigslist_data(product_name):
    headers = {"X-RapidAPI-Key": API_KEY}
    params = {"search": product_name}
    response = requests.get("https://craigslist-scraper.p.rapidapi.com", headers=headers, params=params)
    return response.json()

# Example: Fetch product data from all platforms
product_name = "shirt"
amazon_data = get_amazon_data(product_name)
kijiji_data = get_kijiji_data(product_name)
craigslist_data = get_craigslist_data(product_name)

print(amazon_data)
print(kijiji_data)
print(craigslist_data)'''
