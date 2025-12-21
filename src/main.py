from fastapi import FastAPI, Depends, HTTPException
from contextlib import asynccontextmanager
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy.exc import SQLAlchemyError
import aio_pika
import psutil
import os

from src.database import engine
from src.security import get_current_tenant
from src.models import EmailRequest, Tenant
from src.producer import publish_email_task
from src.rabbitmq import connect_rabbitmq, get_connection

rabbitmq_connection = None

@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_rabbitmq()
    yield
    
    global rabbitmq_connection
    if rabbitmq_connection:
        await rabbitmq_connection.close()

app = FastAPI(title="Email Microservice", lifespan=lifespan)

@app.get("/health")
async def health_check():
    status = {
        "database": {"status": "unknown"},
        "rabbitmq": {"status": "unknown", "queue_length": None},
        "worker": {"status": "unknown"}
    }

    try:
        async with AsyncSession(engine) as session:
            await session.execute("SELECT 1")
        status["database"]["status"] = "ok"
    except SQLAlchemyError:
        status["database"]["status"] = "error"

    if rabbitmq_connection and not rabbitmq_connection.is_closed:
        status["rabbitmq"]["status"] = "ok"
        try:
            channel = await rabbitmq_connection.channel()
            queue = await channel.declare_queue("email_queue", passive=True)
            status["rabbitmq"]["queue_length"] = queue.message_count
        except Exception as e:
            status["rabbitmq"]["status"] = "error"
            status["rabbitmq"]["queue_length"] = None
    else:
        status["rabbitmq"]["status"] = "error"

    try:
        worker_running = any("worker" in p.name() or "src.worker" in p.cmdline() for p in psutil.process_iter())
        status["worker"]["status"] = "ok" if worker_running else "stopped"
    except ImportError:
        status["worker"]["status"] = "unknown"

    return status

@app.post("/emails")
async def send_email(
    email_req: EmailRequest, 
    tenant: Tenant = Depends(get_current_tenant),
    connection: aio_pika.Connection = Depends(get_connection)
):
    if not tenant.is_active:
        raise HTTPException(status_code=403, detail="Tenant is inactive")

    email_data = email_req.dict() 
    email_data['template_file'] = f"{email_req.template_name}.html"

    await publish_email_task(connection, tenant.id, email_data)
    
    return {"message": "Email queued successfully", "status": "queued"}