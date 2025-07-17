#!/usr/bin/env python3
"""
Orchestrator API for receiving contact data from iPhone Shortcuts app.
Saves contact information and optionally triggers LinkedIn connection requests.
"""

import os
import json
import logging
from datetime import datetime, timedelta
from typing import List, Optional
from pathlib import Path
import asyncio
import base64
import uuid

from fastapi import FastAPI, HTTPException, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from pydantic import BaseModel, Field, field_validator
import httpx
import aiofiles

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create data directory if it doesn't exist
DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

# Create media directory for audio and photo files
MEDIA_DIR = DATA_DIR / "media"
MEDIA_DIR.mkdir(exist_ok=True)

# Rate limiting for WhatsApp messages
last_whatsapp_send_time = None
WHATSAPP_RATE_LIMIT_SECONDS = 2  # Don't send more than 1 message every 2 seconds

app = FastAPI(
    title="Contact Orchestrator API",
    description="Receives contact data from iPhone Shortcuts and orchestrates LinkedIn connections",
    version="1.0.0"
)

# Configure CORS
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],  # Allow all origins for ngrok
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Data models
class ContactData(BaseModel):
    """Model for contact information from Shortcuts app."""
    first_name: Optional[str] = Field(None, description="Contact's first name")
    last_name: Optional[str] = Field(None, description="Contact's last name")
    phone_numbers: List[str] = Field(default_factory=list, description="List of phone numbers")
    emails: List[str] = Field(default_factory=list, description="List of email addresses")
    urls: List[str] = Field(default_factory=list, description="List of URLs (LinkedIn, website, etc.)")
    audio: Optional[str] = Field(None, description="Base64 encoded audio file")
    photo: Optional[str] = Field(None, description="Base64 encoded photo file")

    @field_validator('phone_numbers', mode='before')
    @classmethod
    def parse_phone_numbers(cls, v):
        if isinstance(v, str):
            if not v.strip():
                return []
            # Split by newlines and commas, then clean each number
            numbers = []
            # Split by newlines first, then by commas
            for line in v.split('\n'):
                for num in line.split(','):
                    cleaned = num.strip()
                    if cleaned:
                        numbers.append(cleaned)
            return numbers
        return v or []

    @field_validator('emails', mode='before')
    @classmethod
    def parse_emails(cls, v):
        if isinstance(v, str):
            if not v.strip():
                return []
            # Split by newlines and commas, then clean each email
            emails = []
            # Split by newlines first, then by commas
            for line in v.split('\n'):
                for email in line.split(','):
                    cleaned = email.strip()
                    if cleaned:
                        emails.append(cleaned)
            return emails
        return v or []

    @field_validator('urls', mode='before')
    @classmethod
    def parse_urls(cls, v):
        if isinstance(v, str):
            if not v.strip():
                return []
            # Split by newlines and commas, then clean each URL
            urls = []
            # Split by newlines first, then by commas
            for line in v.split('\n'):
                for url in line.split(','):
                    cleaned = url.strip()
                    if cleaned:
                        urls.append(cleaned)
            return urls
        return v or []

    class Config:
        json_schema_extra = {
            "example": {
                "first_name": "John",
                "last_name": "Doe",
                "phone_numbers": ["+1234567890"],
                "emails": ["john.doe@example.com"],
                "urls": ["https://www.linkedin.com/in/johndoe/"]
            }
        }


class ContactResponse(BaseModel):
    """Response model for contact submission."""
    success: bool
    message: str
    contact_id: str
    linkedin_status: Optional[str] = None


# Helper functions
def generate_contact_id() -> str:
    """Generate a unique contact ID based on timestamp."""
    return datetime.now().strftime("%Y%m%d_%H%M%S_%f")[:-3]


