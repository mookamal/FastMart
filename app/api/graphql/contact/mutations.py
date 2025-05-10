import strawberry
from typing import Optional
from pydantic import BaseModel, EmailStr, ValidationError 
from strawberry.types import Info

from app.services.email.service import email_service

def validate_email(email: str) -> EmailStr:
    class EmailModel(BaseModel):
        email_address: EmailStr

    try:
        validated_model = EmailModel(email_address=email)
        return validated_model.email_address
    except ValidationError as e:
        print(f"Validation error: {str(e)}")
        raise ValueError("Invalid email address")

@strawberry.input
class ContactInput:
    """Input type for contact form submissions"""
    name: str
    email: str
    subject: str
    message: str

@strawberry.type
class ContactResult:
    """Result type for contact form submissions"""
    success: bool
    message: str

@strawberry.type
class ContactMutation:
    @strawberry.mutation
    async def contact_us(
        self, 
        info: Info,
        input: ContactInput
    ) -> ContactResult:
        """Submit a contact form that sends an email to administrators"""
        try:
            # Validate the email address
            email = validate_email(input.email)
    
            # Send the contact email
            success = await email_service.send_contact_email(
                name=input.name,
                email=email,
                subject=input.subject,
                message=input.message
            )
            
            if success:
                return ContactResult(
                    success=True,
                    message="Your message has been sent successfully. We'll get back to you soon."
                )
            else:
                return ContactResult(
                    success=False,
                    message="There was a problem sending your message. Please try again later."
                )
                
        except ValueError as e:
            # Handle invalid email format
            print(f"Invalid email format: {str(e)}")
            return ContactResult(
                success=False,
                message="Please provide a valid email address."
            )
        except Exception as e:
            # Handle any other exceptions
            return ContactResult(
                success=False,
                message=f"An unexpected error occurred: {str(e)}"
            )