#!/usr/bin/env python3
"""
Test script for the improved LinkedIn automation.
"""

import asyncio
import aiohttp
import json

BASE_URL = "http://localhost:8001"

async def test_connect():
    """Test connecting with David Gelberg."""
    async with aiohttp.ClientSession() as session:
        data = {
            "name": "David Gelberg"
        }
        
        try:
            async with session.post(f"{BASE_URL}/api/add-connection", json=data) as response:
                result = await response.json()
                print(f"LinkedIn connection test result: {json.dumps(result, indent=2)}")
                return result
        except Exception as e:
            print(f"Error testing LinkedIn connection: {str(e)}")
            return {"success": False, "error": str(e)}

async def test_health():
    """Test health check endpoint."""
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(f"{BASE_URL}/health") as response:
                result = await response.json()
                print(f"LinkedIn health check result: {json.dumps(result, indent=2)}")
                return result
        except Exception as e:
            print(f"Error testing LinkedIn health: {str(e)}")
            return {"success": False, "error": str(e)}

async def main():
    """Run all tests."""
    print("Testing LinkedIn Automation API...")
    
    # Test health check
    await test_health()
    
    # Test connecting with David Gelberg
    await test_connect()
    
    print("LinkedIn tests completed!")

if __name__ == "__main__":
    asyncio.run(main())