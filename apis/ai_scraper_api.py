import os
from dotenv import load_dotenv
import requests
import json

# Use a relative path like the other API modules so this works on any
# machine / deployment, not just the original dev box.
load_dotenv("apikeys.env")

api_key = os.getenv('API_KEY')

def get_ai_scraper_data(url="https://example.com", summary=False):
    if not api_key:
        return {"status": "Error", "message": "API_KEY is missing. Check apikeys.env."}

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

    try:
        # Timeout so a slow/hung scraper can't block the whole /search request
        # (all APIs run in a ThreadPoolExecutor that waits for every task).
        response = requests.post(
            ai_scraper_url, headers=headers, data=json.dumps(data), timeout=20
        )
    except requests.exceptions.Timeout:
        return {"status": "Error", "message": "AI scraper timed out."}
    except Exception as e:
        return {"status": "Error", "message": str(e)}

    # Check if the response is successful
    if response.status_code == 200:
        return response.json()  # Return JSON response with data
    else:
        return {"Error": response.status_code, "Message": response.text}
