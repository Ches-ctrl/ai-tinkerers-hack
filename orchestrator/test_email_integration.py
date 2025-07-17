#!/usr/bin/env python3
"""
Test email integration specifically in the orchestrator.
"""

import asyncio
import aiohttp
import json

BASE_URL = "http://localhost:8000"

async def test_email_integration():
    """Test email integration through orchestrator."""
    print("📧 Testing Email Integration through Orchestrator")
    print("=" * 60)
    
    # Test contact that should trigger email
    contact_with_email = {
        "first_name": "Charlie",
        "last_name": "Cheesman",
        "phone_numbers": ["+1234567890"],
        "emails": ["charlie@cheddar.jobs"],
        "urls": [],
        "audio": None,
        "photo": None
    }
    
    try:
        async with aiohttp.ClientSession() as session:
            print("📤 Sending contact with email through orchestrator...")
            async with session.post(f"{BASE_URL}/api/contact", json=contact_with_email) as response:
                if response.status == 200:
                    result = await response.json()
                    print(f"✅ Contact processed successfully!")
                    print(f"📋 Contact ID: {result['contact_id']}")
                    print(f"📊 Full Status: {result['linkedin_status']}")
                    
                    # Check if email was mentioned in status
                    if "Email sent successfully" in result['linkedin_status']:
                        print("✅ Email was sent successfully through orchestrator!")
                        return True
                    elif "Email failed" in result['linkedin_status']:
                        print("❌ Email failed through orchestrator")
                        return False
                    else:
                        print("⚠️ Email status not found in response")
                        return False
                else:
                    error_text = await response.text()
                    print(f"❌ Orchestrator error: {response.status} - {error_text}")
                    return False
                    
    except Exception as e:
        print(f"❌ Error testing email integration: {str(e)}")
        return False

async def test_orchestrator_to_email_worker():
    """Test orchestrator's ability to call email worker directly."""
    print("\n🔗 Testing Orchestrator -> Email Worker Connection")
    print("=" * 60)
    
    try:
        # Test if orchestrator can reach email worker
        import httpx
        
        async with httpx.AsyncClient() as client:
            print("📡 Testing orchestrator's connection to email worker...")
            
            # This simulates what the orchestrator does
            email_data = {
                "first_name": "Charlie",
                "last_name": "Cheesman",
                "email": "charlie@cheddar.jobs",
                "company": "Cheddar",
                "title": "Founder",
                "photo_path": None
            }
            
            response = await client.post(
                "http://localhost:8002/api/send-networking-email",
                json=email_data,
                timeout=30.0
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get('success'):
                    print("✅ Orchestrator can successfully call email worker!")
                    return True
                else:
                    print(f"❌ Email worker returned failure: {result.get('message')}")
                    return False
            else:
                print(f"❌ HTTP error: {response.status_code}")
                return False
                
    except Exception as e:
        print(f"❌ Connection error: {str(e)}")
        return False

async def main():
    """Run integration tests."""
    print("🧪 Email Integration Diagnostic")
    print("=" * 60)
    
    # Test direct connection first
    connection_success = await test_orchestrator_to_email_worker()
    
    # Test full integration
    integration_success = await test_email_integration()
    
    print("\n" + "=" * 60)
    print("📊 DIAGNOSTIC RESULTS")
    print("=" * 60)
    print(f"Orchestrator -> Email Worker: {'✅ PASS' if connection_success else '❌ FAIL'}")
    print(f"Full Integration: {'✅ PASS' if integration_success else '❌ FAIL'}")
    
    if connection_success and integration_success:
        print("\n🎉 Email integration is working correctly!")
    else:
        print("\n⚠️ Email integration has issues - check the logs above.")

if __name__ == "__main__":
    asyncio.run(main())