async def save_media_file(base64_data: str, file_type: str, contact_id: str) -> Optional[str]:
    """Save base64 encoded media file to disk."""
    if not base64_data or not base64_data.strip():
        return None
    
    try:
        # Clean the base64 data by removing whitespace and newlines
        clean_base64_data = ''.join(base64_data.split())
        
        # Validate base64 data
        if len(clean_base64_data) < 10:  # Too short to be valid media
            logger.warning(f"{file_type} data too short ({len(clean_base64_data)} chars), skipping")
            return None
        
        # Check if it looks like base64 (basic validation)
        # Valid base64 characters: A-Z, a-z, 0-9, +, /, =
        valid_base64_chars = set('ABCDEFGHIJKLMNOPQRSTUVWXYZabcdefghijklmnopqrstuvwxyz0123456789+/=')
        if not all(c in valid_base64_chars for c in clean_base64_data):
            logger.warning(f"{file_type} data contains invalid base64 characters, skipping")
            return None
        
        # Decode base64 data
        media_data = base64.b64decode(clean_base64_data, validate=True)
        
        # Basic size check
        if len(media_data) < 100:  # Too small to be valid media
            logger.warning(f"{file_type} decoded data too small ({len(media_data)} bytes), skipping")
            return None
        
        # Generate filename
        if file_type == "audio":
            extension = "m4a"  # Common format from iOS
        elif file_type == "photo":
            extension = "jpg"  # Common format from iOS
        else:
            extension = "bin"
        
        filename = f"{contact_id}_{file_type}_{uuid.uuid4().hex[:8]}.{extension}"
        filepath = MEDIA_DIR / filename
        
        # Write file
        async with aiofiles.open(filepath, 'wb') as f:
            await f.write(media_data)
        
        logger.info(f"Saved {file_type} file: {filepath} ({len(media_data)} bytes)")
        return str(filepath)
        
    except Exception as e:
        logger.error(f"Error saving {file_type} file: {str(e)}")
        return None


async def send_whatsapp_message_with_photo(contact: ContactData, contact_id: str, photo_path: Optional[str] = None) -> dict:
    """Send WhatsApp message with photo via the WhatsApp bridge API."""
    whatsapp_api_url = os.getenv("WHATSAPP_API_URL", "http://localhost:8080")
    
    if not contact.phone_numbers:
        return {"success": False, "message": "No phone numbers available"}
    
    # Create personalized message
    name_parts = [contact.first_name, contact.last_name]
    full_name = " ".join(part for part in name_parts if part)
    
    message = f"Hi {contact.first_name or 'there'}! "
    message += f"Great meeting you{f' {contact.first_name}' if contact.first_name else ''}. "
    message += "Thanks for sharing your contact info. Looking forward to staying in touch!"
    
    # Try each phone number until one succeeds
    for i, phone_number in enumerate(contact.phone_numbers):
        if not phone_number.strip():
            continue
            
        logger.info(f"Trying phone number {i+1}/{len(contact.phone_numbers)}: {phone_number}")
        
        result = await try_send_whatsapp_to_number_with_photo(phone_number, message, photo_path, whatsapp_api_url)
        
        if result.get("success"):
            return {
                "success": True,
                "message": f"WhatsApp message sent to {clean_phone_number(phone_number)} (number {i+1})",
                "phone_number_used": clean_phone_number(phone_number)
            }
        else:
            logger.warning(f"Failed to send to {phone_number}: {result.get('message', 'Unknown error')}")
    
    return {
        "success": False,
        "message": f"Failed to send WhatsApp message to all {len(contact.phone_numbers)} phone numbers"
    }


