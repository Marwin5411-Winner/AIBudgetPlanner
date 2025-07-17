import streamlit as st
import pandas as pd
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import PromptTemplate
from langchain_core.output_parsers import StrOutputParser
from langchain.chains import LLMChain # Not needed if using LCEL
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate

#Tool imports
from Tools.google_map_search import GoogleMapSearchTool
from Tools.flight_search import FlightSearchTool



# print(map_tool.name)
# print(map_tool.invoke({"query": "coffee shop", "location": "Bangkok"}))  # Example usage with Bangkok coordinates

# --- Page Configuration ---
st.set_page_config(page_title="AI Budget Planner", layout="wide", initial_sidebar_state="expanded")
st.title("💸 AI Budget Planner")
st.caption("Plan your activities like eating out, movies, and travel within your budget scope using AI.")

# --- API Key Management ---
try:
    # Ensure st.secrets is available and the key exists
    if hasattr(st, 'secrets') and "GOOGLE_API_KEY" in st.secrets:
        GOOGLE_API_KEY = st.secrets["GOOGLE_API_KEY"]
    else:
        GOOGLE_API_KEY = None
except Exception: 
    GOOGLE_API_KEY = None

if not GOOGLE_API_KEY:
    GOOGLE_API_KEY = st.sidebar.text_input(
        "Enter your Google API Key:",
        type="password",
        help="Get your API key from Google AI Studio. The app requires this key to function.",
        key="google_api_key_input_sidebar"
    )
    
    GOOGLE_MAPS_API_KEY = st.sidebar.text_input(
        "Enter your Google Maps API Key:",
        type="password",
        help="Get your API key from Google Cloud Console. The app requires this key to search for places.",
        key="google_maps_api_key_input_sidebar"
    )
    
    st.sidebar.info("""
    **✈️ Flight Search Available!**
    
    This app now supports real flight search powered by Google Flights. You can include flight bookings in your budget plans by specifying:
    - Departure and destination airports (IATA codes like LAX, JFK, CDG)
    - Travel dates in YYYY-MM-DD format
    - Trip type (one-way or round-trip)
    - Number of passengers and seat class
    
    Example: "Round-trip flight from LAX to JFK on 2025-08-15 returning 2025-08-20"
    """)

else:
    st.sidebar.success("✅ API Keys configured!")
    st.sidebar.info("""
    **✈️ Flight Search Ready!**
    
    Include flights in your budget by specifying:
    - Airport codes (LAX, JFK, CDG, etc.)
    - Dates (YYYY-MM-DD format)
    - Trip details (one-way/round-trip)
    """)

# Only show Google Maps API input if Google API key is provided
if GOOGLE_API_KEY and not GOOGLE_MAPS_API_KEY:
    GOOGLE_MAPS_API_KEY = st.sidebar.text_input(
        "Enter your Google Maps API Key:",
        type="password",
        help="Get your API key from Google Cloud Console. This is only needed for local place searches.",
        key="google_maps_api_key_input_sidebar_conditional"
    )

# --- Langchain Setup ---
llm = None
budget_agent_executor = None 

