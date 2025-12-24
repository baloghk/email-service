from fastapi import FastAPI, Depends, HTTPException, File, UploadFile, Form
from contextlib import asynccontextmanager
from sqlmodel.ext.asyncio.session import AsyncSession
from sqlalchemy import text
from typing import List, Optional
import aio_pika
import json
import os
import uuid
from pathlib import Path

from src.database import engine
from src.security import get_current_tenant
from src.models import Tenant
from src.producer import publish_email_task
from src.rabbitmq import connect_rabbitmq, get_connection

MEDIA_DIR = Path("/app/media/attachments")
MEDIA_DIR.mkdir(parents=True, exist_ok=True)

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
async def send_email_with_attachments(
    emails: str = Form(...),
    subject: str = Form(...),
    template_name: str = Form(...),
    template_body: str = Form(...),
    attachments: Optional[List[UploadFile]] = File(None),
    tenant: Tenant = Depends(get_current_tenant),
    connection: aio_pika.Connection = Depends(get_connection)
):
    
    if not tenant.is_active:
        raise HTTPException(status_code=403, detail="Tenant is inactive")
    
    try:
        emails_list = json.loads(emails)
        template_body_dict = json.loads(template_body)
    except json.JSONDecodeError as e:
        raise HTTPException(status_code=400, detail=f"Invalid JSON format: {str(e)}")
    
    attachment_paths = []
    if attachments:
        print(f"Received {len(attachments)} attachment(s)")
        for file in attachments:
            print(f"Processing file: {file.filename}, content_type: {file.content_type}")
            
            file_extension = Path(file.filename).suffix
            unique_filename = f"{uuid.uuid4()}{file_extension}"
            file_path = MEDIA_DIR / unique_filename
            
            content = await file.read()
            with open(file_path, "wb") as f:
                f.write(content)
            
            print(f"Saved to: {file_path} (exists: {file_path.exists()})")
            
            attachment_paths.append({
                "path": str(file_path),
                "filename": str(file.filename),
                "content_type": str(file.content_type or "application/octet-stream")
            })
            
            print(f"Attachment saved: {file.filename} -> {file_path} ({len(content)} bytes)")
    else:
        print("No attachments received")
    
    email_data = {
        "emails": emails_list,
        "subject": subject,
        "template_name": template_name,
        "template_body": template_body_dict,
        "template_file": f"{template_name}.html",
        "attachments": attachment_paths
    }
    
    await publish_email_task(connection, tenant.id, email_data)
    
    return {
        "message": "Email queued successfully",
        "status": "queued",
        "attachment_count": len(attachment_paths)
    }