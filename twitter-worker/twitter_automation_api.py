#!/usr/bin/env python3
"""
Twitter automation API for following users and interacting with tweets.
"""

import os
import json
import logging
import asyncio
from typing import Optional, Tuple, Dict, List
from pathlib import Path
from datetime import datetime

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from playwright.async_api import async_playwright, Browser, BrowserContext, Page
from dotenv import load_dotenv

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Twitter Automation API",
    description="API for automating Twitter interactions",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

class TwitterRequest(BaseModel):
    """Model for Twitter automation request."""
    username: str = Field(..., description="Twitter username (without @)")
    action: str = Field(..., description="Action to perform: 'follow', 'like', 'retweet', 'reply'")
    tweet_url: Optional[str] = Field(None, description="Tweet URL for like/retweet/reply actions")
    message: Optional[str] = Field(None, description="Message for reply action")

class TwitterResponse(BaseModel):
    """Model for Twitter automation response."""
    success: bool
    message: str
    username: str
    action: str
    profile_url: Optional[str] = None

class TwitterAutomationAPI:
    def __init__(self):
        self.browser: Optional[Browser] = None
        self.context: Optional[BrowserContext] = None
        self.page: Optional[Page] = None
        self.session_file = Path("twitter_session.json")
        self.is_initialized = False
        self.is_logged_in = False
        
        # Twitter credentials
        self.email = os.getenv("TWITTER_EMAIL")
        self.password = os.getenv("TWITTER_PASSWORD")
        
        # Create data directory
        Path("data").mkdir(exist_ok=True)
        
        logger.info("Initialized Twitter Automation API")
        if self.email and self.password:
            logger.info(f"Twitter credentials loaded for: {self.email}")
        else:
            logger.warning("Twitter credentials not found in environment variables")
    
    async def _initialize_browser(self) -> None:
        """Initialize browser with session persistence."""
        if self.is_initialized:
            return
            
        try:
            playwright = await async_playwright().start()
            
            # Launch browser in headful mode
            self.browser = await playwright.firefox.launch(
                headless=False,
                slow_mo=100,  # Add slight delay for more human-like behavior
                args=[
                    "--disable-blink-features=AutomationControlled",
                    "--disable-web-security",
                    "--disable-features=VizDisplayCompositor"
                ]
            )
            
            # Create context with session data if it exists
            context_options = {
                "viewport": {"width": 1280, "height": 720},
                "user_agent": "Mozilla/5.0 (Macintosh; Intel Mac OS X 10_15_7) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36"
            }
            
            # Load session if exists
            if self.session_file.exists():
                with open(self.session_file, 'r') as f:
                    session_data = json.load(f)
                    context_options["storage_state"] = session_data
                    logger.info("Loaded existing Twitter session")
            
            self.context = await self.browser.new_context(**context_options)
            self.page = await self.context.new_page()
            
            self.is_initialized = True
            logger.info("Browser initialized successfully")
            
        except Exception as e:
            logger.error(f"Failed to initialize browser: {str(e)}")
            raise
    
    async def _save_session(self) -> None:
        """Save current session state."""
        if self.context:
            try:
                session_data = await self.context.storage_state()
                with open(self.session_file, 'w') as f:
                    json.dump(session_data, f, indent=2)
                logger.info("Session saved successfully")
            except Exception as e:
                logger.error(f"Failed to save session: {str(e)}")
    
    async def _check_login_status(self) -> bool:
        """Check if user is logged into Twitter."""
        try:
            await self.page.goto("https://twitter.com/home", wait_until="networkidle")
            
            # Check if we're on the login page
            current_url = self.page.url
            if "login" in current_url or "signin" in current_url:
                return False
                
            # Check for elements that indicate we're logged in
            try:
                await self.page.wait_for_selector('nav[aria-label="Primary"]', timeout=5000)
                self.is_logged_in = True
                return True
            except:
                self.is_logged_in = False
                return False
                
        except Exception as e:
            logger.error(f"Error checking login status: {str(e)}")
            return False
    
    async def _login(self) -> bool:
        """Log into Twitter."""
        if not self.email or not self.password:
            logger.error("Twitter credentials not provided")
            return False
            
        try:
            logger.info("Attempting to log into Twitter...")
            await self.page.goto("https://twitter.com/login", wait_until="networkidle")
            await asyncio.sleep(2)
            
            # Enter email
            email_selectors = [
                'input[name="text"]',
                'input[autocomplete="username"]',
                'input[type="text"]'
            ]
            
            for selector in email_selectors:
                try:
                    email_input = await self.page.wait_for_selector(selector, timeout=5000)
                    if email_input:
                        await email_input.click()
                        await self._human_like_typing(selector, self.email)
                        await asyncio.sleep(1)
                        
                        # Click Next button
                        next_button = await self.page.wait_for_selector('div[role="button"]:has-text("Next")', timeout=3000)
                        if next_button:
                            await next_button.click()
                            await asyncio.sleep(2)
                        break
                except:
                    continue
            
            # Enter password
            password_selectors = [
                'input[name="password"]',
                'input[type="password"]',
                'input[autocomplete="current-password"]'
            ]
            
            for selector in password_selectors:
                try:
                    password_input = await self.page.wait_for_selector(selector, timeout=5000)
                    if password_input:
                        await password_input.click()
                        await self._human_like_typing(selector, self.password)
                        await asyncio.sleep(1)
                        
                        # Click Log in button
                        login_button = await self.page.wait_for_selector('div[role="button"]:has-text("Log in")', timeout=3000)
                        if login_button:
                            await login_button.click()
                            await asyncio.sleep(3)
                        break
                except:
                    continue
            
            # Check if login was successful
            await asyncio.sleep(3)
            if await self._check_login_status():
                logger.info("Successfully logged into Twitter")
                await self._save_session()
                return True
            else:
                logger.error("Failed to log into Twitter")
                return False
                
        except Exception as e:
            logger.error(f"Error during Twitter login: {str(e)}")
            return False
    
    async def _human_like_typing(self, selector: str, text: str) -> None:
        """Type text with human-like delays."""
        element = await self.page.wait_for_selector(selector)
        await element.click()
        
        # Clear existing text
        await self.page.keyboard.press("Control+a")
        await self.page.keyboard.press("Delete")
        
        # Type character by character with random delays
        for char in text:
            await self.page.keyboard.type(char)
            await asyncio.sleep(0.05 + (0.1 * __import__('random').random()))
    
    async def _follow_user(self, username: str) -> Tuple[bool, str, Optional[str]]:
        """Follow a user on Twitter."""
        try:
            profile_url = f"https://twitter.com/{username}"
            await self.page.goto(profile_url, wait_until="networkidle")
            
            # Wait for page to load
            await asyncio.sleep(2)
            
            # Look for follow button
            follow_selectors = [
                'div[data-testid="follow"]',
                'button[data-testid="follow"]',
                'div[role="button"]:has-text("Follow")',
                'button:has-text("Follow")'
            ]
            
            follow_button = None
            for selector in follow_selectors:
                try:
                    follow_button = await self.page.wait_for_selector(selector, timeout=3000)
                    if follow_button:
                        break
                except:
                    continue
            
            if not follow_button:
                return False, f"Could not find follow button for @{username}", profile_url
            
            # Check if already following
            button_text = await follow_button.inner_text()
            if "Following" in button_text or "Unfollow" in button_text:
                return True, f"Already following @{username}", profile_url
            
            # Click follow button
            await follow_button.click()
            await asyncio.sleep(2)
            
            # Verify follow action
            try:
                await self.page.wait_for_selector('div[data-testid="unfollow"], button[data-testid="unfollow"]', timeout=5000)
                return True, f"Successfully followed @{username}", profile_url
            except:
                return False, f"Follow action may have failed for @{username}", profile_url
                
        except Exception as e:
            logger.error(f"Error following user {username}: {str(e)}")
            return False, f"Error following @{username}: {str(e)}", profile_url
    
    async def _like_tweet(self, tweet_url: str) -> Tuple[bool, str]:
        """Like a tweet."""
        try:
            await self.page.goto(tweet_url, wait_until="networkidle")
            await asyncio.sleep(2)
            
            # Look for like button
            like_selectors = [
                'div[data-testid="like"]',
                'button[data-testid="like"]',
                'div[role="button"][aria-label*="Like"]'
            ]
            
            like_button = None
            for selector in like_selectors:
                try:
                    like_button = await self.page.wait_for_selector(selector, timeout=3000)
                    if like_button:
                        break
                except:
                    continue
            
            if not like_button:
                return False, "Could not find like button"
            
            # Check if already liked
            try:
                unlike_button = await self.page.query_selector('div[data-testid="unlike"]')
                if unlike_button:
                    return True, "Tweet already liked"
            except:
                pass
            
            # Click like button
            await like_button.click()
            await asyncio.sleep(1)
            
            # Verify like action
            try:
                await self.page.wait_for_selector('div[data-testid="unlike"]', timeout=5000)
                return True, "Successfully liked tweet"
            except:
                return False, "Like action may have failed"
                
        except Exception as e:
            logger.error(f"Error liking tweet: {str(e)}")
            return False, f"Error liking tweet: {str(e)}"
    
    async def _retweet_tweet(self, tweet_url: str) -> Tuple[bool, str]:
        """Retweet a tweet."""
        try:
            await self.page.goto(tweet_url, wait_until="networkidle")
            await asyncio.sleep(2)
            
            # Look for retweet button
            retweet_selectors = [
                'div[data-testid="retweet"]',
                'button[data-testid="retweet"]',
                'div[role="button"][aria-label*="Retweet"]'
            ]
            
            retweet_button = None
            for selector in retweet_selectors:
                try:
                    retweet_button = await self.page.wait_for_selector(selector, timeout=3000)
                    if retweet_button:
                        break
                except:
                    continue
            
            if not retweet_button:
                return False, "Could not find retweet button"
            
            # Click retweet button
            await retweet_button.click()
            await asyncio.sleep(1)
            
            # Confirm retweet in popup
            try:
                confirm_button = await self.page.wait_for_selector('div[data-testid="retweetConfirm"]', timeout=3000)
                await confirm_button.click()
                await asyncio.sleep(1)
                return True, "Successfully retweeted"
            except:
                return False, "Could not confirm retweet"
                
        except Exception as e:
            logger.error(f"Error retweeting: {str(e)}")
            return False, f"Error retweeting: {str(e)}"
    
    async def _reply_to_tweet(self, tweet_url: str, message: str) -> Tuple[bool, str]:
        """Reply to a tweet."""
        try:
            await self.page.goto(tweet_url, wait_until="networkidle")
            await asyncio.sleep(2)
            
            # Look for reply button
            reply_selectors = [
                'div[data-testid="reply"]',
                'button[data-testid="reply"]',
                'div[role="button"][aria-label*="Reply"]'
            ]
            
            reply_button = None
            for selector in reply_selectors:
                try:
                    reply_button = await self.page.wait_for_selector(selector, timeout=3000)
                    if reply_button:
                        break
                except:
                    continue
            
            if not reply_button:
                return False, "Could not find reply button"
            
            # Click reply button
            await reply_button.click()
            await asyncio.sleep(2)
            
            # Find tweet compose box
            compose_selectors = [
                'div[data-testid="tweetTextarea_0"]',
                'div[role="textbox"][aria-label*="reply"]',
                'div[contenteditable="true"][aria-label*="reply"]'
            ]
            
            compose_box = None
            for selector in compose_selectors:
                try:
                    compose_box = await self.page.wait_for_selector(selector, timeout=3000)
                    if compose_box:
                        break
                except:
                    continue
            
            if not compose_box:
                return False, "Could not find reply compose box"
            
            # Type the reply
            await compose_box.click()
            await self._human_like_typing('div[data-testid="tweetTextarea_0"]', message)
            await asyncio.sleep(1)
            
            # Send the reply
            try:
                send_button = await self.page.wait_for_selector('div[data-testid="tweetButton"]', timeout=3000)
                await send_button.click()
                await asyncio.sleep(2)
                return True, "Successfully replied to tweet"
            except:
                return False, "Could not send reply"
                
        except Exception as e:
            logger.error(f"Error replying to tweet: {str(e)}")
            return False, f"Error replying to tweet: {str(e)}"
    
    async def execute_action(self, request: TwitterRequest) -> TwitterResponse:
        """Execute a Twitter action."""
        try:
            await self._initialize_browser()
            
            # Check if logged in
            if not await self._check_login_status():
                logger.info("Not logged in, attempting automatic login...")
                if await self._login():
                    logger.info("Login successful, proceeding with action")
                else:
                    return TwitterResponse(
                        success=False,
                        message="Failed to log into Twitter. Please check credentials or log in manually.",
                        username=request.username,
                        action=request.action
                    )
            
            # Execute the requested action
            if request.action == "follow":
                success, message, profile_url = await self._follow_user(request.username)
                await self._save_session()
                return TwitterResponse(
                    success=success,
                    message=message,
                    username=request.username,
                    action=request.action,
                    profile_url=profile_url
                )
            
            elif request.action == "like":
                if not request.tweet_url:
                    return TwitterResponse(
                        success=False,
                        message="Tweet URL is required for like action",
                        username=request.username,
                        action=request.action
                    )
                success, message = await self._like_tweet(request.tweet_url)
                await self._save_session()
                return TwitterResponse(
                    success=success,
                    message=message,
                    username=request.username,
                    action=request.action
                )
            
            elif request.action == "retweet":
                if not request.tweet_url:
                    return TwitterResponse(
                        success=False,
                        message="Tweet URL is required for retweet action",
                        username=request.username,
                        action=request.action
                    )
                success, message = await self._retweet_tweet(request.tweet_url)
                await self._save_session()
                return TwitterResponse(
                    success=success,
                    message=message,
                    username=request.username,
                    action=request.action
                )
            
            elif request.action == "reply":
                if not request.tweet_url or not request.message:
                    return TwitterResponse(
                        success=False,
                        message="Tweet URL and message are required for reply action",
                        username=request.username,
                        action=request.action
                    )
                success, message = await self._reply_to_tweet(request.tweet_url, request.message)
                await self._save_session()
                return TwitterResponse(
                    success=success,
                    message=message,
                    username=request.username,
                    action=request.action
                )
            
            else:
                return TwitterResponse(
                    success=False,
                    message=f"Unknown action: {request.action}",
                    username=request.username,
                    action=request.action
                )
                
        except Exception as e:
            logger.error(f"Error executing Twitter action: {str(e)}")
            return TwitterResponse(
                success=False,
                message=f"Error executing action: {str(e)}",
                username=request.username,
                action=request.action
            )
    
    async def close(self):
        """Close browser resources."""
        if self.browser:
            await self.browser.close()
            self.is_initialized = False

