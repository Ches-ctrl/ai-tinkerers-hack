#!/usr/bin/env python3
"""
LinkedIn connection automation script using Playwright with stealth mode.
This script automates the process of adding a LinkedIn connection.
"""

import os
import sys
import time
import asyncio
from urllib.parse import quote
from dotenv import load_dotenv
from playwright.async_api import async_playwright, TimeoutError
from playwright_stealth import stealth_async

load_dotenv()


class LinkedInAutomation:
    def __init__(self, email=None, password=None):
        self.email = email or os.getenv('LINKEDIN_EMAIL')
        self.password = password or os.getenv('LINKEDIN_PASSWORD')
        self.browser = None
        self.context = None
        self.page = None

        if not self.email or not self.password:
            raise ValueError("LinkedIn email and password must be provided via environment variables or parameters")

    async def setup_browser(self):
        """Initialize browser with stealth mode enabled."""
        playwright = await async_playwright().start()

        # Launch browser in headful mode so you can watch the automation
        self.browser = await playwright.chromium.launch(
            headless=False,
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-accelerated-2d-canvas',
                '--disable-gpu'
            ]
        )

        # Create context with realistic viewport
        self.context = await self.browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
        )

        self.page = await self.context.new_page()

        # Apply stealth mode to avoid detection
        await stealth_async(self.page)

    async def login(self):
        """Log into LinkedIn."""
        print("Navigating to LinkedIn login page...")
        await self.page.goto('https://www.linkedin.com/login')

        # Wait for login form
        await self.page.wait_for_selector('#username', timeout=10000)

        print("Filling in login credentials...")
        # Type slowly to appear more human-like
        await self.page.type('#username', self.email, delay=100)
        await self.page.type('#password', self.password, delay=100)

        # Click sign in button
        await self.page.click('button[type="submit"]')

        print("Logging in...")
        # Wait for navigation or potential security check
        try:
            await self.page.wait_for_url('https://www.linkedin.com/feed/', timeout=30000)
            print("Successfully logged in!")
        except TimeoutError:
            # Check if we're on a security checkpoint
            if 'checkpoint' in self.page.url or 'challenge' in self.page.url:
                print("Security checkpoint detected. Please complete the verification manually.")
                print("Press Enter when you've completed the verification...")
                input()
            else:
                print(f"Login might have failed. Current URL: {self.page.url}")

    async def add_connection(self, profile_url=None, name=None, message=None):
        """Add a LinkedIn connection by profile URL or search by name."""
        if profile_url:
            await self._add_by_profile_url(profile_url, message)
        elif name:
            await self._add_by_search(name, message)
        else:
            raise ValueError("Either profile_url or name must be provided")

    async def _add_by_profile_url(self, profile_url, message=None):
        """Add connection directly from profile URL."""
        print(f"Navigating to profile: {profile_url}")
        await self.page.goto(profile_url)

        # Wait for page to load
        await self.page.wait_for_load_state('networkidle')
        await asyncio.sleep(2)  # Additional wait for dynamic content

        # Find and click connect button
        connect_button_selectors = [
            'button:has-text("Connect")',
            'button[aria-label*="Connect"]',
            '.pvs-profile-actions__action:has-text("Connect")',
            'button.pv-s-profile-actions__action:has-text("Connect")'
        ]

        connect_clicked = False
        for selector in connect_button_selectors:
            try:
                await self.page.click(selector, timeout=5000)
                connect_clicked = True
                print("Clicked Connect button")
                break
            except:
                continue

        if not connect_clicked:
            print("Could not find Connect button. The person might already be a connection or the button is not available.")
            return False

        # Wait for modal to appear
        await asyncio.sleep(2)

        # Check if we need to add a note
        try:
            add_note_button = await self.page.wait_for_selector('button:has-text("Add a note")', timeout=3000)
            if add_note_button and message:
                await add_note_button.click()
                await asyncio.sleep(1)

                # Type the message
                note_textarea = await self.page.wait_for_selector('textarea[name="message"]', timeout=5000)
                await note_textarea.type(message, delay=50)
                await asyncio.sleep(1)
        except:
            print("No 'Add a note' option available or no message provided")

        # Send the connection request
        send_button_selectors = [
            'button:has-text("Send")',
            'button[aria-label="Send invitation"]',
            'button.ml1:has-text("Send")'
        ]

        for selector in send_button_selectors:
            try:
                await self.page.click(selector, timeout=5000)
                print("Connection request sent successfully!")
                return True
            except:
                continue

        print("Could not send connection request")
        return False

    async def _add_by_search(self, name, message=None):
        """Search for a person and add them as a connection."""
        print(f"Searching for: {name}")

        # Navigate to search with people filter
        search_url = f'https://www.linkedin.com/search/results/people/?keywords={quote(name)}'
        await self.page.goto(search_url)

        # Wait for search results
        await self.page.wait_for_selector('.search-results-container', timeout=10000)
        await asyncio.sleep(2)

        # Click on the first result
        first_result = await self.page.query_selector('.entity-result__title-text a')
        if first_result:
            profile_url = await first_result.get_attribute('href')
            print(f"Found profile: {profile_url}")

            # Use the profile URL method to add connection
            await self._add_by_profile_url(profile_url, message)
        else:
            print("No search results found")
            return False

    async def close(self):
        """Close the browser."""
        if self.browser:
            await self.browser.close()


async def main():
    """Main function to run the automation."""
    # Example usage
    automation = LinkedInAutomation()

    try:
        await automation.setup_browser()
        await automation.login()

        # Example 1: Add by profile URL
        # await automation.add_connection(
        #     profile_url="https://www.linkedin.com/in/example-profile/",
        #     message="Hi! I'd like to connect with you on LinkedIn."
        # )

        # Example 2: Add by searching name
        # await automation.add_connection(
        #     name="John Doe",
        #     message="Hi John! I'd like to connect with you on LinkedIn."
        # )

        # Keep browser open for manual inspection
        print("\nAutomation complete. Press Enter to close the browser...")
        input()

    except Exception as e:
        print(f"Error: {e}")
    finally:
        await automation.close()


if __name__ == "__main__":
    # Command line usage
    if len(sys.argv) > 1:
        if len(sys.argv) == 2:
            # Profile URL provided
            asyncio.run(main())
        else:
            print("Usage: python linkedin_add_connection.py [profile_url]")
            print("   or: Set up profile URL in the script and run without arguments")
    else:
        asyncio.run(main())
