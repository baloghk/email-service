# Email Microservice

A robust, asynchronous, **multi-tenant** microservice for sending templated emails using **Python**, **FastAPI**, and **PostgreSQL**. Containerized with **Docker** for easy deployment.

## Features

- **FastAPI based** — High performance and easy-to-use API
- **Multi-Tenancy** — Supports multiple clients/configurations via API Keys stored in a database
- **Database Backed** — Configuration (SMTP credentials) is securely stored in PostgreSQL
- **Queue-Based Architecture** — Uses **RabbitMQ** for reliable, asynchronous email processing
- **Scalable Worker Service** — Separate worker containers handle email sending independently with idempotency and error recovery
- **File Attachments** — Upload and attach files to emails (stored in `/app/media/attachments`, auto-cleaned after sending)
- **Message Deduplication** — Prevents duplicate email sending with processed message tracking
- **Health Monitoring** — Built-in health checks for database, RabbitMQ, and queue status
- **Templating** — HTML email support using **Jinja2** templates
- **Dockerized** — Ready-to-use `Dockerfile` and `docker-compose.yml` (development and production)
- **Dev & Prod Ready** — Configured for Mailhog (local) or real SMTP providers (Gmail, AWS SES, etc.)

## Tech Stack

- **Core:** Python 3.10, FastAPI, Uvicorn
- **Database:** PostgreSQL, SQLModel, AsyncPG
- **Message Queue:** RabbitMQ with aio-pika
- **Email:** FastAPI-Mail
- **Infrastructure:** Docker & Docker Compose

## Installation & Setup

### 1. Clone the Repository

```bash
git clone https://github.com/baloghk/email-service.git
cd email-service
```

### 2. Environment Configuration

The project uses environment variables for database and service setup. Copy the example file:

```bash
cp .env.example .env
```

Open `.env` and configure your settings for **development** (with Mailhog):

```env
INIT_DB=True
ENCRYPTION_KEY=your-secret-encryption-key-here
RABBITMQ_USER=guest
RABBITMQ_PASSWORD=guest
POSTGRES_USER=postgres
POSTGRES_PASSWORD=postgres
POSTGRES_DB=email_db
```

For **production**, you'll need to provide actual SMTP credentials and RabbitMQ configuration:

```env
INIT_DB=False
ENCRYPTION_KEY=your-secret-encryption-key-here
DATABASE_URL=postgresql+asyncpg://postgres:password@db:5432/email_db
RABBITMQ_URL=amqp://user:password@rabbitmq:5672/
POSTGRES_USER=postgres
POSTGRES_PASSWORD=secure-password
POSTGRES_DB=email_db
RABBITMQ_USER=rabbitmq_user
RABBITMQ_PASSWORD=rabbitmq_password
IMAGE_NAME=your-registry/email-service
```

When running with Docker Compose (development), the `DATABASE_URL` and `RABBITMQ_URL` are automatically configured to use the Docker service names.

### 3. Run with Docker

**Development Setup** (with Mailhog for testing):

```bash
docker-compose up --build
```

**Production Setup** (with external SMTP providers):

```bash
docker-compose -f docker-compose.prod.yml up --build
```

**Development Services:**
- **API Container:** FastAPI application at http://localhost:8000
- **Worker Container:** Processes queued email tasks
- **PostgreSQL Container:** Database on port `5433` (user: `postgres`, password: `postgres`)
- **RabbitMQ Container:** Message queue at `localhost:5672`, Management UI at http://localhost:15672
- **Mailhog Container:** SMTP server at `localhost:1025`, Email UI at http://localhost:8025

**Production Services:**
- **API Container:** FastAPI application at port `8000`
- **Worker Container:** Processes queued email tasks
- **PostgreSQL Container:** Database on port `5432`
- **RabbitMQ Container:** Message queue at port `5672`, Management UI at port `15672`

After startup, the database will automatically initialize tables if `INIT_DB=True`.

### 4. Configure Client Credentials

The service requires client credentials to send emails. You'll need to set up a configuration entry with:

- A unique API key for authentication
- SMTP server credentials (server, port, username, password)
- Sender email address
- TLS/SSL settings
- Active status flag

### 5. Verify the Setup

