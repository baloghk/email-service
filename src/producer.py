import aio_pika
import json
import uuid


async def publish_email_task(connection, tenant_id: int, email_req_data: dict):
    message_id = str(uuid.uuid4())

    payload = {
        "message_id": message_id,
        "tenant_id": tenant_id,
        "email": email_req_data
    }

    body = json.dumps(payload).encode("utf-8")

    async with connection.channel() as channel:
        await channel.default_exchange.publish(
            aio_pika.Message(
                body=body,
                message_id=message_id,
                content_type="application/json",
                delivery_mode=aio_pika.DeliveryMode.PERSISTENT,
            ),
            routing_key="email_queue"
        )

    print(f"Email task queued (JSON): {message_id}")
    return message_id
