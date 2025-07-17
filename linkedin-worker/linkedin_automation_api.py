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

from playwright.async_api import async_playwright, TimeoutError, Page
from dotenv import load_dotenv

load_dotenv()


async def human_like_delay(min_ms: int = 100, max_ms: int = 300):
    """Add a minimal delay for UI responsiveness."""
    delay = random.uniform(min_ms, max_ms) / 1000
    await asyncio.sleep(delay)


async def human_like_typing(page, selector: str, text: str, delay_range: tuple = (10, 30)):
    """Type text with minimal delays between keystrokes."""
    element = await page.wait_for_selector(selector)
    await element.click()
    await asyncio.sleep(0.05)  # Small delay after click
    
    for char in text:
        await element.type(char)
        delay = random.uniform(delay_range[0], delay_range[1]) / 1000
        await asyncio.sleep(delay)


async def human_like_scroll(page, amount: int = 300):
    """Scroll the page like a human would."""
    await page.evaluate(f'window.scrollBy(0, {amount})')
    await human_like_delay(100, 200)


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
            
            # First, check if we're already on LinkedIn and logged in
            current_url = self.page.url
            print(f"Current page URL: {current_url}")
            
            # If we're already on LinkedIn, check if we're logged in
            if 'linkedin.com' in current_url and 'login' not in current_url:
                print("Already on LinkedIn, checking login status...")
                try:
                    # Look for elements that indicate we're logged in
                    await self.page.wait_for_selector('.global-nav__primary-link, .feed-shared-actor__name, [data-test-global-nav-profile]', timeout=3000)
                    self.is_logged_in = True
                    print("Session loaded successfully - already logged in and on LinkedIn")
                    return
                except:
                    print("Not logged in, will need to login")
                    self.is_logged_in = False
                    return
            
            # Test if session is still valid - try to go to feed page
            try:
                print("Navigating to LinkedIn feed to test session...")
                await self.page.goto('https://www.linkedin.com/feed/', wait_until='domcontentloaded', timeout=15000)
                await human_like_delay(500, 1000)
                
                # Check if we're actually logged in by looking for LinkedIn-specific elements
                try:
                    # Wait for either login form or feed content
                    await self.page.wait_for_selector('input[name="session_key"], .feed-shared-actor__name, .global-nav__primary-link, [data-test-global-nav-profile]', timeout=8000)
                    
                    # If we can find login form, session expired
                    if await self.page.query_selector('input[name="session_key"]'):
                        print("Session expired - found login form")
                        self.is_logged_in = False
                    # If we're on feed page with navigation, we're logged in
                    elif 'feed' in self.page.url or ('linkedin.com' in self.page.url and 'login' not in self.page.url):
                        self.is_logged_in = True
                        print("Session loaded successfully - navigated to feed and logged in")
                    else:
                        print("Session status unclear, will attempt login")
                        self.is_logged_in = False
                        
                except Exception as e:
                    print(f"Error checking session status: {e}")
                    print("Will attempt login")
                    self.is_logged_in = False
                    
            except Exception as e:
                print(f"Error loading feed page: {e}")
                print("Will attempt login")
                self.is_logged_in = False
                
        except Exception as e:
            print(f"Failed to load session: {e}")
            print("Will need to login")
    
    async def _login(self):
        """Log into LinkedIn with error handling and realistic behavior."""
        try:
            print("Logging into LinkedIn...")
            await self.page.goto('https://www.linkedin.com/login', wait_until='networkidle')
            await human_like_delay(200, 500)
            
            # Wait for and fill login form with human-like behavior
            await self.page.wait_for_selector('#username', timeout=10000)
            await human_like_delay(100, 200)
            
            # Type email with human-like delays
            await human_like_typing(self.page, '#username', self.email)
            await human_like_delay(100, 200)
            
            # Type password with human-like delays
            await human_like_typing(self.page, '#password', self.password)
            await human_like_delay(100, 200)
            
            # Click sign in with slight delay
            await self.page.click('button[type="submit"]')
            await human_like_delay(500, 1000)
            
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
            await human_like_delay(200, 500)
            
            # Scroll down a bit to simulate reading the profile
            await human_like_scroll(self.page, 300)
            await human_like_delay(100, 200)
            
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
                        await human_like_delay(100, 200)
                        await send_button.click()
                        await human_like_delay(200, 500)
                        print("Connection request sent successfully")
                        return True, "Connection request sent successfully", profile_url
                except:
                    continue
            
            return False, "Could not send connection request", profile_url
            
        except Exception as e:
            return False, f"Error accessing profile: {str(e)}", profile_url
    
    async def _add_by_search(self, name: str, message: Optional[str] = None) -> Tuple[bool, str, Optional[str]]:
        """Search for a person and add them as a connection using the search box."""
        try:
            print(f"Searching LinkedIn for: {name}")
            print(f"Current URL: {self.page.url}")
            
            # First, make sure we're on a LinkedIn page where we can search
            if 'linkedin.com' not in self.page.url:
                print("Not on LinkedIn, navigating to feed page...")
                await self.page.goto('https://www.linkedin.com/feed/', wait_until='networkidle')
                await human_like_delay(500, 1000)
            
            # Find and click the search box
            search_selectors = [
                'input[placeholder*="Search"]',
                '.search-global-typeahead__input',
                'input[role="combobox"]',
                '#global-nav-search .search-global-typeahead__input'
            ]
            
            search_input = None
            for selector in search_selectors:
                try:
                    search_input = await self.page.wait_for_selector(selector, timeout=3000)
                    if search_input:
                        print(f"Found search input with selector: {selector}")
                        break
                except:
                    continue
            
            if not search_input:
                print("Could not find search input, trying direct URL approach...")
                # Fallback to direct URL
                search_url = f'https://www.linkedin.com/search/results/people/?keywords={quote(name)}&origin=GLOBAL_SEARCH_HEADER'
                print(f"Using direct search URL: {search_url}")
                await self.page.goto(search_url, wait_until='networkidle')
                await human_like_delay(500, 1000)
            else:
                # Clear any existing text and type the search query
                await search_input.click()
                await human_like_delay(200, 400)
                await search_input.fill('')  # Clear existing text
                await human_like_delay(100, 200)
                await search_input.type(name)
                await human_like_delay(500, 1000)
                
                # Press Enter or click search
                await search_input.press('Enter')
                await human_like_delay(1000, 2000)
                
                # Wait for search results to load
                await self.page.wait_for_load_state('networkidle')
                await human_like_delay(500, 1000)
                
                # Click on People tab if it exists
                try:
                    people_tab = await self.page.wait_for_selector('button:has-text("People")', timeout=3000)
                    if people_tab:
                        await people_tab.click()
                        await human_like_delay(500, 1000)
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
                '.reusable-search-simple-insight a',
                '.entity-result__content a[href*="/in/"]',
                '.search-result-card__title a',
                'a[href*="/in/"][data-test-app-aware-link]'
            ]
            
            first_result = None
            for selector in result_selectors:
                try:
                    # Wait for any profile links to appear
                    await self.page.wait_for_selector(selector, timeout=5000)
                    first_result = await self.page.query_selector(selector)
                    if first_result:
                        print(f"Found profile result with selector: {selector}")
                        break
                except:
                    continue
            
            if not first_result:
                print(f"No profile results found for '{name}'. Available elements:")
                # Debug: print available elements
                try:
                    elements = await self.page.query_selector_all('a[href*="/in/"]')
                    print(f"Found {len(elements)} profile links")
                    for i, elem in enumerate(elements[:3]):  # Show first 3
                        href = await elem.get_attribute('href')
                        text = await elem.text_content()
                        print(f"  {i+1}. {text} -> {href}")
                except:
                    pass
                return False, f"No profile results found for '{name}'", None
            
            # Get profile URL for return value
            profile_url = await first_result.get_attribute('href')
            if profile_url.startswith('/'):
                profile_url = f"https://www.linkedin.com{profile_url}"
            
            print(f"Found profile: {profile_url}")
            
            # Look for ANY Connect button on the page (search results or profile)
            print("Looking for Connect button anywhere on the page...")
            
            # Try to find Connect buttons using different strategies
            connect_clicked = False
            
            # Strategy 1: Direct text search - most reliable
            try:
                print("Strategy 1: Looking for buttons with 'Connect' text...")
                all_buttons = await self.page.query_selector_all('button')
                for button in all_buttons:
                    button_text = await button.text_content()
                    if button_text and 'Connect' in button_text.strip():
                        is_visible = await button.is_visible()
                        if is_visible:
                            print(f"Found Connect button with text: '{button_text.strip()}'")
                            await human_like_delay(100, 200)
                            await button.click()
                            connect_clicked = True
                            print("Successfully clicked Connect button")
                            break
            except Exception as e:
                print(f"Strategy 1 failed: {str(e)}")
            
            # Strategy 2: Aria-label search if Strategy 1 failed
            if not connect_clicked:
                try:
                    print("Strategy 2: Looking for buttons with Connect aria-label...")
                    connect_buttons = await self.page.query_selector_all('button[aria-label*="Connect"]')
                    for button in connect_buttons:
                        is_visible = await button.is_visible()
                        if is_visible:
                            aria_label = await button.get_attribute('aria-label')
                            print(f"Found Connect button with aria-label: '{aria_label}'")
                            await human_like_delay(100, 200)
                            await button.click()
                            connect_clicked = True
                            print("Successfully clicked Connect button")
                            break
                except Exception as e:
                    print(f"Strategy 2 failed: {str(e)}")
            
            # Strategy 3: Class-based search if previous strategies failed
            if not connect_clicked:
                try:
                    print("Strategy 3: Looking with class-based selectors...")
                    all_connect_selectors = [
                        '.artdeco-button:has-text("Connect")',
                        'button.artdeco-button:has-text("Connect")',
                        '.entity-result button:has-text("Connect")',
                        '.search-result button:has-text("Connect")',
                        'button[data-test-app-aware-link]:has-text("Connect")',
                        'button.artdeco-button--2:has-text("Connect")'
                    ]
                    
                    for i, selector in enumerate(all_connect_selectors):
                        try:
                            print(f"Trying selector {i+1}/{len(all_connect_selectors)}: {selector}")
                            connect_buttons = await self.page.query_selector_all(selector)
                            if connect_buttons:
                                print(f"Found {len(connect_buttons)} Connect button(s) with selector: {selector}")
                                for button in connect_buttons:
                                    is_visible = await button.is_visible()
                                    if is_visible:
                                        print(f"Clicking visible Connect button")
                                        await human_like_delay(100, 200)
                                        await button.click()
                                        connect_clicked = True
                                        print("Successfully clicked Connect button")
                                        break
                                if connect_clicked:
                                    break
                        except Exception as e:
                            print(f"Selector {selector} failed: {str(e)}")
                            continue
                except Exception as e:
                    print(f"Strategy 3 failed: {str(e)}")
            
            # Strategy 4: Click on the profile and then look for Connect button
            if not connect_clicked:
                try:
                    print("Strategy 4: Clicking on profile link to go to profile page...")
                    await human_like_delay(100, 200)
                    await first_result.click()
                    await human_like_delay(2000, 3000)  # Wait for profile to load
                    
                    # Now look for Connect button on the profile page
                    profile_connect_selectors = [
                        'button:has-text("Connect")',
                        'button[aria-label*="Connect"]',
                        '.pvs-profile-actions button:has-text("Connect")',
                        '.pv-s-profile-actions button:has-text("Connect")'
                    ]
                    
                    for selector in profile_connect_selectors:
                        try:
                            connect_button = await self.page.wait_for_selector(selector, timeout=3000)
                            if connect_button:
                                is_visible = await connect_button.is_visible()
                                if is_visible:
                                    print(f"Found Connect button on profile page with selector: {selector}")
                                    await human_like_delay(100, 200)
                                    await connect_button.click()
                                    connect_clicked = True
                                    print("Successfully clicked Connect button on profile page")
                                    break
                        except:
                            continue
                except Exception as e:
                    print(f"Strategy 4 failed: {str(e)}")
            
            if connect_clicked:
                # Connect button clicked, wait for modal
                await human_like_delay(1000, 2000)  # Wait for modal to appear
                print("Connect button clicked, handling modal...")
                
                # Handle the connection modal
                try:
                    # Look for the modal and handle it
                    modal_selectors = [
                        '[data-test-modal-container]',
                        '.artdeco-modal',
                        '.send-invite',
                        '[role="dialog"]'
                    ]
                    
                    modal_found = False
                    for selector in modal_selectors:
                        try:
                            modal = await self.page.wait_for_selector(selector, timeout=3000)
                            if modal:
                                print(f"Found modal with selector: {selector}")
                                modal_found = True
                                break
                        except:
                            continue
                    
                    if modal_found:
                        # Look for Send button in modal
                        send_selectors = [
                            'button:has-text("Send")',
                            'button[aria-label*="Send"]',
                            'button.ml1:has-text("Send")',
                            'button[data-test-modal-primary-action]',
                            'button.artdeco-button--primary:has-text("Send")'
                        ]
                        
                        send_clicked = False
                        for selector in send_selectors:
                            try:
                                send_button = await self.page.wait_for_selector(selector, timeout=3000)
                                if send_button:
                                    print(f"Found Send button with selector: {selector}")
                                    await human_like_delay(100, 200)
                                    await send_button.click()
                                    send_clicked = True
                                    print("Connection request sent successfully")
                                    break
                            except:
                                continue
                        
                        if send_clicked:
                            await human_like_delay(500, 1000)
                            return True, "Connection request sent successfully", profile_url
                        else:
                            return False, "Could not find Send button in modal", profile_url
                    else:
                        print("No modal found, connection might have been sent immediately")
                        return True, "Connection request sent (no modal needed)", profile_url
                        
                except Exception as e:
                    print(f"Error handling modal: {str(e)}")
                    return False, f"Error handling connection modal: {str(e)}", profile_url
            else:
                print("No Connect button found anywhere on page")
            
            if not connect_clicked:
                # Debug: Check what buttons are actually available
                print("Connect button not found. Available buttons:")
                try:
                    all_buttons = await self.page.query_selector_all('button')
                    for i, button in enumerate(all_buttons[:10]):  # Show first 10 buttons
                        text = await button.text_content()
                        aria_label = await button.get_attribute('aria-label')
                        print(f"  {i+1}. Text: '{text}' | Aria-label: '{aria_label}'")
                except:
                    pass
                
                # Check if already connected
                if await self.page.query_selector('button:has-text("Message")'):
                    return False, "Already connected to this person", profile_url
                return False, "Connect button not found - profile may be restricted", profile_url
            
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
        """Clean up browser resources and save session."""
        try:
            # Save session before cleanup if we have a context
            if self.context and self.is_logged_in:
                print("Saving session before cleanup...")
                await self._save_session()
        except Exception as e:
            print(f"Error saving session during cleanup: {e}")
        
        await self._cleanup_browser()