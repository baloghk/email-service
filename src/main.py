from fastapi import FastAPI, Depends, HTTPException
from contextlib import asynccontextmanager
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy import text
import aio_pika

from src.database import engine
from src.security import get_current_tenant
from src.models import EmailRequest, Tenant
from src.producer import publish_email_task
from src.rabbitmq import connect_rabbitmq, get_connection

@asynccontextmanager
async def lifespan(app: FastAPI):
    await connect_rabbitmq()
    yield
    try:
        connection = get_connection()
        await connection.close()
    except RuntimeError:
        pass

app = FastAPI(title="Email Microservice", lifespan=lifespan)

@app.get("/health")
async def health_check():
    status = {
        "database": {"status": "unknown"},
        "rabbitmq": {"status": "unknown", "queue_length": None},
    }

    try:
        async with AsyncSession(engine) as session:
            await session.exec(text("SELECT 1"))
        status["database"]["status"] = "ok"
    except Exception as e:
        print(f"DB Health Check Error: {e}")
        status["database"]["status"] = "error"

    try:
        rmq_conn = get_connection()
        
        if not rmq_conn.is_closed:
            status["rabbitmq"]["status"] = "ok"
            try:
                async with rmq_conn.channel() as channel:
                    queue = await channel.declare_queue("email_queue", passive=True)
                    status["rabbitmq"]["queue_length"] = queue.declaration_result.message_count
            
            except aio_pika.exceptions.ChannelClosed as e:
                print(f"RabbitMQ Queue Error (Not Found): {e}")
                status["rabbitmq"]["queue_length"] = "error: queue not found"
            
            except Exception as e:
                print(f"RabbitMQ General Error: {e}")
                status["rabbitmq"]["queue_length"] = f"error: {str(e)}"
        else:
            status["rabbitmq"]["status"] = "closed"
            
    except RuntimeError:
        status["rabbitmq"]["status"] = "error (not connected)"

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