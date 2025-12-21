from fastapi import HTTPException, Security, Depends
from fastapi.security import APIKeyHeader
from sqlmodel import select, Session
from pathlib import Path

from src.database import get_session
from src.models import Tenant
from src.utils import decrypt_data

api_key_header = APIKeyHeader(name="X-API-KEY", auto_error=False)

BASE_DIR = Path(__file__).resolve().parent 
TEMPLATE_FOLDER = BASE_DIR / "templates"

async def get_current_tenant(
    api_key: str = Security(api_key_header), 
    session: Session = Depends(get_session)
) -> Tenant:
    
    if not api_key:
        raise HTTPException(status_code=403, detail="Could not validate credentials")
    
    statement = select(Tenant).where(Tenant.api_key == api_key)
    result = await session.exec(statement)
    tenant = result.first()

    if not tenant:
        raise HTTPException(status_code=403, detail="Invalid API Key")
        
    return tenant