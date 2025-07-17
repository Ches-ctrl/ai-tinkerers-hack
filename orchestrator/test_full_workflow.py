#!/usr/bin/env python3
"""
Comprehensive test of the orchestrator and all workers.
"""

import asyncio
import aiohttp
import json
import base64
from datetime import datetime

BASE_URL = "http://localhost:8000"

# Sample contact data for testing
TEST_CONTACT = {
    "first_name": "Test",
    "last_name": "User",
    "phone_numbers": ["+1234567890"],
    "emails": ["test.user@example.com"],
    "urls": ["https://www.linkedin.com/in/testuser"],
    "audio": None,  # No audio for this test
    "photo": None   # No photo for this test
}

# Sample contact with photo (base64 encoded 1x1 pixel PNG)
SAMPLE_PHOTO_B64 = "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChAI9jU77kgAAAABJRU5ErkJggg=="

TEST_CONTACT_WITH_MEDIA = {
    "first_name": "Media",
    "last_name": "Test",
    "phone_numbers": ["+1987654321"],
    "emails": ["media.test@example.com"],
    "urls": ["https://www.linkedin.com/in/mediatest"],
    "audio": None,
    "photo": SAMPLE_PHOTO_B64
}

async def test_orchestrator_health():
    """Test orchestrator health check."""
    print("🏥 Testing Orchestrator Health...")
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{BASE_URL}/health") as response:
                if response.status == 200:
                    result = await response.json()
                    print(f"✅ Orchestrator Health: {result}")
                    return True
                else:
                    print(f"❌ Orchestrator Health Check Failed: {response.status}")
                    return False
    except Exception as e:
        print(f"❌ Error testing orchestrator health: {str(e)}")
        return False

async def test_worker_health(worker_name, port):
    """Test individual worker health."""
    print(f"🏥 Testing {worker_name} Worker Health...")
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"http://localhost:{port}/health") as response:
                if response.status == 200:
                    result = await response.json()
                    print(f"✅ {worker_name} Worker Health: {result}")
                    return True
                else:
                    print(f"❌ {worker_name} Worker Health Check Failed: {response.status}")
                    return False
    except Exception as e:
        print(f"❌ Error testing {worker_name} worker health: {str(e)}")
        return False

async def test_contact_creation():
    """Test basic contact creation."""
    print("👤 Testing Contact Creation...")
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(f"{BASE_URL}/api/contact", json=TEST_CONTACT) as response:
                if response.status == 200:
                    result = await response.json()
                    print(f"✅ Contact Created: {result}")
                    return True, result.get('contact_id')
                else:
                    error_text = await response.text()
                    print(f"❌ Contact Creation Failed: {response.status} - {error_text}")
                    return False, None
    except Exception as e:
        print(f"❌ Error creating contact: {str(e)}")
        return False, None

async def test_contact_with_media():
    """Test contact creation with media."""
    print("📸 Testing Contact Creation with Media...")
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(f"{BASE_URL}/api/contact", json=TEST_CONTACT_WITH_MEDIA) as response:
                if response.status == 200:
                    result = await response.json()
                    print(f"✅ Contact with Media Created: {result}")
                    return True, result.get('contact_id')
                else:
                    error_text = await response.text()
                    print(f"❌ Contact with Media Creation Failed: {response.status} - {error_text}")
                    return False, None
    except Exception as e:
        print(f"❌ Error creating contact with media: {str(e)}")
        return False, None

async def test_contacts_list():
    """Test contacts listing."""
    print("📋 Testing Contacts List...")
    try:
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{BASE_URL}/api/contacts") as response:
                if response.status == 200:
                    result = await response.json()
                    print(f"✅ Contacts Listed: {len(result)} contacts found")
                    return True
                else:
                    error_text = await response.text()
                    print(f"❌ Contacts List Failed: {response.status} - {error_text}")
                    return False
    except Exception as e:
        print(f"❌ Error listing contacts: {str(e)}")
        return False

async def test_media_serving():
    """Test media file serving."""
    print("🖼️ Testing Media Serving...")
    try:
        # First get contacts to find a photo
        async with aiohttp.ClientSession() as session:
            async with session.get(f"{BASE_URL}/api/contacts") as response:
                if response.status == 200:
                    contacts = await response.json()
                    photo_contacts = [c for c in contacts if c.get('photo_file')]
                    
                    if photo_contacts:
                        photo_file = photo_contacts[0]['photo_file']
                        filename = photo_file.replace('data/media/', '')
                        
                        async with session.get(f"{BASE_URL}/api/media/{filename}") as media_response:
                            if media_response.status == 200:
                                content_type = media_response.headers.get('content-type', '')
                                content_length = media_response.headers.get('content-length', '0')
                                print(f"✅ Media Served: {filename} ({content_type}, {content_length} bytes)")
                                return True
                            else:
                                print(f"❌ Media Serving Failed: {media_response.status}")
                                return False
                    else:
                        print("⚠️ No photo contacts found to test media serving")
                        return True
                else:
                    print(f"❌ Could not get contacts for media test: {response.status}")
                    return False
    except Exception as e:
        print(f"❌ Error testing media serving: {str(e)}")
        return False