async def try_send_whatsapp_to_number_with_photo(phone_number: str, message: str, photo_path: Optional[str], whatsapp_api_url: str) -> dict:
    """Try to send WhatsApp message with photo to a specific number."""
    cleaned_number = clean_phone_number(phone_number)
    
    # Enforce global rate limit
    await enforce_whatsapp_rate_limit()
    
    async with httpx.AsyncClient() as client:
        try:
            # Prepare the request payload
            request_data = {
                "recipient": cleaned_number,
                "message": message
            }
            
            # If we have a photo, add the media_path (WhatsApp bridge expects file path)
            if photo_path and os.path.exists(photo_path):
                # Convert to absolute path for WhatsApp bridge
                abs_photo_path = os.path.abspath(photo_path)
                request_data["media_path"] = abs_photo_path
                logger.info(f"Sending WhatsApp message with photo to {cleaned_number}: {abs_photo_path}")
            else:
                logger.info(f"Sending text-only WhatsApp message to {cleaned_number}")
            
            response = await client.post(
                f"{whatsapp_api_url}/api/send",
                json=request_data,
                timeout=30.0
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get("success"):
                    logger.info(f"WhatsApp message sent to {cleaned_number}: {result}")
                    return result
                else:
                    logger.warning(f"WhatsApp API returned failure for {cleaned_number}: {result}")
                    return result
            else:
                logger.error(f"WhatsApp API error for {cleaned_number}: {response.status_code} - {response.text}")
                return {"success": False, "message": f"WhatsApp API error: {response.status_code}"}
                
        except httpx.ConnectError:
            logger.warning("WhatsApp bridge API not available")
            return {"success": False, "message": "WhatsApp bridge not available"}
        except Exception as e:
            logger.error(f"Error connecting to WhatsApp API for {cleaned_number}: {str(e)}")
            return {"success": False, "message": str(e)}


async def save_contact_to_file(contact: ContactData, contact_id: str) -> tuple[str, Optional[str], Optional[str]]:
    """Save contact data to a JSON file and handle media files."""
    filename = DATA_DIR / f"contact_{contact_id}.json"

    # Save audio and photo files if present
    audio_path = None
    photo_path = None
    
    if contact.audio:
        audio_path = await save_media_file(contact.audio, "audio", contact_id)
    
    if contact.photo:
        photo_path = await save_media_file(contact.photo, "photo", contact_id)

    contact_dict = contact.dict()
    contact_dict["id"] = contact_id
    contact_dict["timestamp"] = datetime.now().isoformat()
    
    # Add file paths to contact data, remove base64 data
    contact_dict["audio_file"] = audio_path
    contact_dict["photo_file"] = photo_path
    # Remove base64 data from JSON (too large)
    contact_dict.pop("audio", None)
    contact_dict.pop("photo", None)

    async with aiofiles.open(filename, 'w') as f:
        await f.write(json.dumps(contact_dict, indent=2))

    return str(filename), audio_path, photo_path


def clean_phone_number(phone_number: str) -> str:
    """Clean and normalize phone number for WhatsApp."""
    # Remove spaces, dashes, parentheses, dots
    cleaned = phone_number.replace(" ", "").replace("-", "").replace("(", "").replace(")", "").replace(".", "")
    # Remove + if present, WhatsApp bridge expects raw number
    if cleaned.startswith("+"):
        cleaned = cleaned[1:]
    return cleaned


async def enforce_whatsapp_rate_limit():
    """Enforce global WhatsApp rate limit of 1 message every 2 seconds."""
    global last_whatsapp_send_time
    now = datetime.now()
    
    if last_whatsapp_send_time is not None:
        time_since_last = now - last_whatsapp_send_time
        if time_since_last < timedelta(seconds=WHATSAPP_RATE_LIMIT_SECONDS):
            wait_time = WHATSAPP_RATE_LIMIT_SECONDS - time_since_last.total_seconds()
            logger.info(f"Rate limiting: waiting {wait_time:.1f} seconds before sending WhatsApp message")
            await asyncio.sleep(wait_time)
    
    last_whatsapp_send_time = datetime.now()


async def try_send_whatsapp_to_number(phone_number: str, message: str, whatsapp_api_url: str) -> dict:
    """Try to send WhatsApp message to a specific number."""
    cleaned_number = clean_phone_number(phone_number)
    
    # Enforce global rate limit
    await enforce_whatsapp_rate_limit()
    
    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{whatsapp_api_url}/api/send",
                json={
                    "recipient": cleaned_number,
                    "message": message
                },
                timeout=30.0
            )
            
            if response.status_code == 200:
                result = response.json()
                if result.get("success"):
                    logger.info(f"WhatsApp message sent to {cleaned_number}: {result}")
                    return result
                else:
                    logger.warning(f"WhatsApp API returned failure for {cleaned_number}: {result}")
                    return result
            else:
                logger.error(f"WhatsApp API error for {cleaned_number}: {response.status_code} - {response.text}")
                return {"success": False, "message": f"WhatsApp API error: {response.status_code}"}
                
        except httpx.ConnectError:
            logger.warning("WhatsApp bridge API not available")
            return {"success": False, "message": "WhatsApp bridge not available"}
        except Exception as e:
            logger.error(f"Error connecting to WhatsApp API for {cleaned_number}: {str(e)}")
            return {"success": False, "message": str(e)}


