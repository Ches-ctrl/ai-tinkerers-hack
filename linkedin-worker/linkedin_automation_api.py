#!/usr/bin/env python3
"""
LinkedIn automation class optimized for API usage.
Runs in headless mode with persistent session.
"""

import os
import asyncio
import json
import random
from typing import Tuple, Optional
from urllib.parse import quote
from pathlib import Path

from playwright.async_api import async_playwright, TimeoutError
from dotenv import load_dotenv

load_dotenv()


async def human_like_delay(min_ms: int = 500, max_ms: int = 2000):
    """Add a human-like delay to avoid bot detection."""
    delay = random.uniform(min_ms, max_ms) / 1000
    await asyncio.sleep(delay)


async def human_like_typing(page, selector: str, text: str, delay_range: tuple = (50, 150)):
    """Type text with human-like delays between keystrokes."""
    element = await page.wait_for_selector(selector)
    await element.click()
    await asyncio.sleep(0.1)  # Small delay after click
    
    for char in text:
        await element.type(char)
        delay = random.uniform(delay_range[0], delay_range[1]) / 1000
        await asyncio.sleep(delay)


async def human_like_scroll(page, amount: int = 300):
    """Scroll the page like a human would."""
    await page.evaluate(f'window.scrollBy(0, {amount})')
    await human_like_delay(300, 800)


