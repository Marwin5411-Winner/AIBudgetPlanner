#!/usr/bin/env python3
"""
Test script for the Flight Search Tool
This demonstrates various use cases for the flight search functionality.
"""

from Tools.flight_search import FlightSearchTool

def test_basic_search():
    """Test basic one-way flight search."""
    print("=" * 60)
    print("TEST 1: Basic One-Way Flight Search")
    print("=" * 60)
    
    tool = FlightSearchTool()
    result = tool._run(
        from_airport="LAX",
        to_airport="JFK",
        departure_date="2025-08-15"
    )
    print(result)

def test_round_trip():
    """Test round-trip flight search."""
    print("\n" + "=" * 60)
    print("TEST 2: Round-Trip Flight Search")
    print("=" * 60)
    
    tool = FlightSearchTool()
    result = tool._run(
        from_airport="NYC",
        to_airport="LON",
        departure_date="2025-09-01",
        return_date="2025-09-10",
        trip_type="round-trip",
        adults=2
    )
    print(result)

def test_family_trip():
    """Test family trip with multiple passengers."""
    print("\n" + "=" * 60)
    print("TEST 3: Family Trip with Children")
    print("=" * 60)
    
    tool = FlightSearchTool()
    result = tool._run(
        from_airport="MIA",
        to_airport="CDG",
        departure_date="2025-07-20",
        return_date="2025-07-30",
        trip_type="round-trip",
        seat_class="premium-economy",
        adults=2,
        children=2
    )
    print(result)

def test_business_class():
    """Test business class flight search."""
    print("\n" + "=" * 60)
    print("TEST 4: Business Class Flight")
    print("=" * 60)
    
    tool = FlightSearchTool()
    result = tool._run(
        from_airport="SFO",
        to_airport="NRT",
        departure_date="2025-10-15",
        seat_class="business",
        adults=1
    )
    print(result)

def test_error_handling():
    """Test error handling with invalid inputs."""
    print("\n" + "=" * 60)
    print("TEST 5: Error Handling")
    print("=" * 60)
    
    tool = FlightSearchTool()
    
    # Test invalid airport code
    print("Testing invalid airport code:")
    result = tool._run(
        from_airport="INVALID",
        to_airport="JFK",
        departure_date="2025-08-15"
    )
    print(result)
    
    print("\n" + "-" * 40)
    
    # Test past date
    print("Testing past date:")
    result = tool._run(
        from_airport="LAX",
        to_airport="JFK",
        departure_date="2024-01-01"
    )
    print(result)

if __name__ == "__main__":
    print("Flight Search Tool - Comprehensive Test Suite")
    print("This will test various scenarios and use cases for flight search.")
    print("\nNote: Tests use real Google Flights data and may take a moment to complete.")
    
    # Run all tests
    test_basic_search()
    test_round_trip()
    test_family_trip()
    test_business_class()
    test_error_handling()
    
    print("\n" + "=" * 60)
    print("All tests completed!")
    print("=" * 60)
