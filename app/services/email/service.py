from typing import List, Dict, Any, Optional
from pathlib import Path
import os

from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from fastapi_mail.errors import ConnectionErrors
from pydantic import EmailStr

from app.services.email.config import get_email_settings

class EmailService:
    """Service for sending emails using FastAPI-Mail"""
    
    def __init__(self):
        email_settings = get_email_settings()
        self.config = ConnectionConfig(
            MAIL_USERNAME=email_settings.MAIL_USERNAME,
            MAIL_PASSWORD=email_settings.MAIL_PASSWORD,
            MAIL_FROM=email_settings.MAIL_FROM,
            MAIL_PORT=email_settings.MAIL_PORT,
            MAIL_SERVER=email_settings.MAIL_SERVER,
            MAIL_FROM_NAME=email_settings.MAIL_FROM_NAME,
            MAIL_STARTTLS=email_settings.MAIL_STARTTLS,
            MAIL_SSL_TLS=email_settings.MAIL_SSL_TLS,
            USE_CREDENTIALS=email_settings.MAIL_USE_CREDENTIALS,
            VALIDATE_CERTS=email_settings.MAIL_VALIDATE_CERTS,
            TEMPLATE_FOLDER=Path(os.path.join(os.path.dirname(__file__), "templates")),
        )
        self.fastmail = FastMail(self.config)
        self.contact_recipients = email_settings.CONTACT_RECIPIENTS
    
    async def send_email(
        self,
        recipients: List[EmailStr],
        subject: str,
        body: str,
        template_name: Optional[str] = None,
        template_body: Optional[Dict[str, Any]] = None,
        cc: Optional[List[EmailStr]] = None,
        bcc: Optional[List[EmailStr]] = None,
        subtype: MessageType = MessageType.html,
        reply_to: Optional[List[EmailStr]] = None,
    ) -> bool:
        """Send an email with optional template"""
        try:
            recipients_list = [str(r) for r in recipients]
            cc_list = [str(r) for r in cc] if cc else []
            bcc_list = [str(r) for r in bcc] if bcc else []
            reply_to_list = [str(r) for r in reply_to] if reply_to else []
            message = MessageSchema(
                subject=subject,
                recipients=recipients_list,
                body=body if template_name is None else None,
                template_body=template_body,
                cc=cc_list,
                bcc=bcc_list,
                subtype=subtype,
                reply_to=reply_to_list
            )
            
            if template_name:
                await self.fastmail.send_message(message, template_name=template_name)
            else:
                await self.fastmail.send_message(message)
            return True
        except ConnectionErrors as e:
            # In a production environment, you would log this error
            print(f"Failed to send email: {str(e)}")
            return False
    
    async def send_contact_email(
        self,
        name: str,
        email: EmailStr,
        subject: str,
        message: str
    ) -> bool:
        """Send a contact form email to administrators"""
        template_body = {
            "name": name,
            "email": email,
            "subject": subject,
            "message": message
        }
        
        return await self.send_email(
            recipients=self.contact_recipients,
            subject=f"Contact Form: {subject}",
            body="",  # Not used with template
            template_name="contact.html",
            template_body=template_body,
            reply_to=[email]
        )

# Create a singleton instance
email_service = EmailService()