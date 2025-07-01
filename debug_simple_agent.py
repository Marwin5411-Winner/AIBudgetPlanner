#!/usr/bin/env python3
"""
Debug version to test agent tool calling.
"""

import os
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain.agents import create_tool_calling_agent, AgentExecutor
from langchain_core.prompts import ChatPromptTemplate
from Tools.google_map_search import GoogleMapSearchTool

def debug_agent():
    """Debug the agent tool calling."""
    
    google_api_key = os.getenv("GOOGLE_API_KEY")
    google_maps_api_key = os.getenv("GOOGLE_MAPS_API_KEY")
    
    if not google_api_key or not google_maps_api_key:
        print("❌ API keys not found")
        return False
    
    try:
        print("🔧 Initializing LLM...")
        llm = ChatGoogleGenerativeAI(
            model="gemini-1.5-flash-latest",
            google_api_key=google_api_key,
            temperature=0.7,
        )
        
        print("🔧 Initializing GoogleMapSearch tool...")
        map_tool = GoogleMapSearchTool(api_key=google_maps_api_key)
        tools = [map_tool]
        
        print(f"Tool name: {map_tool.name}")
        print(f"Tool description: {map_tool.description}")
        print(f"Return direct: {map_tool.return_direct}")
        
        print("🔧 Creating simple agent prompt...")
        agent_prompt = ChatPromptTemplate.from_messages([
            ("system", """You are a helpful assistant. You have access to a GoogleMapSearch tool.
            When asked to find places, you MUST use the GoogleMapSearch tool.
            
            The tool takes these parameters:
            - query (required): what to search for (e.g., "coffee shop", "restaurant")
            - location (optional): where to search (e.g., "Bangkok", "New York")
            - radius (optional): search radius in meters (default 5000)
            
            ALWAYS call the GoogleMapSearch tool when asked to find places. Do not provide hypothetical results!"""),
            ("human", "{input}"),
            ("placeholder", "{agent_scratchpad}")
        ])
        
        print("🔧 Creating agent...")
        agent = create_tool_calling_agent(llm, tools, agent_prompt)
        
        print("🔧 Creating agent executor...")
        agent_executor = AgentExecutor(
            agent=agent, 
            tools=tools, 
            verbose=True,  # Show all steps
            max_iterations=10,
            return_intermediate_steps=True,  # Show intermediate steps
            handle_parsing_errors=True
        )
        
        print("🧪 Testing simple tool call...")
        test_input = {
            "input": "Find 2 coffee shops in Bangkok using the GoogleMapSearch tool"
        }
        
        print("\n" + "="*50)
        print("AGENT EXECUTION:")
        print("="*50)
        
        result = agent_executor.invoke(test_input)
        
        print("\n" + "="*50)
        print("FINAL RESULT:")
        print("="*50)
        print(result.get("output", str(result)))
        
        if result.get("intermediate_steps"):
            print("\n" + "="*50)
            print("INTERMEDIATE STEPS:")
            print("="*50)
            for step in result["intermediate_steps"]:
                print(f"Action: {step[0]}")
                print(f"Result: {step[1]}")
                print("-" * 30)
        
        return True
        
    except Exception as e:
        print(f"❌ Debug test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    debug_agent()
