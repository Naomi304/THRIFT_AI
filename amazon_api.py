import os
from dotenv import load_dotenv
import requests

# Load environment variables from .env file
load_dotenv(dotenv_path="C:/Users/naomi/THRIFT_AI/apikeys.env")

# Get the API key from .env
api_key = os.getenv('API_KEY') 

def get_amazon_data(brand, item_type, size, color, material, condition):
    amazon_url = "https://real-time-amazon-data.p.rapidapi.com/product-details"
    headers = {
        "X-RapidAPI-Key": api_key,
        "X-RapidAPI-Host": "real-time-amazon-data.p.rapidapi.com"
    }
    params = {
        "brand": brand,
        "type": item_type,
        "size": size,
        "color": color,
        "material": material,
        "condition": condition
    }
    
    response = requests.get(amazon_url, headers=headers, params=params)
    
    if response.status_code == 200:
        return response.json()
    else:
        return {"Error": response.status_code, "Message": response.text}

