from typing import List, Dict, Any
from langchain.tools import BaseTool
import requests
import os
from pydantic import BaseModel, Field

class GoogleMapInput(BaseModel):
    query: str = Field(..., description="The search query for places or shops.")
    location: str = Field(None, description="Optional location to refine the search (latitude,longitude).")
    radius: int = Field(5000, description="Search radius in meters (default is 5000).")


class GoogleMapSearchTool(BaseTool):
    name: str = "GoogleMapSearch"
    description: str = (
        "Search for places or shops using Google Maps API. "
        "Input should be a query string describing the place or shop, and optionally a location."
    )
    args_schema = GoogleMapInput
    return_direct: bool = True

    def __init__(self, api_key: str = None):
        super().__init__()
        self.api_key = api_key or os.getenv("GOOGLE_MAPS_API_KEY")
        if not self.api_key:
            raise ValueError("Google Maps API key must be provided.")

    def _search_places(self, query: str, location: str = None, radius: int = 5000) -> List[Dict[str, Any]]:
        endpoint = "https://maps.googleapis.com/maps/api/place/textsearch/json"
        params = {
            "query": query,
            "key": self.api_key,
            "radius": radius
        }
        if location:
            params["location"] = location

        response = requests.get(endpoint, params=params)
        response.raise_for_status()
        results = response.json().get("results", [])
        return [
            {
                "name": place.get("name"),
                "address": place.get("formatted_address"),
                "location": place.get("geometry", {}).get("location"),
                "rating": place.get("rating"),
                "types": place.get("types"),
            }
            for place in results
        ]

    def _run(self, query: str, location: str = None) -> List[Dict[str, Any]]:
        return self._search_places(query, location)

    async def _arun(self, query: str, location: str = None) -> List[Dict[str, Any]]:
        """Asynchronous version of the run method."""
        return self._search_places(query, location)

# Example usage:
# tool = GoogleMapSearchTool(api_key="YOUR_API_KEY")
# results = tool.run("coffee shop", "13.7563,100.5018")  # Bangkok coordinates
# print(results)