class LinkedInAutomationAPI:
    def __init__(self):
        self.email = os.getenv('LINKEDIN_EMAIL')
        self.password = os.getenv('LINKEDIN_PASSWORD')
        self.playwright = None
        self.browser = None
        self.context = None
        self.page = None
        self.is_logged_in = False
        self.session_file = Path("linkedin_session.json")
        
        if not self.email or not self.password:
            raise ValueError("LinkedIn email and password must be set in environment variables")
    
    async def initialize(self):
        """Initialize browser and login to LinkedIn."""
        if self.is_logged_in and self.page:
            return  # Already initialized
            
        await self._setup_browser()
        await self._load_session()
        if not self.is_logged_in:
            await self._login()
            await self._save_session()
    
    async def _setup_browser(self):
        """Initialize browser with stealth mode."""
        try:
            # Clean up any existing instances
            if self.page:
                try:
                    await self.page.close()
                except:
                    pass
            if self.context:
                try:
                    await self.context.close()
                except:
                    pass
            if self.browser:
                try:
                    await self.browser.close()
                except:
                    pass
            if self.playwright:
                try:
                    await self.playwright.stop()
                except:
                    pass
            
            # Start fresh
            self.playwright = await async_playwright().start()
            
            # Launch Firefox instead of Chrome (more stable on macOS)
            self.browser = await self.playwright.firefox.launch(
                headless=False
            )
            
            # Create context with realistic settings
            self.context = await self.browser.new_context(
                viewport={'width': 1366, 'height': 768},
                user_agent='Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36'
            )
            
            # Create page
            self.page = await self.context.new_page()
            
            # Test page is working
            await self.page.goto('about:blank')
            
        except Exception as e:
            print(f"Error setting up browser: {e}")
            # Clean up on error
            await self._cleanup_browser()
            raise
    
    async def _save_session(self):
        """Save browser session cookies to file."""
        try:
            cookies = await self.context.cookies()
            storage_state = await self.context.storage_state()
            
            session_data = {
                "cookies": cookies,
                "storage_state": storage_state
            }
            
            with open(self.session_file, 'w') as f:
                json.dump(session_data, f, indent=2)
            
            print("Session saved successfully")
        except Exception as e:
            print(f"Failed to save session: {e}")
    
    async def _load_session(self):
        """Load browser session from file."""
        try:
            if not self.session_file.exists():
                print("No session file found, will need to login")
                return
            
            with open(self.session_file, 'r') as f:
                session_data = json.load(f)
            
            # Set storage state
            await self.context.add_cookies(session_data["cookies"])
            
            # Test if session is still valid
            await self.page.goto('https://www.linkedin.com/feed/', wait_until='networkidle')
            await human_like_delay(2000, 3000)
            
            # Check if we're actually logged in
            if 'feed' in self.page.url and 'login' not in self.page.url:
                self.is_logged_in = True
                print("Session loaded successfully - already logged in")
            else:
                print("Session expired, will need to login")
                
        except Exception as e:
            print(f"Failed to load session: {e}")
            print("Will need to login")
    
    async def _login(self):
        """Log into LinkedIn with error handling and realistic behavior."""
        try:
            print("Logging into LinkedIn...")
            await self.page.goto('https://www.linkedin.com/login', wait_until='networkidle')
            await human_like_delay(1000, 2000)
            
            # Wait for and fill login form with human-like behavior
            await self.page.wait_for_selector('#username', timeout=10000)
            await human_like_delay(500, 1000)
            
            # Type email with human-like delays
            await human_like_typing(self.page, '#username', self.email)
            await human_like_delay(300, 600)
            
            # Type password with human-like delays
            await human_like_typing(self.page, '#password', self.password)
            await human_like_delay(500, 1000)
            
            # Click sign in with slight delay
            await self.page.click('button[type="submit"]')
            await human_like_delay(2000, 3000)
            
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
        """Add connection directly from profile URL with realistic behavior."""
        try:
            print(f"Visiting profile: {profile_url}")
            await self.page.goto(profile_url, wait_until='networkidle')
            await human_like_delay(2000, 4000)
            
            # Scroll down a bit to simulate reading the profile
            await human_like_scroll(self.page, 300)
            await human_like_delay(1000, 2000)
            
            # Try multiple selectors for connect button
            connect_selectors = [
                'button:has-text("Connect")',
                'button[aria-label*="Connect"]',
                '.pvs-profile-actions button:has-text("Connect")',
                'div[data-test-icon="connect-medium"] + span',
                '.pv-s-profile-actions button:has-text("Connect")'
            ]
            
            connect_clicked = False
            for selector in connect_selectors:
                try:
                    element = await self.page.wait_for_selector(selector, timeout=3000)
                    if element:
                        await human_like_delay(500, 1000)  # Pause before clicking
                        await element.click()
                        connect_clicked = True
                        print("Clicked Connect button")
                        break
                except:
                    continue
            
            if not connect_clicked:
                # Check if already connected
                if await self.page.query_selector('button:has-text("Message")'):
                    return False, "Already connected to this person", profile_url
                return False, "Connect button not found - profile may be restricted", profile_url
            
            # Handle connection modal with realistic delays
            await human_like_delay(2000, 3000)
            
            # Send connection request without note (just connect)
            await human_like_delay(1000, 2000)
            
            send_selectors = [
                'button:has-text("Send")',
                'button[aria-label*="Send"]',
                'button.ml1:has-text("Send")',
                'button[data-test-modal-primary-action]'
            ]
            
            for selector in send_selectors:
                try:
                    send_button = await self.page.wait_for_selector(selector, timeout=3000)
                    if send_button:
                        await human_like_delay(300, 600)
                        await send_button.click()
                        await human_like_delay(1000, 2000)
                        print("Connection request sent successfully")
                        return True, "Connection request sent successfully", profile_url
                except:
                    continue
            
            return False, "Could not send connection request", profile_url
            
        except Exception as e:
            return False, f"Error accessing profile: {str(e)}", profile_url
    
    async def _add_by_search(self, name: str, message: Optional[str] = None) -> Tuple[bool, str, Optional[str]]:
        """Search for a person and add them as a connection using global search."""
        try:
            # Use global search URL format like the example provided
            search_url = f'https://www.linkedin.com/search/results/all/?keywords={quote(name)}&origin=GLOBAL_SEARCH_HEADER&sid=YDb'
            print(f"Searching LinkedIn for: {name}")
            print(f"Search URL: {search_url}")
            
            await self.page.goto(search_url, wait_until='networkidle')
            await human_like_delay(2000, 3000)
            
            # Look for "People" tab and click it to filter to people results
            try:
                people_tab = await self.page.wait_for_selector('button:has-text("People")', timeout=5000)
                if people_tab:
                    await people_tab.click()
                    await human_like_delay(2000, 3000)
                    print("Clicked People tab to filter results")
            except:
                print("Could not find People tab, continuing with all results")
            
            # Scroll a bit to make it look more natural
            await human_like_scroll(self.page, 200)
            
            # Look for profile results - try multiple selectors
            result_selectors = [
                '.entity-result__title-text a',
                '.search-result__title-text a',
                '[data-test-app-aware-link] .entity-result__title-text a',
                '.reusable-search-simple-insight a'
            ]
            
            first_result = None
            for selector in result_selectors:
                try:
                    first_result = await self.page.wait_for_selector(selector, timeout=3000)
                    if first_result:
                        break
                except:
                    continue
            
            if not first_result:
                return False, f"No profile results found for '{name}'", None
            
            profile_url = await first_result.get_attribute('href')
            
            # Clean up the URL
            if profile_url.startswith('/'):
                profile_url = f"https://www.linkedin.com{profile_url}"
            
            print(f"Found profile: {profile_url}")
            
            return await self._add_by_profile_url(profile_url, message)
            
        except Exception as e:
            return False, f"Search error: {str(e)}", None
    
    async def _cleanup_browser(self):
        """Clean up browser resources."""
        try:
            if self.page:
                await self.page.close()
                self.page = None
        except Exception as e:
            print(f"Error closing page: {e}")
        
        try:
            if self.context:
                await self.context.close()
                self.context = None
        except Exception as e:
            print(f"Error closing context: {e}")
        
        try:
            if self.browser:
                await self.browser.close()
                self.browser = None
        except Exception as e:
            print(f"Error closing browser: {e}")
        
        try:
            if self.playwright:
                await self.playwright.stop()
                self.playwright = None
        except Exception as e:
            print(f"Error stopping playwright: {e}")
        
        self.is_logged_in = False

    async def cleanup(self):
        """Clean up browser resources."""
        await self._cleanup_browser()