- **API Docs:** http://localhost:8000/docs
- **Health Check:** http://localhost:8000/health
- **RabbitMQ Management:** http://localhost:15672 (user: `guest`, password: `guest`)
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
GET /health
```

Returns the status of the service and its dependencies (database, RabbitMQ, and queue length).

**Response:**
```json
{
  "database": {
    "status": "ok"
  },
  "rabbitmq": {
    "status": "ok",
    "queue_length": 0
  }
}
```

### Send Emails

```
POST /emails
```

Sends an email to a list of recipients using a specific template. The email request is queued for processing by the worker service. Supports optional file attachments.

**Headers:**
```
X-API-KEY: my-secret-api-key
```

**Request Body (multipart/form-data):**

- `emails` — JSON array of recipient email addresses
- `subject` — Email subject line
- `template_name` — The name of the HTML file in `src/templates` (without `.html` extension)
- `template_body` — JSON object of variables to inject into the Jinja2 template
- `attachments` — (Optional) One or more files to attach to the email

**Response:**
```json
{
  "message": "Email queued successfully",
  "status": "queued",
  "attachment_count": 0
}
```

**Example cURL Request (without attachments):**

```bash
curl -X POST "http://localhost:8000/emails" \
     -H "X-API-KEY: my-secret-api-key" \
     -F "emails=[\"user@example.com\"]" \
     -F "subject=Test Email via Queue" \
     -F "template_name=test" \
     -F "template_body={\"name\":\"Developer\",\"message\":\"Email queued for processing!\"}"
```

**Example cURL Request (with attachments):**

```bash
curl -X POST "http://localhost:8000/emails" \
     -H "X-API-KEY: my-secret-api-key" \
     -F "emails=[\"user@example.com\"]" \
     -F "subject=Email with Attachments" \
     -F "template_name=test" \
     -F "template_body={\"name\":\"Developer\"}" \
     -F "attachments=@/path/to/document.pdf" \
     -F "attachments=@/path/to/image.png"
```

The email will be queued in RabbitMQ and processed asynchronously by the worker service. Check the Mailhog UI (development) or your email provider to verify delivery.

## Message Queue Structure

The worker service consumes messages from the `email_queue` with the following structure:

```json
{
  "message_id": "unique-message-uuid",
  "tenant_id": 1,
  "email": {
    "emails": ["recipient@example.com"],
    "subject": "Email Subject",
    "template_name": "test",
    "template_body": {
      "name": "John",
      "message": "Hello!"
    },
    "template_file": "test.html",
    "attachments": [
      {
        "path": "/app/media/attachments/uuid.pdf",
        "filename": "document.pdf",
        "content_type": "application/pdf"
      }
    ]
  }
}
```

### Message Processing Features

- **Idempotency** — Messages with duplicate `message_id` are skipped to prevent duplicate emails
- **Tenant Validation** — Verifies tenant exists and retrieves SMTP configuration
- **Attachment Handling** — Attachments are validated, attached to the email, and automatically cleaned up after sending
- **Error Handling** — Failed messages are logged with full traceback; cleanup is performed on errors
- **Worker Concurrency** — Processes up to 5 messages concurrently (configurable via `prefetch_count`)

## Troubleshooting

### Common Issues

**Database connection errors**
- Ensure PostgreSQL is running and accessible at the configured `DATABASE_URL`
- Check that credentials match your `.env` configuration
- Verify `INIT_DB=True` on first run to auto-create tables

**RabbitMQ connection errors**
- Ensure RabbitMQ is running and accessible
- Verify `RABBITMQ_URL` is correct
- Check RabbitMQ credentials match your configuration
- View RabbitMQ management UI: http://localhost:15672

**Email not sending**
- Verify tenant API key is correctly configured in the database
- Check tenant is marked as `is_active = True`
- Review SMTP credentials are correct (especially `mail_password` which is encrypted)
- Check worker logs: `docker logs email_worker`
- Verify template file exists in `src/templates/`

**Attachment issues**
- Ensure `/app/media/attachments` directory exists and is writable
- Check file size limits on SMTP server
- Verify attachment content types are correct
- Files are automatically deleted after successful sending

**Message processing errors**
- Check worker is running: `docker ps | grep email_worker`
- View worker logs for detailed error messages
- Ensure `ENCRYPTION_KEY` environment variable is set correctly in worker
- Verify queue message format matches `EmailQueuePayload` schema