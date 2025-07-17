#!/usr/bin/env python3
"""
FastAPI application for LinkedIn automation.
Provides REST API endpoints for adding LinkedIn connections.
"""

import os
import logging
from typing import Optional
from contextlib import asynccontextmanager

from fastapi import FastAPI, HTTPException, BackgroundTasks
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field
from dotenv import load_dotenv

from linkedin_automation_api import LinkedInAutomationAPI

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

# Global automation instance
automation_instance = None


@asynccontextmanager
async def lifespan(app: FastAPI):
    """Manage automation instance lifecycle."""
    global automation_instance
    try:
        automation_instance = LinkedInAutomationAPI()
        # Don't initialize on startup - do it on first request
        logger.info("LinkedIn automation instance created")
        yield
    finally:
        if automation_instance:
            await automation_instance.cleanup()
            logger.info("LinkedIn automation cleaned up")


app = FastAPI(
    title="LinkedIn Automation API",
    description="API for automating LinkedIn connection requests",
    version="1.0.0",
    lifespan=lifespan
)

# Configure CORS for Next.js frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://localhost:3001"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


# Request/Response models
class ConnectionRequest(BaseModel):
    """Model for connection request."""
    profile_url: Optional[str] = Field(None, description="LinkedIn profile URL")
    name: Optional[str] = Field(None, description="Name to search for")
    message: Optional[str] = Field(None, description="Personalized connection message")
    
    class Config:
        json_schema_extra = {
            "example": {
                "profile_url": "https://www.linkedin.com/in/john-doe/",
                "message": "Hi! I'd like to connect with you on LinkedIn."
            }
        }


class ConnectionResponse(BaseModel):
    """Model for connection response."""
    success: bool
    message: str
    profile_url: Optional[str] = None


class HealthResponse(BaseModel):
    """Model for health check response."""
    status: str
    linkedin_connected: bool


# API Endpoints
@app.get("/health", response_model=HealthResponse)
async def health_check():
    """Check API health and LinkedIn connection status."""
    linkedin_connected = False
    if automation_instance:
        linkedin_connected = automation_instance.is_logged_in
    
    return HealthResponse(
        status="healthy",
        linkedin_connected=linkedin_connected
    )


@app.post("/api/add-connection", response_model=ConnectionResponse)
async def add_connection(request: ConnectionRequest):
    """
    Add a LinkedIn connection.
    
    Either profile_url or name must be provided.
    """
    if not automation_instance:
        raise HTTPException(status_code=503, detail="LinkedIn automation not initialized")
    
    # Initialize browser if not already done
    if not automation_instance.is_logged_in:
        try:
            await automation_instance.initialize()
        except Exception as e:
            logger.error(f"Failed to initialize automation: {str(e)}")
            raise HTTPException(status_code=500, detail=f"Failed to initialize: {str(e)}")
    
    if not request.profile_url and not request.name:
        raise HTTPException(status_code=400, detail="Either profile_url or name must be provided")
    
    try:
        success, result_message, profile_url = await automation_instance.add_connection(
            profile_url=request.profile_url,
            name=request.name,
            message=request.message
        )
        
        return ConnectionResponse(
            success=success,
            message=result_message,
            profile_url=profile_url
        )
    except Exception as e:
        logger.error(f"Error adding connection: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to add connection: {str(e)}")


@app.post("/api/process-business-card")
async def process_business_card(data: dict):
    """
    Process business card data from the Next.js frontend.
    Expected format: {
        "name": "John Doe",
        "company": "Example Corp",
        "title": "Software Engineer",
        "linkedin_url": "optional direct URL"
    }
    """
    if not automation_instance:
        raise HTTPException(status_code=503, detail="LinkedIn automation not initialized")
    
    if not automation_instance.is_logged_in:
        raise HTTPException(status_code=401, detail="Not logged into LinkedIn")
    
    try:
        # Extract data from business card
        name = data.get("name")
        company = data.get("company", "")
        title = data.get("title", "")
        linkedin_url = data.get("linkedin_url")
        
        if not name and not linkedin_url:
            raise HTTPException(status_code=400, detail="Name or LinkedIn URL required")
        
        # Create personalized message
        message = f"Hi {name.split()[0] if name else 'there'}! "
        if company:
            message += f"I came across your profile at {company}. "
        message += "I'd like to connect with you on LinkedIn."
        
        # Add connection
        success, result_message, profile_url = await automation_instance.add_connection(
            profile_url=linkedin_url,
            name=name if not linkedin_url else None,
            message=message
        )
        
        return {
            "success": success,
            "message": result_message,
            "profile_url": profile_url,
            "connection_details": {
                "name": name,
                "company": company,
                "title": title
            }
        }
        
    except Exception as e:
        logger.error(f"Error processing business card: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to process business card: {str(e)}")


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8001)