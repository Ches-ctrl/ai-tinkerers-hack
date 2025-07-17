#!/usr/bin/env python3
"""
Test sending a real email to charlie@cheddar.jobs
"""

import asyncio
import aiohttp
import json

BASE_URL = "http://localhost:8002"

async def test_real_email():
    """Test sending an email to charlie@cheddar.jobs."""
    print("📧 Testing Real Email Send to charlie@cheddar.jobs")
    print("=" * 60)
    
    try:
        async with aiohttp.ClientSession() as session:
            # Test networking email endpoint
            email_data = {
                "first_name": "Charlie",
                "last_name": "Cheesman",
                "email": "charlie@cheddar.jobs",
                "company": "Cheddar",
                "title": "Founder",
                "photo_path": None
            }
            
            print(f"📤 Sending networking email to: {email_data['email']}")
            print(f"👤 Contact: {email_data['first_name']} {email_data['last_name']}")
            print(f"🏢 Company: {email_data['company']}")
            print(f"💼 Title: {email_data['title']}")
            print("\n⏳ Sending email...")
            
            async with session.post(f"{BASE_URL}/api/send-networking-email", json=email_data) as response:
                result = await response.json()
                
                if response.status == 200:
                    if result.get('success'):
                        print(f"✅ Email sent successfully!")
                        print(f"📧 To: {result.get('email_sent_to')}")
                        print(f"📋 Message: {result.get('message')}")
                        print(f"👤 Contact Details: {result.get('contact_details')}")
                        return True
                    else:
                        print(f"❌ Email failed: {result.get('message')}")
                        return False
                else:
                    print(f"❌ HTTP Error: {response.status}")
                    print(f"📄 Response: {json.dumps(result, indent=2)}")
                    return False
                    
    except Exception as e:
        print(f"❌ Error testing email: {str(e)}")
        return False

async def test_basic_email():
    """Test sending a basic email."""
    print("\n📧 Testing Basic Email Send")
    print("=" * 60)
    
    try:
        async with aiohttp.ClientSession() as session:
            email_data = {
                "to_email": "charlie@cheddar.jobs",
                "subject": "Test Email from AI Tinkerers Hack",
                "body": """
                <html>
                <body>
                    <h2>Test Email from AI Tinkerers Hack</h2>
                    <p>Hi Charlie,</p>
                    <p>This is a test email from the AI Tinkerers Hack orchestrator system.</p>
                    <p>The email worker is functioning correctly!</p>
                    <p>Best regards,<br>
                    AI Tinkerers Hack System</p>
                </body>
                </html>
                """,
                "from_name": "AI Tinkerers Bot",
                "is_html": True
            }
            
            print(f"📤 Sending basic email to: {email_data['to_email']}")
            print(f"📋 Subject: {email_data['subject']}")
            print("\n⏳ Sending email...")
            
            async with session.post(f"{BASE_URL}/api/send-email", json=email_data) as response:
                result = await response.json()
                
                if response.status == 200:
                    if result.get('success'):
                        print(f"✅ Email sent successfully!")
                        print(f"📧 To: {result.get('to_email')}")
                        print(f"📋 Message: {result.get('message')}")
                        return True
                    else:
                        print(f"❌ Email failed: {result.get('message')}")
                        return False
                else:
                    print(f"❌ HTTP Error: {response.status}")
                    print(f"📄 Response: {json.dumps(result, indent=2)}")
                    return False
                    
    except Exception as e:
        print(f"❌ Error testing basic email: {str(e)}")
        return False

async def main():
    """Run email tests."""
    print("🧪 Starting Email Worker Tests")
    print("=" * 60)
    
    # Test networking email
    networking_success = await test_real_email()
    
    # Test basic email
    basic_success = await test_basic_email()
    
    print("\n" + "=" * 60)
    print("📊 EMAIL TEST RESULTS")
    print("=" * 60)
    print(f"Networking Email: {'✅ PASS' if networking_success else '❌ FAIL'}")
    print(f"Basic Email: {'✅ PASS' if basic_success else '❌ FAIL'}")
    
    if networking_success and basic_success:
        print("\n🎉 ALL EMAIL TESTS PASSED!")
        print("📧 Check charlie@cheddar.jobs inbox for test emails!")
    else:
        print("\n⚠️ Some email tests failed. Check Gmail credentials and settings.")

if __name__ == "__main__":
    asyncio.run(main())