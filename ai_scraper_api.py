import os
from dotenv import load_dotenv
import requests
import json

load_dotenv(dotenv_path="C:/Users/naomi/THRIFT_AI/apikeys.env")

api_key = os.getenv('API_KEY')

def get_ai_scraper_data(api_key, url="https://example.com", summary=False):
    ai_scraper_url = "https://ai-web-scraper1.p.rapidapi.com/"
    
    headers = {
        "Content-Type": "application/json",
        "x-rapidapi-host": "ai-web-scraper1.p.rapidapi.com",
        "x-rapidapi-key": api_key
    }

    data = {
        "url": url,       
        "summary": summary  
    }

    # Send POST request to AI Web Scraper API
    response = requests.post(ai_scraper_url, headers=headers, data=json.dumps(data))
    
    # Check if the response is successful
    if response.status_code == 200:
        return response.json()  # Return JSON response with data
    else:
        return {"Error": response.status_code, "Message": response.text}

# Example call to get the AI scraper data
url_to_scrape = "https://example.com"
ai_scraper_data = get_ai_scraper_data(api_key, url=url_to_scrape, summary=False)

# Print the results from the AI Web Scraper API
print("AI Scraper Data:", ai_scraper_data)
