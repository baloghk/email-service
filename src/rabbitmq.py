import aio_pika
import asyncio
import os

rabbitmq_connection = None

async def connect_rabbitmq(max_retries: int = 5, delay: float = 5.0):
    global rabbitmq_connection
    rabbitmq_url = os.getenv("RABBITMQ_URL")
    if not rabbitmq_url:
        print("RABBITMQ_URL not set, skipping RabbitMQ connection")
        return

    for i in range(max_retries):
        try:
            rabbitmq_connection = await aio_pika.connect_robust(rabbitmq_url)
            print("RabbitMQ Connected!")
            return
        except Exception as e:
            print(f"RabbitMQ connect failed, attempt {i+1}/{max_retries}: {e}")
            await asyncio.sleep(delay)

    print("RabbitMQ not available after retries, continuing without connection")
    rabbitmq_connection = None

def get_connection():
    if rabbitmq_connection is None:
        raise RuntimeError("RabbitMQ not available")
    return rabbitmq_connection
