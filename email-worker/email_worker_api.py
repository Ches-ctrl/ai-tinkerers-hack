#!/usr/bin/env python3
"""
Email worker API for sending emails via SMTP (Gmail).
"""

import os
import logging
from typing import Optional
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.base import MIMEBase
from email import encoders
import aiosmtplib
import asyncio
from pathlib import Path

from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel, Field, EmailStr
from dotenv import load_dotenv

load_dotenv()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = FastAPI(
    title="Email Worker API",
    description="API for sending emails via SMTP",
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

# Email configuration
GMAIL_EMAIL = os.getenv("GMAIL_EMAIL")
GMAIL_APP_PASSWORD = os.getenv("GMAIL_APP_PASSWORD", "gphu nqks mhvd stql")
SMTP_SERVER = os.getenv("SMTP_SERVER", "smtp.gmail.com")
SMTP_PORT = int(os.getenv("SMTP_PORT", "587"))

class EmailRequest(BaseModel):
    """Model for email request."""
    to_email: EmailStr = Field(..., description="Recipient email address")
    subject: str = Field(..., description="Email subject")
    body: str = Field(..., description="Email body (HTML or plain text)")
    from_name: Optional[str] = Field(None, description="Sender name")
    is_html: bool = Field(True, description="Whether body is HTML")
    attachment_path: Optional[str] = Field(None, description="Path to attachment file")

class EmailResponse(BaseModel):
    """Model for email response."""
    success: bool
    message: str
    to_email: str

class EmailWorkerAPI:
    def __init__(self):
        self.smtp_server = SMTP_SERVER
        self.smtp_port = SMTP_PORT
        self.gmail_email = GMAIL_EMAIL
        self.gmail_password = GMAIL_APP_PASSWORD.replace(" ", "")  # Remove spaces
        
        if not self.gmail_email or not self.gmail_password:
            raise ValueError("Gmail email and app password must be set in environment variables")
        
        logger.info(f"Initialized Email Worker with Gmail: {self.gmail_email}")
    
    async def send_email(self, request: EmailRequest) -> EmailResponse:
        """Send an email via SMTP."""
        try:
            # Create message
            msg = MIMEMultipart()
            msg['From'] = f"{request.from_name or 'Networking Bot'} <{self.gmail_email}>"
            msg['To'] = request.to_email
            msg['Subject'] = request.subject
            
            # Add body
            if request.is_html:
                body_part = MIMEText(request.body, 'html')
            else:
                body_part = MIMEText(request.body, 'plain')
            msg.attach(body_part)
            
            # Add attachment if provided
            if request.attachment_path and os.path.exists(request.attachment_path):
                with open(request.attachment_path, "rb") as attachment:
                    part = MIMEBase('application', 'octet-stream')
                    part.set_payload(attachment.read())
                
                encoders.encode_base64(part)
                part.add_header(
                    'Content-Disposition',
                    f'attachment; filename= {os.path.basename(request.attachment_path)}'
                )
                msg.attach(part)
                logger.info(f"Added attachment: {request.attachment_path}")
            
            # Send email
            await aiosmtplib.send(
                msg,
                hostname=self.smtp_server,
                port=self.smtp_port,
                start_tls=True,
                username=self.gmail_email,
                password=self.gmail_password,
            )
            
            logger.info(f"Email sent successfully to {request.to_email}")
            return EmailResponse(
                success=True,
                message=f"Email sent successfully to {request.to_email}",
                to_email=request.to_email
            )
            
        except Exception as e:
            logger.error(f"Failed to send email to {request.to_email}: {str(e)}")
            return EmailResponse(
                success=False,
                message=f"Failed to send email: {str(e)}",
                to_email=request.to_email
            )

# Initialize email worker
email_worker = EmailWorkerAPI()

@app.get("/health")
async def health_check():
    """Health check endpoint."""
    return {
        "status": "healthy",
        "service": "email-worker",
        "smtp_server": SMTP_SERVER,
        "smtp_port": SMTP_PORT
    }

@app.post("/api/send-email", response_model=EmailResponse)
async def send_email_endpoint(request: EmailRequest):
    """Send an email."""
    return await email_worker.send_email(request)

@app.post("/api/send-networking-email")
async def send_networking_email(data: dict):
    """
    Send a networking email to a contact.
    Expected format: {
        "first_name": "John",
        "last_name": "Doe",
        "email": "john.doe@example.com",
        "company": "Example Corp",
        "title": "Software Engineer",
        "photo_path": "optional path to photo"
    }
    """
    try:
        first_name = data.get("first_name", "")
        last_name = data.get("last_name", "")
        email = data.get("email")
        company = data.get("company", "")
        title = data.get("title", "")
        photo_path = data.get("photo_path")
        
        if not email:
            raise HTTPException(status_code=400, detail="Email address is required")
        
        # Create personalized email
        full_name = f"{first_name} {last_name}".strip()
        
        subject = f"Great meeting you{f', {first_name}' if first_name else ''}!"
        
        # Create HTML email body
        body = f"""
        <html>
        <body>
        <p>Hi {first_name or 'there'},</p>
        
        <p>It was great meeting you{f' at {company}' if company else ''}! 
        {f'Your work as {title} sounds really interesting.' if title else ''}</p>
        
        <p>I wanted to reach out and stay connected. Feel free to reach out if you'd like to grab coffee or discuss potential collaborations.</p>
        
        <p>Best regards,<br>
        Your new connection</p>
        </body>
        </html>
        """
        
        # Send email
        email_request = EmailRequest(
            to_email=email,
            subject=subject,
            body=body,
            from_name="Networking Bot",
            is_html=True,
            attachment_path=photo_path
        )
        
        result = await email_worker.send_email(email_request)
        
        return {
            "success": result.success,
            "message": result.message,
            "email_sent_to": email,
            "contact_details": {
                "name": full_name,
                "company": company,
                "title": title
            }
        }
        
    except Exception as e:
        logger.error(f"Error processing networking email: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Failed to send networking email: {str(e)}")

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8002)