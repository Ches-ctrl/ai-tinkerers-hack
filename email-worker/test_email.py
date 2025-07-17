#!/usr/bin/env python3
"""
Test script for Email worker API.
"""

import asyncio
import aiohttp
import json

BASE_URL = "http://localhost:8002"

async def test_health():
    """Test health check endpoint."""
    async with aiohttp.ClientSession() as session:
        try:
            async with session.get(f"{BASE_URL}/health") as response:
                result = await response.json()
                print(f"Email health check result: {json.dumps(result, indent=2)}")
                return result
        except Exception as e:
            print(f"Error testing email health: {str(e)}")
            return {"success": False, "error": str(e)}

async def test_send_email():
    """Test sending a basic email."""
    async with aiohttp.ClientSession() as session:
        data = {
            "to_email": "test@example.com",
            "subject": "Test Email from AI Tinkerers Hack",
            "body": "<h1>Test Email</h1><p>This is a test email from the email worker API.</p>",
            "from_name": "AI Tinkerers Bot",
            "is_html": True
        }
        
        try:
            async with session.post(f"{BASE_URL}/api/send-email", json=data) as response:
                result = await response.json()
                print(f"Send email test result: {json.dumps(result, indent=2)}")
                return result
        except Exception as e:
            print(f"Error sending email: {str(e)}")
            return {"success": False, "error": str(e)}

async def test_networking_email():
    """Test sending a networking email."""
    async with aiohttp.ClientSession() as session:
        data = {
            "first_name": "John",
            "last_name": "Doe",
            "email": "test@example.com",
            "company": "Test Company",
            "title": "Software Engineer"
        }
        
        try:
            async with session.post(f"{BASE_URL}/api/send-networking-email", json=data) as response:
                result = await response.json()
                print(f"Networking email test result: {json.dumps(result, indent=2)}")
                return result
        except Exception as e:
            print(f"Error sending networking email: {str(e)}")
            return {"success": False, "error": str(e)}

async def main():
    """Run all tests."""
    print("Testing Email Worker API...")
    print("=" * 50)
    
    # Test health check
    print("\n1. Testing health check...")
    await test_health()
    
    # Test basic email (commented out to avoid sending actual emails)
    # print("\n2. Testing basic email send...")
    # await test_send_email()
    
    # Test networking email (commented out to avoid sending actual emails)
    # print("\n3. Testing networking email...")
    # await test_networking_email()
    
    print("\n" + "=" * 50)
    print("Email worker tests completed!")
    print("\nNote: Email sending tests are commented out to avoid sending actual emails.")
    print("Uncomment them to test with real email addresses.")

if __name__ == "__main__":
    asyncio.run(main())