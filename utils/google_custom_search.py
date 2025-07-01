# tools/google_custom_search.py
import os
import requests
from dotenv import load_dotenv

load_dotenv()

GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")
GOOGLE_CSE_ID = os.getenv("GOOGLE_CSE_ID")

def google_custom_search(query, num_results=5):
    url = "https://www.googleapis.com/customsearch/v1"
    params = {
        "key": GOOGLE_API_KEY,
        "cx": GOOGLE_CSE_ID,
        "q": query,
        "num": num_results
    }

    response = requests.get(url, params=params)
    results = response.json()

    if "items" not in results:
        return "No results found."

    output = ""
    for item in results["items"]:
        title = item.get("title")
        snippet = item.get("snippet")
        link = item.get("link")
        output += f"{title}\n{snippet}\n{link}\n\n"

    return output.strip()
