import os
from dotenv import load_dotenv
import requests

# Load environment variables from .env file
load_dotenv(dotenv_path="C:/Users/naomi/THRIFT_AI/apikeys.env")

api_key = os.getenv('API_KEY') 


def get_craigslist_data(api_key, search="laptop", location="New York"):
    craigslist_url = "https://craigslist-data.p.rapidapi.com/categories"

    headers = {
        "X-RapidAPI-Key": api_key,
        "X-RapidAPI-Host": "craigslist-data.p.rapidapi.com"
    }

    params = {
        "search": search,
        "location": location
    }

    # Send GET request to Craigslist API
    response = requests.get(craigslist_url, headers=headers, params=params)

    # Check if the response is successful
    if response.status_code == 200:
        return response.json()  # Return JSON response with data
    else:
        return {"Error": response.status_code, "Message": response.text}
craigslist_data = get_craigslist_data(api_key)

print("Craigslist Data:", craigslist_data)