async def send_whatsapp_message(contact: ContactData, contact_id: str) -> dict:
    """Send WhatsApp message via the WhatsApp bridge API with fallback to multiple numbers."""
    whatsapp_api_url = os.getenv("WHATSAPP_API_URL", "http://localhost:8080")
    
    if not contact.phone_numbers:
        return {"success": False, "message": "No phone numbers available"}
    
    # Create personalized message
    name_parts = [contact.first_name, contact.last_name]
    full_name = " ".join(part for part in name_parts if part)
    
    message = f"Hi {contact.first_name or 'there'}! "
    message += f"Great meeting you{f' {contact.first_name}' if contact.first_name else ''}. "
    message += "Thanks for sharing your contact info. Looking forward to staying in touch!"
    
    # Try each phone number until one succeeds
    for i, phone_number in enumerate(contact.phone_numbers):
        if not phone_number.strip():
            continue
            
        logger.info(f"Trying phone number {i+1}/{len(contact.phone_numbers)}: {phone_number}")
        
        result = await try_send_whatsapp_to_number(phone_number, message, whatsapp_api_url)
        
        if result.get("success"):
            return {
                "success": True,
                "message": f"WhatsApp message sent to {clean_phone_number(phone_number)} (number {i+1})",
                "phone_number_used": clean_phone_number(phone_number)
            }
        else:
            logger.warning(f"Failed to send to {phone_number}: {result.get('message', 'Unknown error')}")
            # Rate limit is already enforced in try_send_whatsapp_to_number
    
    return {
        "success": False,
        "message": f"Failed to send WhatsApp message to all {len(contact.phone_numbers)} phone numbers"
    }


async def trigger_linkedin_connection(contact: ContactData, contact_id: str) -> dict:
    """Trigger LinkedIn connection via the LinkedIn worker API."""
    linkedin_api_url = os.getenv("LINKEDIN_API_URL", "http://localhost:8001")

    # Look for LinkedIn URL in the urls list
    linkedin_url = None
    for url in contact.urls:
        if "linkedin.com" in url.lower():
            linkedin_url = url
            break

    # Prepare the request
    name_parts = [contact.first_name, contact.last_name]
    full_name = " ".join(part for part in name_parts if part)

    async with httpx.AsyncClient() as client:
        try:
            response = await client.post(
                f"{linkedin_api_url}/api/add-connection",
                json={
                    "profile_url": linkedin_url,
                    "name": full_name if not linkedin_url and full_name else None,
                    "message": f"Hi {contact.first_name or 'there'}! Great meeting you. I'd like to connect on LinkedIn."
                },
                timeout=30.0
            )

            if response.status_code == 200:
                return response.json()
            else:
                logger.error(f"LinkedIn API error: {response.status_code} - {response.text}")
                return {"success": False, "message": f"LinkedIn API error: {response.status_code}"}

        except httpx.ConnectError:
            logger.warning("LinkedIn worker API not available")
            return {"success": False, "message": "LinkedIn worker not available"}
        except Exception as e:
            logger.error(f"Error connecting to LinkedIn API: {str(e)}")
            return {"success": False, "message": str(e)}


