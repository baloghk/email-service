from fastapi_mail import FastMail, MessageSchema, MessageType, ConnectionConfig
from cryptography.fernet import Fernet
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
import aio_pika
import asyncio
import json
from pydantic import ValidationError
from src.models import EmailQueuePayload
import os
from pathlib import Path

from src.database import engine
from src.models import Tenant, ProcessedEmailMessage

RABBITMQ_URL = os.getenv("RABBITMQ_URL", "amqp://guest:guest@rabbitmq:5672/")
ENCRYPTION_KEY = os.getenv("ENCRYPTION_KEY")

async def get_tenant(session: AsyncSession, tenant_id: int):
    return await session.get(Tenant, tenant_id)

async def is_already_processed(session: AsyncSession, message_id: str) -> bool:
    stmt = select(ProcessedEmailMessage).where(
        ProcessedEmailMessage.message_id == message_id
    )
    result = await session.exec(stmt)
    return result.first() is not None

async def process_email(message: aio_pika.IncomingMessage):
    async with message.process(requeue=False):
        attachment_files: list[Path] = []
        try:
            payload_dict  = json.loads(message.body.decode("utf-8"))
            try:
                payload = EmailQueuePayload.model_validate(payload_dict)
            except ValidationError as e:
                print("Invalid queue message schema:", e)
                return

            message_id = payload.message_id
            tenant_id = payload.tenant_id
            email_data = payload.email

            print(f"[{message_id}] Processing email for tenant {tenant_id}")

            async with AsyncSession(engine) as session:
                
                if await is_already_processed(session, message_id):
                    print(f"[{message_id}] Duplicate message detected, skipping")
                    return

                tenant = await get_tenant(session, tenant_id)
                
                if not tenant:
                    print(f"[{message_id}] Tenant not found")
                    return

                try:
                    cipher = Fernet(ENCRYPTION_KEY)
                    mail_password = cipher.decrypt(
                        tenant.mail_password.encode()
                    ).decode()
                except Exception as e:
                    print(f"[{message_id}] Decryption failed: {e}")
                    raise

                conf = ConnectionConfig(
                    MAIL_USERNAME=tenant.mail_username,
                    MAIL_PASSWORD=mail_password,
                    MAIL_FROM=tenant.mail_from,
                    MAIL_PORT=tenant.mail_port,
                    MAIL_SERVER=tenant.mail_server,
                    MAIL_STARTTLS=tenant.mail_starttls,
                    MAIL_SSL_TLS=tenant.mail_ssl_tls,
                    USE_CREDENTIALS=tenant.use_credentials,
                    VALIDATE_CERTS=tenant.validate_certs,
                    TEMPLATE_FOLDER="/app/src/templates" if os.path.exists("/app/src/templates") else "/app/templates"
                )

                attachments_to_send = []
                if "attachments" in email_data and email_data["attachments"]:
                    for att in email_data["attachments"]:
                        file_path = Path(att["path"])
                        
                        if file_path.exists():
                            attachments_to_send.append(str(file_path))
                            
                            attachment_files.append(file_path)
                            
                            print(f"[{message_id}] Attachment added: {att['filename']} from {file_path}")
                        else:
                            print(f"[{message_id}] Attachment file not found: {file_path}")

                email = MessageSchema(
                    subject=email_data["subject"],
                    recipients=email_data["emails"],
                    template_body=email_data.get("template_body", {}),
                    subtype=MessageType.html,
                    attachments=attachments_to_send if attachments_to_send else []
                )

                fm = FastMail(conf)
                await fm.send_message(
                    email,
                    template_name=email_data["template_file"]
                )

                processed = ProcessedEmailMessage(
                    message_id=message_id,
                    status="SUCCESS"
                )
                session.add(processed)
                await session.commit()

                print(f"[{message_id}] Email sent successfully with {len(attachments_to_send)} attachment(s)")

                for file_path in attachment_files:
                    try:
                        file_path.unlink()
                        print(f"[{message_id}] Attachment deleted: {file_path}")
                    except Exception as e:
                        print(f"[{message_id}] Failed to delete attachment {file_path}: {e}")
        
        except Exception as e:
            print(f"Error processing message: {e}")
            import traceback
            traceback.print_exc()
            
            for file_path in attachment_files:
                try:
                    if file_path.exists():
                        file_path.unlink()
                        print(f"Attachment deleted after error: {file_path}")
                except Exception as cleanup_error:
                    print(f"Failed to cleanup attachment {file_path}: {cleanup_error}")

async def main():
    while True:
        try:
            connection = await aio_pika.connect_robust(RABBITMQ_URL)
            break
        except Exception as e:
            print(f"Waiting for RabbitMQ... ({e})")
            await asyncio.sleep(5)

    queue_name = "email_queue"

    async with connection:
        channel = await connection.channel()
        await channel.set_qos(prefetch_count=5)
        
        queue = await channel.declare_queue(queue_name, durable=True)
        print('Worker waiting for messages...')
        await queue.consume(process_email)
        
        await asyncio.Future()

if __name__ == "__main__":
    asyncio.run(main())