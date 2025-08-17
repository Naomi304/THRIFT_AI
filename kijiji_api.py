import os
from dotenv import load_dotenv
import requests
import urllib.parse

# Load environment variables from .env file
load_dotenv(dotenv_path="C:/Users/naomi/THRIFT_AI/apikeys.env")

# Get the API key from the environment variables
api_key = os.getenv('API_KEY')

def get_kijiji_data_by_url(listing_url):
    """
    Fetches data from Kijiji API based on a provided listing URL.
    :param listing_url: The URL of the Kijiji listing to fetch data for
    :return: JSON response with search results or error message
    """
    # URL encode the provided URL
    encoded_url = urllib.parse.quote(listing_url, safe='')

    # Construct the URL for the "Search By URL" endpoint
    kijiji_url = f"https://kijiji.p.rapidapi.com/searchByURL?url={encoded_url}"

    headers = {
        "X-RapidAPI-Key": api_key,
        "X-RapidAPI-Host": "kijiji.p.rapidapi.com"
    }

    try:
        # Send the GET request to the Kijiji API
        response = requests.get(kijiji_url, headers=headers)

        print(f"Status Code: {response.status_code}")
        print("Response Content:", response.text)

        # Check if the response status code is 200 (OK)
        if response.status_code == 200:
            return response.json()  # Return the JSON response data
        else:
            print(f"Kijiji API Error: {response.status_code}, {response.text}")
            return None
    except Exception as e:
        print(f"Error fetching Kijiji listing data: {str(e)}")
        return None


# Test the function with a specific listing URL. GET RID OF THIS ONCE TESTING IS COMPLETE
 if __name__ == "__main__":
    test_url = "https://www.kijiji.ca/v-laptop/cambridge/dell-xps-15-9510-i7-rtx-3050-ti-32gb-1tb-ssd-4k-oled/1673450675"  # Real URL from Kijiji
    test_data = get_kijiji_data_by_url(test_url)

    if test_data:
        print("Test Data from Kijiji:", test_data)
    else:
        print("No data fetched from Kijiji or an error occurred.")
