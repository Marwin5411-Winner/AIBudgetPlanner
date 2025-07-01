#!/usr/bin/env python3
"""
Debug script for Google Maps API issues.
This script will help identify common problems with the Google Maps API setup.
"""

import os
import sys
import requests
from Tools.google_map_search import GoogleMapSearchTool, test_google_maps_api

def check_api_key():
    """Check if API key is available."""
    api_key = os.getenv("GOOGLE_MAPS_API_KEY")
    if not api_key:
        print("❌ GOOGLE_MAPS_API_KEY environment variable not found")
        return None
    else:
        print(f"✅ API key found: {api_key[:10]}...{api_key[-4:] if len(api_key) > 14 else api_key}")
        return api_key

def check_api_permissions(api_key):
    """Check which APIs are enabled for the given key."""
    print("\n🔍 Checking API permissions...")
    
    # Test Geocoding API
    print("Testing Geocoding API...")
    try:
        response = requests.get(
            "https://maps.googleapis.com/maps/api/geocode/json",
            params={"address": "Bangkok", "key": api_key}
        )
        data = response.json()
        if data.get("status") == "OK":
            print("✅ Geocoding API: Working")
        else:
            print(f"❌ Geocoding API Error: {data.get('status')} - {data.get('error_message', 'Unknown error')}")
    except Exception as e:
        print(f"❌ Geocoding API Exception: {e}")
    
    # Test Places API
    print("Testing Places API...")
    try:
        response = requests.get(
            "https://maps.googleapis.com/maps/api/place/textsearch/json",
            params={"query": "restaurant Bangkok", "key": api_key}
        )
        data = response.json()
        if data.get("status") == "OK":
            print("✅ Places API: Working")
            print(f"   Found {len(data.get('results', []))} results")
        else:
            print(f"❌ Places API Error: {data.get('status')} - {data.get('error_message', 'Unknown error')}")
            if data.get("status") == "REQUEST_DENIED":
                print("   💡 This usually means:")
                print("      - Places API is not enabled in Google Cloud Console")
                print("      - API key doesn't have permission for Places API")
                print("      - Billing is not set up")
    except Exception as e:
        print(f"❌ Places API Exception: {e}")

def run_full_test(api_key):
    """Run the full Google Maps tool test."""
    print("\n🧪 Testing GoogleMapSearchTool...")
    try:
        success = test_google_maps_api(api_key)
        if success:
            print("✅ GoogleMapSearchTool test passed")
        else:
            print("❌ GoogleMapSearchTool test failed")
    except Exception as e:
        print(f"❌ GoogleMapSearchTool test exception: {e}")

def main():
    print("🔧 Google Maps API Debug Tool")
    print("=" * 40)
    
    # Check API key
    api_key = check_api_key()
    if not api_key:
        print("\n💡 To fix this:")
        print("   1. Get a Google Maps API key from Google Cloud Console")
        print("   2. Enable Geocoding API and Places API")
        print("   3. Set up billing")
        print("   4. Set the environment variable:")
        print("      export GOOGLE_MAPS_API_KEY='your_api_key_here'")
        return
    
    # Check API permissions
    check_api_permissions(api_key)
    
    # Run full test
    run_full_test(api_key)
    
    print("\n📋 Common Solutions:")
    print("   1. Enable APIs in Google Cloud Console:")
    print("      - Geocoding API")
    print("      - Places API")
    print("   2. Set up billing account")
    print("   3. Check API key restrictions")
    print("   4. Verify quota limits")

if __name__ == "__main__":
    main()
