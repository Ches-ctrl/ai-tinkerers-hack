#!/usr/bin/env python3
"""
Direct test of LinkedIn automation without API.
"""

import asyncio
import signal
import sys
from linkedin_automation_api import LinkedInAutomationAPI

# Global variable to track automation instance for cleanup
automation_instance = None

def signal_handler(signum, frame):
    """Handle CTRL+C gracefully."""
    print("\n\n🛑 CTRL+C detected - cleaning up...")
    if automation_instance:
        # Run cleanup in event loop
        loop = asyncio.get_event_loop()
        loop.run_until_complete(automation_instance.cleanup())
    print("✅ Cleanup complete - exiting")
    sys.exit(0)

async def test_direct():
    """Test LinkedIn automation directly."""
    global automation_instance
    
    # Set up signal handler for graceful shutdown
    signal.signal(signal.SIGINT, signal_handler)
    
    print("Testing LinkedIn automation directly...")
    print("(Press CTRL+C to exit gracefully)")
    
    automation = None
    try:
        # Create automation instance
        automation = LinkedInAutomationAPI()
        automation_instance = automation  # Store globally for signal handler
        
        print("Initializing browser...")
        await automation.initialize()
        
        print("Browser initialized successfully!")
        print(f"Logged in: {automation.is_logged_in}")
        
        if automation.is_logged_in:
            print("\nTesting connection with David Gelberg...")
            
            success, message, profile_url = await automation.add_connection(
                name="David Gelberg",
                message=None
            )
            
            print(f"Success: {success}")
            print(f"Message: {message}")
            print(f"Profile URL: {profile_url}")
            
            if success:
                print("\n✅ SUCCESS: Connection request sent!")
            else:
                print("\n❌ FAILED: Connection request failed")
        else:
            print("❌ Not logged in - login failed")
            
        # Keep the browser open for inspection
        print("\n🔍 Browser will stay open for inspection.")
        print("Press CTRL+C to exit gracefully.")
        
        # Wait indefinitely until CTRL+C
        while True:
            await asyncio.sleep(1)
            
    except KeyboardInterrupt:
        print("\n🛑 Interrupted by user")
    except Exception as e:
        print(f"❌ ERROR: {str(e)}")
        import traceback
        traceback.print_exc()
    finally:
        if automation:
            print("\nCleaning up...")
            await automation.cleanup()
            automation_instance = None

if __name__ == "__main__":
    asyncio.run(test_direct())