# Email Microservice

A robust, asynchronous, **multi-tenant** microservice for sending templated emails using **Python**, **FastAPI**, and **PostgreSQL**. Containerized with **Docker** for easy deployment.

## Features

- **FastAPI based** — High performance and easy-to-use API
- **Multi-Tenancy** — Supports multiple clients/configurations via API Keys stored in a database
- **Database Backed** — Configuration (SMTP credentials) is securely stored in PostgreSQL
- **Asynchronous Sending** — Uses `BackgroundTasks` to send emails without blocking the response
- **Templating** — HTML email support using **Jinja2** templates
- **Dockerized** — Ready-to-use `Dockerfile` and `docker-compose.yml`
- **Dev & Prod Ready** — Configured for Mailhog (local) or real SMTP providers (Gmail, AWS SES, etc.)

## Tech Stack

- **Core:** Python 3.10, FastAPI, Uvicorn
- **Database:** PostgreSQL, SQLModel, AsyncPG
- **Email:** FastAPI-Mail
- **Infrastructure:** Docker & Docker Compose

## Installation & Setup

### 1. Clone the Repository

```bash
git clone https://github.com/baloghk/email-service.git
cd email-service
```

### 2. Environment Configuration

The project uses environment variables for database setup. Copy the example file:

```bash
cp .env.example .env
```

Open `.env` and configure your settings:

```env
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=email_db
INIT_DB=True
DATABASE_URL=postgresql+asyncpg://postgres:postgres@localhost:5432/email_db
```

When running with Docker Compose, the `DATABASE_URL` is automatically overridden to use the Docker service name (`db` instead of `localhost`).

### 3. Run with Docker

Start the application, database, and Mailhog:

```bash
docker-compose up --build
```

The setup includes:
- **Application Container:** Runs FastAPI application at http://localhost:8000
- **PostgreSQL Container:** Database available at `localhost:5432` (user: `postgres`, password: `postgres`)
- **Mailhog Container:** SMTP server at `localhost:1025` and UI at http://localhost:8025

After startup, the database will automatically initialize tables if `INIT_DB=True`.

### 4. Configure Client Credentials

The service requires client credentials to send emails. You'll need to set up a configuration entry in the database with:

- A unique API key for authentication
- SMTP server credentials (server, port, username, password)
- Sender email address
- TLS/SSL settings

Contact your administrator to set up your client credentials, or use the management API to register a new configuration.

Once configured, you'll receive an API key to authenticate your requests.

### 5. Verify the Setup

- **API Docs:** http://localhost:8000/docs
- **Health Check:** http://localhost:8000/
- **Mailhog UI:** http://localhost:8025

## API Documentation

Access the interactive API documentation at http://localhost:8000/docs

### Authentication

All requests to the email endpoint require API key authentication via the `X-API-KEY` header:

| Header | Value |
|--------|-------|
| `X-API-KEY` | Your assigned API key (e.g., `my-secret-api-key`) |

## Endpoints

### Health Check

```
GET /
```

Returns the status of the service.

### Send Emails

```
POST /emails
```

Sends an email to a list of recipients using a specific template.

**Headers:**
```
X-API-KEY: my-secret-api-key
```

**Request Body:**
```json
{
  "emails": ["recipient@example.com"],
  "subject": "Welcome!",
  "template_name": "test",
  "template_body": {
    "name": "John Doe",
    "message": "This is a dynamic variable passed to the template."
  }
}
```

**Parameters:**

- `emails` — List of recipient email addresses
- `subject` — Email subject line
- `template_name` — The name of the HTML file in `src/templates` (without `.html` extension)
- `template_body` — Dictionary of variables to inject into the Jinja2 template

**Example cURL Request:**

```bash
curl -X POST "http://localhost:8000/emails" \
     -H "Content-Type: application/json" \
     -H "X-API-KEY: my-secret-api-key" \
     -d '{
           "emails": ["user@example.com"],
           "subject": "Test Email via DB Config",
           "template_name": "test",
           "template_body": {
             "name": "Developer",
             "message": "Testing multi-tenancy!"
           }
         }'
```