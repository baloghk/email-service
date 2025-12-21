from fastapi import FastAPI, Depends, HTTPException
from contextlib import asynccontextmanager
import aio_pika
import os

from src.database import init_db
from src.security import get_current_tenant
from src.models import EmailRequest, Tenant
from src.producer import publish_email_task

rabbitmq_connection = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    if os.getenv("INIT_DB", "False") == "True":
        await init_db()
    
    global rabbitmq_connection
    print("Connecting to RabbitMQ...")
    try:
        rabbitmq_url = os.getenv("RABBITMQ_URL", "amqp://guest:guest@rabbitmq:5672/")
        rabbitmq_connection = await aio_pika.connect_robust(rabbitmq_url)
        print("RabbitMQ Connected!")
    except Exception as e:
        print(f"RabbitMQ Connection Failed: {e}")

    yield

    if rabbitmq_connection:
        await rabbitmq_connection.close()
        print("RabbitMQ Connection Closed.")

app = FastAPI(title="Email Microservice", lifespan=lifespan)

async def get_rabbitmq():
    if rabbitmq_connection is None:
        raise HTTPException(status_code=503, detail="RabbitMQ not available")
    return rabbitmq_connection

@app.post("/emails")
async def send_email(
    email_req: EmailRequest, 
    tenant: Tenant = Depends(get_current_tenant),
    connection: aio_pika.Connection = Depends(get_rabbitmq)
):
    if not tenant.is_active:
        raise HTTPException(status_code=403, detail="Tenant is inactive")

    email_data = email_req.dict() 
    email_data['template_file'] = f"{email_req.template_name}.html"

    await publish_email_task(connection, tenant.id, email_data)
    
    return {"message": "Email queued successfully", "status": "queued"}