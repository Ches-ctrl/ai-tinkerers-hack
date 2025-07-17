#!/usr/bin/env python3
"""
Orchestrator API for receiving contact data from iPhone Shortcuts app.
Saves contact information and optionally triggers LinkedIn connection requests.
"""

import os
import json
import logging
from datetime import datetime
from typing import List, Optional
from pathlib import Path

from fastapi import FastAPI, HTTPException, BackgroundTasks, Request
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, validator
import httpx
import aiofiles

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Create data directory if it doesn't exist
DATA_DIR = Path("data")
DATA_DIR.mkdir(exist_ok=True)

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

    @validator('phone_numbers', pre=True)
    def parse_phone_numbers(cls, v):
        if isinstance(v, str):
            return [v] if v.strip() else []
        return v or []

    @validator('emails', pre=True)
    def parse_emails(cls, v):
        if isinstance(v, str):
            return [v] if v.strip() else []
        return v or []

    @validator('urls', pre=True)
    def parse_urls(cls, v):
        if isinstance(v, str):
            return [v] if v.strip() else []
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


async def save_contact_to_file(contact: ContactData, contact_id: str) -> str:
    """Save contact data to a JSON file."""
    filename = DATA_DIR / f"contact_{contact_id}.json"

    contact_dict = contact.dict()
    contact_dict["id"] = contact_id
    contact_dict["timestamp"] = datetime.now().isoformat()

    async with aiofiles.open(filename, 'w') as f:
        await f.write(json.dumps(contact_dict, indent=2))

    return str(filename)


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

        # Save contact to file
        filename = await save_contact_to_file(contact, contact_id)
        logger.info(f"Saved contact {contact_id} to {filename}")

        # Check if we should trigger LinkedIn connection
        linkedin_status = "No LinkedIn action taken"
        if contact.urls and any("linkedin.com" in url.lower() for url in contact.urls):
            # Trigger LinkedIn connection in background
            linkedin_result = await trigger_linkedin_connection(contact, contact_id)
            if linkedin_result.get("success"):
                linkedin_status = "LinkedIn connection request sent"
            else:
                linkedin_status = f"LinkedIn failed: {linkedin_result.get('message', 'Unknown error')}"

        return ContactResponse(
            success=True,
            message=f"Contact saved successfully",
            contact_id=contact_id,
            linkedin_status=linkedin_status
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

        return {
            "count": len(contacts),
            "contacts": contacts
        }
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


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
