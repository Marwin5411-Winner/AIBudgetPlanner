#!/usr/bin/env python3
"""
Simple test to verify the GoogleMapSearch tool works correctly.
"""

import os
from Tools.google_map_search import GoogleMapSearchTool

def test_tool_directly():
    """Test the tool directly without LangChain agent."""
    
    google_maps_api_key = os.getenv("GOOGLE_MAPS_API_KEY")
    if not google_maps_api_key:
        print("❌ GOOGLE_MAPS_API_KEY environment variable not found")
        return False
    
    try:
        print("🔧 Testing GoogleMapSearchTool directly...")
        tool = GoogleMapSearchTool(api_key=google_maps_api_key)
        
        # Test the tool with different input methods
        print("\n1. Testing with keyword arguments...")
        result1 = tool._run(query="coffee shop", location="Bangkok", radius=5000)
        print(f"Result 1: {result1[:200]}...")
        
        print("\n2. Testing with invoke method...")
        result2 = tool.invoke({"query": "restaurant", "location": "Bangkok"})
        print(f"Result 2: {result2[:200]}...")
        
        print("\n3. Testing tool name and description...")
        print(f"Tool name: {tool.name}")
        print(f"Tool description: {tool.description}")
        print(f"Tool args schema: {tool.args_schema}")
        
        return True
        
    except Exception as e:
        print(f"❌ Tool test failed: {e}")
        import traceback
        traceback.print_exc()
        return False

if __name__ == "__main__":
    test_tool_directly()
