from typing import List, Dict, Any, Optional
from langchain.tools import BaseTool
import requests
import os
import logging
from pydantic import BaseModel, Field
from langchain_core.tools.base import ArgsSchema

# Set up logging for debugging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

class GoogleMapInput(BaseModel):
    query: str = Field(..., description="The search query for places or shops.")
    location: Optional[str] = Field(default=None, description="Optional location to refine the search (places).")
    radius: int = Field(default=5000, description="Search radius in meters (default is 5000).")


class GoogleMapSearchTool(BaseTool):
    name: str = "GoogleMapSearch"
    description: str = (
        "Search for places or shops using Google Maps API. "
        "Input should be a query string describing the place or shop, and optionally a location. "
        "This tool returns real places with names, addresses, and ratings. "
        "Use this to find actual places for budget planning, then incorporate the results into your response."
    )
    args_schema: Optional[ArgsSchema] = GoogleMapInput
    api_key: str = ""
    return_direct: bool = False  # Changed to False so the agent continues processing

    def __init__(self, api_key: str = None):
        super().__init__()
        self.api_key = api_key or os.getenv("GOOGLE_MAPS_API_KEY")
        if not self.api_key:
            raise ValueError("Google Maps API key must be provided either as parameter or GOOGLE_MAPS_API_KEY environment variable.")
        logger.info("GoogleMapSearchTool initialized successfully")
    def _get_lat_lng_from_location(self, location: str) -> Optional[str]:
        """Convert a location string to latitude and longitude."""
        try:
            endpoint = "https://maps.googleapis.com/maps/api/geocode/json"
            params = {
                "address": location,
                "key": self.api_key
            }
            logger.info(f"Geocoding location: {location}")
            response = requests.get(endpoint, params=params)
            response.raise_for_status()
            
            data = response.json()
            if data.get("status") != "OK":
                logger.error(f"Geocoding API error: {data.get('status')} - {data.get('error_message', 'Unknown error')}")
                return None
                
            results = data.get("results", [])
            if results:
                lat_lng = results[0].get("geometry", {}).get("location", {})
                coordinates = f"{lat_lng.get('lat')},{lat_lng.get('lng')}"
                logger.info(f"Successfully geocoded {location} to {coordinates}")
                return coordinates
            else:
                logger.warning(f"No geocoding results found for: {location}")
                return None
        except Exception as e:
            logger.error(f"Error geocoding location {location}: {str(e)}")
            return None

    def _search_places(self, query: str, location: str = None, radius: int = 5000) -> List[Dict[str, Any]]:
        """Search for places using Google Places API Text Search."""
        try:
            endpoint = "https://maps.googleapis.com/maps/api/place/textsearch/json"
            params = {
                "query": query,
                "key": self.api_key,
            }
            
            # Add location bias if provided
            if location:
                coordinates = self._get_lat_lng_from_location(location)
                if coordinates:
                    params["location"] = coordinates
                    params["radius"] = radius
                    logger.info(f"Searching with location bias: {coordinates}, radius: {radius}m")
                else:
                    logger.warning(f"Could not geocode location: {location}, searching without location bias")
            
            logger.info(f"Searching for: {query}")
            response = requests.get(endpoint, params=params)
            response.raise_for_status()
            
            data = response.json()
            status = data.get("status")
            
            if status == "OK":
                results = data.get("results", [])
                logger.info(f"Found {len(results)} results")
                return [
                    {
                        "name": place.get("name"),
                        "address": place.get("formatted_address"),
                        "location": place.get("geometry", {}).get("location"),
                        "rating": place.get("rating"),
                        "types": place.get("types"),
                        "place_id": place.get("place_id"),
                        "price_level": place.get("price_level")
                    }
                    for place in results
                ]
            elif status == "ZERO_RESULTS":
                logger.info("No places found for the query")
                return []
            elif status == "REQUEST_DENIED":
                error_msg = data.get("error_message", "API request denied")
                logger.error(f"API request denied: {error_msg}")
                raise Exception(f"Google Places API request denied: {error_msg}")
            elif status == "INVALID_REQUEST":
                error_msg = data.get("error_message", "Invalid request")
                logger.error(f"Invalid request: {error_msg}")
                raise Exception(f"Invalid Google Places API request: {error_msg}")
            elif status == "OVER_QUERY_LIMIT":
                logger.error("API query limit exceeded")
                raise Exception("Google Places API query limit exceeded")
            else:
                error_msg = data.get("error_message", f"Unknown status: {status}")
                logger.error(f"API error: {error_msg}")
                raise Exception(f"Google Places API error: {error_msg}")
                
        except requests.exceptions.RequestException as e:
            logger.error(f"Network error during places search: {str(e)}")
            raise Exception(f"Network error: {str(e)}")
        except Exception as e:
            logger.error(f"Error searching places: {str(e)}")
            raise

    def _run(self, query: str, location: str = None, radius: int = 5000) -> str:
        """Return a string summary of the search results for the LLM."""
        try:
            logger.info(f"Running Google Maps search: query='{query}', location='{location}', radius={radius}")
            places = self._search_places(query, location, radius)
            
            if not places:
                return f"No results found for '{query}'" + (f" near '{location}'" if location else "")
            
            output = [f"Found {len(places)} results for '{query}'" + (f" near '{location}'" if location else "") + ":\n"]
            
            for idx, place in enumerate(places[:10], 1):  # Limit to top 10 results
                rating_str = f"Rating: {place.get('rating', 'N/A')}"
                price_str = f"Price Level: {place.get('price_level', 'N/A')}" if place.get('price_level') else ""
                types_str = f"Types: {', '.join(place.get('types', [])[:3])}" if place.get('types') else ""
                
                result_line = f"{idx}. {place['name']}"
                if place.get('address'):
                    result_line += f" - {place['address']}"
                result_line += f" ({rating_str}"
                if price_str:
                    result_line += f", {price_str}"
                if types_str:
                    result_line += f", {types_str}"
                result_line += ")"
                
                output.append(result_line)
            
            result = "\n".join(output)
            logger.info("Search completed successfully")
            return result
            
        except Exception as e:
            error_msg = f"Error performing Google Maps search: {str(e)}"
            logger.error(error_msg)
            return error_msg

    async def _arun(self, query: str, location: str = None, radius: int = 5000) -> str:
        """Async version of _run."""
        # For now, just call the sync version since requests is not async
        # In production, you might want to use aiohttp for async requests
        return self._run(query, location, radius)

# Test function to validate API connectivity
def test_google_maps_api(api_key: str = None):
    """Test function to validate Google Maps API connectivity."""
    try:
        tool = GoogleMapSearchTool(api_key=api_key)
        result = tool._run("restaurant", "Bangkok", 1000)
        print("API Test Result:")
        print(result)
        return True
    except Exception as e:
        print(f"API Test Failed: {e}")
        return False

# Example usage and testing:
if __name__ == "__main__":
    # Test the API
    print("Testing Google Maps API...")
    test_google_maps_api()
    
    # Example usage:
    # tool = GoogleMapSearchTool(api_key="YOUR_API_KEY")
    # results = tool.run("coffee shop", "Bangkok")
    # print(results)