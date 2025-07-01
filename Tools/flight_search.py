from typing import List, Dict, Any, Optional
from langchain.tools import BaseTool
import logging
from pydantic import BaseModel, Field
from langchain_core.tools.base import ArgsSchema
from datetime import datetime, timedelta
import json

# Set up logging for debugging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

try:
    from fast_flights import FlightData, Passengers, Result, get_flights
except ImportError:
    logger.error("fast-flights package not installed. Please install with: pip install fast-flights")
    raise ImportError("fast-flights package is required but not installed")


class FlightSearchInput(BaseModel):
    from_airport: str = Field(..., description="IATA code of departure airport (e.g., 'TPE', 'JFK', 'LAX')")
    to_airport: str = Field(..., description="IATA code of destination airport (e.g., 'NRT', 'LHR', 'CDG')")
    departure_date: str = Field(..., description="Departure date in YYYY-MM-DD format (e.g., '2025-01-15')")
    return_date: Optional[str] = Field(default=None, description="Return date in YYYY-MM-DD format for round-trip flights (optional)")
    trip_type: str = Field(default="one-way", description="Trip type: 'one-way' or 'round-trip'")
    seat_class: str = Field(default="economy", description="Seat class: 'economy', 'premium-economy', 'business', or 'first'")
    adults: int = Field(default=1, description="Number of adult passengers (1-9)")
    children: int = Field(default=0, description="Number of child passengers (0-8)")
    infants_in_seat: int = Field(default=0, description="Number of infants with their own seat (0-5)")
    infants_on_lap: int = Field(default=0, description="Number of infants on lap (0-5)")


