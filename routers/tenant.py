from typing import List, Optional
from fastapi import APIRouter, Depends, status, HTTPException
from pydantic import BaseModel, EmailStr
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from database import get_db
from models.tenant import Tenant, APIKey
from utils.security import generate_raw_api_key
from utils.exceptions import AppError

router = APIRouter()

class RegisterTenantRequest(BaseModel):
    name: str
    email: EmailStr
    tier: Optional[str] = "free"

class CreateAPIKeyRequest(BaseModel):
    name: Optional[str] = "Default Key"
    rate_limit_rpm: Optional[int] = 60

@router.post("/register", status_code=status.HTTP_201_CREATED)
async def register_tenant(
    body: RegisterTenantRequest,
    db: AsyncSession = Depends(get_db)
):
    """Register a new B2B API organization/tenant (Free plan enabled by default)."""
    # Check if email exists
    existing = await db.execute(select(Tenant).where(Tenant.email == body.email))
    if existing.scalar_one_or_none():
        raise AppError(
            status_code=status.HTTP_400_BAD_REQUEST,
            error_code="EMAIL_EXISTS",
            message="A tenant with this email already exists."
        )

    tenant = Tenant(
        name=body.name,
        email=body.email,
        tier=body.tier or "free",
        monthly_quota=1000  # 1,000 free generations per month
    )
    db.add(tenant)
    await db.commit()
    await db.refresh(tenant)

    # Automatically generate first API Key
    raw_key, key_prefix, key_hash = generate_raw_api_key(environment="live")
    api_key_obj = APIKey(
        tenant_id=tenant.id,
        name="Initial API Key",
        key_prefix=key_prefix,
        key_hash=key_hash,
        rate_limit_rpm=60
    )
    db.add(api_key_obj)
    await db.commit()

    return {
        "tenant": tenant.to_dict(),
        "api_key": {
            "id": api_key_obj.id,
            "name": api_key_obj.name,
            "raw_key": raw_key,  # Note: Displayed ONLY once upon creation!
            "key_prefix": key_prefix,
            "warning": "Make sure to copy your secret API key now. You won't be able to see it again!"
        }
    }

@router.post("/{tenant_id}/api-keys", status_code=status.HTTP_201_CREATED)
async def create_api_key(
    tenant_id: str,
    body: CreateAPIKeyRequest,
    db: AsyncSession = Depends(get_db)
):
    """Create a new API key for an existing tenant."""
    result = await db.execute(select(Tenant).where(Tenant.id == tenant_id))
    tenant = result.scalar_one_or_none()
    if not tenant:
        raise AppError(
            status_code=status.HTTP_44_NOT_FOUND,
            error_code="TENANT_NOT_FOUND",
            message="Tenant not found."
        )

    raw_key, key_prefix, key_hash = generate_raw_api_key(environment="live")
    api_key_obj = APIKey(
        tenant_id=tenant.id,
        name=body.name,
        key_prefix=key_prefix,
        key_hash=key_hash,
        rate_limit_rpm=body.rate_limit_rpm
    )
    db.add(api_key_obj)
    await db.commit()
    await db.refresh(api_key_obj)

    return {
        "api_key": {
            "id": api_key_obj.id,
            "name": api_key_obj.name,
            "raw_key": raw_key,
            "key_prefix": key_prefix,
            "warning": "Make sure to copy your secret API key now. You won't be able to see it again!"
        }
    }

@router.get("/{tenant_id}/api-keys")
async def list_api_keys(
    tenant_id: str,
    db: AsyncSession = Depends(get_db)
):
    """List all active API keys for a tenant."""
    result = await db.execute(select(APIKey).where(APIKey.tenant_id == tenant_id))
    keys = result.scalars().all()
    return {"api_keys": [k.to_dict() for k in keys]}

@router.delete("/{tenant_id}/api-keys/{key_id}")
async def revoke_api_key(
    tenant_id: str,
    key_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Revoke an API key."""
    result = await db.execute(select(APIKey).where(APIKey.id == key_id, APIKey.tenant_id == tenant_id))
    key_obj = result.scalar_one_or_none()
    if not key_obj:
        raise AppError(
            status_code=status.HTTP_404_NOT_FOUND,
            error_code="KEY_NOT_FOUND",
            message="API Key not found."
        )

    key_obj.is_active = False
    await db.commit()
    return {"message": "API key revoked successfully."}

@router.get("/{tenant_id}/usage")
async def get_tenant_usage(
    tenant_id: str,
    db: AsyncSession = Depends(get_db)
):
    """Retrieve current usage statistics and free tier quota for a tenant."""
    result = await db.execute(select(Tenant).where(Tenant.id == tenant_id))
    tenant = result.scalar_one_or_none()
    if not tenant:
        raise AppError(
            status_code=status.HTTP_404_NOT_FOUND,
            error_code="TENANT_NOT_FOUND",
            message="Tenant not found."
        )

    return {
        "tenant_id": tenant.id,
        "name": tenant.name,
        "tier": tenant.tier,
        "monthly_quota": tenant.monthly_quota,
        "quota_remaining": tenant.monthly_quota,
        "pricing": "Free ($0.00)" if tenant.tier in ["starter", "free"] else f"{tenant.tier.capitalize()} Tier"
    }


