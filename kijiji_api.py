import os
from dotenv import load_dotenv
import requests

# Load environment variables from .env file
load_dotenv(dotenv_path="C:/Users/naomi/THRIFT_AI/apikeys.env")

# Get the API key from the environment variables
api_key = os.getenv('API_KEY')

def get_kijiji_data(api_key, keyword="laptop", page=1, sort="dateDesc"):
    kijiji_url = "https://kijiji.p.rapidapi.com/searchByKeyword"
    
    # Set the headers with the RapidAPI key and host
    headers = {
        "X-RapidAPI-Key": api_key,
        "X-RapidAPI-Host": "kijiji.p.rapidapi.com"
    }
    
    # Parameters for search term (keyword), page, and sorting order
    params = {
        "keyword": keyword,   # Search term (e.g., "shirt")
        "page": page,         # Page number for pagination
        "sort": sort          # Sort by date or other options
    }
    
    # Print the request URL for debugging
    print(f"Request URL: {kijiji_url}?keyword={keyword}&page={page}&sort={sort}")
    
    # Send GET request to Kijiji API
    response = requests.get(kijiji_url, headers=headers, params=params)
    
    # Print response status and message for debugging
    print(f"Response Status: {response.status_code}")
    print(f"Response Message: {response.text}")

    # Check if the response is successful
    if response.status_code == 200:
        response_json = response.json()
        
        # Check if there is an error message in the response
        if 'error' in response_json:
            print(f"API Error: {response_json['error']}")
        else:
            return response_json  # Return JSON response with data
    else:
        return {"Error": response.status_code, "Message": response.text}


