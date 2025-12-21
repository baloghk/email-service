from fastapi import FastAPI, BackgroundTasks, Depends
from fastapi_mail import FastMail, MessageSchema, MessageType, ConnectionConfig
from contextlib import asynccontextmanager
import uvicorn
import os

from src.database import init_db
from src.security import get_tenant_config
from src.models import EmailRequest

@asynccontextmanager
async def lifespan(app: FastAPI):
    if os.getenv("INIT_DB", "False") == "True":
        await init_db()
    yield

app = FastAPI(
    title="Email Microservice",
    lifespan=lifespan
)

@app.get("/")
def health_check():
    return {"status": "healthy", "service": "email-service"}

@app.post("/emails")
async def send_email(
    email_req: EmailRequest, 
    background_tasks: BackgroundTasks,
    config: ConnectionConfig = Depends(get_tenant_config)
):
    
    template_file = f"{email_req.template_name}.html"
    
    message = MessageSchema(
        subject=email_req.subject,
        recipients=email_req.emails,
        template_body=email_req.template_body,
        subtype=MessageType.html
    )

    fm = FastMail(config)
    
    background_tasks.add_task(fm.send_message, message, template_name=template_file)
    
    return {"message": "Email sending is in progress..."}

if __name__ == "__main__":
    uvicorn.run("src.main:app", host="0.0.0.0", port=8000, reload=True)