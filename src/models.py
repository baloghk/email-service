from typing import Optional, List, Dict, Any
from sqlmodel import SQLModel, Field
from pydantic import BaseModel, EmailStr
from datetime import datetime

class Tenant(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    name: str
    api_key: str = Field(index=True, unique=True)
    mail_username: str
    mail_password: str
    mail_from: str
    mail_port: int
    mail_server: str
    mail_starttls: bool = True
    mail_ssl_tls: bool = False
    use_credentials: bool = True
    validate_certs: bool = True
    is_active: bool = True


class EmailRequest(BaseModel):
    emails: List[EmailStr]
    subject: str
    template_name: str
    template_body: Dict[str, Any]


class ProcessedEmailMessage(SQLModel, table=True):
    message_id: str = Field(primary_key=True, index=True)
    processed_at: datetime = Field(default_factory=datetime.utcnow)
    status: str

class AttachmentDTO(BaseModel):
    path: str
    filename: str
    content_type: Optional[str] = "application/octet-stream"


class EmailQueuePayload(BaseModel):
    message_id: str
    tenant_id: int
    email: Dict[str, Any]