if GOOGLE_API_KEY:
    try:
        llm = ChatGoogleGenerativeAI(
            model="gemini-2.5-flash",
            google_api_key=GOOGLE_API_KEY,
            temperature=0.5,
            convert_system_message_to_human=True
        )

        # Initialize tools
        tools = []
        
        # Always add flight search tool (doesn't require additional API keys)
        flight_tool = FlightSearchTool()
        tools.append(flight_tool)
        
        # Add Google Maps tool only if API key is available
        if GOOGLE_MAPS_API_KEY:
            map_tool = GoogleMapSearchTool(api_key=GOOGLE_MAPS_API_KEY)
            tools.append(map_tool)

        
        # Agent prompt template with dynamic tool availability
        available_tools_info = "FlightSearch (for flight bookings)"
        if GOOGLE_MAPS_API_KEY:
            available_tools_info += " and GoogleMapSearch (for local places)"
        
        agent_prompt = ChatPromptTemplate.from_messages([
            ("system", f"""You are a friendly, insightful, and practical AI budget planner.
            You have access to these tools: {available_tools_info}.
            
            IMPORTANT: You MUST actually use the appropriate tools for each activity. Do not simulate or provide hypothetical results!
            
            The user has a total budget of {{currency}}{{budget}}.
            The user is located in {{location}} (if provided).
            The user wants to engage in the following activities: {{activities}}.

            STEP-BY-STEP PROCESS:
            1. For EACH activity mentioned by the user, call the appropriate tool:
               - For travel/flights: Use FlightSearch tool with departure/destination airports and dates
               {'- For local places: Use GoogleMapSearch tool with activity and location' if GOOGLE_MAPS_API_KEY else '- For local places: Provide general budget estimates (GoogleMapSearch not available)'}
               - Example: FlightSearch(from_airport="LAX", to_airport="JFK", departure_date="2025-08-15")
               {'- Example: GoogleMapSearch(query="coffee shop", location="Bangkok")' if GOOGLE_MAPS_API_KEY else ''}
            
            2. After getting real results from the tools for all activities, create a comprehensive budget plan
            
            3. Your final response must include:
               - Friendly introduction
               - Feasibility analysis within the budget
               - Budget allocation for each activity
               - Real information found using the tools (with prices, details)
               - Practical money management tips
               - Encouraging conclusion

            TOOL USAGE EXAMPLES:
            - For "flight to Paris": FlightSearch(from_airport="JFK", to_airport="CDG", departure_date="2025-09-01")
            - For "round-trip to Tokyo": FlightSearch(from_airport="LAX", to_airport="NRT", departure_date="2025-08-15", return_date="2025-08-25", trip_type="round-trip")
            {'- For "dining out": GoogleMapSearch(query="restaurant", location="{location}")' if GOOGLE_MAPS_API_KEY else ''}
            
            Remember: ALWAYS use the available tools - never provide simulated results for tool-accessible information!"""),
            ("human", """Create a detailed budget plan for:

Budget: {currency}{budget}
Location: {location}
Activities: {activities}

IMPORTANT: Please use the appropriate tools to find real information for each activity:
- For flights/travel: Use FlightSearch tool with proper airport codes and dates
- For local places: Use GoogleMapSearch tool if available, otherwise provide general estimates

Don't simulate results for tool-accessible information - actually call the available tools!

After using the appropriate tools for each activity, create a comprehensive budget plan that incorporates the real information you found."""),
            ("placeholder", "{agent_scratchpad}")
        ])

        # Create the agent
        agent = create_tool_calling_agent(llm, tools, agent_prompt)
        
        # Create the agent executor with more debugging
        budget_agent_executor = AgentExecutor(
            agent=agent, 
            tools=tools, 
            verbose=True,  # Enable verbose mode to see tool calls
            max_iterations=20,
            return_intermediate_steps=False,
            handle_parsing_errors=True,
            early_stopping_method="generate"  # Ensures complete response generation
        )

    except Exception as e:
        st.sidebar.error(f"Error initializing AI model: {e}")
        st.toast(f"Error initializing AI: {e}", icon="❌")

else:
    st.sidebar.warning("Please enter your Google API Key in the sidebar to enable the AI planner.")
    st.sidebar.info("💡 The flight search tool will work with just the Google API Key. Google Maps API is optional for local place searches.")

# --- User Input Area ---
st.header("Step 1: Your Budget Details", divider="rainbow")
col1, col2 = st.columns([1, 2])

