#!/usr/bin/env python3
"""
Test script for the LangChain agent with Google Maps tool.
This script will help verify that the agent can properly execute the Google Maps search tool.
"""

import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate
from Tools.google_map_search import GoogleMapSearchTool

def test_agent():
    """Test the LangChain agent with Google Maps tool."""
    
    # Check environment variables
    google_api_key = os.getenv("GOOGLE_API_KEY")
    google_maps_api_key = os.getenv("GOOGLE_MAPS_API_KEY")
    
    if not google_api_key:
        print("❌ GOOGLE_API_KEY environment variable not found")
        return False
        
    if not google_maps_api_key:
        print("❌ GOOGLE_MAPS_API_KEY environment variable not found") 
        return False
    
    try:
        print("🔧 Initializing LLM...")
        llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-flash-latest",
            google_api_key=google_api_key,
            temperature=0.7,
        )
        
        print("🔧 Initializing Google Maps tool...")
        map_tool = GoogleMapSearchTool(api_key=google_maps_api_key)
        tools = [map_tool]
        
        print("🔧 Creating agent prompt...")
        agent_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a helpful assistant that can search for places using Google Maps.
            When asked to find places, use the GoogleMapSearch tool to get real results.
            Always use the tool when searching for places - don't provide hypothetical results."""),
            ("human", "{input}"),
            ("placeholder", "{agent_scratchpad}")
        ])
        
        print("🔧 Creating agent...")
        agent = create_tool_calling_agent(llm, tools, agent_prompt)
        
        print("🔧 Creating agent executor...")
        agent_executor = AgentExecutor(
            agent=agent, 
            tools=tools, 
            verbose=True,
            max_iterations=5,
            return_intermediate_steps=False
        )
        
        print("🧪 Testing agent with sample query...")
        test_input = {
            "input": "Find 3 coffee shops in Bangkok, Thailand"
        }
        
        result = agent_executor.invoke(test_input)
        
        print("\n✅ Agent test successful!")
        print("📄 Result:")
        print(result.get("output", str(result)))
        
        return True
        
    except Exception as e:
        print(f"❌ Agent test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

def test_budget_agent():
    """Test the budget planning agent."""
    
    google_api_key = os.getenv("GOOGLE_API_KEY")
    google_maps_api_key = os.getenv("GOOGLE_MAPS_API_KEY")
    
    if not google_api_key or not google_maps_api_key:
        print("❌ API keys not found")
        return False
    
    try:
        print("🔧 Testing budget agent...")
        
        llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-flash-latest",
            google_api_key=google_api_key,
            temperature=0.7,
        )

        map_tool = GoogleMapSearchTool(api_key=google_maps_api_key)
        tools = [map_tool]
        
        agent_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a budget planner. For the given budget and activities, 
            use the GoogleMapSearch tool to find real places for each activity.
            Budget: {currency}{budget}
            Location: {location}
            Activities: {activities}
            
            Use the GoogleMapSearch tool to find 2-3 places for each activity."""),
            ("human", "Create a budget plan for: {currency}{budget} in {location} for activities: {activities}"),
            ("placeholder", "{agent_scratchpad}")
        ])

        agent = create_tool_calling_agent(llm, tools, agent_prompt)
        agent_executor = AgentExecutor(
            agent=agent, 
            tools=tools, 
            verbose=True,
            max_iterations=10,
            return_intermediate_steps=False
        )
        
        test_inputs = {
            "budget": "200", 
            "activities": "dining out, coffee shops", 
            "location": "Bangkok", 
            "currency": "USD"
        }
        
        result = agent_executor.invoke(test_inputs)
        
        print("\n✅ Budget agent test successful!")
        print("📄 Result:")
        print(result.get("output", str(result)))
        
        return True
        
    except Exception as e:
        print(f"❌ Budget agent test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    print("🧪 Testing LangChain Agent with Google Maps Tool")
    print("=" * 50)
    
    print("\n1. Testing basic agent functionality...")
    test_agent()
    
    print("\n" + "=" * 50)
    print("2. Testing budget planning agent...")
    test_budget_agent()
