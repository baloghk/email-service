# Email Microservice

A lightweight, asynchronous microservice for sending templated emails using **Python**, **FastAPI**, and **SMTP**. Containerized with **Docker** for easy deployment.

## Features

- **FastAPI based:** High performance and easy-to-use API.
- **Asynchronous Sending:** Uses `BackgroundTasks` to send emails without blocking the response.
- **Templating:** HTML email support using **Jinja2** templates.
- **Dockerized:** Ready-to-use `Dockerfile` and `docker-compose.yml`.
- **Dev & Prod Ready:** Includes **Mailhog** configuration for local development (capturing emails) and easy switch to real SMTP (Gmail, AWS SES, SendGrid) via environment variables.

## Tech Stack

- Python 3.10
- FastAPI & Uvicorn
- FastAPI-Mail
- Docker & Docker Compose

## Installation & Setup

### 1. Clone the repository

```bash
git clone https://github.com/baloghk/email-service.git
cd email-service
```

### 2. Environment Configuration

The project uses environment variables for configuration. A template file is provided.

Copy the example file:

```bash
cp .env.example .env
```

Open `.env` and configure your settings.

**For Local Development (Mailhog):**

You don't need to change anything if using the default docker-compose setup.

```
MAIL_SERVER=mailhog
MAIL_PORT=1025
MAIL_USERNAME=
MAIL_PASSWORD=
MAIL_SSL_TLS=False
MAIL_STARTTLS=False
USE_CREDENTIALS=False
```

**For Production (e.g., Gmail):**

```
MAIL_SERVER=smtp.gmail.com
MAIL_PORT=587
MAIL_USERNAME=your.email@gmail.com
MAIL_PASSWORD=your_app_password
MAIL_SSL_TLS=False
MAIL_STARTTLS=True
USE_CREDENTIALS=True
```

### 3. Run with Docker (Recommended)

Start the application and the Mailhog service (if configured):

```bash
docker-compose up --build
```

**API URL:** http://localhost:8000

**Mailhog UI:** http://localhost:8025 (If running locally)

## API Documentation

You can access the interactive API documentation and test endpoints using Swagger UI at **http://localhost:8000/docs**. This provides a user-friendly interface to explore all available endpoints, view request/response schemas, and test API calls directly.

### Health Check

**GET** `/`

Returns the status of the service.

```json
{
  "status": "healthy",
  "service": "EmailService",
  "version": "1.0.0"
}
```

### Send Email

**POST** `/send`

Sends an email using a specific template.

**Request Body:**

```json
{
  "emails": ["recipient@example.com"],
  "subject": "Welcome!",
  "template_name": "test",
  "template_body": {
    "name": "Meszaros Lorinc",
    "message": "This is a dynamic variable passed to the template."
  }
}
```

**Parameters:**

- `template_name`: The name of the HTML file in `src/templates` (without `.html` extension).
- `template_body`: Dictionary of variables to inject into the Jinja2 template.

**Example cURL Request:**

```bash
curl -X POST "http://localhost:8000/send" \
     -H "Content-Type: application/json" \
     -d '{
           "emails": ["user@example.com"],
           "subject": "Test Email",
           "template_name": "test",
           "template_body": {
             "name": "Developer",
             "message": "Testing from cURL!"
           }
         }'
```