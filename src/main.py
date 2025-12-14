import os
from pathlib import Path
from fastapi import FastAPI, BackgroundTasks, HTTPException
from fastapi_mail import FastMail, MessageSchema, ConnectionConfig, MessageType
from pydantic import BaseModel, EmailStr
from typing import Dict, List, Any
from dotenv import load_dotenv
import uvicorn

load_dotenv()

app = FastAPI(
    title="Email Microservice",
    description="Microservice for sending templated emails via SMTP",
    version="1.0.0"
)

BASE_DIR = Path(__file__).resolve().parent
TEMPLATE_FOLDER = BASE_DIR / "templates"

conf = ConnectionConfig(
    MAIL_USERNAME=os.getenv("MAIL_USERNAME", ""),
    MAIL_PASSWORD=os.getenv("MAIL_PASSWORD", ""),
    MAIL_FROM=os.getenv("MAIL_FROM", "test@example.com"),
    MAIL_PORT=int(os.getenv("MAIL_PORT", 1025)),
    MAIL_SERVER=os.getenv("MAIL_SERVER", "localhost"),
    MAIL_FROM_NAME=os.getenv("MAIL_FROM_NAME", "Example App"),
    MAIL_STARTTLS=os.getenv("MAIL_STARTTLS") == "True",
    MAIL_SSL_TLS=os.getenv("MAIL_SSL_TLS") == "True",
    USE_CREDENTIALS=os.getenv("USE_CREDENTIALS") == "True",
    VALIDATE_CERTS=os.getenv("VALIDATE_CERTS") == "True",
    TEMPLATE_FOLDER=TEMPLATE_FOLDER
)

class EmailRequest(BaseModel):
    emails: List[EmailStr]
    subject: str
    template_name: str
    template_body: Dict[str, Any]

@app.get("/")
def health_check():
    return {
        "status": "healthy",
        "service": "EmailService",
        "version": "1.0.0"
    }

@app.post("/send")
async def send_email(email_req: EmailRequest, background_tasks: BackgroundTasks):
    
    template_file = f"{email_req.template_name}.html"
    
    message = MessageSchema(
        subject=email_req.subject,
        recipients=email_req.emails,
        template_body=email_req.template_body,
        subtype=MessageType.html
    )

    fm = FastMail(conf)

    try:
        background_tasks.add_task(fm.send_message, message, template_name=template_file)
        return {"message": "Email sending is in progress..", "recipients": email_req.emails}
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))

if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)