with col1:
    bi = st.number_input(
        "💰 Enter your total budget:",
        min_value=0.0,
        step=10.0,
        value=200.0,
        help="Specify your total available budget for the listed activities."
    )
    
    cs = st.selectbox(
        "💵 Select your currency:",
        options=("USD", "EUR", "GBP", "INR", "AUD", "CAD", "JPY", "CNY", "RUB", "BRL", "THB"),
        index=0,
        help="Choose the currency in which your budget is denominated."
    )
    
    li = st.text_input(
        "📍 Enter your location (optional):",
        placeholder="e.g., New York, USA",
        help="Specify your location to tailor the budget plan to local costs."
    )

with col2:
    example_activities = "Round-trip flight from LAX to JFK on 2025-08-15 returning 2025-08-20, 3 restaurant meals in New York, visit Central Park attractions, 2 Broadway show tickets"
    act_i = st.text_area(
        "📝 List desired activities:",
        height=120,
        placeholder=f"e.g., {example_activities}",
        help="List all activities you want to budget for. For flights, include departure/destination airports and dates. Be as specific as possible."
    )

# --- Generate Plan Button ---
st.header("Step 2: Generate Your Plan", divider="rainbow")
if st.button("✨ Generate AI Budget Plan", type="primary", use_container_width=True, help="Click to get your personalized budget plan"):
    if not GOOGLE_API_KEY or not budget_agent_executor:
        st.error("AI Model not initialized. Please ensure your Google API Key and Google Maps API Key are correctly entered in the sidebar and are valid.")
        st.toast("API Key or AI Model issue.", icon="🔑")
    elif bi <= 0:
        st.warning("Please enter a budget amount greater than zero.")
        st.toast("Budget must be positive.", icon="⚠️")
    elif not act_i.strip():
        st.warning("Please list some activities you'd like to plan for.")
        st.toast("Activities list is empty.", icon="⚠️")
    else:
        with st.spinner("🤖 AI is crafting your personalized budget plan... Please wait."):
            try:
                inputs = {
                    "budget": bi, 
                    "activities": act_i, 
                    "location": li or "Not specified", 
                    "currency": cs
                }
                
                # Debug info
                st.info(f"🔧 Debug: Invoking agent with budget={cs}{bi}, location={li or 'Not specified'}, activities={act_i[:50]}...")
                
                ai_response = budget_agent_executor.invoke(inputs)
                # Extract the output from the agent response
                output = ai_response.get("output", str(ai_response))
                
                # Debug info
                st.info(f"🔧 Debug: Agent response type: {type(ai_response)}, keys: {list(ai_response.keys()) if isinstance(ai_response, dict) else 'Not a dict'}")
                
                # Check if the output is just raw tool results (not a proper budget plan)
                if output and len(output.strip()) < 200 or "Found" in output and "results for" in output and "Budget Plan" not in output:
                    st.warning("⚠️ Received incomplete response, trying again with more specific instructions...")
                    
                    # If we got raw search results, create a follow-up to get a proper budget plan
                    follow_up_prompt = f"""You previously found some places using GoogleMapSearch. Now create a complete budget plan for:
                    
                        Budget: {cs}{bi}
                        Location: {li or 'Not specified'}
                        Activities: {act_i}

                        Create a comprehensive budget plan with:
                        1. A friendly introduction
                        2. Feasibility analysis of the activities within the budget
                        3. Suggested budget allocation for each activity
                        4. The real places you found for each activity (from your previous searches)
                        5. Practical budget management tips
                        6. Encouraging conclusion

                        Format it as a proper budget plan, not just a list of places."""
                    
                    fup = budget_agent_executor.invoke({"input": follow_up_prompt})
                    output = fup.get("output", str(fup))

                st.subheader("📊 Your AI-Generated Budget Plan")
                st.markdown(output)
                st.toast("Budget plan generated successfully!", icon="🎉")

            except Exception as e:
                st.error(f"An error occurred while generating the plan: {e}")
                st.toast(f"Generation error: {e}", icon="❌")
                st.info("This might be due to API issues (e.g., quota, invalid key), network problems, or the model couldn't process the request. Please check your keys, try simplifying your request, or try again later.")

# --- Footer ---
st.markdown("---")