import os
from dotenv import load_dotenv
from amazon_api import get_amazon_data
from craigslist_api import get_craigslist_data
from kijiji_api import get_kijiji_data
from ai_scraper_api import get_ai_scraper_data

# Load environment variables
load_dotenv(dotenv_path="C:/Users/naomi/AppData/Local/Programs/Python/Python311/.env")
API_KEY = os.getenv('API_KEY')

# Example requests from all APIs
amazon_data = get_amazon_data(API_KEY)
craigslist_data = get_craigslist_data(API_KEY)
kijiji_data = get_kijiji_data(API_KEY)
ai_scraper_data = get_ai_scraper_data(API_KEY)

# Print the results for all APIs
print("Amazon Data:", amazon_data)
print("Craigslist Data:", craigslist_data)
print("Kijiji Data:", kijiji_data)
print("AI Scraper Data:", ai_scraper_data)
