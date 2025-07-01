# Flight Search Tool Integration

## Overview

The AI Budget Planner now includes a comprehensive flight search tool powered by the `fast-flights` library, which provides access to real Google Flights data. This tool allows users to include actual flight bookings in their budget planning with real prices and flight details.

## Features

✈️ **Real Flight Data**: Access to actual Google Flights data  
🌍 **Global Coverage**: Search flights worldwide using IATA airport codes  
💺 **Multiple Seat Classes**: Economy, Premium Economy, Business, and First Class  
👥 **Multi-Passenger Support**: Adults, children, and infants  
🔄 **Trip Types**: One-way and round-trip flights  
💰 **Price Trends**: Current price trend information (low/typical/high)  
⭐ **Best Deals**: Automatically identifies best flight deals  

## Usage

### In the AI Budget Planner App

1. **Include flight details in your activities**: When describing your desired activities, include specific flight information:
   ```
   Round-trip flight from LAX to JFK on 2025-08-15 returning 2025-08-20, 
   dining in New York restaurants, Broadway show tickets
   ```

2. **Specify airport codes**: Use standard IATA airport codes:
   - LAX (Los Angeles), JFK (New York), CDG (Paris), NRT (Tokyo), etc.

3. **Include dates**: Use YYYY-MM-DD format for dates

4. **The AI will automatically**:
   - Search for real flights using the FlightSearch tool
   - Include actual flight prices in your budget plan
   - Provide flight details like duration, stops, airlines
   - Consider price trends and best deals

### Direct Tool Usage

```python
from Tools.flight_search import FlightSearchTool

# Initialize the tool
flight_tool = FlightSearchTool()

# One-way flight search
result = flight_tool._run(
    from_airport="LAX",
    to_airport="JFK",
    departure_date="2025-08-15"
)

# Round-trip flight search
result = flight_tool._run(
    from_airport="SFO",
    to_airport="NRT",
    departure_date="2025-09-01",
    return_date="2025-09-10",
    trip_type="round-trip",
    seat_class="business",
    adults=2,
    children=1
)
```

## Parameters

### Required Parameters
- `from_airport`: IATA code of departure airport (e.g., 'LAX', 'JFK')
- `to_airport`: IATA code of destination airport (e.g., 'CDG', 'NRT')
- `departure_date`: Departure date in YYYY-MM-DD format

### Optional Parameters
- `return_date`: Return date for round-trip flights (YYYY-MM-DD)
- `trip_type`: "one-way" (default) or "round-trip"
- `seat_class`: "economy" (default), "premium-economy", "business", or "first"
- `adults`: Number of adult passengers (1-9, default: 1)
- `children`: Number of child passengers (0-8, default: 0)
- `infants_in_seat`: Number of infants with seats (0-5, default: 0)
- `infants_on_lap`: Number of infants on lap (0-5, default: 0)

## Output Format

The tool returns detailed flight information including:

- **Flight Search Summary**: Trip type, passengers, dates, seat class
- **Price Trend**: Current market price trend (low/typical/high)
- **Flight Options**: Up to 10 flight options with:
  - Airline names
  - Departure and arrival times
  - Flight duration
  - Number of stops (or "Direct flight")
  - Ticket prices
  - Best deal indicators ⭐
  - Delay information (if available)

## Example Output

```
Flight Search Results for round-trip trip from LAX to JFK (return 2025-08-20)
Passengers: 2 adult(s)
Seat Class: Economy
Departure Date: 2025-08-15
Current Price Trend: typical

Found 10 flight options:

1. JetBlue ⭐ BEST DEAL
   Departure: 4:20 PM on Thu, Aug 15
   Arrival: 12:55 AM on Fri, Aug 16
   Duration: 5 hr 35 min
   Stops: Direct flight
   Price: ₹13150

2. Delta
   Departure: 9:20 PM on Thu, Aug 15
   Arrival: 5:35 AM on Fri, Aug 16
   Duration: 5 hr 15 min
   Stops: Direct flight
   Price: ₹15292
...

💡 Tips:
- Prices may vary and are subject to availability
- Consider booking flexibility for better deals
- Check airline websites for the most up-to-date information
```

## Common Airport Codes

### US Airports
- **LAX**: Los Angeles International
- **JFK**: John F. Kennedy International (New York)
- **LGA**: LaGuardia Airport (New York)
- **SFO**: San Francisco International
- **MIA**: Miami International
- **ORD**: Chicago O'Hare
- **DFW**: Dallas/Fort Worth

### International Airports
- **LHR**: London Heathrow
- **CDG**: Paris Charles de Gaulle
- **NRT**: Tokyo Narita
- **HND**: Tokyo Haneda
- **FRA**: Frankfurt
- **AMS**: Amsterdam Schiphol
- **SIN**: Singapore Changi

## Error Handling

The tool includes comprehensive error handling for:
- Invalid airport codes
- Past dates
- Invalid date formats
- Network connectivity issues
- API service unavailability
- Invalid passenger counts

## Installation

The flight search functionality requires the `fast-flights` package:

```bash
pip install fast-flights
```

This package is automatically included in the `requirements.txt` file.

## Technical Details

- **Powered by**: `fast-flights` library (version 2.2+)
- **Data Source**: Google Flights
- **Protocol**: Base64-encoded Protocol Buffers
- **Reliability**: Uses fallback mode for better reliability
- **Rate Limits**: No API key required, uses Google's public endpoints

## Limitations

- **Date Range**: Can only search for future dates
- **Availability**: Flight availability depends on Google Flights data
- **Pricing**: Prices are indicative and may vary at booking time
- **Booking**: Tool provides information only; actual booking must be done elsewhere

## Integration with Budget Planning

The flight search tool seamlessly integrates with the AI Budget Planner's intelligent agent system:

1. **Automatic Detection**: The AI automatically detects when flight information is needed
2. **Tool Selection**: Chooses the appropriate tool (FlightSearch vs GoogleMapSearch)
3. **Real Data**: Uses actual flight prices in budget calculations
4. **Comprehensive Planning**: Combines flight costs with other activity costs
5. **Smart Recommendations**: Provides budget-aware flight recommendations

## Testing

Run the test suite to verify functionality:

```bash
# Run basic tests
python Tools/flight_search.py

# Run comprehensive test suite  
python test_flight_search.py

# Run interactive demo
python flight_search_demo.py
```

## Troubleshooting

### Common Issues

1. **"Invalid airport code"**: Ensure you're using 3-letter IATA codes (LAX, not Los Angeles)
2. **"Invalid date"**: Use YYYY-MM-DD format and ensure date is in the future
3. **"No flights found"**: Try different dates or nearby airports
4. **Network errors**: Check internet connection; tool requires online access

### Support

For issues with the flight search tool:
1. Check the error message for specific guidance
2. Verify airport codes at [IATA airport code database](https://www.iata.org/en/publications/directories/code-search/)
3. Ensure dates are properly formatted and in the future
4. Try with different date ranges or airports if no results are found

---

*The flight search tool enhances the AI Budget Planner by providing real-world flight data, making budget planning more accurate and practical for travel-related activities.*
