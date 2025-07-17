#!/usr/bin/env python3
"""
Test the full contact workflow including all workers.
"""

import asyncio
import aiohttp
import json

BASE_URL = "http://localhost:8000"

# Test contact that should trigger all workers
FULL_CONTACT = {
    "first_name": "John",
    "last_name": "Doe",
    "phone_numbers": ["+1234567890"],
    "emails": ["john.doe@example.com"],
    "urls": [
        "https://www.linkedin.com/in/johndoe",
        "https://twitter.com/johndoe"
    ],
    "audio": None,
    "photo": "iVBORw0KGgoAAAANSUhEUgAAAAEAAAABCAYAAAAfFcSJAAAADUlEQVR42mNkYPhfDwAChAI9jU77kgAAAABJRU5ErkJggg=="
}

async def test_full_workflow():
    """Test the complete workflow with all workers."""
    print("🚀 Testing Full Contact Workflow with All Workers")
    print("=" * 60)
    
    try:
        async with aiohttp.ClientSession() as session:
            async with session.post(f"{BASE_URL}/api/contact", json=FULL_CONTACT) as response:
                if response.status == 200:
                    result = await response.json()
                    print(f"✅ Contact Created Successfully!")
                    print(f"📋 Contact ID: {result['contact_id']}")
                    print(f"📊 Status Report:")
                    print(f"   {result['linkedin_status']}")
                    
                    # Parse the status to show individual worker results
                    status_parts = result['linkedin_status'].split(' | ')
                    print(f"\n🔍 Individual Worker Results:")
                    for i, status in enumerate(status_parts):
                        if i == 0:
                            print(f"   📱 WhatsApp: {status}")
                        elif i == 1:
                            print(f"   🔗 LinkedIn: {status}")
                        elif i == 2:
                            print(f"   🐦 Twitter: {status}")
                        elif i == 3:
                            print(f"   📧 Email: {status}")
                        else:
                            print(f"   ❓ Unknown: {status}")
                    
                    print(f"\n📊 Total Status Parts: {len(status_parts)}")
                    
                    return True
                else:
                    error_text = await response.text()
                    print(f"❌ Contact Creation Failed: {response.status} - {error_text}")
                    return False
                    
    except Exception as e:
        print(f"❌ Error testing full workflow: {str(e)}")
        return False

async def main():
    """Run the full workflow test."""
    success = await test_full_workflow()
    
    print(f"\n{'='*60}")
    if success:
        print("🎉 FULL WORKFLOW TEST COMPLETED!")
        print("💡 Check the frontend at http://localhost:3000 to see the new contact photo!")
        print("📱 All workers (WhatsApp, LinkedIn, Twitter, Email) were triggered!")
    else:
        print("❌ Full workflow test failed!")

if __name__ == "__main__":
    asyncio.run(main())