# API Endpoints
@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "orchestrator",
        "data_directory": str(DATA_DIR.absolute())
    }


@app.post("/api/debug-raw")
async def debug_raw_request(request: Request):
    """
    Accept any raw request and save it for debugging.
    """
    try:
        body = await request.body()
        body_str = body.decode('utf-8')
        
        # Get headers for debugging
        headers = dict(request.headers)
        
        # Save raw request to debug file
        debug_filename = DATA_DIR / f"debug_raw_{generate_contact_id()}.json"
        debug_data = {
            "method": request.method,
            "url": str(request.url),
            "headers": headers,
            "raw_body": body_str,
            "content_type": headers.get("content-type", "unknown")
        }
        
        async with aiofiles.open(debug_filename, 'w') as f:
            await f.write(json.dumps(debug_data, indent=2))
        
        logger.info(f"Debug raw request saved to: {debug_filename}")
        logger.info(f"Content-Type: {headers.get('content-type', 'unknown')}")
        logger.info(f"Raw request body: {body_str}")
        
        return {
            "success": True,
            "message": "Debug request saved",
            "raw_body": body_str,
            "content_type": headers.get("content-type", "unknown"),
            "saved_to": str(debug_filename)
        }
    except Exception as e:
        logger.error(f"Error processing debug request: {str(e)}")
        return {"success": False, "error": str(e)}


@app.post("/api/contact-debug")
async def debug_contact_request(request: Request):
    """
    Debug endpoint to capture raw request body for troubleshooting.
    """
    try:
        body = await request.body()
        body_str = body.decode('utf-8')

        # Save raw request to debug file
        debug_filename = DATA_DIR / f"debug_request_{generate_contact_id()}.json"
        async with aiofiles.open(debug_filename, 'w') as f:
            await f.write(body_str)

        logger.info(f"Debug request saved to: {debug_filename}")
        logger.info(f"Raw request body: {body_str}")

        return {
            "success": True,
            "message": "Debug request saved",
            "raw_body": body_str,
            "saved_to": str(debug_filename)
        }
    except Exception as e:
        logger.error(f"Error processing debug request: {str(e)}")
        return {"success": False, "error": str(e)}


@app.post("/api/contact", response_model=ContactResponse)
async def receive_contact(contact: ContactData, background_tasks: BackgroundTasks):
    """
    Receive contact data from iPhone Shortcuts app.
    Saves the data to a JSON file and optionally triggers LinkedIn connection.
    """
    try:
        # Log the incoming request for debugging
        logger.info(f"Received contact data: {contact.dict()}")

        # Generate unique ID for this contact
        contact_id = generate_contact_id()

        # Save contact to file and get media file paths
        filename, audio_path, photo_path = await save_contact_to_file(contact, contact_id)
        logger.info(f"Saved contact {contact_id} to {filename}")
        
        if audio_path:
            logger.info(f"Saved audio file: {audio_path}")
        if photo_path:
            logger.info(f"Saved photo file: {photo_path}")

        # Send WhatsApp message if phone number is available
        whatsapp_status = "No WhatsApp action taken"
        if contact.phone_numbers:
            # Use the new function that supports photo sending
            whatsapp_result = await send_whatsapp_message_with_photo(contact, contact_id, photo_path)
            if whatsapp_result.get("success"):
                whatsapp_status = "WhatsApp message sent successfully"
                if photo_path:
                    whatsapp_status += " (with photo)"
            else:
                whatsapp_status = f"WhatsApp failed: {whatsapp_result.get('message', 'Unknown error')}"

        # Check if we should trigger LinkedIn connection
        linkedin_status = "No LinkedIn action taken"
        
        # Try LinkedIn connection if we have name or LinkedIn URL
        should_try_linkedin = False
        full_name = " ".join(part for part in [contact.first_name, contact.last_name] if part)
        
        if contact.urls and any("linkedin.com" in url.lower() for url in contact.urls):
            should_try_linkedin = True
        elif full_name:  # If we have a name, we can try searching
            should_try_linkedin = True
        
        if should_try_linkedin:
            # Trigger LinkedIn connection
            linkedin_result = await trigger_linkedin_connection(contact, contact_id)
            if linkedin_result.get("success"):
                linkedin_status = "LinkedIn connection request sent"
            else:
                linkedin_status = f"LinkedIn failed: {linkedin_result.get('message', 'Unknown error')}"

        return ContactResponse(
            success=True,
            message=f"Contact saved successfully",
            contact_id=contact_id,
            linkedin_status=f"{whatsapp_status} | {linkedin_status}"
        )

    except Exception as e:
        logger.error(f"Error processing contact: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/contacts")
