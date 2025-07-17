#!/usr/bin/env python3
"""
LinkedIn automation class optimized for API usage.
Runs in headless mode with persistent session.
"""

import os
import asyncio
from typing import Tuple, Optional
from urllib.parse import quote

from playwright.async_api import async_playwright, TimeoutError
from playwright_stealth import stealth_async
from dotenv import load_dotenv

load_dotenv()


class LinkedInAutomationAPI:
    def __init__(self):
        self.email = os.getenv('LINKEDIN_EMAIL')
        self.password = os.getenv('LINKEDIN_PASSWORD')
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
        self.is_logged_in = False
        
        if not self.email or not self.password:
            raise ValueError("LinkedIn email and password must be set in environment variables")
    
    async def initialize(self):
        """Initialize browser and login to LinkedIn."""
        await self._setup_browser()
        await self._login()
    
    async def _setup_browser(self):
        """Initialize browser in headless mode for API usage."""
        self.playwright = await async_playwright().start()
        
        # Launch browser in headless mode for server deployment
        self.browser = await self.playwright.chromium.launch(
            headless=True,  # Headless for API usage
            args=[
                '--disable-blink-features=AutomationControlled',
                '--disable-dev-shm-usage',
                '--no-sandbox',
                '--disable-setuid-sandbox',
                '--disable-accelerated-2d-canvas',
                '--disable-gpu',
                '--window-size=1920,1080'
            ]
        )
        
        # Create persistent context for session management
        self.context = await self.browser.new_context(
            viewport={'width': 1920, 'height': 1080},
            user_agent='Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            locale='en-US',
            timezone_id='America/New_York'
        )
        
        self.page = await self.context.new_page()
        
        # Apply stealth mode
        await stealth_async(self.page)
    
    async def _login(self):
        """Log into LinkedIn with error handling."""
        try:
            print("Logging into LinkedIn...")
            await self.page.goto('https://www.linkedin.com/login', wait_until='networkidle')
            
            # Wait for and fill login form
            await self.page.wait_for_selector('#username', timeout=10000)
            await self.page.fill('#username', self.email)
            await self.page.fill('#password', self.password)
            
            # Click sign in
            await self.page.click('button[type="submit"]')
            
            # Wait for successful login
            try:
                await self.page.wait_for_url('https://www.linkedin.com/feed/', timeout=30000)
                self.is_logged_in = True
                print("Successfully logged into LinkedIn")
            except TimeoutError:
                # Check for common issues
                if 'checkpoint' in self.page.url or 'challenge' in self.page.url:
                    print("WARNING: Security checkpoint detected. Manual intervention required.")
                    self.is_logged_in = False
                elif 'login' in self.page.url:
                    print("ERROR: Login failed. Check credentials.")
                    self.is_logged_in = False
                else:
                    # Assume successful login if we're not on login page
                    self.is_logged_in = True
                    print("Login completed")
                    
        except Exception as e:
            print(f"Login error: {str(e)}")
            self.is_logged_in = False
            raise
    
    async def add_connection(
        self, 
        profile_url: Optional[str] = None, 
        name: Optional[str] = None, 
        message: Optional[str] = None
    ) -> Tuple[bool, str, Optional[str]]:
        """
        Add a LinkedIn connection and return success status with message.
        
        Returns:
            Tuple of (success: bool, message: str, profile_url: str or None)
        """
        if not self.is_logged_in:
            return False, "Not logged into LinkedIn", None
        
        try:
            if profile_url:
                return await self._add_by_profile_url(profile_url, message)
            elif name:
                return await self._add_by_search(name, message)
            else:
                return False, "Either profile_url or name must be provided", None
        except Exception as e:
            return False, f"Error: {str(e)}", None
    
    async def _add_by_profile_url(self, profile_url: str, message: Optional[str] = None) -> Tuple[bool, str, Optional[str]]:
        """Add connection directly from profile URL."""
        try:
            await self.page.goto(profile_url, wait_until='networkidle')
            await asyncio.sleep(2)
            
            # Try multiple selectors for connect button
            connect_selectors = [
                'button:has-text("Connect")',
                'button[aria-label*="Connect"]',
                '.pvs-profile-actions button:has-text("Connect")',
                'div[data-test-icon="connect-medium"] + span'
            ]
            
            connect_clicked = False
            for selector in connect_selectors:
                try:
                    element = await self.page.wait_for_selector(selector, timeout=3000)
                    if element:
                        await element.click()
                        connect_clicked = True
                        break
                except:
                    continue
            
            if not connect_clicked:
                # Check if already connected
                if await self.page.query_selector('button:has-text("Message")'):
                    return False, "Already connected to this person", profile_url
                return False, "Connect button not found - profile may be restricted", profile_url
            
            # Handle connection modal
            await asyncio.sleep(2)
            
            # Add note if provided
            if message:
                try:
                    add_note = await self.page.wait_for_selector('button:has-text("Add a note")', timeout=3000)
                    if add_note:
                        await add_note.click()
                        await asyncio.sleep(1)
                        
                        note_field = await self.page.wait_for_selector('textarea[name="message"]', timeout=3000)
                        await note_field.fill(message)
                except:
                    pass
            
            # Send connection request
            send_selectors = [
                'button:has-text("Send")',
                'button[aria-label*="Send"]',
                'button.ml1:has-text("Send")'
            ]
            
            for selector in send_selectors:
                try:
                    await self.page.click(selector, timeout=3000)
                    return True, "Connection request sent successfully", profile_url
                except:
                    continue
            
            return False, "Could not send connection request", profile_url
            
        except Exception as e:
            return False, f"Error accessing profile: {str(e)}", profile_url
    
    async def _add_by_search(self, name: str, message: Optional[str] = None) -> Tuple[bool, str, Optional[str]]:
        """Search for a person and add them as a connection."""
        try:
            search_url = f'https://www.linkedin.com/search/results/people/?keywords={quote(name)}'
            await self.page.goto(search_url, wait_until='networkidle')
            await asyncio.sleep(2)
            
            # Get first search result
            first_result = await self.page.query_selector('.entity-result__title-text a')
            if not first_result:
                return False, f"No results found for '{name}'", None
            
            profile_url = await first_result.get_attribute('href')
            
            # Clean up the URL
            if profile_url.startswith('/'):
                profile_url = f"https://www.linkedin.com{profile_url}"
            
            return await self._add_by_profile_url(profile_url, message)
            
        except Exception as e:
            return False, f"Search error: {str(e)}", None
    
    async def cleanup(self):
        """Clean up browser resources."""
        if self.page:
            await self.page.close()
        if self.context:
            await self.context.close()
        if self.browser:
            await self.browser.close()
        if self.playwright:
            await self.playwright.stop()
        self.is_logged_in = False