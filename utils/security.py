import secrets
import hashlib
from datetime import datetime
from typing import Optional, Tuple
from fastapi import Security, HTTPException, status, Depends
from fastapi.security.api_key import APIKeyHeader
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database import get_db
from models.tenant import APIKey, Tenant
from utils.exceptions import AppError

API_KEY_HEADER = APIKeyHeader(name="X-API-Key", auto_error=False)

def generate_raw_api_key(environment: str = "live") -> Tuple[str, str, str]:
    """
    Generates a secure random API Key.
    Returns (raw_key, key_prefix, key_hash)
    Example raw key: qg_live_8f3a91b2c4e5f6a7b8c9d0e1f2a3b4c5
    """
    random_hex = secrets.token_hex(20)
    raw_key = f"qg_{environment}_{random_hex}"
    key_prefix = raw_key[:12]
    key_hash = hashlib.sha256(raw_key.encode("utf-8")).hexdigest()
    return raw_key, key_prefix, key_hash

def hash_api_key(raw_key: str) -> str:
    """Hashes a raw API key string using SHA-256."""
    return hashlib.sha256(raw_key.encode("utf-8")).hexdigest()

async def get_current_tenant(
    api_key_header: Optional[str] = Security(API_KEY_HEADER),
    db: AsyncSession = Depends(get_db)
) -> Tenant:
    """
    FastAPI dependency to validate X-API-Key header against active tenants in DB.
    """
    if not api_key_header:
        raise AppError(
            status_code=status.HTTP_401_UNAUTHORIZED,
            error_code="MISSING_API_KEY",
            message="X-API-Key header is missing from request."
        )

    hashed_key = hash_api_key(api_key_header.strip())
    
    # Query API key and join Tenant
    stmt = select(APIKey).where(
        APIKey.key_hash == hashed_key,
        APIKey.is_active == True
    )
    result = await db.execute(stmt)
    api_key_obj = result.scalar_one_or_none()

    if not api_key_obj:
        raise AppError(
            status_code=status.HTTP_401_UNAUTHORIZED,
            error_code="INVALID_API_KEY",
            message="Provided API Key is invalid or inactive."
        )

    # Fetch associated Tenant
    tenant_stmt = select(Tenant).where(
        Tenant.id == api_key_obj.tenant_id,
        Tenant.is_active == True
    )
    tenant_result = await db.execute(tenant_stmt)
    tenant = tenant_result.scalar_one_or_none()

    if not tenant:
        raise AppError(
            status_code=status.HTTP_403_FORBIDDEN,
            error_code="TENANT_INACTIVE",
            message="The organization associated with this API key is inactive."
        )

    # Update last_used_at timestamp
    api_key_obj.last_used_at = datetime.utcnow()
    await db.commit()

    return tenant