# Initialize Twitter automation
twitter_automation = TwitterAutomationAPI()

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "twitter-worker",
        "session_exists": twitter_automation.session_file.exists()
    }

@app.post("/api/follow", response_model=TwitterResponse)
async def follow_user(data: dict):
    """Follow a Twitter user."""
    username = data.get("username")
    if not username:
        raise HTTPException(status_code=400, detail="Username is required")
    
    request = TwitterRequest(username=username, action="follow")
    return await twitter_automation.execute_action(request)

@app.post("/api/like", response_model=TwitterResponse)
async def like_tweet(data: dict):
    """Like a tweet."""
    tweet_url = data.get("tweet_url")
    if not tweet_url:
        raise HTTPException(status_code=400, detail="Tweet URL is required")
    
    request = TwitterRequest(username="", action="like", tweet_url=tweet_url)
    return await twitter_automation.execute_action(request)

@app.post("/api/retweet", response_model=TwitterResponse)
async def retweet_tweet(data: dict):
    """Retweet a tweet."""
    tweet_url = data.get("tweet_url")
    if not tweet_url:
        raise HTTPException(status_code=400, detail="Tweet URL is required")
    
    request = TwitterRequest(username="", action="retweet", tweet_url=tweet_url)
    return await twitter_automation.execute_action(request)

@app.post("/api/reply", response_model=TwitterResponse)
async def reply_to_tweet(data: dict):
    """Reply to a tweet."""
    tweet_url = data.get("tweet_url")
    message = data.get("message")
    
    if not tweet_url or not message:
        raise HTTPException(status_code=400, detail="Tweet URL and message are required")
    
    request = TwitterRequest(username="", action="reply", tweet_url=tweet_url, message=message)
    return await twitter_automation.execute_action(request)

@app.post("/api/execute", response_model=TwitterResponse)
async def execute_twitter_action(request: TwitterRequest):
    """Execute any Twitter action."""
    return await twitter_automation.execute_action(request)

@app.on_event("shutdown")
async def shutdown_event():
    """Clean up resources on shutdown."""
    await twitter_automation.close()

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8003)