class FlightSearchTool(BaseTool):
    name: str = "FlightSearch"
    description: str = (
        "Search for flights using Google Flights data. "
        "Input should include departure and destination airport codes (IATA format), "
        "departure date, and optionally return date for round-trip flights. "
        "This tool returns real flight information including prices, airlines, duration, and stops. "
        "Use this to find actual flight options for budget planning."
    )
    args_schema: Optional[ArgsSchema] = FlightSearchInput
    return_direct: bool = False

    def __init__(self):
        super().__init__()
        logger.info("FlightSearchTool initialized successfully")

    def _validate_date(self, date_str: str) -> bool:
        """Validate date format and ensure it's not in the past."""
        try:
            date_obj = datetime.strptime(date_str, "%Y-%m-%d")
            # Check if date is not in the past (allow today)
            if date_obj.date() < datetime.now().date():
                return False
            return True
        except ValueError:
            return False

    def _validate_airport_code(self, code: str) -> bool:
        """Basic validation for IATA airport codes."""
        return len(code) == 3 and code.isalpha() and code.isupper()

    def _format_flight_info(self, flight) -> Dict[str, Any]:
        """Format flight information for better readability."""
        try:
            return {
                "airline": getattr(flight, 'name', 'Unknown'),
                "departure_time": getattr(flight, 'departure', 'N/A'),
                "arrival_time": getattr(flight, 'arrival', 'N/A'),
                "duration": getattr(flight, 'duration', 'N/A'),
                "stops": getattr(flight, 'stops', 'N/A'),
                "price": getattr(flight, 'price', 'N/A'),
                "is_best": getattr(flight, 'is_best', False),
                "delay": getattr(flight, 'delay', None),
                "time_ahead": getattr(flight, 'arrival_time_ahead', None)
            }
        except Exception as e:
            logger.error(f"Error formatting flight info: {str(e)}")
            return {"error": "Could not format flight information"}

    def _search_flights(self, from_airport: str, to_airport: str, departure_date: str, 
                       return_date: Optional[str] = None, trip_type: str = "one-way",
                       seat_class: str = "economy", adults: int = 1, children: int = 0,
                       infants_in_seat: int = 0, infants_on_lap: int = 0) -> Result:
        """Search for flights using the fast-flights library."""
        try:
            # Prepare flight data
            flight_data = [
                FlightData(date=departure_date, from_airport=from_airport, to_airport=to_airport)
            ]
            
            # Add return flight data for round-trip
            if trip_type == "round-trip" and return_date:
                flight_data.append(
                    FlightData(date=return_date, from_airport=to_airport, to_airport=from_airport)
                )

            # Create passengers object
            passengers = Passengers(
                adults=adults,
                children=children,
                infants_in_seat=infants_in_seat,
                infants_on_lap=infants_on_lap
            )

            logger.info(f"Searching flights: {from_airport} → {to_airport} on {departure_date}")
            if trip_type == "round-trip" and return_date:
                logger.info(f"Return flight: {to_airport} → {from_airport} on {return_date}")

            # Perform the search with fallback mode for better reliability
            result = get_flights(
                flight_data=flight_data,
                trip=trip_type,
                seat=seat_class,
                passengers=passengers,
                fetch_mode="fallback"  # Use fallback mode for better reliability
            )

            return result

        except Exception as e:
            logger.error(f"Error searching flights: {str(e)}")
            raise

    def _run(self, from_airport: str, to_airport: str, departure_date: str,
             return_date: Optional[str] = None, trip_type: str = "one-way",
             seat_class: str = "economy", adults: int = 1, children: int = 0,
             infants_in_seat: int = 0, infants_on_lap: int = 0) -> str:
        """Return a string summary of the flight search results for the LLM."""
        try:
            # Input validation
            if not self._validate_airport_code(from_airport):
                return f"Invalid departure airport code: {from_airport}. Please use 3-letter IATA codes (e.g., 'JFK', 'LAX')."
            
            if not self._validate_airport_code(to_airport):
                return f"Invalid destination airport code: {to_airport}. Please use 3-letter IATA codes (e.g., 'JFK', 'LAX')."
            
            if not self._validate_date(departure_date):
                return f"Invalid departure date: {departure_date}. Please use YYYY-MM-DD format and ensure the date is not in the past."
            
            if trip_type == "round-trip":
                if not return_date:
                    return "Return date is required for round-trip flights."
                if not self._validate_date(return_date):
                    return f"Invalid return date: {return_date}. Please use YYYY-MM-DD format and ensure the date is not in the past."
                
                # Check if return date is after departure date
                dep_date = datetime.strptime(departure_date, "%Y-%m-%d")
                ret_date = datetime.strptime(return_date, "%Y-%m-%d")
                if ret_date <= dep_date:
                    return "Return date must be after departure date."

            if adults < 1 or adults > 9:
                return "Number of adults must be between 1 and 9."
            
            if children < 0 or children > 8:
                return "Number of children must be between 0 and 8."

            logger.info(f"Running flight search: {from_airport} → {to_airport} on {departure_date}")
            
            # Perform the search
            result = self._search_flights(
                from_airport=from_airport,
                to_airport=to_airport,
                departure_date=departure_date,
                return_date=return_date,
                trip_type=trip_type,
                seat_class=seat_class,
                adults=adults,
                children=children,
                infants_in_seat=infants_in_seat,
                infants_on_lap=infants_on_lap
            )

            # Format the results
            output = []
            
            # Add search summary
            passenger_summary = f"{adults} adult(s)"
            if children > 0:
                passenger_summary += f", {children} child(ren)"
            if infants_in_seat > 0:
                passenger_summary += f", {infants_in_seat} infant(s) with seat"
            if infants_on_lap > 0:
                passenger_summary += f", {infants_on_lap} infant(s) on lap"

            trip_summary = f"{trip_type} trip from {from_airport} to {to_airport}"
            if trip_type == "round-trip" and return_date:
                trip_summary += f" (return {return_date})"
            
            output.append(f"Flight Search Results for {trip_summary}")
            output.append(f"Passengers: {passenger_summary}")
            output.append(f"Seat Class: {seat_class.title()}")
            output.append(f"Departure Date: {departure_date}")
            
            # Add price trend information if available
            if hasattr(result, 'current_price') and result.current_price:
                output.append(f"Current Price Trend: {result.current_price}")
            
            output.append("")  # Empty line for formatting

            # Check if flights were found
            if not hasattr(result, 'flights') or not result.flights:
                output.append("No flights found for the specified criteria.")
                output.append("Suggestions:")
                output.append("- Try different dates")
                output.append("- Check if airport codes are correct")
                output.append("- Consider nearby airports")
                return "\n".join(output)

            # Display flight results
            flights = result.flights[:10]  # Limit to top 10 results
            output.append(f"Found {len(flights)} flight options:\n")

            for idx, flight in enumerate(flights, 1):
                flight_info = self._format_flight_info(flight)
                
                if "error" in flight_info:
                    continue
                
                # Mark best flights
                best_indicator = " ⭐ BEST DEAL" if flight_info.get('is_best', False) else ""
                
                flight_line = f"{idx}. {flight_info['airline']}{best_indicator}"
                output.append(flight_line)
                
                # Add flight details
                if flight_info['departure_time'] != 'N/A':
                    output.append(f"   Departure: {flight_info['departure_time']}")
                if flight_info['arrival_time'] != 'N/A':
                    output.append(f"   Arrival: {flight_info['arrival_time']}")
                if flight_info['duration'] != 'N/A':
                    output.append(f"   Duration: {flight_info['duration']}")
                if flight_info['stops'] != 'N/A':
                    stops_text = "Direct flight" if flight_info['stops'] == 0 else f"{flight_info['stops']} stop(s)"
                    output.append(f"   Stops: {stops_text}")
                if flight_info['price'] != 'N/A':
                    output.append(f"   Price: {flight_info['price']}")
                if flight_info['delay']:
                    output.append(f"   Delay: {flight_info['delay']}")
                
                output.append("")  # Empty line between flights

            # Add helpful tips
            output.append("💡 Tips:")
            output.append("- Prices may vary and are subject to availability")
            output.append("- Consider booking flexibility for better deals")
            output.append("- Check airline websites for the most up-to-date information")
            
            result_text = "\n".join(output)
            logger.info("Flight search completed successfully")
            return result_text

        except Exception as e:
            error_msg = f"Error performing flight search: {str(e)}"
            logger.error(error_msg)
            
            # Provide helpful error message
            if "connection" in str(e).lower() or "network" in str(e).lower():
                return f"Network error occurred while searching for flights. Please check your internet connection and try again. Error: {str(e)}"
            elif "api" in str(e).lower():
                return f"Flight search service is temporarily unavailable. Please try again later. Error: {str(e)}"
            else:
                return f"An error occurred while searching for flights: {str(e)}"

    async def _arun(self, from_airport: str, to_airport: str, departure_date: str,
                    return_date: Optional[str] = None, trip_type: str = "one-way",
                    seat_class: str = "economy", adults: int = 1, children: int = 0,
                    infants_in_seat: int = 0, infants_on_lap: int = 0) -> str:
        """Async version of _run."""
        return self._run(
            from_airport=from_airport,
            to_airport=to_airport,
            departure_date=departure_date,
            return_date=return_date,
            trip_type=trip_type,
            seat_class=seat_class,
            adults=adults,
            children=children,
            infants_in_seat=infants_in_seat,
            infants_on_lap=infants_on_lap
        )


# Test function to validate the flight search tool
def test_flight_search():
    """Test function to validate flight search functionality."""
    try:
        tool = FlightSearchTool()
        
        # Test with a simple one-way flight
        print("Testing one-way flight search...")
        result = tool._run(
            from_airport="LAX",
            to_airport="JFK", 
            departure_date="2025-08-15",
            adults=1
        )
        print("One-way Flight Search Result:")
        print(result)
        print("\n" + "="*50 + "\n")
        
        # Test with round-trip flight
        print("Testing round-trip flight search...")
        result = tool._run(
            from_airport="SFO",
            to_airport="NRT",
            departure_date="2025-09-01",
            return_date="2025-09-10",
            trip_type="round-trip",
            seat_class="business",
            adults=2
        )
        print("Round-trip Flight Search Result:")
        print(result)
        
        return True
    except Exception as e:
        print(f"Flight Search Test Failed: {e}")
        return False


# Example usage and testing
if __name__ == "__main__":
    # Test the flight search tool
    print("Testing Flight Search Tool...")
    test_flight_search()
    
    # Example usage:
    # tool = FlightSearchTool()
    # results = tool.run(
    #     from_airport="LAX",
    #     to_airport="JFK",
    #     departure_date="2025-08-15"
    # )
    # print(results)