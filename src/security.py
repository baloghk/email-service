from fastapi import HTTPException, Security, status, Depends
from fastapi.security import APIKeyHeader
from fastapi_mail import ConnectionConfig
from sqlmodel import select
from sqlmodel.ext.asyncio.session import AsyncSession
from pathlib import Path

from src.database import get_session
from src.models import Tenant
from src.utils import decrypt_data

api_key_header = APIKeyHeader(name="X-API-KEY", auto_error=False)

BASE_DIR = Path(__file__).resolve().parent 
TEMPLATE_FOLDER = BASE_DIR / "templates"

async def get_tenant_config(
    api_key: str = Security(api_key_header),
    session: AsyncSession = Depends(get_session)
) -> ConnectionConfig:
    
    if not api_key:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Missing API Key (X-API-KEY header)"
        )

    statement = select(Tenant).where(Tenant.api_key == api_key)
    result = await session.exec(statement)
    tenant = result.first()

    if not tenant:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail="Invalid API Key"
        )
    
    real_password = decrypt_data(tenant.mail_password)

    return ConnectionConfig(
        MAIL_USERNAME=tenant.mail_username,
        MAIL_PASSWORD=real_password,
        MAIL_FROM=tenant.mail_from,
        MAIL_PORT=tenant.mail_port,
        MAIL_SERVER=tenant.mail_server,
        MAIL_FROM_NAME=tenant.name,
        MAIL_STARTTLS=tenant.mail_starttls,
        MAIL_SSL_TLS=tenant.mail_ssl_tls,
        USE_CREDENTIALS=tenant.use_credentials,
        VALIDATE_CERTS=tenant.validate_certs,
        TEMPLATE_FOLDER=TEMPLATE_FOLDER
    )