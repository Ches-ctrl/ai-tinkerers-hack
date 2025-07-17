#!/usr/bin/env python3
"""
Test script to connect with David Gelberg on LinkedIn.
"""

import asyncio
import httpx
import json

async def test_david_gelberg():
    """Test connecting with David Gelberg via the LinkedIn API."""

    # API endpoint
    url = "http://localhost:8001/api/add-connection"

    # Test data
    test_data = {
        "name": "Himanshu Agarwal",
        "message": None  # No message, just connect
    }

    print("Testing LinkedIn connection with David Gelberg...")
    print(f"URL: {url}")
    print(f"Data: {json.dumps(test_data, indent=2)}")
    print("\n" + "="*50)

    try:
        async with httpx.AsyncClient(timeout=60.0) as client:
            response = await client.post(url, json=test_data)

            print(f"Status Code: {response.status_code}")
            print(f"Response: {json.dumps(response.json(), indent=2)}")

            if response.status_code == 200:
                result = response.json()
                if result.get("success"):
                    print("\n✅ SUCCESS: Connection request sent!")
                    print(f"Profile URL: {result.get('profile_url')}")
                else:
                    print("\n❌ FAILED: Connection request failed")
                    print(f"Reason: {result.get('message')}")
            else:
                print(f"\n❌ API ERROR: {response.status_code}")
                print(f"Error: {response.text}")

    except httpx.ConnectError:
        print("\n❌ CONNECTION ERROR: Could not connect to LinkedIn API")
        print("Make sure the LinkedIn worker is running on port 8001")
    except Exception as e:
        print(f"\n❌ ERROR: {str(e)}")

if __name__ == "__main__":
    asyncio.run(test_david_gelberg())