async def list_contacts():
    """List all saved contacts."""
    try:
        contacts = []
        for file in DATA_DIR.glob("contact_*.json"):
            async with aiofiles.open(file, 'r') as f:
                content = await f.read()
                contacts.append(json.loads(content))

        # Sort by timestamp (newest first)
        contacts.sort(key=lambda x: x.get("timestamp", ""), reverse=True)

        return contacts
    except Exception as e:
        logger.error(f"Error listing contacts: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/contact/{contact_id}")
async def get_contact(contact_id: str):
    """Get a specific contact by ID."""
    filename = DATA_DIR / f"contact_{contact_id}.json"

    if not filename.exists():
        raise HTTPException(status_code=404, detail="Contact not found")

    try:
        async with aiofiles.open(filename, 'r') as f:
            content = await f.read()
            return json.loads(content)
    except Exception as e:
        logger.error(f"Error reading contact: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.post("/api/trigger-linkedin/{contact_id}")
async def manually_trigger_linkedin(contact_id: str):
    """Manually trigger LinkedIn connection for a saved contact."""
    filename = DATA_DIR / f"contact_{contact_id}.json"

    if not filename.exists():
        raise HTTPException(status_code=404, detail="Contact not found")

    try:
        async with aiofiles.open(filename, 'r') as f:
            content = await f.read()
            contact_data = json.loads(content)

        # Convert back to ContactData model
        contact = ContactData(
            first_name=contact_data["first_name"],
            last_name=contact_data["last_name"],
            phone_numbers=contact_data.get("phone_numbers", []),
            emails=contact_data.get("emails", []),
            urls=contact_data.get("urls", [])
        )

        # Trigger LinkedIn connection
        result = await trigger_linkedin_connection(contact, contact_id)

        return result

    except Exception as e:
        logger.error(f"Error triggering LinkedIn: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


@app.get("/api/media/{filename}")
async def serve_media(filename: str):
    """Serve media files (photos, audio) from the media directory."""
    try:
        media_path = MEDIA_DIR / filename
        
        if not media_path.exists():
            raise HTTPException(status_code=404, detail="Media file not found")
        
        # Check if it's a safe file type
        allowed_extensions = {'.jpg', '.jpeg', '.png', '.gif', '.mp3', '.wav', '.m4a', '.ogg'}
        file_ext = media_path.suffix.lower()
        
        if file_ext not in allowed_extensions:
            raise HTTPException(status_code=400, detail="File type not allowed")
        
        # Determine media type
        if file_ext in {'.jpg', '.jpeg'}:
            media_type = "image/jpeg"
        elif file_ext == '.png':
            media_type = "image/png"
        elif file_ext == '.gif':
            media_type = "image/gif"
        elif file_ext == '.mp3':
            media_type = "audio/mpeg"
        elif file_ext == '.wav':
            media_type = "audio/wav"
        elif file_ext == '.m4a':
            media_type = "audio/mp4"
        elif file_ext == '.ogg':
            media_type = "audio/ogg"
        else:
            media_type = "application/octet-stream"
        
        return FileResponse(
            path=str(media_path),
            media_type=media_type,
            filename=filename
        )
        
    except Exception as e:
        logger.error(f"Error serving media file {filename}: {str(e)}")
        raise HTTPException(status_code=500, detail=str(e))


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
