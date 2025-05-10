# Contact Form GraphQL Module

This module provides a GraphQL mutation for handling contact form submissions using the `fastapi-mail` package.

## Setup

1. Add the following environment variables to your `.env` file:

```
MAIL_USERNAME=your_email@example.com
MAIL_PASSWORD=your_email_password
MAIL_FROM=noreply@example.com
MAIL_FROM_NAME=Your Project Name
MAIL_SERVER=smtp.example.com
MAIL_PORT=587
MAIL_TLS=True
MAIL_SSL=False
CONTACT_RECIPIENTS=admin1@example.com,admin2@example.com
```

2. Install the required package:

```bash
pip install fastapi-mail==1.4.1
```

## Usage

Use the following GraphQL mutation in your frontend:

```graphql
mutation ContactUs($input: ContactInput!) {
  contactUs(input: $input) {
    success
    message
  }
}
```

With variables:

```json
{
  "input": {
    "name": "John Doe",
    "email": "john@example.com",
    "subject": "Question about your service",
    "message": "Hello, I have a question about..."
  }
}
```

## Response

The mutation returns a `ContactResult` with:

- `success`: Boolean indicating if the email was sent successfully
- `message`: A user-friendly message about the result

## Implementation Details

This module is part of a larger email service that can be extended for other email features. The implementation follows a modular approach with:

- Reusable email service in `app/services/email/`
- HTML email templates in `app/services/email/templates/`
- Configuration settings in `app/services/email/config.py`