async def test_linkedin_worker():
    """Test LinkedIn worker functionality."""
    print("🔗 Testing LinkedIn Worker...")
    try:
        async with aiohttp.ClientSession() as session:
            test_data = {
                "name": "Test User",
                "message": "Test connection from orchestrator test"
            }
            
            async with session.post("http://localhost:8001/api/add-connection", json=test_data, timeout=30) as response:
                if response.status == 200:
                    result = await response.json()
                    print(f"✅ LinkedIn Worker Response: {result}")
                    return True
                else:
                    error_text = await response.text()
                    print(f"❌ LinkedIn Worker Failed: {response.status} - {error_text}")
                    return False
    except Exception as e:
        print(f"❌ Error testing LinkedIn worker: {str(e)}")
        return False

async def test_email_worker():
    """Test Email worker functionality."""
    print("📧 Testing Email Worker...")
    try:
        async with aiohttp.ClientSession() as session:
            test_data = {
                "first_name": "Test",
                "last_name": "User",
                "email": "test@example.com",
                "company": "Test Company",
                "title": "Test Engineer"
            }
            
            async with session.post("http://localhost:8002/api/send-networking-email", json=test_data) as response:
                if response.status == 200:
                    result = await response.json()
                    print(f"✅ Email Worker Response: {result}")
                    return True
                else:
                    error_text = await response.text()
                    print(f"❌ Email Worker Failed: {response.status} - {error_text}")
                    return False
    except Exception as e:
        print(f"❌ Error testing Email worker: {str(e)}")
        return False

async def test_twitter_worker():
    """Test Twitter worker functionality."""
    print("🐦 Testing Twitter Worker...")
    try:
        async with aiohttp.ClientSession() as session:
            test_data = {
                "username": "testuser"
            }
            
            async with session.post("http://localhost:8003/api/follow", json=test_data, timeout=30) as response:
                if response.status == 200:
                    result = await response.json()
                    print(f"✅ Twitter Worker Response: {result}")
                    return True
                else:
                    error_text = await response.text()
                    print(f"❌ Twitter Worker Failed: {response.status} - {error_text}")
                    return False
    except Exception as e:
        print(f"❌ Error testing Twitter worker: {str(e)}")
        return False

async def main():
    """Run comprehensive test suite."""
    print("🧪 Starting Comprehensive Orchestrator Test")
    print("=" * 60)
    
    # Track test results
    results = {
        "orchestrator_health": False,
        "linkedin_health": False,
        "email_health": False,
        "twitter_health": False,
        "contact_creation": False,
        "contact_with_media": False,
        "contacts_list": False,
        "media_serving": False,
        "linkedin_worker": False,
        "email_worker": False,
        "twitter_worker": False
    }
    
    # Test health checks
    results["orchestrator_health"] = await test_orchestrator_health()
    results["linkedin_health"] = await test_worker_health("LinkedIn", 8001)
    results["email_health"] = await test_worker_health("Email", 8002)
    results["twitter_health"] = await test_worker_health("Twitter", 8003)
    
    print("\n" + "=" * 60)
    
    # Test orchestrator functionality
    results["contact_creation"], contact_id = await test_contact_creation()
    results["contact_with_media"], media_contact_id = await test_contact_with_media()
    results["contacts_list"] = await test_contacts_list()
    results["media_serving"] = await test_media_serving()
    
    print("\n" + "=" * 60)
    
    # Test worker functionality
    results["linkedin_worker"] = await test_linkedin_worker()
    results["email_worker"] = await test_email_worker()
    results["twitter_worker"] = await test_twitter_worker()
    
    print("\n" + "=" * 60)
    print("🏁 TEST RESULTS SUMMARY")
    print("=" * 60)
    
    passed = sum(1 for result in results.values() if result)
    total = len(results)
    
    for test_name, result in results.items():
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{test_name.replace('_', ' ').title()}: {status}")
    
    print(f"\n📊 Overall Score: {passed}/{total} tests passed")
    
    if passed == total:
        print("🎉 ALL TESTS PASSED! The orchestrator is fully functional.")
    else:
        print("⚠️ Some tests failed. Check the logs above for details.")
    
    return passed == total

if __name__ == "__main__":
    asyncio.run(main())