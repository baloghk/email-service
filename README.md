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

The project uses environment variables primarily for the database connection. Copy the example file:

```bash
cp .env.example .env
```

Open `.env` and ensure the database settings are correct. The defaults work out-of-the-box with the provided `docker-compose.yml`:

```env
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=email_db
INIT_DB=True
DATABASE_URL=postgresql+asyncpg://postgres:postgres@db:5432/email_db
```

### 3. Run with Docker

Start the application, database, and Mailhog:

```bash
docker-compose up --build
```

- **API URL:** http://localhost:8000
- **Mailhog UI:** http://localhost:8025
- **Swagger UI:** http://localhost:8000/docs

### 4. Create a Tenant (Crucial Step!)

Since configurations are stored in the database, you must create a tenant to send emails. Access the database shell:

```bash
docker exec -it email_db psql -U postgres -d email_db
```

Insert a test tenant configured for Mailhog:

```sql
INSERT INTO tenant (name, api_key, mail_username, mail_password, mail_from, mail_port, mail_server, mail_starttls, mail_ssl_tls, use_credentials, validate_certs)
VALUES ('Dev Tenant', 'my-secret-api-key', '', '', 'test@example.com', 1025, 'mailhog', false, false, false, false);
```

> **Note:** If you want to use Gmail or another provider, replace the values (port 587, `smtp.gmail.com`, etc.) and set `use_credentials` to `true`.

## API Documentation

Access the interactive API documentation at http://localhost:8000/docs

### Authentication

This service uses header-based authentication. You must provide the correct API Key in the header for every request to `/emails`:

| Header | Value |
|--------|-------|
| `X-API-KEY` | The key stored in the database (e.g., `my-secret-api-key`) |

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