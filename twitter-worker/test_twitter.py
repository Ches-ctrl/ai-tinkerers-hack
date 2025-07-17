#!/usr/bin/env python3
"""
Test script for Twitter automation API.
"""

import asyncio
import aiohttp
import json

BASE_URL = "http://localhost:8003"

async def test_follow_user():
    """Test following a user."""
    async with aiohttp.ClientSession() as session:
        data = {
            "username": "elonmusk"
        }
        
        async with session.post(f"{BASE_URL}/api/follow", json=data) as response:
            result = await response.json()
            print(f"Follow test result: {json.dumps(result, indent=2)}")
            return result

async def test_like_tweet():
    """Test liking a tweet."""
    async with aiohttp.ClientSession() as session:
        data = {
            "tweet_url": "https://twitter.com/elonmusk/status/1234567890"  # Replace with actual tweet URL
        }
        
        async with session.post(f"{BASE_URL}/api/like", json=data) as response:
            result = await response.json()
            print(f"Like test result: {json.dumps(result, indent=2)}")
            return result

async def test_health_check():
    """Test health check endpoint."""
    async with aiohttp.ClientSession() as session:
        async with session.get(f"{BASE_URL}/health") as response:
            result = await response.json()
            print(f"Health check result: {json.dumps(result, indent=2)}")
            return result

async def main():
    """Run all tests."""
    print("Testing Twitter Automation API...")
    
    # Test health check
    await test_health_check()
    
    # Test following a user
    await test_follow_user()
    
    # Uncomment to test liking a tweet (need valid tweet URL)
    # await test_like_tweet()
    
    print("Tests completed!")

if __name__ == "__main__":
    asyncio.run(main())