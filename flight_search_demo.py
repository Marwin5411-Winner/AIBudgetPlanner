#!/usr/bin/env python3
"""
Example usage of the FlightSearchTool in the AI Budget Planner context.
This demonstrates how the flight search tool integrates with LangChain agents.
"""

import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate
from Tools.flight_search import FlightSearchTool

def demo_flight_search_agent():
    """Demonstrate flight search integration with LangChain agent."""
    
    # Note: In production, get API key from environment or Streamlit secrets
    api_key = input("Enter your Google API Key (or press Enter to skip): ").strip()
    if not api_key:
        print("Skipping agent demo - no API key provided")
        return
    
    try:
        # Initialize LLM
        llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            google_api_key=api_key,
            temperature=0.7,
            convert_system_message_to_human=True
        )
        
        # Initialize tools
        flight_tool = FlightSearchTool()
        tools = [flight_tool]
        
        # Create agent prompt
        prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a helpful travel budget assistant. You have access to a FlightSearch tool that can find real flight prices and information from Google Flights.

When users ask about flights or travel budgets, use the FlightSearch tool to get actual flight prices and details. Always specify:
- from_airport and to_airport using IATA codes (like LAX, JFK, CDG)
- departure_date in YYYY-MM-DD format
- For round trips, include return_date and set trip_type="round-trip"
- Number of passengers (adults, children, etc.)

Provide helpful budget advice based on the real flight prices you find."""),
            ("human", "{input}"),
            ("placeholder", "{agent_scratchpad}")
        ])
        
        # Create agent
        agent = create_tool_calling_agent(llm, tools, prompt)
        agent_executor = AgentExecutor(
            agent=agent,
            tools=tools,
            verbose=True,
            max_iterations=10,
            handle_parsing_errors=True
        )
        
        print("🤖 Flight Search Agent Demo")
        print("=" * 50)
        print("Ask me about flight prices and travel budgets!")
        print("Examples:")
        print("- 'What's the cost for a round-trip flight from LAX to JFK in August 2025?'")
        print("- 'Help me budget for a trip from San Francisco to Tokyo in September'")
        print("- 'Find flights from Miami to Paris for 2 people'")
        print("\nType 'quit' to exit")
        print("=" * 50)
        
        while True:
            user_input = input("\n👤 You: ").strip()
            if user_input.lower() in ['quit', 'exit', 'bye']:
                print("👋 Goodbye!")
                break
            
            if not user_input:
                continue
                
            try:
                print(f"\n🤖 Agent: Searching for flight information...")
                response = agent_executor.invoke({"input": user_input})
                print(f"\n🤖 Agent: {response.get('output', 'No response generated')}")
            except Exception as e:
                print(f"❌ Error: {e}")
                
    except Exception as e:
        print(f"❌ Failed to initialize agent: {e}")

def demo_direct_flight_search():
    """Demonstrate direct flight search without agent."""
    print("\n" + "=" * 60)
    print("Direct Flight Search Demo")
    print("=" * 60)
    
    tool = FlightSearchTool()
    
    # Example searches
    examples = [
        {
            "description": "One-way flight LAX to JFK",
            "params": {
                "from_airport": "LAX",
                "to_airport": "JFK",
                "departure_date": "2025-08-15"
            }
        },
        {
            "description": "Round-trip business class SFO to NRT",
            "params": {
                "from_airport": "SFO",
                "to_airport": "NRT",
                "departure_date": "2025-09-01",
                "return_date": "2025-09-10",
                "trip_type": "round-trip",
                "seat_class": "business",
                "adults": 2
            }
        }
    ]
    
    for i, example in enumerate(examples, 1):
        print(f"\n--- Example {i}: {example['description']} ---")
        try:
            result = tool._run(**example['params'])
            print(result)
        except Exception as e:
            print(f"Error: {e}")
        
        if i < len(examples):
            input("\nPress Enter to continue to next example...")

if __name__ == "__main__":
    print("✈️ Flight Search Tool Integration Demo")
    print("This demonstrates the flight search capabilities in the AI Budget Planner")
    
    choice = input("\nChoose demo:\n1. Direct flight search\n2. Agent integration (requires Google API key)\n\nEnter 1 or 2: ").strip()
    
    if choice == "1":
        demo_direct_flight_search()
    elif choice == "2":
        demo_flight_search_agent()
    else:
        print("Invalid choice. Running direct flight search demo...")
        demo_direct_flight_search()
    
    print("\n🎉 Demo completed!")
